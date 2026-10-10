# part of the Pet: things it does on its own when it's idle (besides walking, hopping, dancing and napping):
# stargazing at night, practising a spell that backfires, and reading a little book of its own.
import datetime
import math
import random

from .art import (ARMS, BAND_C, HAT, HAT_C, LEFT_WAVE, MOON, MOON_C, ORANGE, POCKET_BOOK, POCKET_BOOK_C, SHINY,
    SINGED_HAT_C, SOOT, SPARK, STAR_C, STARS_C, WAND_C, WAVE)
from .config import ACT_CHANCE
from .lines import BACKFIRE_LINES, BOOK_LINES, PRACTICE_LINES, STARGAZE_LINES, WISH_LINES

# the practice spell's timeline (seconds): hat on, casting, poof!, sooty and dazed, shaking it off, done
POOF, SHAKE, PRACTICE_END = 2.5, 5.0, 6.0
STARS = ((-130, -60), (-100, -98), (-78, -38), (88, -88), (122, -46), (150, -104), (-150, -22), (110, -128))


class IdleMixin:
    def start_act(self, kind=None):
        # picks something to do (stargazing only at night). returns True if it started.
        if not self.anim.get() or self.held or not self.grounded():
            return False
        if kind is None:
            hour = datetime.datetime.now().hour
            kinds = ["practice", "book"] + (["stargaze", "stargaze"] if hour >= 21 or hour < 5 else [])
            kind = random.choice(kinds)
        self.state, self.act, self.act_t, self.act_said = "act", kind, 0.0, False
        self.state_t = {"stargaze": random.uniform(25, 45), "practice": PRACTICE_END,
                        "book": random.uniform(15, 30)}[kind]
        if kind == "stargaze":
            self.say(self.pick(STARGAZE_LINES))
        elif kind == "practice":
            self.say(self.pick(PRACTICE_LINES))
        self.tally({"stargaze": "stargazes", "practice": "backfires", "book": "books"}[kind])
        return True

    def maybe_act(self):
        # (when it's done standing about) now and then, one of these instead
        return random.random() < ACT_CHANCE and not self.full() and self.start_act()

    def act_tick(self, dt, s):
        t0, self.act_t = self.act_t, self.act_t + dt
        t, kind = self.act_t, self.act
        self.state_t -= dt
        pb = max(1, round(2 * s))
        bw, bh = max(1, round(4 * s)), max(2, round(8 * s))
        if kind == "practice":
            if 0.3 < t < POOF:
                self.cast_t = t   # (the wand hand waves like the wizard's)
                self.part_t -= dt
                if self.part_t <= 0:
                    self.spawn("spark")
                    self.part_t = random.uniform(0.1, 0.2) if t < POOF - 0.5 else 0.35   # it starts to fizzle...
            if t0 < POOF <= t:   # ...poof!
                self.play("pop")
                for i in range(16):
                    a = i / 16 * 2 * math.pi
                    self.parts.append({"kind": "puff", "x": 9 * bw + math.cos(a) * 6 * bw, "y": 2 * bh + math.sin(a) * bh,
                                       "vx": math.cos(a) * 40 * s, "vy": math.sin(a) * 20 * s - 15 * s,
                                       "life": random.uniform(0.7, 1.2), "c": i % 2})
            if POOF < t < SHAKE and random.random() < dt * 5:   # a wisp of smoke off the singed hat
                self.parts.append({"kind": "puff", "x": 9 * bw + random.uniform(-2, 2) * pb, "y": -9 * pb,
                                   "vx": random.uniform(-6, 6) * s, "vy": -25 * s, "life": 0.9, "c": 1})
            if t0 < POOF + 1.2 <= t:
                self.say(self.pick(BACKFIRE_LINES), force=True)
        elif kind == "stargaze":
            if int(t0 / 6) != int(t / 6):   # a shooting star now and then
                self.shooting_at = t
                if random.random() < 0.5:
                    self.say(self.pick(WISH_LINES))
        elif kind == "book" and not self.act_said and t > self.state_t * 0.5:   # (halfway through, a comment)
            self.act_said = True
            if random.random() < 0.6:
                self.say(self.pick(BOOK_LINES))
        if self.state_t <= 0:
            self.state, self.state_t, self.act = "idle", 2.0, None

    def act_frame(self):
        # what the drawing needs (20 steps a second), or None
        if self.state != "act" or not self.act:
            return None
        return (self.act, int(self.act_t * 20), int((self.act_t - self.shooting_at) * 20))

    def act_pose(self, act):
        # overrides for how it looks: {sink, eyes, eye_dir, eye_v, arms, legs, shift}
        kind, step, _ = act
        t = step / 20
        if kind == "stargaze":   # lying on its back, arms out, looking up
            return {"sink": "lie", "legs": (), "eyes": "open", "eye_dir": 0, "eye_v": -1, "arms": LEFT_WAVE[1] + WAVE[1]}
        if kind == "book":       # sat down, holding the book, reading
            return {"sink": "half", "eyes": "open", "eye_dir": 0, "eye_v": 1, "arms": LEFT_WAVE[0] + WAVE[0]}
        if t < POOF:             # waving the wand, very focused
            return {"eyes": "open", "eye_dir": 1, "eye_v": -1,
                    "arms": (ARMS[0],) + WAVE[int(t / 0.25) % 2] if t > 0.3 else ARMS}
        if t < SHAKE:            # blasted: sooty, eyes shut, arms flung out
            return {"eyes": "closed", "eye_dir": 0, "eye_v": 0, "arms": LEFT_WAVE[0] + WAVE[0], "sink": "half"}
        return {"eyes": "open", "eye_dir": 0, "eye_v": 0, "arms": ARMS, "shift": (-1, 1)[int(t / 0.08) % 2]}   # shakes it off

    def body_colour(self):
        return SHINY if self.shiny else ORANGE

    def act_body(self, act):
        kind, step, _ = act
        return SOOT if kind == "practice" and POOF <= step / 20 < SHAKE else None

    def draw_act(self, act, px, py, sink, bw, bh, pb, pet_w, pet_h):
        kind, step, shoot = act
        t, c = step / 20, self.canvas
        s = self.s()
        mid = px + pet_w // 2
        if kind == "stargaze":
            kick = int(t * 2.5) % 2   # on its back, little feet up in the air, kicking now and then
            for i, col in enumerate((4, 6, 11, 13)):
                up = bh // 2 if (i % 2) == kick and int(t / 3) % 2 else 0
                c.create_rectangle(px + col * bw, py + sink - bh + up, px + (col + 1) * bw, py + sink + 1,
                                   fill=self.body_colour(), outline="")
            for k, (dx, dy) in enumerate(STARS):   # twinkling stars, out to the sides (clear of the bubbles)
                if (int(t * 2) + k) % 4:
                    self.glyph(SPARK, mid + dx * s, py + dy * s, pb, STARS_C[k % len(STARS_C)])
            self.glyph(MOON, mid - 128 * s, py - 120 * s, pb, MOON_C, shadow=False)
            st = shoot / 20
            if 0 <= st < 0.7:   # a shooting star streaking across
                k = st / 0.7
                hx, hy = mid + (60 + 100 * k) * s, py + (-135 + 55 * k) * s
                for i in range(5):
                    c.create_rectangle(round(hx - i * 3 * pb), round(hy - i * 1.6 * pb), round(hx - i * 3 * pb + pb),
                                       round(hy - i * 1.6 * pb + pb), fill=STARS_C[0] if i == 0 else STARS_C[1],
                                       outline="")
        elif kind == "book":
            rows = POCKET_BOOK
            pb = max(2, round(pb * 1.25))   # (a touch bigger than the small pictures)
            w = len(rows[0]) * pb
            x0, y0 = mid - w / 2, py + sink + 2 * bh
            self.glyph(rows, x0, y0, pb, POCKET_BOOK_C)
            turn = t % 5
            if turn < 0.3:   # turning a page
                a, b = (7, 12) if turn < 0.15 else (1, 6)
                c.create_rectangle(round(x0 + a * pb), round(y0 - pb), round(x0 + b * pb), round(y0 + 4 * pb),
                                   fill=POCKET_BOOK_C["p"], outline="")
        elif kind == "practice":
            if t < SHAKE + 0.4:   # the wizard hat (singed after the poof)
                hat_c = {"#": HAT_C, "y": BAND_C, "*": STAR_C} if t < POOF else SINGED_HAT_C
                hx = px + 3 * bw + (12 * bw - len(HAT[0]) * pb) // 2
                self.glyph(HAT, hx, py + sink - (len(HAT) - 1) * pb, pb, hat_c, shadow=False)
            if 0.3 < t < POOF:   # the wand, in the waving hand
                hand_y = py + sink + self.hand() * bh
                for i in range(5):
                    x1, y1 = px + 17 * bw + i * pb, hand_y - (i + 1) * pb
                    c.create_rectangle(x1, y1, x1 + pb, y1 + pb, fill=WAND_C, outline="")
