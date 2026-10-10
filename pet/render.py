# part of the Pet: drawing the mascot, its bubbles and effects.
import math
import time
import tkinter.font as tkfont

from .art import (ARMS, BAND_C, BLOCK_H, BLOCK_W, BLUSH, BLUSH_C, BODY, BUBBLE, BUBBLE_TEXT, CHUTE, CHUTE_R,
    CHUTE_W, EYE, EYES, FULL_C, FULL_EDGE, HAT, HAT_C, HAY_C, HEART, HEART_C, KEY, LEFT_WAVE, LEGS_AIR,
    LEGS_STAND, LEGS_STEP, NOTE, NOTE_C, ORANGE, PANIC_C, RED, SHADOW, SPARK, SPARK_C, SPEECH, SPEECH_TEXT,
    STAR_C, STRING_C, TRACK, WAND_C, WARN_C, WAVE, ZZZ, ZZZ_C)
from .config import SPEAK_CPS
from .ui import round_rect, wrap


class RenderMixin:
    # drawing. only redraws when something visible changed; moving is just moving the window.
    def frame(self):
        anim = self.anim.get()
        now = time.time()
        grounded = self.grounded()
        airborne = self.held or not grounded
        sleeping = anim and self.state == "sleep"
        dancing = anim and self.state == "dance" and grounded
        wiz = anim and self.state == "work" and not airborne
        full = self.full()
        squash = anim and grounded and not self.held and (self.squash_t > 0 or self.pressed)
        walking = anim and self.state == "walk" and self.walking_allowed() and grounded and not squash
        beat = int(self.dance_t / 0.25) % 4 if dancing else 0
        chute = anim and self.chute and not grounded
        hay = anim and self.hay_t > 0
        if sleeping or hay:
            legs = ()
        elif self.held:
            legs = LEGS_STEP if int(self.clock / 0.12) % 2 else LEGS_AIR   # wiggling
        elif airborne:
            legs = LEGS_AIR
        elif dancing:
            legs = LEGS_STEP if beat % 2 else LEGS_STAND
        else:
            legs = LEGS_STEP if walking and self.step % 2 else LEGS_STAND
        if sleeping or (anim and self.dizzy_t > 0):
            eyes = "closed"
        elif anim and (self.happy_t > 0 or dancing):
            eyes = "happy"
        elif anim and self.worried_t > 0:
            eyes = "worried"   # a claude code tool call just failed
        elif anim and self.blink_t > 0:
            eyes = "closed"
        elif full and not airborne:
            eyes = "tired"   # a hard day's work
        else:
            eyes = "open"
        if wiz:
            eye_dir = 1   # watching the wand
        else:
            eye_dir = self.dir if walking else (self.look_d if anim and self.look_t > 0 and not sleeping else 0)
        if sleeping or hay:
            sink = "lie"   # lying down, or sat in the hay
        elif squash or (dancing and beat in (1, 3)) or (full and grounded and self.state == "idle"):
            sink = "half"   # squished, bopping to the beat, or slumped because the limit is full
        else:
            sink = None
        if wiz:
            arms = (ARMS[0],) + WAVE[1 - self.hand()]
        elif anim and self.stretch_t > 0 and not sleeping:
            arms = LEFT_WAVE[1] + WAVE[1]
        elif dancing:
            arms = (LEFT_WAVE[1] + (ARMS[1],), ARMS, (ARMS[0],) + WAVE[1], LEFT_WAVE[1] + WAVE[1])[beat]
        elif chute:
            arms = LEFT_WAVE[1] + WAVE[1]   # holding the strings
        elif anim and self.wave_t > 0 and not sleeping:
            arms = (ARMS[0],) + WAVE[int(self.wave_t / 0.18) % 2]
        else:
            arms = ARMS
        parts = tuple((p["kind"], round(p["x"]), round(p["y"]), p["c"]) for p in self.parts) if anim else ()
        show = (self.bubble_mode.get() != "hover" or self.hovering or self.held
                or self.details.visible or now < self.hover_until)
        speech = None
        if self.speech:
            if now > self.speech["until"] or self.hidden:
                self.speech = None
            else:
                text = self.speech["text"]
                typed = int((now - self.speech["start"]) * SPEAK_CPS) if anim else len(text)
                speech = (text, min(len(text), typed))
        bars = tuple(self.bubble_bars()) if self.bubble_style.get() == "bars" and self.data else None
        rot = None
        if anim and (self.held or self.angle):
            pw, ph = self.pet_px
            gx, gy = self.grab_local if self.held else (pw / 2, ph / 2)
            rot = (round(self.angle, 2), round(gx), round(gy))
        return (self.scale, legs, eyes, eye_dir, sink, arms, self.hand() if wiz else None, self.warn_level(),
                wiz, parts, tuple(self.bubble_segments()), bars, bool(self.error), show, speech, rot,
                round(math.sin(self.clock * 1.6) * 1.4) if chute else None,
                (0, -1, 0, 1)[beat] if dancing else 0,
                int(self.clock * 8) % 12 if anim and self.dizzy_t > 0 else None,
                sleeping and int(self.clock / 1.4) % 2 == 1, hay)

    def redraw(self):
        f = self.frame()
        if f != self.last_frame:
            self.draw(f)
            self.last_frame = f
        self.place()

    def font(self, px, bold=True):
        if (px, bold) not in self.fonts:
            self.fonts[(px, bold)] = tkfont.Font(root=self.root, family="Segoe UI", size=-px,
                                                 weight="bold" if bold else "normal")
        return self.fonts[(px, bold)]

    def glyph(self, rows, x, y, b, color, shadow=True):
        # a little picture made of b-sized squares. color is one colour, or {letter: colour}.
        # the dark shadow makes it show on any wallpaper.
        passes = ((max(1, b // 2), SHADOW), (0, color)) if shadow else ((0, color),)
        for d, col in passes:
            for r, line in enumerate(rows):
                for i, ch in enumerate(line):
                    if ch != ".":
                        fill = col if isinstance(col, str) else col.get(ch, col["#"])
                        self.canvas.create_rectangle(x + i * b + d, y + r * b + d, x + (i + 1) * b + d,
                                                     y + (r + 1) * b + d, fill=fill, outline="")

    def draw(self, f):
        (_, legs, eyes, eye_dir, sink_kind, arms, wand, warn, wiz, parts, segs, bars, err, show_bubble,
         speech, rot, chute, shift, dizzy, breath, hay) = f
        c = self.canvas
        c.delete("all")
        s = self.s()
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        pb = max(1, round(2 * s))     # small blocks for hearts, z's, sparks, the hat
        pet_w, pet_h = 18 * bw, 5 * bh
        font = self.font(max(8, round(11 * s)))
        pad = round(7 * s)
        if rot:
            show_bubble = False   # the usage bubble steps aside while it's tumbling about

        # usage bubble size: numbers, or two little bars
        if bars:
            lfont = self.font(max(8, round(10 * s)))
            lab_w = max(lfont.measure(lab) for lab, _, _ in bars)
            bar_w, bar_h = round(56 * s), max(3, round(5 * s))
            row_h = lfont.metrics("linespace")
            bub_w = 2 * pad + lab_w + round(6 * s) + bar_w + (round(10 * s) if err else 0)
            bub_h = len(bars) * row_h + round(6 * s)
        else:
            dot, dgap, sgap = max(4, round(6 * s)), round(4 * s), round(9 * s)
            bub_w = 2 * pad + sum(dot + dgap + font.measure(t) for t, _ in segs) + sgap * (len(segs) - 1)
            bub_h = font.metrics("linespace") + round(6 * s)
        ring = max(2, round(2 * s)) if warn else 0         # the warning ring's thickness
        tail, gap = max(2, round(4 * s)), round(2 * s) + 2 * ring + (max(2, round(1.5 * s)) if warn == 3 else 0)

        # speech bubble size
        sp_lines, sp_w, sp_h = [], 0, 0
        if speech:
            sfont = self.font(max(8, round(11 * s)), bold=False)
            key = (speech[0], s)
            if key not in self.wraps:
                self.wraps[key] = wrap(speech[0], sfont, round(190 * s))
            sp_lines = self.wraps[key]
            sp_w = max(sfont.measure(ln) for ln in sp_lines) + 2 * round(8 * s)
            sp_h = len(sp_lines) * sfont.metrics("linespace") + 2 * round(5 * s)

        side = round(30 * s)                               # room for z's, notes and sparks
        above = max((len(HAT) - 1) * pb if wiz else 0,     # room above the head: hat, parachute, stars
                    (len(CHUTE) + 10) * pb if chute is not None else 0,
                    6 * pb if dizzy is not None else 0)
        # the window is ONE fixed size whatever the mascot is doing, and its middle always sits at the
        # same spot in it. resizing or shifting the window between frames made windows flash a dark box
        # or the mascot flicker, because moving and redrawing a window don't happen at the same instant.
        hd = math.ceil(math.hypot(pet_w, pet_h) / 2) + 2   # a tilted body reaches this far from its middle
        ring_max = max(2, round(2 * s)) + max(2, round(1.5 * s))
        lh = self.font(max(8, round(11 * s)), bold=False).metrics("linespace")
        bub_max = max(2 * self.font(max(8, round(10 * s))).metrics("linespace"), font.metrics("linespace")) + round(6 * s)
        cy = (pet_h - pet_h // 2 + (len(CHUTE) + 10) * pb + round(2 * s) + 3 * ring_max + 2 * tail + bub_max
              + round(3 * s) + 4 * lh + 2 * round(5 * s) + round(40 * s))   # room for everything above it
        W = max(round(320 * s), len(CHUTE[0]) * pb + 2 * side, 2 * hd + 2 * side, bub_w + 4 * ring_max, sp_w + 4)
        cx = W // 2
        H = cy + hd
        sink = {"lie": bh, "half": bh // 2}.get(sink_kind, 0)
        up = 0

        if rot:
            # tilted: every block becomes a turned square around the body's middle
            ang = rot[0]
            ca, sa = math.cos(ang), math.sin(ang)
            mx, my = pet_w / 2, pet_h / 2
            px, py = cx - pet_w // 2, cy - pet_h // 2
            # how far the tilted body rises above its middle, so speech can sit just above it
            up = max(0, math.ceil(-min(dx * sa + dy * ca for dx in (-mx, mx) for dy in (-my, my))))

            def emit(x1, y1, x2, y2, color):
                pts = []
                for lx, ly in ((x1 - 0.5, y1 - 0.5), (x2 + 0.5, y1 - 0.5), (x2 + 0.5, y2 + 0.5), (x1 - 0.5, y2 + 0.5)):
                    dx, dy = lx - mx, ly - my
                    pts += [cx + dx * ca - dy * sa, cy + dx * sa + dy * ca]
                c.create_polygon(pts, fill=color, outline="")
        else:
            px, py = cx - pet_w // 2 + shift * max(1, bw // 2), cy - pet_h // 2

            def emit(x1, y1, x2, y2, color):
                c.create_rectangle(px + x1, py + y1, px + x2, py + y2, fill=color, outline="")

        def block(col, row, cols=1, color=ORANGE):
            y1 = row * bh + sink
            emit(col * bw, y1, (col + cols) * bw, min(y1 + bh, pet_h), color)

        # the mascot
        for row, line in enumerate(BODY):
            start, end = line.index("#"), line.rindex("#") + 1
            if row == 0 and breath:
                start, end = start + 1, end - 1   # breathing out while asleep
            block(start, row, end - start)
        for col, row in arms:
            block(col, row)
        for col in legs:
            block(col, 4)
        for col in EYES:
            x1, y1 = (col + eye_dir) * bw, bh + sink
            if eyes in ("open", "worried"):
                emit(x1, y1, x1 + bw, y1 + bh, EYE)
            elif eyes == "tired":   # heavy eyelids
                emit(x1, y1 + bh // 2, x1 + bw, y1 + bh, EYE)
            else:   # a thin line: low for closed, high for a happy squint
                ly = y1 + (bh // 5 if eyes == "happy" else bh // 2)
                emit(x1, ly, x1 + bw, ly + max(1, bh // 4), EYE)
        if eyes == "worried":   # little slanted eyebrows
            for col, inner in ((EYES[0] + eye_dir, 1), (EYES[1] + eye_dir, -1)):
                yb, th = sink + bh // 2, max(1, bh // 6)
                emit((col - 1) * bw if inner > 0 else col * bw, yb + th, col * bw if inner > 0 else (col + 1) * bw,
                     yb + 2 * th, EYE)
                emit(col * bw if inner > 0 else (col - 1) * bw, yb, (col + 1) * bw if inner > 0 else col * bw,
                     yb + th, EYE)
        if eyes == "happy":
            for col in BLUSH:
                block(col, 2, color=BLUSH_C)
        if wiz and not rot:
            # wizard hat on the head, wand in the raised hand
            hx = px + 3 * bw + (12 * bw - len(HAT[0]) * pb) // 2
            self.glyph(HAT, hx, py + sink - (len(HAT) - 1) * pb, pb,
                       {"#": HAT_C, "y": BAND_C, "*": STAR_C}, shadow=False)
            hand_y = py + sink + wand * bh
            for i in range(5):
                x1, y1 = px + 17 * bw + i * pb, hand_y - (i + 1) * pb
                c.create_rectangle(x1, y1, x1 + pb, y1 + pb, fill=WAND_C, outline="")
            x1, y1 = px + 17 * bw + 4 * pb, hand_y - 7 * pb
            c.create_rectangle(x1, y1, x1 + 2 * pb, y1 + 2 * pb, fill=STAR_C, outline="")
        if chute is not None and not rot:
            # the parachute, with strings down to its raised hands and head
            cw = len(CHUTE[0]) * pb
            cx0, cy0 = px + pet_w // 2 - cw // 2 + chute * pb, py + sink - (len(CHUTE) + 10) * pb
            self.glyph(CHUTE, cx0, cy0, pb, {"r": CHUTE_R, "w": CHUTE_W, "#": CHUTE_R})
            cb = cy0 + len(CHUTE) * pb
            lw = max(1, round(s))
            for sx_, ex in ((cx0 + pb, px + 1.5 * bw), (cx0 + cw - pb, px + 16.5 * bw),
                            (cx0 + cw * 0.35, px + 7 * bw), (cx0 + cw * 0.65, px + 11 * bw)):
                c.create_line(sx_, cb, ex, py + sink, fill=STRING_C, width=lw)
        if dizzy is not None and not rot:
            # three little stars circling its head
            cx, cy = px + 9 * bw, py + sink - 3 * pb
            for k in range(3):
                a = dizzy / 12 * 2 * math.pi + k * 2 * math.pi / 3
                self.glyph(SPARK, cx + math.cos(a) * 7 * bw - 1.5 * pb, cy + math.sin(a) * 2 * pb - 1.5 * pb,
                           pb, STAR_C)

        if hay and not rot:
            # a pile of hay round its middle: rows of straw, wider at the bottom (no outline, like the mascot)
            mid, base = px + pet_w // 2, py + pet_h
            half_w, rows = pet_w // 2 + 3 * bw, max(3, round(1.8 * bh / pb))
            for row in range(rows):
                w2 = round(half_w * (1 - 0.6 * (row / rows) ** 2) / pb) * pb
                y2 = base - row * pb
                c.create_rectangle(mid - w2, y2 - pb, mid + w2, y2, fill=HAY_C[0], outline="")
                for i in range(-w2 // pb, w2 // pb):   # streaks of lighter and darker straw
                    k = (i * 7 + row * 3) % 9
                    if k < 3:
                        c.create_rectangle(mid + i * pb, y2 - pb, mid + (i + 1) * pb, y2,
                                           fill=HAY_C[1 + k % 2], outline="")
            top = base - rows * pb
            for i, (dx, lean) in enumerate(((-0.5, -1), (-0.2, 0), (0.15, 1), (0.45, 1), (-0.35, 1))):
                x0 = mid + round(dx * half_w / pb) * pb   # stray straws poking out of the top
                for j in range(3):
                    c.create_rectangle(x0 + lean * j * pb, top - (j + 1) * pb, x0 + lean * j * pb + pb, top - j * pb,
                                       fill=HAY_C[1 + i % 2], outline="")

        # z's, notes and sparkles drift up behind the bubbles, so they never cover the words
        for kind, x, y, ci in parts:
            if kind in ("z", "Z"):
                self.glyph(ZZZ, px + x, py + y, pb + (pb // 2 + 1 if kind == "Z" else 0), ZZZ_C)
            elif kind == "spark":
                self.glyph(SPARK, px + x, py + y, pb, SPARK_C[ci], shadow=False)
            elif kind == "note":
                self.glyph(NOTE, px + x, py + y, pb, NOTE_C[ci])
            elif kind == "straw":
                c.create_rectangle(px + x, py + y, px + x + 2 * pb, py + y + pb, fill=HAY_C[ci], outline="")

        # the usage bubble. text only ever sits on solid bubbles, so there's no fuzzy edge
        # against the see-through colour.
        bx, by = (W - bub_w) // 2, py - above - gap - tail - bub_h
        if show_bubble:
            mid = W // 2
            ring_c = {1: WARN_C, 2: PANIC_C, 3: FULL_C}.get(warn, KEY)
            if warn:   # a ring around the bubble and its tail: yellow, red, or black when it's all used up
                t2 = tail + 2 * ring
                if warn == 3:   # a silver edge so the black ring shows on dark backgrounds too
                    e = max(2, round(1.5 * s))
                    round_rect(c, bx - ring - e, by - ring - e, bx + bub_w + ring + e, by + bub_h + ring + e,
                               round(5 * s) + ring + e, FULL_EDGE)
                    c.create_polygon(mid - t2 - e, by + bub_h, mid + t2 + e, by + bub_h, mid, by + bub_h + t2 + e,
                                     fill=FULL_EDGE, outline="")
                round_rect(c, bx - ring, by - ring, bx + bub_w + ring, by + bub_h + ring, round(5 * s) + ring,
                           ring_c, bg=FULL_EDGE if warn == 3 else KEY)
                c.create_polygon(mid - t2, by + bub_h - 1, mid + t2, by + bub_h - 1, mid, by + bub_h + t2,
                                 fill=ring_c, outline="")
            round_rect(c, bx, by, bx + bub_w, by + bub_h, round(5 * s), BUBBLE, bg=ring_c, smooth=bool(warn))
            c.create_polygon(mid - tail, by + bub_h - 1, mid + tail, by + bub_h - 1, mid, by + bub_h + tail,
                             fill=BUBBLE, outline="")
            if bars:
                y = by + round(3 * s)
                for lab, pct, color in bars:
                    ym = y + row_h // 2
                    c.create_text(bx + pad, ym, anchor="w", text=lab, fill=BUBBLE_TEXT, font=lfont)
                    x1 = bx + pad + lab_w + round(6 * s)
                    c.create_rectangle(x1, ym - bar_h // 2, x1 + bar_w, ym - bar_h // 2 + bar_h, fill=TRACK, outline="")
                    c.create_rectangle(x1, ym - bar_h // 2, x1 + round(bar_w * min(pct, 100) / 100),
                                       ym - bar_h // 2 + bar_h, fill=color, outline="")
                    y += row_h
                if err:
                    d = max(4, round(6 * s))
                    c.create_oval(bx + bub_w - pad - d + round(2 * s), by + round(4 * s),
                                  bx + bub_w - pad + round(2 * s), by + round(4 * s) + d, fill=RED, outline="")
            else:
                x, ym = bx + pad, by + bub_h // 2
                for i, (text, color) in enumerate(segs):
                    if i:
                        x += sgap
                    c.create_oval(x, ym - dot // 2, x + dot, ym - dot // 2 + dot, fill=color, outline="")
                    x += dot + dgap
                    c.create_text(x, ym, anchor="w", text=text, fill=BUBBLE_TEXT, font=font)
                    x += font.measure(text)

        # the speech bubble, above the usage bubble. it types itself out.
        if speech:
            sx, sy = (W - sp_w) // 2, by - ring - tail - round(3 * s) - sp_h
            if rot:
                sy = cy - up - round(6 * s) - tail - sp_h
            round_rect(c, sx, sy, sx + sp_w, sy + sp_h, round(6 * s), SPEECH)
            mid = W // 2
            c.create_polygon(mid - tail, sy + sp_h - 1, mid + tail, sy + sp_h - 1, mid, sy + sp_h + tail,
                             fill=SPEECH, outline="")
            left, lh = speech[1], sfont.metrics("linespace")
            for i, ln in enumerate(sp_lines):
                if left <= 0:
                    break
                c.create_text(sx + round(8 * s), sy + round(5 * s) + i * lh, anchor="nw", text=ln[:left],
                              fill=SPEECH_TEXT, font=sfont)
                left -= len(ln) + 1

        # hearts pop up above everything
        for kind, x, y, _ in parts:
            if kind == "heart":
                self.glyph(HEART, px + x, py + y, pb, HEART_C)

        if (W, H) != self.size:
            c.configure(width=W, height=H)
        self.size, self.half, self.top_margin = (W, H), max(pet_w, bub_w, sp_w) / 2 + 2, by
        self.center_x, self.feet_win = cx, cy - pet_h // 2 + pet_h   # where the body sits in the window
        self.body_at, self.pet_px = (px, py), (pet_w, pet_h)
        highest = sy if speech else by if show_bubble else py - above
        self.bubble_top = highest - py   # relative to the head: where new hearts appear
        body = (cx - hd, cy - hd, cx + hd, cy + hd) if rot else (px, py - above, px + pet_w, py + pet_h)
        self.rects = {"pet": body, "bubble": (bx, by, bx + bub_w, by + bub_h + tail) if show_bubble else None}
