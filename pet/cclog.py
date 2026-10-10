# reading claude code's local logs for token counts, costs and stats (only numbers, never text).
import datetime
import json
import time
from collections import Counter
from pathlib import Path

from .config import CC_LOGS, CC_SCAN_SECONDS
from .storage import log_error
from .usage import parse_time


# api list prices, dollars per million tokens: (model id starts with, input, output, cache read).
# cache writes cost 1.25x input (5 minute cache) or 2x input (1 hour cache). first match wins.
# these are what the same tokens would cost on the api. on a subscription plan you don't pay them.
PRICES = [("claude-opus-5-5", 4, 20, 0.20), ("claude-opus-5", 5, 25, 0.50), ("claude-opus-4", 5, 25, 0.50),
          ("claude-fable-5-1", 10, 50, 0.25), ("claude-fable-5", 10, 50, 1.00), ("claude-mythos", 10, 50, 0.25),
          ("claude-sonnet-5", 2, 10, 0.20), ("claude-sonnet-4", 3, 15, 0.30),
          ("claude-haiku-5", 0.10, 0.50, 0.01), ("claude-haiku-4", 1, 5, 0.10)]


def answer_cost(a):
    # api-price dollars for one logged answer, or None for a model we don't have a price for
    price = next((pr for pr in PRICES if a[2].startswith(pr[0])), None)
    if price is None:
        return None
    _, pin, pout, pread = price
    cw1h = a[7] if len(a) > 7 else 0
    return (a[3] * pin + a[4] * pout + (a[5] - cw1h) * 1.25 * pin + cw1h * 2 * pin + a[6] * pread) / 1e6


def fmt_money(d):
    return f"${d:,.2f}" if d < 1000 else f"${d:,.0f}"


# rough book sizes in tokens, for the fun comparison in the claude code tab
BOOKS = [("The Little Prince", 22_000), ("The Great Gatsby", 61_000), ("The Hobbit", 124_000),
         ("Pride and Prejudice", 156_000), ("Moby-Dick", 270_000), ("The Lord of the Rings", 625_000),
         ("War and Peace", 760_000), ("all seven Harry Potter books", 1_400_000)]

# ---- claude code's local logs ----

def fmt_tokens(n):
    if n < 1000:
        return str(n)
    for div, unit in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if n >= div:
            return f"{n / div:.1f}".rstrip("0").rstrip(".") + unit


def pretty_model(m):
    # "claude-opus-5-5" -> "Opus 5.5", "claude-3-5-haiku-20241022" -> "Haiku 3.5"
    parts = [p for p in m.replace("claude-", "").split("-") if not (p.isdigit() and len(p) >= 8)]
    words = [p.capitalize() for p in parts if not p.isdigit()]
    nums = [p for p in parts if p.isdigit()]
    return " ".join(words) + (" " + ".".join(nums) if nums else "")


def hour_label(h):
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def compare_line(tokens):
    fits = [(name, size) for name, size in BOOKS if tokens >= 2 * size]
    if fits:
        name, size = fits[-1]
        return f"You've used ~{tokens / size:.0f}× more tokens than {name}."
    if tokens >= BOOKS[0][1]:
        return f"That's about as many tokens as {BOOKS[0][0]}."
    return f"That's {100 * tokens / BOOKS[0][1]:.0f}% of {BOOKS[0][0]} so far."


def build_stats(answers, lines, starts=None, real=None):
    # the claude code tab's numbers, for all time, 30 days and 7 days.
    # starts (session -> first time) = peak hour is when sessions start, like the claude app.
    # real = each answer once. the cost estimate always uses that, whichever way tokens are counted.
    real = answers if real is None else real
    today = datetime.date.today()
    by_day = Counter()
    for a in answers:
        by_day[a[0].date()] += a[3] + a[4] + a[5] + a[6]
    today_cost = sum(c for a in real if a[0].date() == today and (c := answer_cost(a)) is not None)
    out = {"today": by_day.get(today, 0), "today_cost": today_cost, "heat": dict(by_day), "ranges": {}}
    for name, days in (("all", None), ("30d", 30), ("7d", 7)):
        since = None if days is None else today - datetime.timedelta(days=days - 1)
        A = [a for a in answers if since is None or a[0].date() >= since]
        L = [ln for ln in lines if since is None or ln[0].date() >= since]
        models, parts = Counter(), [0, 0, 0, 0]
        for a in A:
            for i in range(4):
                parts[i] += a[3 + i]
            if not a[2].startswith("<"):   # skip claude code's made-up "<synthetic>" entries
                models[a[2]] += a[3] + a[4] + a[5] + a[6]
        hours = Counter(ln[0].hour for ln in L)
        if starts:
            began = Counter(t.hour for t in starts.values() if since is None or t.date() >= since)
            hours = began or hours
        projects, proj_sessions, cost, unpriced = Counter(), {}, 0.0, False
        for a in A:
            proj = a[8] if len(a) > 8 else "?"
            projects[proj] += a[3] + a[4] + a[5] + a[6]
            proj_sessions.setdefault(proj, set()).add(a[1])
        for a in real:
            if since is None or a[0].date() >= since:
                c = answer_cost(a)
                if c is None:
                    unpriced = unpriced or not a[2].startswith("<")
                else:
                    cost += c
        out["ranges"][name] = {
            "sessions": len({ln[1] for ln in L}), "messages": len(L), "tokens": sum(parts),
            "parts": parts, "days": len({ln[0].date() for ln in L}),
            "peak": hours.most_common(1)[0][0] if hours else None, "models": models.most_common(),
            "projects": [(name_, tok, len(proj_sessions[name_])) for name_, tok in projects.most_common()],
            "cost": cost, "unpriced": unpriced,
        }
    return out


