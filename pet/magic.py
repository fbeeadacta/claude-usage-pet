# part of the Pet: the wizard's jobs. what claude code is doing (from its tool names) becomes a bit of magic:
# a spell tome (reading), a quill on a scroll (writing), falling runes (commands), a crystal ball (the web),
# a summoned little helper (agents), floating sticky notes (planning), a big question mark (asking you),
# a rune circle (add-on tools) and a thought bubble (thinking, or shortening the conversation).
# the wizard hat stays on for all of them. positions are relative to the body's top left (px, py), like particles.
import math
import random
import time

from .art import (ARMS, BODY, CIRCLE_C, EYE, EYES, HAT, HAT_C, HAT_COLOURS, HOURGLASS_C, LEFT_WAVE, LEGS_STAND,
    NOTES_C, ORANGE, ORB_C, SUMMON_C, QMARK, QMARK_BACK, QMARK_C, QMARK_EDGE, QMARK_MINI, QMARK_TINTS, QUILL,
    QUILL_C, RAIN_C, ROLL_C, RUNE_GLYPHS, RUNE_SMALL, SCRIBBLE_C, SCROLL_C, SIGIL_GLOW, STAR_C, TOME, TOME_C,
    WAND_C, WAVE)
from .fun import smooth

# how long a job's look stays after claude last used that kind of tool (seconds)
JOB_HOLD = {"ask": 120, "think": 6, "compact": 10}
HOURGLASS_TURN = 4.5   # seconds for the sand to run through and the hourglass to turn over
HOURGLASS_FLIP = 0.88  # the last part of that is the turning over
SIDE_JOBS = ("read", "write", "web", "agent", "ask", "think", "compact")   # these have a prop beside the mascot


