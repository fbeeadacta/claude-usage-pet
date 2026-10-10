# part of the Pet: being called over, quiet mode, seasons, session wrap-ups, the tour, the diary, the tray
# icon, fetch, and rare visitors (a shiny colour, a ufo, a cat).
import datetime
import math
import random
import time

from .art import BALL, BALL_C, CAT_A, CAT_B, CAT_C
from .cclog import fmt_minutes, fmt_tokens
from .config import (BEDTIME_END, CAT_HOURS, CHUTE_HEIGHT, COME_DROP, FETCH_SECONDS, GRAVITY, QUIET_FOR,
    SESSION_DONE_MIN, SPRINT, UFO_HOURS, WALK_SPEED)
from .lines import (AWAY_RECAP, BEDTIME_LINES, CAT_LINES, COME_LINES, DROP_IN_LINES, FETCH_BACK, FETCH_GOT, FETCH_START,
    QUIET_LINES, RECAP_LINES, SEASON_LINES, SHINY_LINES, TOUR_LINES, UFO_LINES, WELCOME_LINES, CONTINUE_LINES)
from .sprites import Sprite
from .storage import log_error
from .tray import Tray
from .usage import parse_rows, short_error
from .winapi import summoned, windows_quiet


def season(day=None):
    # which special day (or season) it is, for the outfits. None most of the year.
    d = day or datetime.date.today()
    if d.month == 10 and 25 <= d.day <= 31:
        return "halloween"
    if d.month == 12 and d.day <= 26:
        return "christmas"
    if (d.month, d.day) in ((12, 31), (1, 1)):
        return "newyear"
    if (d.month, d.day) == (10, 9):
        return "birthday"   # the day the pet was first made
    if (d.month, d.day) == (2, 14):
        return "valentine"
    return None


def smooth(k):
    k = min(1.0, max(0.0, k))
    return k * k * (3 - 2 * k)


# the ufo's timeline, in seconds: flies in, beam on, lifts the mascot, keeps it a moment, drops it, flies off
UFO_BEAM, UFO_LIFT, UFO_GONE, UFO_DROP, UFO_END = 1.5, 2.6, 4.6, 6.6, 8.0


