# part of the Pet: drawing the mascot, its bubbles and effects.
import math
import time
import tkinter.font as tkfont

from .art import (ARMS, BEAM_C, BLOCK_H, BLOCK_W, BLUSH, BLUSH_C, BODY, BUBBLE, BUBBLE_TEXT, BUCKET, BUCKET_C,
    CANDLE, CANDLE_BASE, CANDLE_C, CHUTE, CHUTE_R, CHUTE_W, EYE, EYES, FULL_C, FULL_EDGE, GLOW_C, GRIP_C, HARNESS_C,
    HAT, HAT_COLOURS, HAY_C, HEART, HEART_C, KEY, LEFT_WAVE, LEGS_AIR, LEGS_STAND, LEGS_STEP, MC_WATER, MOTE_C,
    NOTE, NOTE_C, ORANGE, OUTFITS, PANIC_C, RED, SHADOW, SHINY, SMOKE_C, SPARK, SPARK_C, SPEECH, SPEECH_TEXT,
    STAR_C, STRING_C, TRACK, UFO, UFO_C, UFO_LIGHTS, WAND_C, WARN_C, WAVE, ZZZ, ZZZ_C)
from .bungee import HARNESS_RING
from .config import HAY_TIME, SPEAK_CPS
from .fun import UFO_BEAM, UFO_DROP, UFO_END, UFO_GONE, season, smooth
from .magic import SIDE_JOBS
from .travel import FADES
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
        squash = anim and grounded and not self.held and (self.squash_t > 0 or self.pressed)
        walking = (anim and grounded and not squash
                   and ((self.state == "walk" and self.walking_allowed()) or self.goto_x is not None
                        or abs(self.walk_v) > 2 * self.s()))
        beat = int(self.dance_t / 0.25) % 4 if dancing else 0
        chute = anim and self.chute and not grounded
        hay = int((HAY_TIME - self.hay_t) * 30) + 1 if anim and self.hay_t > 0 else 0   # (how long it's been in it)
        straws = anim and self.straw_t > 0 and not self.held
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
        else:
            eyes = "open"
        job = self.job_frame() if wiz else None   # what claude is doing, as a wizard job (pet/magic.py)
        pose = self.job_pose(job) if job else None
        eye_v = 0
        if wiz:
            eye_dir, eye_v = pose[1:3] if pose else (1, 0)   # watching the wand, or the job
        elif walking or (anim and self.look_t > 0 and not sleeping):
            eye_dir = self.dir if walking else self.look_d
        elif anim and not sleeping and eyes in ("open", "worried"):
            eye_dir, eye_v = self.gaze()   # watching your mouse pointer
        else:
            eye_dir = 0
        if hay:
            sink = "hay"   # sat in the hay pile (pet/hay.py)
        elif sleeping:
            sink = "lie"   # lying down
        elif squash or (dancing and beat in (1, 3)):
            sink = "half"   # squished, or bopping to the beat
        else:
            sink = None
        if wiz and pose:
            arms = pose[0]
        elif wiz:
            arms = (ARMS[0],) + WAVE[1 - self.hand()]
        elif anim and self.stretch_t > 0 and not sleeping:
            arms = LEFT_WAVE[1] + WAVE[1]
        elif dancing:
            arms = (LEFT_WAVE[1] + (ARMS[1],), ARMS, (ARMS[0],) + WAVE[1], LEFT_WAVE[1] + WAVE[1])[beat]
        elif chute:
            arms = LEFT_WAVE[1] + WAVE[1]   # holding the strings
        elif anim and self.wave_t > 0 and not sleeping:
            arms = (ARMS[0],) + WAVE[int(self.wave_t / 0.18) % 2]
        elif anim and self.bungee_frame():   # dangling from the bungee cord, waving
            arms = (ARMS[0],) + WAVE[int(self.clock / 0.18) % 2]
        else:
            arms = ARMS
        act = self.act_frame() if anim and grounded and not self.held else None   # an idle activity (pet/idle.py)
        shift = (0, -1, 0, 1)[beat] if dancing else 0
        if act:
            pose = self.act_pose(act)
            sink = pose.get("sink", sink)
            legs = pose.get("legs", legs)
            eyes, eye_dir, eye_v = pose.get("eyes", eyes), pose.get("eye_dir", eye_dir), pose.get("eye_v", eye_v)
            arms, shift = pose.get("arms", arms), pose.get("shift", shift)
        trip = self.trip_frame() if anim and not self.held else None   # on its way to another monitor
        if trip:
            pose = self.trip_pose(trip)
            sink = pose.get("sink", sink)
            legs = pose.get("legs", legs)
            eyes, eye_dir, eye_v = pose.get("eyes", eyes), pose.get("eye_dir", eye_dir), pose.get("eye_v", eye_v)
            arms = pose.get("arms", arms)
        bucket = self.bucket_frame() if anim and not self.held else None   # the water bucket jump (pet/bucket.py)
        harness = anim and self.bungee is not None   # bungee jumping (pet/bungee.py)
        water = self.water_depth() if anim and not self.held else 0
        if bucket and bucket[4]:
            eye_dir, eye_v = 0, 1   # looking down at where the water's going
        stunt = self.stunt_pose() if anim and not self.held else None   # zipline, pole, web swing (pet/stunts.py)
        pole = None
        if stunt:
            arms, legs = stunt.get("arms", arms), stunt.get("legs", legs)
            eye_dir, pole = stunt.get("eye_dir", eye_dir), stunt.get("pole")
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
        night = self.bedtime_now() if self.dev_outfit is None else self.dev_outfit == "bedtime"   # (dev mode's pick)
        lead = 1 if self.dir > 0 else 0   # the hand on the side it's heading (or last headed): 0 left, 1 right
        cap = "bedtime_right" if lead else "bedtime"   # (the bobble flops out behind it)
        outfit = None if wiz else cap if night else self.dev_outfit or (season() if self.seasonal.get() else None)
        candle = None   # at bedtime: held in its lead hand, or put down on that side while it sleeps
        if night and not wiz and not hay and not dancing and not act and not trip and not bucket:
            where = "floor" if sleeping else "hold" if ARMS[lead] in arms else None
            candle = (where, lead, int(self.clock * 5) % 2 if anim else 0) if where else None
        helpers = (self.helpers(), int(self.clock * 5)) if wiz else None
        ufo = None
        if anim and self.ufo:
            u, s = self.ufo, self.s()
            t, pb, ph = u["t"], max(1, round(2 * s)), self.pet_px[1]
            floor = self.screens[self.si].wb
            top = floor - ph - self.ufo_lift(s) - 3 * s - len(UFO) * 2 * pb   # the saucer's top, on the screen
            dx = 0
            if t < UFO_BEAM:
                top -= (1 - smooth(t / UFO_BEAM)) * 60 * s   # flying in
            elif t > UFO_DROP:
                k = smooth((t - UFO_DROP) / (UFO_END - UFO_DROP))   # flying off
                top, dx = top - k * 80 * s, k * 140 * s
            ufo = (round(top - (self.y - ph)), round(dx), UFO_BEAM <= t < UFO_DROP, UFO_GONE <= t < UFO_DROP,
                   int(t * 4) % 2, round(floor - (self.y - ph)))
        return (self.scale, legs, eyes, eye_dir, sink, arms, self.hand() if wiz and not job else None, self.warn_level(),
                wiz, parts, tuple(self.bubble_segments()), bars, bool(self.error), show, speech, rot,
                round(math.sin(self.clock * 1.6) * 1.4) if chute else None,
                shift,
                int(self.clock * 8) % 12 if anim and self.dizzy_t > 0 else None,
                sleeping and int(self.clock / 1.4) % 2 == 1, hay, eye_v, outfit, helpers, ufo, self.shiny, job, act,
                candle, trip, straws, bucket, water, harness, pole)

    def gaze(self):
        # which way to look so it's watching your mouse pointer, when the pointer's nearby
        s = self.s()
        dx = self.mouse[0] - self.x
        dy = self.mouse[1] - (self.y - self.pet_px[1] * 0.7)
        if abs(dx) > 420 * s or abs(dy) > 420 * s:
            return 0, 0
        return (1 if dx > 24 * s else -1 if dx < -24 * s else 0), (-1 if dy < -40 * s else 1 if dy > 24 * s else 0)

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
                        fill = col if isinstance(col, str) else col.get(ch) or col["#"]
                        self.canvas.create_rectangle(x + i * b + d, y + r * b + d, x + (i + 1) * b + d,
                                                     y + (r + 1) * b + d, fill=fill, outline="")

    def draw(self, f):
        (_, legs, eyes, eye_dir, sink_kind, arms, wand, warn, wiz, parts, segs, bars, err, show_bubble,
         speech, rot, chute, shift, dizzy, breath, hay, eye_v, outfit, helpers, ufo, shiny, job, act, candle, trip, straws,
         bucket, water, harness, pole) = f
        c = self.canvas
        c.delete("all")
        s = self.s()
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        pb = max(1, round(2 * s))     # small blocks for hearts, z's, sparks, the hat
        pet_w, pet_h = 18 * bw, 5 * bh
        font = self.font(max(8, round(11 * s)))
        pad = round(7 * s)
        if rot or ufo or (trip and (trip[0] not in ("wings", "jetpack", "balloon", "portal") or trip[-1] is not None
                                    or trip[-2])):
            show_bubble = False   # the usage bubble steps aside while it's tumbling about, abducted or climbing

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
        clip = trip[-1] if trip and not rot else None   # sinking through a portal or trapdoor: the floor hides the rest
        fade = trip[-2] if trip else 0   # teleporting or inside something: see-through steps, 4 = gone
        stip = FADES.get(fade)
        hide_look = rot or clip is not None or fade or (trip and trip[0] == "teleport")
        look = OUTFITS.get(outfit) if not hide_look else None
        above = max((len(HAT) - 1) * pb if wiz else 0,     # room above the head: hat, outfit, parachute, stars
                    (len(look[0]) + 1) * pb if look else 0,   # (a little gap, so the bubble's tail clears it)
                    (len(CHUTE) + 10) * pb if chute is not None else 0,
                    6 * pb if dizzy is not None else 0,
                    self.trip_room(trip, pb) if trip else 0,
                    self.act_room(act) if act else 0,
                    self.hay_lift((hay - 1) / 30, s) + ((len(look[0]) + 1) * pb if look else 0) if hay else 0)
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
        if sink_kind == "hay":   # sat up in the dip on top of the haystack
            sink = -self.hay_lift((hay - 1) / 30, s)
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
                if clip is not None:
                    y2 = min(y2, clip)
                    if y2 <= y1:
                        return
                if stip:
                    c.create_rectangle(px + x1, py + y1, px + x2, py + y2, fill=color, outline="", stipple=stip)
                else:
                    c.create_rectangle(px + x1, py + y1, px + x2, py + y2, fill=color, outline="")

        body_c = SHINY if shiny else ORANGE

        def block(col, row, cols=1, color=body_c):
            y1 = row * bh + sink
            emit(col * bw, y1, (col + cols) * bw, min(y1 + bh, pet_h), color)

        if ufo and ufo[2] and not rot:
            # the tractor beam, behind the mascot: see-through stripes from the saucer down to the floor
            top, bottom = py + ufo[0] + len(UFO) * 2 * pb, py + ufo[5]
            mid = px + pet_w // 2 + ufo[1]
            c.create_polygon(mid - 8 * pb, top, mid + 8 * pb, top, mid + pet_w // 2 + 3 * bw, bottom,
                             mid - pet_w // 2 - 3 * bw, bottom, fill=BEAM_C, outline="", stipple="gray50")
        gone = bool(ufo and ufo[3]) or fade >= 4   # inside the saucer (or the cannon, or mid-teleport)
        if trip and not rot:   # wings go behind it
            self.draw_trip(trip, "back", px, py, sink, bw, bh, pb, pet_w, pet_h)
        if job and not rot:   # the far side of a job's magic goes behind the mascot (and runes falling behind it)
            self.draw_job(job, "back", px, py)
            for kind, x, y, ci in parts:
                if kind == "glyph" and ci < 100:
                    self.rune(px + x, py + y, pb, ci)

        if hay and not rot:   # the back of the hay pile, behind it
            e = (hay - 1) / 30
            self.draw_hay(c, px + pet_w / 2, py + pet_h, s, "back", self.hay_squash(e), 1.0, math.sin(e * 2.2) * 0.15,
                          self.hay_flip)

        # the mascot
        for row, line in enumerate(BODY if not gone else ()):
            start, end = line.index("#"), line.rindex("#") + 1
            if row == 0 and breath:
                start, end = start + 1, end - 1   # breathing out while asleep
            block(start, row, end - start)
        if pole and not rot and not gone:
            # hugging the fireman's pole (pet/stunts.py): the bit of pole in front of it, then its hands and feet
            # wrapped round it
            mx = px + pet_w // 2
            self.pole_strip(c, mx, py + pet_h + pole[0], py + pet_h + pole[1], pb)
            for y1, y2 in ((0.9, 1.5), (2.1, 2.7), (4.1, 4.6)):   # (a dark crease under each, so they show)
                emit(pet_w // 2 - 2 * pb, y1 * bh, pet_w // 2 + 2 * pb, y2 * bh, body_c)
                emit(pet_w // 2 - 2 * pb, y2 * bh, pet_w // 2 + 2 * pb, y2 * bh + max(1, pb // 2), GRIP_C)
        for col, row in arms if not gone else ():
            block(col, row)
        for col in legs if not gone else ():
            block(col, 4)
        if harness and not gone:
            # the bungee harness (pet/bungee.py): black webbing. a belt with a silver buckle, and a strap down to a
            # silver ring low in the middle, between its legs, where the cord hooks on. a thin lighter line along
            # the belt's top gives the webbing a bit of sheen.
            # (careful: "ring" is the warning ring's thickness, used for the usage bubble below)
            sw, belt = max(2, bw // 2), (3.15 * bh, 3.75 * bh)
            emit(3 * bw, belt[0], 15 * bw, belt[1], HARNESS_C[0])
            emit(3 * bw, belt[0], 15 * bw, belt[0] + max(1, bh // 10), HARNESS_C[1])
            emit(8.3 * bw, belt[0] - 0.05 * bh, 9.7 * bw, belt[1] + 0.05 * bh, HARNESS_C[2])   # the buckle
            emit(8.6 * bw, belt[0] + 0.15 * bh, 9.4 * bw, belt[1] - 0.15 * bh, HARNESS_C[0])
            emit(9 * bw - sw / 2, belt[1], 9 * bw + sw / 2, 4 * bh, HARNESS_C[0])
            ring_y = HARNESS_RING * bh + pet_h / 2
            emit(8 * bw, ring_y - 0.3 * bh, 10 * bw, ring_y + 0.3 * bh, HARNESS_C[2])
            emit(9 * bw - sw / 2, ring_y - 0.1 * bh, 9 * bw + sw / 2, ring_y + 0.1 * bh, HARNESS_C[0])
        for col in EYES if not gone else ():
            x1, y1 = (col + eye_dir) * bw, bh + sink + eye_v * max(1, bh // 4)
            if eyes in ("open", "worried"):
                emit(x1, y1, x1 + bw, y1 + bh, EYE)
            else:   # a thin line: low for closed, high for a happy squint
                ly = y1 + (bh // 5 if eyes == "happy" else bh // 2)
                emit(x1, ly, x1 + bw, ly + max(1, bh // 4), EYE)
        if eyes == "worried" and not gone:   # little slanted eyebrows
            for col, inner in ((EYES[0] + eye_dir, 1), (EYES[1] + eye_dir, -1)):
                yb, th = sink + bh // 2, max(1, bh // 6)
                emit((col - 1) * bw if inner > 0 else col * bw, yb + th, col * bw if inner > 0 else (col + 1) * bw,
                     yb + 2 * th, EYE)
                emit(col * bw if inner > 0 else (col - 1) * bw, yb, (col + 1) * bw if inner > 0 else col * bw,
                     yb + th, EYE)
        if eyes == "happy" and not gone:
            for col in BLUSH:
                block(col, 2, color=BLUSH_C)
        if look and not gone:
            # a seasonal outfit on its head (the wizard hat takes its place while it works)
            rows_, colours = look
            hx = px + 3 * bw + (12 * bw - len(rows_[0]) * pb) // 2
            self.glyph(rows_, hx, py + sink - (len(rows_) - 1) * pb, pb, colours,
                       shadow=not outfit.startswith("bedtime"))   # (the nightcap has no dark edge, like the wizard hat)
        if candle and not rot and not gone:
            # a candle for a night light, with little rays of light round the flame
            where, right, flick = candle
            rows_ = CANDLE[flick] + CANDLE_BASE
            if right:   # in the right hand: the same picture, flipped
                rows_ = [ln[::-1] for ln in rows_]
                x0 = px + pet_w - 4 * pb if where == "hold" else px + pet_w - 2 * pb
            else:
                x0 = px - 4 * pb if where == "hold" else px - 6 * pb
            y0 = py + sink if where == "hold" else py + pet_h - 12 * pb
            gx, gy = x0 + (6 if right else 1) * pb, y0 + 2 * pb   # the flame's middle block
            for k, (dx, dy) in enumerate(((0, -1), (1, -1), (1, 0), (1, 1), (-1, 1), (-1, 0), (-1, -1))):
                r = 3 + (k + flick) % 2   # (none straight down: that's the candle)
                x1, y1 = gx + dx * r * pb, gy + dy * r * pb
                c.create_rectangle(x1, y1, x1 + pb, y1 + pb, fill=GLOW_C, outline="")
            self.glyph(rows_, x0, y0, pb, CANDLE_C, shadow=False)
        if bucket and not rot and not gone:
            # the water bucket in its lead hand: full or empty, or upside down while it tips it out
            look, full, lead, dip, _ = bucket
            x0, y0 = self.bucket_xy(look, lead, dip)
            self.glyph(BUCKET if look == "hold" else BUCKET[3:][::-1], px + x0, py + sink + y0, pb,
                       BUCKET_C if full else dict(BUCKET_C, w=BUCKET_C["e"]))
        if wiz and not rot:
            # wizard hat on the head, then whatever the job brings along (pet/magic.py)
            hx = px + 3 * bw + (12 * bw - len(HAT[0]) * pb) // 2
            self.glyph(HAT, hx, py + sink - (len(HAT) - 1) * pb, pb,
                       HAT_COLOURS, shadow=False)
            if job:
                self.draw_job(job, "front", px, py)
            if helpers and helpers[0]:   # (on the other side from a job's prop)
                away = -job[2] if job and job[0] in SIDE_JOBS else None
                self.draw_helpers(px, py, pet_w, pet_h, bw, bh, pb, *helpers, away=away)
        if wiz and not rot and wand is not None:   # the wand in the raised hand
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
        if act and not rot:
            self.draw_act(act, px, py, sink, bw, bh, pb, pet_w, pet_h)
        if trip and not rot:
            self.draw_trip(trip, "front", px, py, sink, bw, bh, pb, pet_w, pet_h)
        if dizzy is not None and not rot:
            # three little stars circling its head
            cx, cy = px + 9 * bw, py + sink - 3 * pb
            for k in range(3):
                a = dizzy / 12 * 2 * math.pi + k * 2 * math.pi / 3
                self.glyph(SPARK, cx + math.cos(a) * 7 * bw - 1.5 * pb, cy + math.sin(a) * 2 * pb - 1.5 * pb,
                           pb, STAR_C)

        if hay and not rot:   # the front of the hay pile, in front of it (pet/hay.py)
            e = (hay - 1) / 30
            self.draw_hay(c, px + pet_w / 2, py + pet_h, s, "front", self.hay_squash(e), 1.0, math.sin(e * 2.2) * 0.15,
                          self.hay_flip)
        if water and not rot:   # standing in its water: a see-through strip of it in front of its legs, as wide as
            # the source block on the water's own window behind (pet/bucket.py), with the same lighter top
            top, bottom = py + pet_h - water, py + pet_h
            c.create_rectangle(px - bw, top, px + pet_w + bw, bottom, fill=MC_WATER[1], outline="", stipple="gray50")
            c.create_rectangle(px - bw, top, px + pet_w + bw, top + pb, fill=MC_WATER[2], outline="")
        if straws and not rot and not gone:   # a couple of straws stuck on its head
            for col, lean, colour in ((6, -1, HAY_C[1]), (10, 1, HAY_C[0]), (11, 1, HAY_C[1])):
                for j in range(3):
                    x1, y1 = px + col * bw + lean * j * pb, py + sink - (j + 1) * pb
                    c.create_rectangle(x1, y1, x1 + pb, y1 + pb, fill=colour, outline="")

        # z's, notes and sparkles drift up behind the bubbles, so they never cover the words
        for kind, x, y, ci in parts:
            if kind in ("z", "Z"):
                self.glyph(ZZZ, px + x, py + y, pb + (pb // 2 + 1 if kind == "Z" else 0), ZZZ_C)
            elif kind == "spark":
                self.glyph(SPARK, px + x, py + y, pb, SPARK_C[ci], shadow=False)
            elif kind == "puff":   # smoke
                c.create_rectangle(px + x, py + y, px + x + 2 * pb, py + y + 2 * pb, fill=SMOKE_C[ci], outline="")
            elif kind == "dot":   # paint, ice chips, splashes, bits of balloon (its colour is in ci)
                c.create_rectangle(px + x, py + y, px + x + pb, py + y + pb, fill=ci, outline="")
            elif kind == "mote":   # a single glowing speck
                c.create_rectangle(px + x, py + y, px + x + pb, py + y + pb, fill=MOTE_C[ci], outline="")
            elif kind == "glyph" and ci >= 100:   # a falling rune, in front of the mascot
                self.rune(px + x, py + y, pb, ci)
            elif kind == "note":
                self.glyph(NOTE, px + x, py + y, pb, NOTE_C[ci])
            elif kind == "straw":
                c.create_rectangle(px + x, py + y, px + x + 2 * pb, py + y + pb, fill=HAY_C[ci], outline="")

        if ufo and not rot:
            # the saucer itself, in front, so the mascot disappears up into it
            ux = px + pet_w // 2 + ufo[1] - len(UFO[0]) * pb   # (drawn twice as chunky: it's bigger than the mascot)
            self.glyph(UFO, ux, py + ufo[0], 2 * pb, dict(UFO_C, l=UFO_LIGHTS[ufo[4]]))

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
            if ufo:   # above the saucer
                sy = min(sy, py + ufo[0] - tail - round(3 * s) - sp_h)
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

    def draw_helpers(self, px, py, pet_w, pet_h, bw, bh, pb, n, beat, away=None):
        # little apprentice wizards beside it, one for each extra claude code session that's busy
        c, s = self.canvas, self.s()
        mbw, mbh, mpb = max(1, bw // 2), max(1, bh // 2), max(1, pb // 2)
        mw, mh, gap = 18 * mbw, 5 * mbh, round(8 * s)
        sc = self.screens[self.si]
        first = away or (-1 if self.x > (sc.wl + sc.wr) / 2 else 1)   # start on the side with more room
        for i in range(n):
            side, k = (first if i % 2 == 0 else -first), i // 2
            x0 = px + pet_w + gap + k * (mw + gap) if side > 0 else px - gap - mw - k * (mw + gap)
            y0 = py + pet_h - mh - (mpb * 2 if (beat + i * 2) % 5 == 0 else 0)   # a little hop now and then

            def blk(col, row, cols=1, color=ORANGE):
                c.create_rectangle(x0 + col * mbw, y0 + row * mbh, x0 + (col + cols) * mbw, y0 + (row + 1) * mbh,
                                   fill=color, outline="")

            for row, line in enumerate(BODY):
                a = line.index("#")
                blk(a, row, line.rindex("#") + 1 - a)
            for col, row in ARMS:
                blk(col, row)
            for col in LEGS_STAND:
                blk(col, 4)
            for col in EYES:
                blk(col, 1, color=EYE)
            hx = x0 + 3 * mbw + (12 * mbw - len(HAT[0]) * mpb) // 2
            self.glyph(HAT, hx, y0 - (len(HAT) - 1) * mpb, mpb, HAT_COLOURS, shadow=False)
            wx = x0 + (17 * mbw if side > 0 else 0)   # a tiny wand, with a twinkling tip
            for j in range(3):
                c.create_rectangle(wx + side * j * mpb, y0 + 2 * mbh - (j + 1) * mpb,
                                   wx + side * j * mpb + mpb, y0 + 2 * mbh - j * mpb, fill=WAND_C, outline="")
            tip = STAR_C if (beat + i) % 2 else SPARK_C[1]
            c.create_rectangle(wx + side * 3 * mpb, y0 + 2 * mbh - 5 * mpb, wx + side * 3 * mpb + 2 * mpb,
                               y0 + 2 * mbh - 3 * mpb, fill=tip, outline="")
