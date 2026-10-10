# reading claude code's local logs for token counts, costs and stats (only numbers, never text).
import datetime
import gzip
import json
import os
import time
from collections import Counter
from pathlib import Path

from .config import CC_CACHE, CC_LOGS, CC_SCAN_SECONDS
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
    out["recent"] = recent_sessions(answers, lines, real)
    # sessions with anything between midnight and 5 am (for the pet's diary)
    out["late"] = len({ln[1] for ln in lines if ln[0].hour < 5})
    return out


def recent_sessions(answers, lines, real, keep=8):
    # the latest sessions, newest first: start, end, messages, tokens, api-price cost, project and main model
    span, msgs = {}, Counter()
    for when, sid in lines:
        a, b = span.get(sid, (when, when))
        span[sid] = (min(a, when), max(b, when))
        msgs[sid] += 1
    latest = sorted(span, key=lambda sid: span[sid][1], reverse=True)[:keep]
    want = set(latest)
    tokens, cost, proj, model = Counter(), Counter(), {}, {}
    for a in answers:
        if a[1] in want:
            n = a[3] + a[4] + a[5] + a[6]
            tokens[a[1]] += n
            proj.setdefault(a[1], Counter())[a[8] if len(a) > 8 else "?"] += n
            if not a[2].startswith("<"):
                model.setdefault(a[1], Counter())[a[2]] += n
    for a in real:
        if a[1] in want and (c := answer_cost(a)) is not None:
            cost[a[1]] += c
    return [{"id": sid, "start": span[sid][0], "end": span[sid][1], "messages": msgs[sid], "tokens": tokens[sid],
             "cost": cost[sid], "project": proj[sid].most_common(1)[0][0] if sid in proj else "?",
             "model": model[sid].most_common(1)[0][0] if sid in model else None} for sid in latest]


def fmt_minutes(seconds):
    m = max(1, round(seconds / 60))
    return f"{m} min" if m < 60 else f"{m // 60}h {m % 60:02d}m"


# claude code's tool names, as the jobs the mascot can show. only the reading one has a look so far;
# the rest are listed in PROJECT_NOTES.md under ideas.
JOBS = {"Read": "read", "Grep": "read", "Glob": "read", "NotebookRead": "read", "LS": "read"}
CHUNK = 4 * 2 ** 20   # logs are read this much at a time, so a huge log never sits in memory all at once
CACHE_VERSION = 1


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
        self.job = (0.0, None)    # (when, kind) of the last tool claude used that the mascot has a look for
        self.active = {}          # session -> when it last wrote something (live, since the pet started)
        self.dirty, self.saved_at = False, 0.0   # for the cache file

    def run(self):
        try:
            self.load_cache()
        except Exception:
            log_error("reading the saved claude code numbers")
            self.__init__()   # start from scratch: it just re-reads every log
        while True:
            try:
                t0 = time.perf_counter()
                self.scan()
                self.scan_ms = (time.perf_counter() - t0) * 1000   # for the performance page
                if self.dirty and time.time() - self.saved_at > 300:
                    self.save_cache()
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
            while size > start:   # a bit at a time, so a huge log doesn't sit in memory all at once
                try:
                    with open(f, "rb") as fh:
                        fh.seek(start)
                        chunk = fh.read(min(size - start, CHUNK))
                except OSError:
                    break
                end = chunk.rfind(b"\n")
                if end < 0:
                    if len(chunk) == CHUNK:   # one enormous line: skip it
                        nxt = self.skip_line(f, start + CHUNK)
                        self.offsets[str(f)], start = nxt, nxt
                        continue
                    break   # only half a line so far
                start += end + 1
                self.offsets[str(f)] = start
                self.dirty = True
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
        if not self.ready:
            self.save_cache()   # the first full read is the slow one: save it straight away
        self.ready = True

    def skip_line(self, f, pos):
        # where the line that's still going at pos ends (just after its newline), or the file's end
        with open(f, "rb") as fh:
            fh.seek(pos)
            while True:
                block = fh.read(CHUNK)
                if not block:
                    return pos
                i = block.find(b"\n")
                if i >= 0:
                    return pos + i + 1
                pos += len(block)

    # ---- the cache: numbers already read, so a restart only reads what's new ----
    def save_cache(self):
        t = lambda d: round(d.timestamp(), 3)
        row = lambda a: [t(a[0])] + list(a[1:])
        data = {"v": CACHE_VERSION, "logs": str(CC_LOGS), "offsets": self.offsets,
                "seen_answers": [list(k) for k in self.seen_answers], "seen_lines": list(self.seen_lines),
                "answers": [row(a) for a in self.answers], "copies": [row(a) for a in self.copies],
                "starts": {k: t(v) for k, v in self.starts.items()}, "lines": [[t(w), s] for w, s in self.lines]}
        tmp = CC_CACHE.with_name(CC_CACHE.name + ".tmp")
        try:
            with gzip.open(tmp, "wt", encoding="utf-8") as fh:
                json.dump(data, fh, separators=(",", ":"))
            os.replace(tmp, CC_CACHE)
        except OSError:
            log_error("saving the claude code numbers")
        self.dirty, self.saved_at = False, time.time()

    def load_cache(self):
        # picks up where the last run left off. if any log it knew got shorter or disappeared, it starts over,
        # so deleted logs drop out of the stats like before.
        try:
            with gzip.open(CC_CACHE, "rt", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError, EOFError):
            return
        if not isinstance(data, dict) or data.get("v") != CACHE_VERSION or data.get("logs") != str(CC_LOGS):
            return
        offsets = {str(k): int(v) for k, v in data["offsets"].items()}
        for path, off in offsets.items():
            try:
                if Path(path).stat().st_size < off:
                    return
            except OSError:
                return
        when = lambda ts: datetime.datetime.fromtimestamp(float(ts)).astimezone()
        row = lambda a: (when(a[0]), str(a[1]), str(a[2]), *(int(v) for v in a[3:8]), str(a[8]))
        answers, copies = [row(a) for a in data["answers"]], [row(a) for a in data["copies"]]
        lines = [(when(w), str(s)) for w, s in data["lines"]]
        self.starts = {str(k): when(v) for k, v in data["starts"].items()}
        self.seen_answers = {tuple(k) for k in data["seen_answers"]}
        self.seen_lines = set(data["seen_lines"])
        self.answers, self.copies, self.lines, self.offsets = answers, copies, lines, offsets
        self.saved_at = time.time()

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
        if self.ready:
            self.active[session] = time.time()   # this session is doing something right now
        m = d.get("message")
        if d["type"] == "user" and isinstance(m, dict) and isinstance(m.get("content"), list):
            if self.ready and any(isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error")
                                  for b in m["content"]):
                self.last_error = time.time()   # a tool call failed
        if self.ready and d["type"] == "assistant" and isinstance(m, dict) and isinstance(m.get("content"), list):
            for b in m["content"]:   # which tool claude reached for (just its name, never what it was given)
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    self.job = (time.time(), JOBS.get(str(b.get("name"))))
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