class ClaudeCodeLog:
    # reads claude code's logs (~/.claude/projects/**/*.jsonl) a little at a time, in the background.
    # keeps only numbers: times, session ids, model names and token counts. never message text.
    def __init__(self):
        self.offsets = {}         # file -> bytes read so far
        self.seen_answers = set() # (message id, request id). each answer is logged several times.
        self.seen_lines = set()   # line ids, so nothing is counted twice
        self.answers = []         # (local time, session, model, input, output, cache write, cache read)
        self.copies = []          # the extra logged copies of those answers (the claude app counts them too)
        self.starts = {}          # session -> its first line's time
        self.lines = []           # (local time, session) for every user and assistant line
        self.last_error = 0.0     # when a tool call last failed (for the worried face)
        self.stats = None         # summary for the panel
        self.last_growth = 0.0    # when new output tokens last appeared
        self.built_at = 0.0
        self.ready = False

    def run(self):
        while True:
            try:
                t0 = time.perf_counter()
                self.scan()
                self.scan_ms = (time.perf_counter() - t0) * 1000   # for the performance page
            except Exception:
                log_error("reading claude code's logs")   # a weird log line must never stop the pet
            time.sleep(CC_SCAN_SECONDS)

    def scan(self):
        new_output, changed = 0, False
        try:
            files = list(CC_LOGS.rglob("*.jsonl"))
        except OSError:
            files = []
        for f in files:
            try:
                size = f.stat().st_size
            except OSError:
                continue
            start = self.offsets.get(str(f), 0)
            if size < start:
                start = 0   # the file was rewritten. the seen sets stop double counting.
            if size == start:
                continue
            try:
                with open(f, "rb") as fh:
                    fh.seek(start)
                    chunk = fh.read(size - start)
            except OSError:
                continue
            end = chunk.rfind(b"\n")
            if end < 0:
                continue   # only half a line so far
            self.offsets[str(f)] = start + end + 1
            for raw in chunk[:end].split(b"\n"):
                got = self.take(raw)
                if got is not None:
                    changed = True
                    new_output += got
        if new_output and self.ready:
            self.last_growth = time.time()
        if self.stats is None or (changed and time.time() - self.built_at > 10):
            self.stats = {"real": build_stats(self.answers, self.lines),
                          "app": build_stats(self.answers + self.copies, self.lines, self.starts, self.answers)}
            self.built_at = time.time()
        self.ready = True

    def usage_curve(self, start, end):
        # claude code's token use between two times as a running total, roughly weighted by what each
        # kind of token costs (output most, cache reads least), for estimating the chart's early part
        pts = sorted((a[0].timestamp(), a[3] + 5 * a[4] + 1.25 * a[5] + 0.1 * a[6])
                     for a in list(self.answers) if start <= a[0].timestamp() <= end)
        out, total = [], 0.0
        for ts, w in pts:
            total += w
            out.append((ts, total))
        step = max(1, len(out) // 150)   # no need for more than ~150 points
        return out[::step] + out[-1:] if out else []

    def take(self, raw):
        # one log line -> output tokens it added (None if it was nothing new)
        try:
            d = json.loads(raw)
        except ValueError:
            return None
        if not isinstance(d, dict) or d.get("type") not in ("user", "assistant"):
            return None
        uid = d.get("uuid")
        if uid in self.seen_lines:
            return None
        when = parse_time(d.get("timestamp") or "")
        if when is None:
            return None
        when = when.astimezone()   # your local time
        if uid:
            self.seen_lines.add(uid)
        session = d.get("sessionId") or "?"
        self.lines.append((when, session))
        if session not in self.starts or when < self.starts[session]:
            self.starts[session] = when
        m = d.get("message")
        if d["type"] == "user" and isinstance(m, dict) and isinstance(m.get("content"), list):
            if self.ready and any(isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error")
                                  for b in m["content"]):
                self.last_error = time.time()   # a tool call failed
        if d["type"] == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict):
            u = m["usage"]
            n = [int(u.get(k) or 0) for k in ("input_tokens", "output_tokens",
                                              "cache_creation_input_tokens", "cache_read_input_tokens")]
            cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
            cw1h = int(cc.get("ephemeral_1h_input_tokens") or 0)
            project = Path(str(d.get("cwd") or "?")).name or "?"   # the folder claude code worked in
            row = (when, session, str(m.get("model") or "unknown"), *n, cw1h, project)
            key = (m.get("id"), d.get("requestId"))
            if key in self.seen_answers:
                self.copies.append(row)   # same answer, logged again
                return 0
            self.seen_answers.add(key)
            self.answers.append(row)
            return n[1]
        return 0
