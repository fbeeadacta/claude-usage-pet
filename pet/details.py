# the details panel that shows when you hover the mascot (plan and claude code tabs).
import datetime
import math
import time
import tkinter as tk
import tkinter.font as tkfont

from .art import ORANGE, PARK, RED, TRACK
from .cclog import compare_line, fmt_minutes, fmt_money, fmt_tokens, hour_label, pretty_model
from .config import SESSION_DONE_MIN
from .ui import Fader, move_window, round_corners, round_rect
from .usage import (bar_color, fmt_day, fmt_time, fmt_when, forecast, pace_info, parse_rows, parse_time,
    period_seconds, reset_text)


# ---- details panel (hover the mascot) ----

PANEL_W = 320
HEAT = ["#2c2c2e", "#173c6e", "#1f57a6", "#2b74e0", "#5aa2ff"]   # empty day, then busier and busier


class Details:
    BG, FG, DIM, CARD = "#1c1c1e", "#f2f2f7", "#8e8e93", "#2c2c2e"
    FASTC, SLOWC = "#d9a441", "#5ea1ff"

    def __init__(self, pet):
        self.pet = pet
        self.win = tk.Toplevel(pet.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.win.configure(bg=self.BG)
        self.win.geometry(f"10x10+{PARK}+{PARK}")   # starts parked off screen
        self.canvas = tk.Canvas(self.win, bg=self.BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonRelease-1>", self.click)
        self.canvas.bind("<Button-3>", pet.show_menu)
        self.visible = self.pinned = self.rounded = False
        self.hits, self.rect, self.px_size, self.fonts = [], None, (10, 10), {}
        self.anchor_x = self.anchor_bottom = 0
        self.avoid = (0, 0, 0, 0)
        self.s = 1.0
        self.curve_key, self.curve = None, []   # cached estimate for the plan chart
        self.fader = Fader(self.win, 0.0, 1.0, self.place)

    def show(self, pinned=False):
        p = self.pet
        self.pinned = self.pinned or pinned
        p.pin_var.set(self.pinned)
        if self.visible:
            return
        self.visible = True
        self.anchor_x = p.x   # opens just above the bubble if there's room
        self.anchor_bottom = (p.geo[3] if p.geo else p.screens[p.si].wb) + p.top_margin - round(6 * p.dpi)
        # the space the mascot and its bubble take up, which the panel must not cover
        self.avoid = (round(p.x - p.half), self.anchor_bottom, round(p.x + p.half), round(p.y))
        self.draw()
        if not self.rounded:
            round_corners(self.win)
            self.rounded = True
        self.fader.to(1.0, instant=not p.anim.get())

    def hide(self):
        if not self.visible:
            return
        self.visible = self.pinned = False
        self.pet.pin_var.set(False)
        self.fader.to(0.0, instant=not self.pet.anim.get())

    def place(self):
        p = self.pet
        if not self.visible and self.fader.alpha <= 0.001:
            move_window(self.win, PARK, PARK)
            self.rect = None
            return
        pw, ph = self.px_size
        sc = p.screens[p.si]
        gap = round(8 * p.dpi)
        left, top, right, feet = self.avoid
        x = min(max(sc.wl + 4, round(self.anchor_x - pw / 2)), sc.wr - pw - 4)
        if self.anchor_bottom - ph >= sc.wt + 4:
            y = self.anchor_bottom - ph            # above the bubble (the usual place)
        elif feet + gap + ph <= sc.wb - 4:
            y = feet + gap                         # high up (on a window): below the mascot instead
        else:                                      # no room above or below: beside it
            x = right + gap if right + gap + pw <= sc.wr - 4 else max(sc.wl + 4, left - gap - pw)
            y = min(max(sc.wt + 4, feet - ph), sc.wb - ph - 4)
        self.rect = (x, y, x + pw, y + ph)
        y += round((1 - self.fader.alpha) * 10 * p.dpi)   # slides up a little as it fades in
        move_window(self.win, x, y, pw, ph)

    def click(self, e):
        p = self.pet
        for name, x1, y1, x2, y2 in self.hits:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                if name == "close":
                    self.hide()
                    return
                kind, val = name.split(":")
                {"tab": p.panel_tab, "view": p.cc_view, "range": p.cc_range, "chart": p.plan_chart}[kind].set(val)
                self.draw()
                p.save()
                return

    # drawing helpers. positions are in base units (PANEL_W wide) times self.s.
    def font(self, size, bold=False):
        px = max(8, round(size * 4 / 3 * self.s))
        if (px, bold) not in self.fonts:
            self.fonts[(px, bold)] = tkfont.Font(root=self.win, family="Segoe UI", size=-px,
                                                 weight="bold" if bold else "normal")
        return self.fonts[(px, bold)]

    def text(self, x, y, text, fill, size, bold=False, anchor="nw", width=None):
        kw = {"width": width * self.s} if width else {}
        item = self.canvas.create_text(x * self.s, y * self.s, anchor=anchor, fill=fill, font=self.font(size, bold),
                                       text=text, **kw)
        return self.canvas.bbox(item)[3] / self.s   # where the text ends, for wrapped lines

    def rect_(self, x1, y1, x2, y2, fill):
        s = self.s
        self.canvas.create_rectangle(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=0)

    def line(self, x1, y1, x2, y2, fill, width=1):
        s = self.s
        self.canvas.create_line(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=max(1, round(width * s)))

    def pill(self, x, y, label, on, hit, right=False):
        # a small tab button. returns its width.
        s = self.s
        w = self.font(8, True).measure(label) / s + 12
        if right:
            x -= w
        if on:
            round_rect(self.canvas, x * s, y * s, (x + w) * s, (y + 17) * s, 4 * s, TRACK, self.BG, True)
        self.text(x + 6, y + 8.5, label, self.FG if on else self.DIM, 8, True, "w")
        self.hits.append((hit, x * s, y * s, (x + w) * s, (y + 17) * s))
        return w

    def draw(self):
        p = self.pet
        self.s = s = p.dpi * min(1.6, max(1.0, p.scale))
        # every tab and view gets the same height, so the tabs never jump when you switch
        tallest = 0
        for tab, view in (("plan", "overview"), ("cc", "overview"), ("cc", "models"), ("cc", "projects"),
                          ("sessions", None)):
            tallest = max(tallest, self.draw_tab(tab, view))
        self.draw_tab(p.panel_tab.get(), p.cc_view.get())
        H = tallest + 12
        self.px_size = (round(PANEL_W * s), round(H * s))
        self.canvas.configure(width=self.px_size[0], height=self.px_size[1])
        self.place()

    def draw_tab(self, tab, view):
        # draws one tab from scratch and returns how tall it came out
        p, s, W = self.pet, self.s, PANEL_W
        self.canvas.delete("all")
        self.hits = []
        x = 10
        for name, label in (("plan", "Plan"), ("cc", "Claude Code"), ("sessions", "Sessions")):
            x += self.pill(x, 8, label, tab == name, "tab:" + name) + 4
        self.text(W - 16, 7, "\u00d7", self.DIM, 11, True, "n")      # close button
        self.hits.append(("close", (W - 30) * s, 2 * s, (W - 2) * s, 28 * s))
        if tab == "sessions":
            return self.draw_sessions(38)
        return self.draw_plan(38) if tab == "plan" else self.draw_cc(38, view)

    def draw_plan(self, y):
        p = self.pet
        W = PANEL_W
        rows = parse_rows(p.data) if p.data else []
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = time.time()
        wait = "updating..." if p.busy else f"next update in {max(0, math.ceil(p.next_at - now))}s"
        self.text(12, y, (f"updated {fmt_time(p.updated)} · " if p.updated else "") + wait, self.DIM, 8)
        y += 22
        if p.quiet():   # no talking or sounds right now
            until = (f" until {fmt_time(datetime.datetime.fromtimestamp(p.hush_until))}"
                     if time.time() < p.hush_until else "")
            self.text(12, y - 6, f"Quiet mode{until}: no talking or sounds.", self.SLOWC, 8)
            y += 14
        for r in rows:
            seen = p.seen.get(r["key"])
            unchanged = now - seen[1] if seen else 0
            el, msg, kind = pace_info(r["key"], r["pct"], r["resets"], now_dt, unchanged)
            self.text(12, y, r["label"], self.FG, 9, True)
            self.text(W - 12, y, f"{r['pct']:.0f}%", self.FG, 9, True, "ne")
            self.rect_(12, y + 20, W - 12, y + 26, TRACK)
            self.rect_(12, y + 20, 12 + (W - 24) * min(r["pct"], 100) / 100, y + 26, bar_color(r["pct"]))
            if el is not None:   # the pace tick: where the clock is in this window
                tx = 12 + (W - 24) * el / 100
                self.line(tx, y + 16, tx, y + 30, self.FG, 2)
            when = parse_time(r["resets"])
            at = f" · {fmt_when(when.astimezone(), r['key'])}" if when else ""
            self.text(12, y + 32, reset_text(r["resets"], now_dt) + at, self.DIM, 8)
            if msg:
                y = self.text(12, y + 46, msg, self.FASTC if kind == "fast" else self.SLOWC, 8, True,
                              width=W - 24) + 8
            else:
                y += 54
        if p.error:   # the problem in red; any how-to-fix steps after it in plain text, easier to read
            head, _, steps = p.error.partition(chr(10) * 2)
            y = self.text(12, y, head, RED, 8, True, width=W - 24) + 8
            if steps:
                y = self.text(12, y, steps, self.FG, 8, width=W - 24) + 10
        elif not rows:
            self.text(12, y, "loading...", self.DIM, 8)
            y += 20
        if rows:
            y = self.draw_chart(y + 6, rows, now_dt)
        st = p.cc_stats()
        if st:
            self.text(12, y, f"Claude Code today: {fmt_tokens(st['today'])} tokens · about "
                             f"{fmt_money(st['today_cost'])} at API prices", self.DIM, 8, width=PANEL_W - 24)
            y += 18
        return y

    def draw_chart(self, y, rows, now_dt):
        # usage so far in the current window, against the pace line, plus a forecast
        p, s, W = self.pet, self.s, PANEL_W
        which = p.plan_chart.get()
        key = "five_hour" if which == "5h" else "seven_day"
        r = next((r for r in rows if r["key"] == key), None)
        self.text(12, y + 8.5, "This window", self.FG, 8.5, True, "w")
        x = W - 10
        for name, label in (("7d", "Week"), ("5h", "5-hour")):
            x -= self.pill(x, y, label, which == name, "chart:" + name, right=True) + 2
        y += 26
        reset = parse_time(r["resets"]) if r else None
        if not r or reset is None:
            self.text(12, y, "No data for this limit yet.", self.DIM, 8)
            return y + 24
        period = period_seconds(key)
        start = reset.timestamp() - period
        now = time.time()
        pts = [(h[0], h[1] if key == "five_hour" else h[2]) for h in p.history if h[0] >= start]
        pts = [(tt, v) for tt, v in pts if v is not None]
        # before the pet's first check in this window there's no real data. estimate it from when
        # claude code used tokens, scaled so it meets the first real number. drawn dotted.
        first_t, first_v = pts[0] if pts else (now, r["pct"])
        est = []
        if first_t - start > 300 and first_v > 0:
            ck = (round(start), round(first_t), len(p.cc.answers))
            if self.curve_key != ck:
                self.curve_key, self.curve = ck, p.cc.usage_curve(start, first_t)
            if self.curve and self.curve[-1][1] > 0:
                k = first_v / self.curve[-1][1]
                est = [(start, 0.0)] + [(tt, v * k) for tt, v in self.curve] + [(first_t, first_v)]
            else:
                est = [(start, 0.0), (first_t, first_v)]
        pts = pts + [(now, r["pct"])]
        # the box
        x0, x1, y0, y1 = 12, W - 12, y, y + 74
        round_rect(self.canvas, x0 * s, y0 * s, x1 * s, y1 * s, 6 * s, self.CARD, self.BG, True)
        ix0, ix1, iy0, iy1 = x0 + 8, x1 - 8, y0 + 8, y1 - 8
        fx = lambda tt: ix0 + (ix1 - ix0) * min(1.0, max(0.0, (tt - start) / period))
        fy = lambda v: iy1 - (iy1 - iy0) * min(100.0, max(0.0, v)) / 100
        for v in (50, 100):   # faint guide lines at 50% and 100%
            self.rect_(ix0, fy(v), ix1, fy(v) + 0.6, "#3a3a3c")
        self.text(ix0 + 2, fy(100) + 1, "100%", "#6e6e73", 6.5)
        # the pace line: where you'd be if you used it evenly until the reset
        self.canvas.create_line(fx(start) * s, fy(0) * s, fx(reset.timestamp()) * s, fy(100) * s,
                                fill="#6e6e73", width=max(1, round(s)), dash=(3, 3))
        color = bar_color(r["pct"])
        if est:
            line = []
            for tt, v in est:
                line += [fx(tt) * s, fy(v) * s]
            self.canvas.create_line(*line, fill=color, width=max(2, round(2 * s)), dash=(2, 3))
        if len(pts) >= 2:
            line = []
            for tt, v in pts:
                line += [fx(tt) * s, fy(v) * s]
            self.canvas.create_line(*line, fill=color, width=max(2, round(2 * s)))
        nx, ny = fx(now) * s, fy(r["pct"]) * s
        d = max(3, round(3 * s))
        self.canvas.create_oval(nx - d, ny - d, nx + d, ny + d, fill=color, outline="")
        if len(pts) < 2 and not est:
            self.text((ix0 + ix1) / 2, iy0 + 16, "the line fills in as I check your usage", self.DIM, 7.5,
                      anchor="n")
        st_dt = datetime.datetime.fromtimestamp(start)
        self.text(x0, y1 + 3, fmt_time(st_dt) if key == "five_hour" else fmt_day(st_dt), "#6e6e73", 7)
        self.text(x1, y1 + 3, f"resets {fmt_when(reset.astimezone(), key)}",
                  "#6e6e73", 7, anchor="ne")
        if est:
            self.text((x0 + x1) / 2, y1 + 3, "dotted = estimate", "#6e6e73", 7, anchor="n")
        y = y1 + 20
        # the forecast
        fc = forecast(key, r["pct"], r["resets"], now_dt)
        if fc is None:
            msg, col = "Too early in this window for a forecast.", self.DIM
        else:
            proj, out = fc
            if out is not None:
                left = reset.timestamp() - out
                gap = f"{left / 3600:.0f}h" if left >= 3600 else f"{left / 60:.0f}m"
                msg, col = (f"At this pace you'll run out around {fmt_when(datetime.datetime.fromtimestamp(out), key)}, "
                            f"about {gap} before the reset."), self.FASTC
            elif r["pct"] >= 100:
                msg, col = "All used up. It comes back at the reset.", RED
            else:
                msg, col = f"At this pace you'll use about {proj:.0f}% by the reset.", "#4caf7d"
        return self.text(12, y, msg, col, 8, True, width=W - 24) + 12

    def draw_cc(self, y, view):
        p = self.pet
        W, s = PANEL_W, self.s
        rng = p.cc_range.get()
        x = 10
        for name, label in (("overview", "Overview"), ("models", "Models"), ("projects", "Projects")):
            x += self.pill(x, y, label, view == name, "view:" + name) + 2
        x = W - 10
        for name, label in (("7d", "7d"), ("30d", "30d"), ("all", "All")):
            x -= self.pill(x, y, label, rng == name, "range:" + name, right=True) + 2
        y += 32
        st = p.cc_stats()
        if st is None:
            self.text(12, y, "reading Claude Code's logs...", self.DIM, 8)
            return y + 20
        r = st["ranges"][rng]
        if not r["messages"]:
            self.text(12, y, "No Claude Code activity on this computer in this period.", self.DIM, 8, width=W - 24)
            return y + 34
        if view == "overview":
            fav = pretty_model(r["models"][0][0]) if r["models"] else "-"
            cards = [("Sessions", f"{r['sessions']:,}"), ("Messages", f"{r['messages']:,}"),
                     ("Total tokens", fmt_tokens(r["tokens"])), ("Active days", f"{r['days']:,}"),
                     ("Peak hour", "-" if r["peak"] is None else hour_label(r["peak"])), ("Favorite model", fav)]
            cw = (W - 28 - 16) / 3
            for i, (label, val) in enumerate(cards):
                cx, cy = 14 + (i % 3) * (cw + 8), y + (i // 3) * 50
                round_rect(self.canvas, cx * s, cy * s, (cx + cw) * s, (cy + 42) * s, 6 * s, self.CARD, self.BG, True)
                self.text(cx + 8, cy + 6, label, self.DIM, 7.5)
                self.text(cx + 8, cy + 21, val, self.FG, 9.5, True)
            y += 106
            # activity over the last 26 weeks, one square per day, sunday at the top
            heat, today = st["heat"], datetime.date.today()
            start = today - datetime.timedelta(days=(today.weekday() + 1) % 7 + 7 * 25)
            busiest = max([v for d, v in heat.items() if d >= start] or [0])
            pitch = int((W - 28) * s // 26)            # whole pixels, so every square is the same size
            cell = pitch - max(2, round(2 * s))
            gx, gy = round(14 * s), round(y * s)
            for col in range(26):
                for row in range(7):
                    d = start + datetime.timedelta(days=col * 7 + row)
                    if d > today:
                        continue
                    v = heat.get(d, 0)
                    lvl = 1 + min(3, int(4 * v / busiest)) if v and busiest else 0
                    x0, y0 = gx + col * pitch, gy + row * pitch
                    self.canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell, fill=HEAT[lvl], width=0)
            y += 7 * pitch / s + 12
            y = self.text(14, y, compare_line(r["tokens"]), self.DIM, 8, width=W - 28) + 4
            y = self.text(14, y, self.cost_line(r), self.DIM, 8, width=W - 28) + 12
        elif view == "projects":
            total = r["tokens"] or 1
            for name, tok, sessions in r["projects"][:5]:
                label = name if len(name) <= 30 else name[:29] + "…"
                self.text(12, y, label, self.FG, 9, True)
                self.text(W - 12, y, f"{fmt_tokens(tok)} · {100 * tok / total:.0f}%", self.FG, 9, True, "ne")
                self.rect_(12, y + 20, W - 12, y + 25, TRACK)
                self.rect_(12, y + 20, 12 + (W - 24) * tok / total, y + 25, "#5ea1ff")
                self.text(12, y + 28, f"{sessions} session{'s' if sessions != 1 else ''}", self.DIM, 7)
                y += 46
            if len(r["projects"]) > 5:
                y = self.text(12, y, f"and {len(r['projects']) - 5} more", self.DIM, 8) + 8
        else:
            total = r["tokens"] or 1
            for m, t in r["models"][:4]:
                self.text(12, y, pretty_model(m), self.FG, 9, True)
                self.text(W - 12, y, f"{fmt_tokens(t)} · {100 * t / total:.0f}%", self.FG, 9, True, "ne")
                self.rect_(12, y + 20, W - 12, y + 25, TRACK)
                self.rect_(12, y + 20, 12 + (W - 24) * t / total, y + 25, ORANGE)
                y += 34
            i_, o_, w_, r_ = r["parts"]
            self.text(12, y, f"input {fmt_tokens(i_)} · output {fmt_tokens(o_)}", self.DIM, 8)
            self.text(12, y + 16, f"cache write {fmt_tokens(w_)} · cache read {fmt_tokens(r_)}", self.DIM, 8)
            y = self.text(12, y + 32, self.cost_line(r), self.DIM, 8, width=W - 24) + 12
        how = ("Counted like the Claude app (every logged copy), from this computer's logs." if p.cc_app.get()
               else "Real count (each answer once), from this computer's logs.")
        return self.text(14, y, how, self.DIM, 7, width=W - 28) + 4

    def draw_sessions(self, y):
        # the latest claude code sessions, newest first: a recap of each
        p, W = self.pet, PANEL_W
        st = p.cc_stats()
        if st is None:
            self.text(12, y, "reading Claude Code's logs...", self.DIM, 8)
            return y + 20
        recent = st.get("recent", [])[:5]
        y = self.text(12, y, "Your latest Claude Code sessions on this computer", self.FG, 8.5, True) + 10
        if not recent:
            self.text(12, y, "No sessions yet.", self.DIM, 8)
            return y + 24
        now = time.time()
        for ses in recent:
            start = ses["start"]
            label = ses["project"] if len(ses["project"]) <= 28 else ses["project"][:27] + "…"
            self.text(12, y, label, self.FG, 9, True)
            self.text(W - 12, y, f"{fmt_tokens(ses['tokens'])} tokens", self.FG, 9, True, "ne")
            busy = now - max(ses["end"].timestamp(), p.cc.active.get(ses["id"], 0.0)) < SESSION_DONE_MIN * 60
            mins = fmt_minutes((ses["end"] - start).total_seconds())
            when = f"{fmt_day(start)} {fmt_time(start)} · {mins} · {ses['messages']} messages"
            end = self.text(12, y + 19, when, self.DIM, 7.5)
            if busy:   # still going
                self.text(W - 12, y + 19, "active now", ORANGE, 7.5, True, "ne")
            model = pretty_model(ses["model"]) + " · " if ses["model"] else ""
            self.text(12, end + 1, f"{model}about {fmt_money(ses['cost'])} at API prices", self.DIM, 7.5)
            y += 54
        how = ("Tokens counted like the Claude app." if p.cc_app.get() else "Tokens counted once per answer.")
        return self.text(14, y, how + " A session counts as finished after "
                         f"{SESSION_DONE_MIN} minutes with nothing new.", self.DIM, 7, width=W - 28) + 4

    def cost_line(self, r):
        # what these tokens would cost on the pay-as-you-go api (always counted once)
        extra = " (some models have no price here)" if r["unpriced"] else ""
        return f"About {fmt_money(r['cost'])} at API prices{extra}. Your plan covers this; it's for comparison."