class MagicMixin:
    def job(self):
        # what claude code is doing right now, as a wizard job (None = just the wand and sparkles)
        if self.dev_job is not None:   # (pretend work from dev mode)
            return self.dev_job[1]
        when, kind = self.cc.job
        return kind if kind and time.time() - when < JOB_HOLD.get(kind, 8) else None

    def job_side(self):
        # props go on the side with more room: towards the middle of the screen
        sc = self.screens[self.si]
        return 1 if self.x < (sc.wl + sc.wr) / 2 else -1

    def job_frame(self):
        # what the drawing needs to know (changes 30 times a second while a job is on)
        kind = self.job()
        if not kind:
            return None
        return (kind, int(self.cast_t * 30), self.job_side(), int(min(5.0, time.time() - self.job_since) * 30))

    def dims(self):
        s = self.s()
        bw, bh = max(1, round(4 * s)), max(2, round(8 * s))
        return s, bw, bh, max(1, round(2 * s)), 18 * bw, 5 * bh

    # ---- how the mascot holds itself for each job ----
    def job_pose(self, job):
        # (arms, eye direction, eyes up -1 / down 1, wand side or None)
        kind, phase, side, _ = job
        t = phase / 30
        flap = int(t / 0.22) % 2
        up_both = LEFT_WAVE[1] + WAVE[1]
        side_arm = (lambda frame: (ARMS[0],) + WAVE[frame]) if side > 0 else (lambda frame: LEFT_WAVE[frame] + (ARMS[1],))
        if kind == "read":
            return LEFT_WAVE[0] + WAVE[0], side, 0, None       # arms out, holding the book up with magic
        if kind == "write":
            return side_arm(flap), side, 0, None                # conducting the quill
        if kind == "bash":
            return (LEFT_WAVE[flap] + WAVE[1 - flap]), 0, -1, None   # both hands up, runes raining down
        if kind == "web":
            return side_arm(1), side, 0, side                   # wand up: wingardium leviosa
        if kind == "agent":
            return up_both, side, 1, None                       # summoning, looking down at the circle
        if kind == "plan":
            return (LEFT_WAVE[flap] + WAVE[flap]), 0, -1, None  # keeping the notes up
        if kind == "ask":
            return side_arm(1), side, -1, None                  # pointing up at the question
        if kind == "mcp":
            return LEFT_WAVE[0] + WAVE[0], 0, 1, None           # arms out, channelling the circle
        return LEFT_WAVE[0] + WAVE[0], side, 0, None           # thinking: watching the hourglass, hands out

    # ---- where the props are (shared by the drawing and the particles) ----
    def props(self, kind, t, jt, side):
        s, bw, bh, pb, pw, ph = self.dims()
        mid, edge = pw / 2, (pw if side > 0 else 0)
        out = {}
        if kind == "read":
            tb = pb
            w = len(TOME[0][0]) * tb
            x0 = edge + 10 * s if side > 0 else edge - 10 * s - w
            phase = t % 3.0   # a page turns every 3 seconds, over 0.75 s
            out["tome"] = (x0, -9 * tb + round(math.sin(t * 2)) * tb, tb, int(phase / 0.15) + 1 if phase < 0.75 else 0,
                           int(t / 3.0) % len(TOME))
        elif kind == "write":
            w = 22 * pb
            x0 = edge + 12 * s if side > 0 else edge - 12 * s - w
            out["scroll"] = (x0, -8 * pb + math.sin(t * 2) * pb)
            chars = int(jt * 12) % 110           # writes 5 lines of 18, then pauses and starts a fresh page
            line = min(4, chars // 18)
            done = min(18, chars - line * 18) if chars < 90 else 18
            out["written"] = min(90, chars)
            sx, sy = out["scroll"]
            out["nib"] = (sx + 2 * pb + done * pb + math.sin(t * 25) * pb * 0.7,
                          sy + (4 + 2 * line) * pb + math.cos(t * 31) * pb * 0.5)
        elif kind == "web":
            r = 8 * pb
            out["orb"] = (edge + side * (24 * s + r) + math.sin(t * 0.85) * 1.5 * pb,
                          -2 * pb + math.sin(t * 1.7) * 3 * pb, r)
            hx = (17 * bw + pb if side > 0 else -pb)
            out["tip"] = (hx + side * 5 * pb + math.sin(t * 3) * pb, bh - 6 * pb)   # the wand's tip, swishing
        elif kind == "agent":
            mbw = max(1, bw // 2)
            out["portal"] = (edge + side * (20 * s + 9 * mbw), ph - pb, 14 * mbw, max(3, 5 * s))
        elif kind == "ask":
            qb = max(2, round(pb * 1.5))
            out["q"] = (edge + side * 40 * s - (len(QMARK[0]) * qb if side < 0 else 0) + math.sin(t * 1.3) * pb,
                        -40 * s + math.sin(t * 2.2) * 2 * pb, qb)
        elif kind in ("think", "compact"):
            out["float"] = (mid + side * (mid + 24 * s), -6 * s + round(math.sin(t * 1.8)) * pb)   # (whole blocks: stays crisp)
            out["sand"] = (t % HOURGLASS_TURN) / HOURGLASS_TURN   # how much sand has run down
        elif kind == "plan":
            out["notes"] = [(mid + math.cos(t * 1.2 + k * math.pi / 2) * (mid + 26 * s),
                             ph * 0.4 - 6 * pb + math.sin(t * 1.2 + k * math.pi / 2) * 13 * s + math.sin(t * 2 + k) * 2 * pb,
                             math.sin(t * 1.2 + k * math.pi / 2), k) for k in range(4)]
        elif kind == "mcp":
            out["ring"] = (mid, ph - 3 * pb, mid + 24 * s, max(4, 9 * s))
        return out

    # ---- particles while it works ----
    def job_spawn(self, kind):
        # one puff of particles for this job; returns the seconds until the next
        s, bw, bh, pb, pw, ph = self.dims()
        t, jt, side = self.cast_t, time.time() - self.job_since, self.job_side()
        at = self.props(kind, t, jt, side)
        R = random.uniform

        def mote(x, y, vx, vy, life, colours):
            self.parts.append({"kind": "mote", "x": x, "y": y, "vx": vx * s, "vy": vy * s, "life": life,
                               "c": random.choice(colours)})

        if kind == "read":
            x0, y0, tb, _, _ = at["tome"]
            # little runes and sparkles float up off the pages
            self.parts.append({"kind": "glyph", "x": x0 + R(2, 22) * tb, "y": y0 + R(0, 4) * tb, "vx": R(-8, 8) * s,
                               "vy": -R(22, 42) * s, "life": R(0.7, 1.1),
                               "c": random.randrange(len(RUNE_GLYPHS)) + 10 * random.choice((3, 4)) + 100})
            mote(x0 + R(2, 24) * tb, y0 + R(1, 8) * tb, R(-10, 10), R(-30, -10), 0.6, (0, 3, 1))
            return R(0.12, 0.22)
        if kind == "write":
            nx, ny = at["nib"]
            for _ in range(2):   # ink and gold flecks off the nib
                mote(nx, ny, R(-15, 15), R(-30, 5), R(0.3, 0.6), (0, 4, 3, 7))
            return 0.07
        if kind == "bash":
            # a column of runes falls past it, brightest at the bottom, like rain on a window
            x, v, front = R(-50 * s, pw + 50 * s), R(70, 115), random.random() < 0.35
            for k in range(4):
                self.parts.append({"kind": "glyph", "x": x, "y": -42 * s - k * 12 * s - R(0, 20 * s), "vx": 0.0,
                                   "vy": v * s, "life": (ph + 70 * s + k * 12 * s) / (v * s),
                                   "c": random.randrange(len(RUNE_GLYPHS)) + 10 * min(2, k) + (100 if front else 0)})
            mote(R(0, pw), -2 * pb, R(-10, 10), R(-40, -15), 0.5, (6, 3))
            return R(0.1, 0.17)
        if kind == "web":
            ox, oy, r = at["orb"]
            a = R(0, 2 * math.pi)   # sparkles circling the ball, and a few drifting off it
            mote(ox + math.cos(a) * (r + 2 * pb), oy + math.sin(a) * (r + 2 * pb), -math.sin(a) * 40,
                 math.cos(a) * 40 - 10, 0.6, (1, 3, 2))
            tx, ty = at["tip"]
            mote(tx, ty, (ox - tx) * 1.6 / s, (oy - ty) * 1.6 / s, 0.6, (0, 3))   # the levitation stream
            return 0.08
        if kind == "agent":
            gx, gy, rx, ry = at["portal"]
            a = R(0, 2 * math.pi)
            mote(gx + math.cos(a) * rx, gy + math.sin(a) * ry, 0, R(-70, -35), R(0.5, 0.9), (4, 5, 3))
            return 0.06
        if kind == "plan":
            x, y, depth, k = random.choice(at["notes"])
            mote(x, y, R(-10, 10), R(-25, -5), 0.5, (0, 2, 3))
            return 0.12
        if kind == "ask":
            qx, qy, qb = at["q"]
            mote(qx + R(-2, 9) * qb, qy + R(-2, 12) * qb, R(-12, 12), R(-25, -5), 0.6, (7, 3, 0))
            return 0.14
        if kind == "mcp":
            cx, cy, rx, ry = at["ring"]
            a = R(0, 2 * math.pi)
            mote(cx + math.cos(a) * rx, cy + math.sin(a) * ry, 0, R(-60, -30), R(0.5, 0.8), (4, 5, 3))
            return 0.05
        cx, cy = at["float"]
        cb = max(2, round(pb * 1.5))
        if kind == "compact":   # sparkles drawn in toward the scroll as it rolls up
            a = R(0, 2 * math.pi)
            mote(cx + math.cos(a) * 26 * s, cy + math.sin(a) * 16 * s, -math.cos(a) * 45, -math.sin(a) * 45, 0.55,
                 (0, 3, 4))
            return 0.08
        # thinking: a glimmer of sand, and the odd sparkle drifting off the glass
        mote(cx + R(-5, 5) * cb, cy + R(-6, 6) * cb, R(-10, 10), R(-25, -8), 0.6, (0, 7, 3))
        if at["sand"] > HOURGLASS_FLIP:   # turning itself over: a little burst
            for _ in range(6):
                a = R(0, 2 * math.pi)
                mote(cx, cy, math.cos(a) * 60, math.sin(a) * 60, 0.45, (0, 3, 7))
        return R(0.15, 0.25)

    # ---- drawing ----
    def draw_job(self, job, stage, px, py):
        # stage "back" is drawn before the mascot, "front" after it
        kind, phase, side, jphase = job
        t, jt = phase / 30, jphase / 30
        s, bw, bh, pb, pw, ph = self.dims()
        at = self.props(kind, t, jt, side)
        c = self.canvas

        def rect(x0, y0, x1, y1, fill):
            c.create_rectangle(round(px + x0), round(py + y0), round(px + x1), round(py + y1), fill=fill, outline="")

        if kind == "read":
            x0, y0, tb, flip, page = at["tome"]
            if stage == "front":
                cols = dict(TOME_C, b=SIGIL_GLOW[int(t * 4) % len(SIGIL_GLOW)])   # the sigil pulses
                self.glyph(TOME[page], px + x0, py + y0, tb, cols)
                if flip:   # a page turning, right to left: lifting, standing up at the spine, settling down
                    a, top, b, bottom = ((20, -1, 25, 3), (15, -2, 22, 8), (12, -4, 14, 9), (5, -2, 11, 8),
                                         (2, -1, 10, 9))[flip - 1]
                    rect(x0 + a * tb, y0 + top * tb, x0 + b * tb, y0 + bottom * tb, TOME_C["p"])
                    edge_col = a if flip <= 3 else b - 1
                    rect(x0 + edge_col * tb, y0 + top * tb, x0 + (edge_col + 1) * tb, y0 + bottom * tb, TOME_C["P"])
        elif kind == "write" and stage == "front":
            sx, sy = at["scroll"]
            w = 22 * pb
            rect(sx, sy + pb, sx + w, sy + 15 * pb, SCROLL_C)                  # the parchment
            for y_ in (sy, sy + 15 * pb):                                        # rolled ends
                rect(sx - pb, y_, sx + w + pb, y_ + 2 * pb, ROLL_C)
            written = at["written"]
            for i in range(5):   # handwriting: wobbly ink, line by line, with gaps between the words
                n = max(0, min(18, written - i * 18))
                for j in range(n):
                    if (j + i * 2) % 6 == 5:
                        continue
                    dy = -(pb // 2) if (j * 7 + i * 3) % 4 == 0 else 0
                    rect(sx + (2 + j) * pb, sy + (4 + 2 * i) * pb + dy, sx + (3 + j) * pb,
                         sy + (5 + 2 * i) * pb + dy, SCRIBBLE_C)
            nx, ny = at["nib"]
            qb = max(2, round(pb * 1.5))   # the quill, nib on the ink
            self.glyph(QUILL, px + nx, py + ny - 6 * qb, qb, QUILL_C)
        elif kind == "web" and stage == "front":
            ox, oy, r = at["orb"]
            self.orb(px + ox, py + oy, r, pb, t)
            hx = px + (17 * bw + pb if side > 0 else -pb)   # the wand, from the raised hand toward the ball
            tx, ty = at["tip"]
            for i in range(5):
                x = hx + side * i * pb + (tx - (hx - px + side * 5 * pb)) * i / 5
                c.create_rectangle(round(x), round(py + bh - (i + 1) * pb), round(x + pb), round(py + bh - i * pb),
                                   fill=WAND_C, outline="")
            c.create_rectangle(round(px + tx - pb), round(py + ty - pb), round(px + tx + pb), round(py + ty + pb),
                               fill=STAR_C, outline="")
        elif kind == "agent":
            gx, gy, rx, ry = at["portal"]
            self.ellipse_ring(px + gx, py + gy, rx, ry, pb, t * 3, SUMMON_C, "back" if stage == "back" else "front")
            if stage == "front":   # a little one of itself, rising out of the circle
                mbw, mbh, mpb = max(1, bw // 2), max(1, bh // 2), max(1, pb // 2)
                rise = min(1.0, jt / 1.6)
                rise = rise * rise * (3 - 2 * rise)
                mw, mh = 18 * mbw, 5 * mbh
                hop = mpb * 2 if rise >= 1 and int(t * 3) % 3 == 0 else 0
                self.draw_mini(px + gx - mw / 2, py + gy - mh * rise - hop, mbw, mbh, mpb, -side,
                               int(t * 5), clip=py + gy, wave=rise >= 1)
        elif kind == "plan":
            for x, y, depth, k in at["notes"]:   # behind the mascot on the far side of the circle, in front on the near
                if (depth < 0) == (stage == "back"):
                    self.note(px + x, py + y, pb, k, math.sin(t * 2 + k) * 0.3)
        elif kind == "ask":
            qx, qy, qb = at["q"]
            self.question(px + qx, py + qy, qb, t, stage)
        elif kind == "mcp":
            cx, cy, rx, ry = at["ring"]
            self.ellipse_ring(px + cx, py + cy, rx, ry, pb, t * 2, CIRCLE_C, stage, dots=44)
            self.ellipse_ring(px + cx, py + cy, rx * 0.62, ry * 0.62, pb, -t * 3, CIRCLE_C[::-1], stage, dots=22)
            for k in range(6):   # runes riding round the circle
                a = t * 0.8 + k * math.pi / 3
                if (math.sin(a) < 0) == (stage == "back"):
                    self.glyph(RUNE_SMALL[k % len(RUNE_SMALL)], px + cx + math.cos(a) * rx - 1.5 * pb,
                               py + cy + math.sin(a) * ry - 3 * pb, pb, CIRCLE_C[k % 2])
        elif kind == "think" and stage == "front":
            # a magic hourglass floating beside it: glowing sand runs down, then it flips itself over
            cx, cy = at["float"]
            self.hourglass(px + cx, py + cy, pb, at["sand"], t)
        elif kind == "compact" and stage == "front":
            # shortening the conversation: a floating scroll rolling itself up, then unrolling again
            cx, cy = at["float"]
            cb = max(2, round(pb * 1.5))
            half = round(2 + 5 * (0.5 + 0.5 * math.cos(t * 2.2))) * cb   # the open part, shrinking and growing
            thick = cb * (3 if half <= 3 * cb else 2)                    # rolled up: fatter rolls
            rect(cx - half, cy - 4 * cb, cx + half, cy + 4 * cb, SCROLL_C)
            for i in range(-3, 4, 2):   # its writing, squeezed along with it
                if half > 2 * cb:
                    rect(cx - half + cb, cy + i * cb, cx + half - cb, cy + i * cb + max(1, cb // 2), SCRIBBLE_C)
            for ex in (cx - half - thick, cx + half):
                rect(ex, cy - 5 * cb, ex + thick, cy + 5 * cb, ROLL_C)
                rect(ex + thick // 3, cy - 6 * cb, ex + thick - thick // 3, cy + 6 * cb, HAT_C)   # the rod's ends

    def rune(self, x, y, b, ci):
        # one falling rune, drawn as a few strokes (each row's runs of blocks in one go: it's drawn a lot)
        c, colour = self.canvas, RAIN_C[ci // 10 % 10]
        for r, row in enumerate(RUNE_GLYPHS[ci % 10]):
            i = 0
            while i < len(row):
                if row[i] == "#":
                    j = i
                    while j < len(row) and row[j] == "#":
                        j += 1
                    c.create_rectangle(x + i * b, y + r * b, x + j * b, y + (r + 1) * b, fill=colour, outline="")
                    i = j
                else:
                    i += 1

    def orb(self, cx, cy, r, b, t):
        # a crystal ball, cell by cell: a dark rim, glass shaded lighter at the top, a nebula swirling inside,
        # twinkling stars, a shine and a pale reflection. it sits in a little gold claw cradle that floats with it.
        c = self.canvas
        n = int(r // b)

        def cell(i, j, col):
            c.create_rectangle(round(cx + i * b), round(cy + j * b), round(cx + (i + 1) * b), round(cy + (j + 1) * b),
                               fill=col, outline="")

        stars = ((-2, 1), (2, -3), (1, 3), (-3, -1), (3, 1))
        for j in range(-n, n):
            for i in range(-n, n):
                d = math.hypot(i + 0.5, j + 0.5)
                if d > n:
                    continue
                v = (j + 0.5) / n
                col = ORB_C["rim"] if d > n - 1 else ORB_C["top"] if v < -0.4 else ORB_C["mid"] if v < 0.3 else ORB_C["low"]
                if d <= n - 1.5:
                    a = math.atan2(j + 0.5, i + 0.5)
                    swirl = 2 * a - d * 0.8 + t * 2.2   # two spiral arms, turning
                    if math.sin(swirl) > 0.72:
                        col = ORB_C["pink"] if int((swirl + math.pi / 2) // (2 * math.pi)) % 2 else ORB_C["cyan"]
                    elif math.sin(swirl) > 0.4:
                        col = ORB_C["haze"]
                    if n - 2.4 < d and 0.2 < a < 1.3:
                        col = ORB_C["glint"]   # the reflection, low on the right
                cell(i, j, col)
        for k, (i, j) in enumerate(stars):
            if (k + int(t * 3)) % 3 == 0:
                cell(i, j, ORB_C["shine"])
        for i, j, col in ((-4, -5, "shine"), (-5, -4, "shine"), (-4, -4, "shine"), (-3, -6, "glint"), (-6, -3, "glint")):
            cell(i, j, ORB_C[col])
        # the cradle: claws up the sides, a ring, a stem and a foot
        g, o = ORB_C["gold"], ORB_C["bronze"]
        for i, j, col in ((-n + 1, n - 3, g), (-n + 1, n - 2, g), (-n + 2, n - 1, g), (n - 2, n - 3, g), (n - 2, n - 2, g),
                          (n - 3, n - 1, g)):
            cell(i, j, col)
        for i in range(-4, 4):
            cell(i, n, g)
        for i in range(-3, 3):
            cell(i, n + 1, o)
        for i in (-1, 0):
            cell(i, n + 2, g)
        for i in range(-3, 3):
            cell(i, n + 3, g if abs(i + 0.5) < 2 else o)

    def question(self, x0, y0, qb, t, stage):
        # a chunky golden question mark: a 3d edge, a band of light sweeping across, a dot that bounces on its own,
        # a coin-flip spin every few seconds, and three tiny question marks circling it
        c = self.canvas
        w, h = len(QMARK[0]), len(QMARK)
        mx, my = x0 + w * qb / 2, y0 + (h + 3) * qb / 2
        mb = max(2, qb * 2 // 3)
        for k in range(3):   # the little ones: behind on the far side of their circle, in front on the near
            a = t * 1.6 + k * 2 * math.pi / 3
            if (math.sin(a) < 0) == (stage == "back"):
                self.glyph(QMARK_MINI, mx + math.cos(a) * 7 * qb - 1.5 * mb, my + math.sin(a) * 2.5 * qb - 2.5 * mb, mb,
                           QMARK_TINTS[k])
        if stage == "back":
            return
        spin = (t % 3.2) / 0.6
        scale = math.cos(spin * 2 * math.pi) if spin < 1 else 1.0   # side-on in the middle of a spin
        face = QMARK_C if scale >= 0 else QMARK_BACK
        sweep = (t * 14) % 30
        depth = max(1, qb // 2)

        def cell(x, y, col, off=0):
            left = mx + (x - w / 2) * qb * scale
            right = mx + (x + 1 - w / 2) * qb * scale
            x1, x2 = min(left, right), max(left, right)
            if x2 - x1 < 1:
                x2 = x1 + 1
            c.create_rectangle(round(x1 + off), round(y0 + y * qb + off), round(x2 + off), round(y0 + (y + 1) * qb + off),
                               fill=col, outline="")

        for layer in ("edge", "face"):
            for y, row in enumerate(QMARK):
                for x, ch in enumerate(row):
                    if ch == "#":
                        if layer == "edge":
                            if abs(scale) > 0.3:
                                cell(x, y, QMARK_EDGE, depth)
                        else:
                            lit = scale > 0 and 0 <= x + y - sweep < 2
                            cell(x, y, "#fff3c4" if lit else face)
        hop = abs(math.sin(t * 4)) * 2.5 * qb   # the dot bounces under it
        for x in (3, 4, 5):
            for y in (0, 1):
                for col, off in ((QMARK_EDGE, depth), (QMARK_C, 0)):
                    c.create_rectangle(round(x0 + x * qb + off), round(y0 + (h + 1 + y) * qb - hop + off),
                                       round(x0 + (x + 1) * qb + off), round(y0 + (h + 2 + y) * qb - hop + off),
                                       fill=col, outline="")

    def ellipse_ring(self, cx, cy, rx, ry, b, turn, colours, stage, dots=26):
        # a flat glowing ring on the floor. the far half is drawn behind the mascot, the near half in front.
        c = self.canvas
        for i in range(dots):
            a = i / dots * 2 * math.pi
            if (math.sin(a) < 0) != (stage == "back"):
                continue
            bright = (math.cos(a - turn) + 1) / 2   # a band of light running round it
            col = colours[2] if bright > 0.85 else colours[0] if (i % 2) else colours[1]
            x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
            c.create_rectangle(round(x - b / 2), round(y - b / 2), round(x + b / 2), round(y + b / 2), fill=col,
                               outline="")

    def note(self, cx, cy, b, k, tilt):
        # a sticky note, a little tilted, with two scribbled lines
        paper, strip = NOTES_C[k % len(NOTES_C)]
        ca, sa = math.cos(tilt), math.sin(tilt)

        def poly(x0, y0, x1, y1, fill):
            pts = []
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                pts += [cx + x * ca - y * sa, cy + x * sa + y * ca]
            self.canvas.create_polygon(pts, fill=fill, outline="")

        h = 4 * b
        poly(-h + b / 2, -h + b / 2, h + b / 2, h + b / 2, "#2b1a14")   # a soft shadow
        poly(-h, -h, h, h, paper)
        poly(-h, -h, h, -h + b, strip)
        for y in (-0.5 * b, 1.2 * b):
            poly(-h + b, y, h - b * (1.5 if y > 0 else 1), y + max(1, b / 2), "#6b6a65")

    def hourglass(self, cx, cy, b, phase, t):
        # an ornate hourglass, cell by cell: gold caps with finials, turned wooden posts, glass with a highlight,
        # sand that funnels down in the top bulb and piles up in the bottom one. at the end it turns itself over.
        c = self.canvas
        sand = min(1.0, phase / HOURGLASS_FLIP)                       # how much has run down
        turn = math.pi * smooth((phase - HOURGLASS_FLIP) / (1 - HOURGLASS_FLIP)) if phase > HOURGLASS_FLIP else 0.0
        W, H, mid = 15, 21, 7
        cells = {}
        for x in range(1, 14):
            cells[(x, 0)] = "G"                                       # top cap: light edge, gold, finials
        for x in range(15):
            cells[(x, 1)] = "o" if x in (0, 14) else "g"
            cells[(x, 19)] = "o" if x in (0, 14) else "g"
        for x in range(1, 14):
            cells[(x, 20)] = "o"
        for y in range(2, 19):                                        # turned wooden posts with gold collars
            for x in (1, 13):
                cells[(x, y)] = "g" if y in (2, 18) else ("W" if y % 4 == 0 else "w")
        profile = {3: 4, 4: 4, 5: 4, 6: 3, 7: 2, 8: 1, 9: 1, 10: 0}   # each row's half-width inside the glass
        for y in range(11, 18):
            profile[y] = profile[20 - y]
        for x in range(3, 12):
            cells[(x, 2)] = cells[(x, 18)] = "l"
        top_rows = round(7 * (1 - sand))                             # sand left in the top bulb (rows 3..9)
        pile = round(7 * sand)                                        # sand piled in the bottom bulb (rows 11..17)
        for y in range(3, 18):
            half = profile[y]
            cells[(mid - half - 1, y)] = cells[(mid + half + 1, y)] = "l"
            for x in range(mid - half, mid + half + 1):
                fill = "i"
                if y <= 9 and y >= 10 - top_rows:
                    surface = y == 10 - top_rows
                    if not (surface and x == mid and top_rows > 1):   # the dip where it drains away
                        fill = "y"
                elif y >= 11 and y >= 18 - pile:
                    k = y - (18 - pile)                               # rows from the top of the pile
                    if abs(x - mid) <= k + 1:                         # a mound, wider toward the bottom
                        fill = "y"
                if fill == "y" and (x * 3 + y * 5) % 7 == 0:
                    fill = "Y"                                        # darker grains
                cells[(x, y)] = fill
            if y in (4, 5, 6, 12, 13, 14) and half >= 3:
                cells[(mid - half, y)] = "h"                          # a shine down the left of each bulb
        if 0.01 < sand < 1:                                           # the falling stream, flickering
            for y in range(10, 18 - pile):
                if (y + int(t * 12)) % 3:
                    cells[(mid, y)] = "y"
        if int(t * 2) % 3 == 0:                                       # a twinkle of magic in the empty glass
            cells[(mid + 2, 4 if sand > 0.5 else 15)] = "s"
        x0, y0 = cx - W * b / 2, cy - H * b / 2
        ca, sa = math.cos(turn), math.sin(turn)
        for (x, y), ch in cells.items():
            col = HOURGLASS_C[ch]
            if not turn:
                c.create_rectangle(round(x0 + x * b), round(y0 + y * b), round(x0 + (x + 1) * b), round(y0 + (y + 1) * b),
                                   fill=col, outline="")
                continue
            pts = []   # turning over: every cell becomes a turned square round the middle
            for dx, dy in ((x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)):
                rx, ry = x0 + dx * b - cx, y0 + dy * b - cy
                pts += [cx + rx * ca - ry * sa, cy + rx * sa + ry * ca]
            c.create_polygon(pts, fill=col, outline="")

    def draw_mini(self, x0, y0, mbw, mbh, mpb, side, beat, clip=None, wave=False):
        # a little one of the mascot, with its own hat and wand. clip = nothing below this line (rising from the floor)
        c = self.canvas

        def blk(col, row, cols=1, color=ORANGE):
            top, bottom = y0 + row * mbh, y0 + (row + 1) * mbh
            if clip is not None:
                bottom = min(bottom, clip)
            if bottom > top:
                c.create_rectangle(x0 + col * mbw, top, x0 + (col + cols) * mbw, bottom, fill=color, outline="")

        for row, line in enumerate(BODY):
            a = line.index("#")
            blk(a, row, line.rindex("#") + 1 - a)
        arms = ARMS if not wave else ((ARMS[0],) + WAVE[beat % 2] if side > 0 else LEFT_WAVE[beat % 2] + (ARMS[1],))
        for col, row in arms:
            blk(col, row)
        for col in LEGS_STAND:
            blk(col, 4)
        for col in EYES:
            blk(col, 1, color=EYE)
        if clip is None or y0 < clip:
            hx = x0 + 3 * mbw + (12 * mbw - len(HAT[0]) * mpb) // 2
            self.glyph(HAT, hx, y0 - (len(HAT) - 1) * mpb, mpb, HAT_COLOURS, shadow=False)