class FunMixin:
    # ---- coming over when called ----
    def come_here(self):
        # the shortcut, the tray icon or starting the pet again: it comes to your mouse
        self.user_hidden = False
        self.check_fullscreen()
        if self.hidden or self.held or not self.anim.get():
            return
        mx, my = self.root.winfo_pointerxy()
        si = self.find_screen(mx, my)
        si = self.nearest_screen(mx, my) if si is None else si
        sc = self.screens[si]
        self.last_touch = time.time()
        self.stop_fetch()
        self.wake(hop=False)
        if self.ufo and not self.ufo.get("dropped"):
            return   # busy being abducted. it'll be right back.
        tx = min(max(mx, sc.wl + self.half), sc.wr - self.half)
        if si == self.si and self.plat is None and self.grounded() and abs(tx - self.x) <= COME_DROP * self.s():
            self.goto_x, self.goto_why = tx, "come"
            self.say(self.pick(COME_LINES), force=True)
            return
        # far away, up on a window, or on another monitor: it parachutes in right above your mouse
        self.si, self.x = si, tx
        s = self.s()
        self.plat, self.through, self.leaping, self.leap_plan, self.diving = None, False, None, None, False
        self.hay_t = self.squash_t = self.pending_v = 0.0
        self.y = max(sc.mt + self.pet_px[1] + 20 * s, sc.wb - (CHUTE_HEIGHT + 90) * s)
        self.vx, self.vy, self.angle, self.spin = 0.0, 200 * s, 0.0, 0.0
        self.goto_x, self.goto_why, self.dropping_in = None, None, True
        self.state, self.state_t = "idle", 2.0
        self.say(self.pick(DROP_IN_LINES), force=True)

    def chase(self, dt, s):
        # running to a spot (called over, or after the ball). returns True while it's on its way.
        dx = self.goto_x - self.x
        if abs(dx) <= 6 * s:
            self.goto_x = None
            self.arrived()
            return True
        if self.state == "sleep":
            self.wake(hop=False)
        self.state, self.dir = "walk", (1 if dx > 0 else -1)
        x0, step = self.x, min(abs(dx), WALK_SPEED * SPRINT * s * dt)
        self.move_x(self.dir * step)
        self.tally("walked", abs(self.x - x0) / self.screens[self.si].dpi)
        if self.plat is not None and not self.plat_box[1] <= self.x <= self.plat_box[3]:
            self.plat = None   # ran off the edge of its window: it lands and keeps going
        elif abs(self.x - x0) < 0.01 * step:
            self.goto_x = None   # a wall it can't get past: it stops there
            self.arrived()
        self.step_t += dt * 2   # quick little steps
        if self.step_t >= 0.18:
            self.step_t, self.step = 0.0, self.step + 1
        return True

    def arrived(self):
        why, self.goto_why = self.goto_why, None
        self.state, self.state_t = "idle", 2.0
        if why == "come":
            self.wave_t = 1.4
        elif why == "fetch":
            self.reach_ball()
        elif why == "return":
            self.drop_ball()

    # ---- what claude code is up to ----
    def helpers(self):
        # one little apprentice for each extra claude code session busy right now (up to 3)
        if not self.apprentices.get():
            return 0
        now = time.time()
        busy = sum(1 for t in list(self.cc.active.values()) if now - t < 45)
        return max(0, min(3, busy - 1))

    # ---- bedtime ----
    def bedtime_now(self):
        # nightcap and candle time: from the chosen hour until BEDTIME_END in the morning
        if not self.bedtime.get():
            return False
        h, a = datetime.datetime.now().hour, self.bedtime_at.get()
        return (h >= a or h < BEDTIME_END) if a > BEDTIME_END else a <= h < BEDTIME_END

    # ---- quiet mode ----
    def quiet(self):
        # no talking and no sounds: for an hour from the menu, during quiet hours, or when windows says so
        if time.time() < self.hush_until:
            return True
        if self.quiet_hours.get():
            h, a, b = datetime.datetime.now().hour, self.quiet_from.get(), self.quiet_to.get()
            if ((a <= h or h < b) if a > b else (a <= h < b)):
                return True
        return bool(self.dnd.get() and self.win_quiet)

    def toggle_hush(self):
        if time.time() < self.hush_until:
            self.hush_until = 0.0
            self.say("I'm back! did you miss me?", force=True)
        else:
            self.say(self.pick(QUIET_LINES), force=True)   # (said just before it goes quiet)
            self.hush_until = time.time() + QUIET_FOR
            self.stop_music()
        self.save()

    def restart_tour(self):
        self.script, self.next_line = list(TOUR_LINES), time.time() + 0.5

    def welcome(self, now):
        # (just started) welcome back, and maybe an offer to carry on with the last claude code session's project
        hour = datetime.datetime.now().hour
        part = "morning" if 5 <= hour < 12 else "evening" if 17 <= hour < 23 else "late" if hour < 5 or hour >= 23             else "day"
        lines = [self.pick(WELCOME_LINES[part] + WELCOME_LINES["any"])]
        if part == "morning":
            self.greeted = datetime.date.today().isoformat()   # (that was the good morning)
        st = self.cc_stats()
        last = (st or {}).get("recent", [None])[0] if st else None
        if last and last["project"] not in ("?", ""):
            ago = now - last["end"].timestamp()
            kind = "warm" if ago < 3 * 3600 else "recent" if ago < 3 * 86400 else "old"
            days = max(1, round(ago / 86400))
            lines.append(self.pick(CONTINUE_LINES[kind]).format(project=last["project"], days=days))
        self.script = lines + self.script
        self.next_line = now

    # ---- the diary ----
    def tally(self, key, n=1):
        # counts things for the pet's diary (settings > about & stats)
        self.log[key] = self.log.get(key, 0) + n
        if not self.log_since:
            self.log_since = datetime.date.today().isoformat()

    # ---- once a second ----
    def fun_tick(self, now, present, working):
        self.win_quiet = windows_quiet() if self.dnd.get() else False
        if not present or self.hidden:
            return
        today = datetime.date.today().isoformat()
        if self.welcome_due and (self.cc.stats is not None or now - self.started > 15):
            self.welcome_due = False   # (waits a moment for claude code's logs, for the project name)
            self.welcome(now)
        if self.script and now >= self.next_line and not self.speech and self.state != "sleep":
            # lines said one after another: the tour, the welcome back
            if self.chatter.get() == "off":
                self.script, self.toured = [], True   # it was asked not to talk
            elif self.say(self.script[0], force=True):
                self.script.pop(0)
                self.next_line = self.speech["until"] + 1.2
                self.toured = self.toured or not self.script
            return
        day = season() if self.seasonal.get() else None
        if day and self.season_said != today and not self.speech and self.state != "sleep":
            if self.say(self.pick(SEASON_LINES[day]), force=True):
                self.season_said = today
                self.wave_t = 1.4
        night = self.bedtime_now()
        if night and self.was_bedtime is False and self.state != "sleep":   # (not when it starts up at night)
            self.say(self.pick(BEDTIME_LINES))
        self.was_bedtime = night
        if self.shiny and not self.shiny_said and not self.speech and self.say(self.pick(SHINY_LINES), force=True):
            self.shiny_said = True
            self.tally("shiny")
        if day == "newyear":   # fireworks around midnight
            t = datetime.datetime.now()
            if (t.month == 12 and t.hour == 23 and t.minute >= 55) or (t.month == 1 and t.hour == 0):
                if random.random() < 0.6:
                    self.spawn("burst")
        if not working:
            self.check_recaps(now)
        self.rare_tick(now)

    # ---- claude code session wrap-ups ----
    def check_recaps(self, now):
        # a session that's gone quiet for a while gets a short wrap-up. ones that finished while you
        # were away are rolled into one line when you're back.
        st = self.cc_stats()
        if not st or self.speech or self.state == "sleep" or self.details.visible:
            return
        done = []
        for ses in st.get("recent", []):
            end = ses["end"].timestamp()
            if ses["id"] in self.recapped or end < self.started or ses["messages"] < 4:
                continue
            last = max(end, self.cc.active.get(ses["id"], 0.0))
            if now - last >= SESSION_DONE_MIN * 60:
                done.append(ses)
        if not done:
            return
        if len(done) == 1:
            line = self.pick(RECAP_LINES).format(what=self.recap_what(done[0]))
        else:
            line = AWAY_RECAP.format(n=len(done), tokens=fmt_tokens(sum(d["tokens"] for d in done)))
        if self.say(line, force=True):
            self.recapped = (self.recapped + [d["id"] for d in done])[-50:]

    def recap_what(self, ses):
        # "34 min on Token Tracker, 58 messages, 2.1M tokens"
        mins = fmt_minutes((ses["end"] - ses["start"]).total_seconds())
        return f"{mins} on {ses['project']}, {ses['messages']} messages, {fmt_tokens(ses['tokens'])} tokens"

    # ---- tray icon and being called from outside ----
    def outside_tick(self):
        # 10 times a second: starting the pet again calls it over, and tray clicks
        if summoned(self.summon):
            self.come_here()
        if self.tray is None:
            return
        while not self.tray.events.empty():
            what = self.tray.events.get_nowait()
            if what == "left":
                self.come_here()
            elif what == "right":
                mx, my = self.root.winfo_pointerxy()
                self.details.hide()
                self.popup.show(mx, my)

    def tray_tick(self):
        # once a second: the tray icon there or not, and its tooltip
        if not self.tray_on.get():
            if self.tray is not None:
                self.tray.hide()
            return
        if self.tray is None:
            try:
                self.tray = Tray()
            except Exception:
                log_error("making the tray icon")
                self.tray_on.set(False)
                return
        rows = {r["key"]: r for r in parse_rows(self.data)} if self.data else {}
        parts = [f"{lab} {rows[k]['pct']:.0f}%" for k, lab in (("five_hour", "5-hour"), ("seven_day", "Weekly"))
                 if k in rows]
        tip = "Claude usage pet"
        if parts:
            tip += "\n" + " · ".join(parts)
        if self.error:
            tip += "\n" + short_error(self.error)
        if time.time() < self.hush_until:
            tip += "\nquiet for now"
        pcts = [rows[k]["pct"] for k in ("five_hour", "seven_day") if k in rows]
        self.tray.update(tip, max(pcts) if pcts else None)
        if not self.tray.shown:
            self.tray.show()

    # ---- fetch ----
    def start_fetch(self):
        # (menu: play fetch) a ball flies from your mouse toward the roomier side, and off the mascot goes
        if self.hidden or not self.anim.get():
            return
        s, sc = self.s(), self.screens[self.si]
        mx, my = self.root.winfo_pointerxy()
        side = 1 if sc.wr - self.x > self.x - sc.wl else -1
        x, y = min(max(mx, sc.wl + 10), sc.wr - 10), min(max(my, sc.mt + 20), sc.wb - 10)
        self.toss_ball(x, y, side * random.uniform(450, 800) * s, -random.uniform(250, 450) * s)
        self.say(self.pick(FETCH_START), force=True)

    def toss_ball(self, x, y, vx, vy):
        if self.ball_sprite is None:
            self.ball_sprite = Sprite(self.root)
            c = self.ball_sprite.canvas
            c.bind("<Button-1>", self.ball_press)
            c.bind("<B1-Motion>", self.ball_motion)
            c.bind("<ButtonRelease-1>", self.ball_release)
        si = self.find_screen(x, y)
        self.ball = {"x": x, "y": y, "vx": vx, "vy": vy, "phase": "fly", "until": 0.0, "trail": [],
                     "si": self.nearest_screen(x, y) if si is None else si}
        self.fetch_at = time.time() + 0.35   # a moment to watch it fly, then the chase

    def ball_tick(self, dt):
        b = self.ball
        if b is None:
            return
        if self.hidden:
            self.ball_sprite.hide()
            return
        s, now = self.s(), time.time()
        pb = max(2, round(3 * s))
        sc = self.screens[b["si"]]
        rad = 3 * pb
        if b["phase"] == "pet":   # in its mouth, out front
            pw, ph = self.pet_px
            b["x"], b["y"] = self.x + self.dir * (pw / 2 + rad * 0.5), self.y - ph * 0.3
        elif b["phase"] == "fly":
            g = GRAVITY * s
            b["vy"] += g * dt
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            if b["x"] < sc.wl + rad or b["x"] > sc.wr - rad:   # bounces off the screen's sides
                b["x"] = min(max(b["x"], sc.wl + rad), sc.wr - rad)
                b["vx"] = -b["vx"] * 0.6
            if b["y"] - 2 * rad < sc.mt:
                b["y"], b["vy"] = sc.mt + 2 * rad, abs(b["vy"]) * 0.4
            if b["y"] >= sc.wb:
                b["y"] = sc.wb
                b["vy"] = -b["vy"] * 0.5 if b["vy"] > 140 * s else 0.0
                if b["vy"] == 0.0:   # rolling along the floor
                    b["vx"] -= math.copysign(min(abs(b["vx"]), 750 * s * dt), b["vx"])
                    if abs(b["vx"]) < 4 * s:
                        b["vx"], b["phase"], b["until"] = 0.0, "rest", now + FETCH_SECONDS
        elif b["phase"] == "rest" and now > b["until"] and self.goto_why != "fetch":
            self.ball = None   # nobody played with it for a while: it goes away
            self.ball_sprite.hide()
            return
        if self.goto_why == "fetch":   # keeps running at it while it rolls
            self.goto_x = self.reach_x(b["x"])
        elif self.fetch_at and now >= self.fetch_at and not self.held and self.ufo is None and b["phase"] != "mouse":
            self.fetch_at = 0.0
            self.wake(hop=False)
            if self.state == "dance":
                self.state = "idle"
            self.goto_x, self.goto_why = self.reach_x(b["x"]), "fetch"
        self.ball_sprite.show(BALL, BALL_C, pb, b["x"], b["y"])

    def reach_x(self, x):
        lo, hi = self.x_limits()
        return min(max(x, lo), hi)

    def reach_ball(self):
        b = self.ball
        if b is None or b["phase"] not in ("fly", "rest"):
            return
        s = self.s()
        if self.plat is not None:   # the ball's down on the taskbar: hop down to it
            self.drop_off(through=True)
            self.goto_x, self.goto_why = self.reach_x(b["x"]), "fetch"
            return
        if abs(b["x"] - self.x) <= 26 * s and b["y"] >= self.screens[self.si].wb - 20 * s:
            b["phase"], b["vx"], b["vy"] = "pet", 0.0, 0.0   # got it. now back to you.
            self.say(self.pick(FETCH_GOT), force=True)
            mx, my = self.root.winfo_pointerxy()
            self.goto_x, self.goto_why = self.reach_x(mx), "return"
        elif b["phase"] == "fly":
            self.goto_x, self.goto_why = self.reach_x(b["x"]), "fetch"   # still rolling: after it
        else:
            self.say("I can't reach it!", force=True)

    def drop_ball(self):
        b = self.ball
        if b is None or b["phase"] != "pet":
            return
        b["phase"], b["vx"], b["vy"] = "fly", self.dir * 40 * self.s(), -120 * self.s()
        self.tally("fetches")
        self.happy_t = 1.2
        self.spawn("heart")
        self.say(self.pick(FETCH_BACK), force=True)

    def stop_fetch(self):
        # picked up or called away mid-game: the ball drops where it is, and the game stops
        if self.goto_why in ("fetch", "return"):
            self.goto_x = self.goto_why = None
        self.fetch_at = 0.0
        if self.ball and self.ball["phase"] == "pet":
            self.ball.update(phase="fly", vx=0.0, vy=0.0)

    def ball_press(self, e):
        b = self.ball
        if b is None:
            return
        if b["phase"] == "pet":
            self.say("hey! that's mine! ok, fine.", force=True)
        if self.goto_why in ("fetch", "return"):
            self.goto_x = self.goto_why = None
        self.fetch_at = 0.0
        b["phase"], b["trail"] = "mouse", [(time.perf_counter(), e.x_root, e.y_root)]
        self.ball_motion(e)

    def ball_motion(self, e):
        b = self.ball
        if b is None or b["phase"] != "mouse":
            return
        now = time.perf_counter()
        b["trail"] = [t for t in b["trail"] if now - t[0] < 0.1] + [(now, e.x_root, e.y_root)]
        pb = max(2, round(3 * self.s()))
        b["x"], b["y"] = e.x_root, e.y_root + 3 * pb
        si = self.find_screen(e.x_root, e.y_root)
        if si is not None:
            b["si"] = si
        self.ball_sprite.show(BALL, BALL_C, pb, b["x"], b["y"])

    def ball_release(self, e):
        # thrown: it keeps most of your mouse speed, and the mascot goes after it
        b = self.ball
        if b is None or b["phase"] != "mouse":
            return
        s, now = self.s(), time.perf_counter()
        trail = [t for t in b["trail"] if now - t[0] < 0.12]
        vx = vy = 0.0
        if len(trail) >= 2 and trail[-1][0] - trail[0][0] > 0.02:
            d = trail[-1][0] - trail[0][0]
            vx, vy = (trail[-1][1] - trail[0][1]) / d * 0.7, (trail[-1][2] - trail[0][2]) / d * 0.7
            k = min(1.0, 2200 * s / max(1.0, math.hypot(vx, vy)))
            vx, vy = vx * k, vy * k
        b.update(phase="fly", vx=vx, vy=vy)
        self.fetch_at = time.time() + 0.25
        self.last_touch = time.time()

    # ---- rare visitors ----
    def rare_tick(self, now):
        if not (self.rare.get() and self.anim.get()) or self.hidden or self.held:
            return
        if self.ufo or self.cat or self.ball or self.goto_x is not None or self.state in ("sleep", "work"):
            return
        if self.plat is None and self.grounded() and random.random() < 1 / (UFO_HOURS * 3600):
            self.start_ufo()
        elif random.random() < 1 / (CAT_HOURS * 3600):
            self.start_cat()

    def start_ufo(self):
        if self.ufo or self.plat is not None or not self.grounded():
            return
        self.stop_fetch()
        self.state, self.state_t = "idle", 2.0
        self.ufo = {"t": 0.0, "dropped": False, "said": False}

    def ufo_tick(self, dt):
        # runs every frame while there's a ufo. returns True while it has hold of the mascot.
        u = self.ufo
        u["t"] += dt
        t, s = u["t"], self.s()
        if t >= UFO_END:
            self.ufo = None
            return False
        if u["dropped"]:
            return False
        if t > 0.8 and not u["said"]:
            u["said"] = True
            self.say(self.pick(UFO_LINES), force=True)
        self.worried_t = max(self.worried_t, 0.3)
        floor = self.screens[self.si].wb
        self.vx = self.vy = 0.0
        if t < UFO_LIFT:
            self.y = floor
        elif t < UFO_DROP:
            self.y = floor - self.ufo_lift(s) * smooth((t - UFO_LIFT) / (UFO_GONE - UFO_LIFT))
        else:   # dropped: it falls back down like anything else
            u["dropped"] = True
            self.ufo_fall = True
            self.tally("ufo")
            return False
        return True

    def ufo_lift(self, s):
        return 56 * s   # from the floor up into the saucer

    def start_cat(self):
        sc = self.screens[self.si]
        d = random.choice((-1, 1))
        if self.cat_sprite is None:
            self.cat_sprite = Sprite(self.root)
            self.cat_sprite.canvas.bind("<Button-1>", self.cat_click)
        self.cat = {"x": sc.wl - 30 if d > 0 else sc.wr + 30, "dir": d, "speed": 60.0, "sit": 0.0, "met": False,
                    "si": self.si, "t": 0.0}

    def cat_tick(self, dt):
        c = self.cat
        if c is None:
            return
        sc, s = self.screens[min(c["si"], len(self.screens) - 1)], self.s()
        if self.hidden:
            self.cat_sprite.hide()
            return
        c["t"] += dt
        if c["sit"] > 0:
            c["sit"] -= dt
        else:
            c["x"] += c["dir"] * c["speed"] * s * dt
        if not c["met"] and c["si"] == self.si and self.plat is None and self.grounded() and not self.held \
                and abs(c["x"] - self.x) < self.pet_px[0]:
            c["met"], c["sit"] = True, 2.5   # it stops to say hi
            self.look_d, self.look_t = (1 if c["x"] > self.x else -1), 2.5
            self.happy_t = 1.5
            self.spawn("heart")
            if self.state == "walk":
                self.state, self.state_t = "idle", 3.0
            self.say(self.pick(CAT_LINES), force=True)
        if c["x"] < sc.wl - 60 or c["x"] > sc.wr + 60:
            if c["met"] or c["t"] > 2:
                self.cat = None
                self.cat_sprite.hide()
                self.tally("cats")
            return
        pb = max(2, round(3 * s))
        legs = CAT_A if c["sit"] > 0 or int(c["t"] / 0.2) % 2 else CAT_B
        self.cat_sprite.show(legs, CAT_C, pb, c["x"], sc.wb, flip=c["dir"] < 0)

    def cat_click(self, e):
        c = self.cat
        if c:
            self.play("meow")
            c["met"], c["sit"], c["speed"] = True, 0.0, 200.0   # startled: off it runs
