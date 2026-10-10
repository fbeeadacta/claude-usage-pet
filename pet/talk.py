# part of the Pet: speech bubbles, sounds, moods and reactions.
import datetime
import math
import random
import threading
import time
import winsound

from .art import BLOCK_H, BLOCK_W, HAY_C, NOTE_C, RUNE_C, SPARK_C
from .config import (ATTENTION_MIN, CHATTER, CHAT_GAP, CREDENTIALS, HOP_HEIGHT, IDLE_TALK_MIN,
    SLEEP_AFTER_MIN, SPEAK_CPS, WORK_HOLD)
from .lines import (ATTENTION_LINES, BORED_LINES, CURIOUS_LINES, DANCE_LINES, FULL_LINES, HIGH_LINES,
    IDLE_LINES, LATE_LINES, MORNING_LINES, OOPS_LINES, POKE_COUNT, POKE_LINES, QUOTES, SLEEP_LINES,
    TOME_LINES, WAKE_LINES, WALK_LINES, WORKING, WORK_DONE, WORK_START)
from .sounds import SOUNDS, make_sound
from .storage import log_error
from .winapi import fullscreen_screens, idle_seconds, notify


class TalkMixin:
    # talking
    def say(self, text, force=False):
        # shows a speech bubble. force = it's about something that just happened, so skip the cooldown.
        rate = CHATTER[self.chatter.get()]
        now = time.time()
        if rate == 0 or self.hidden or (not force and now < self.quiet_until) or self.quiet():
            return False
        self.recent.append(text)
        self.speech = {"text": text, "start": now,
                       "until": now + 2.6 + len(text) / SPEAK_CPS + 0.03 * len(text)}
        self.quiet_until = now + 20 / max(rate, 1)   # a short breather between lines
        return True

    def pick(self, lines):
        # a random line it hasn't said lately (if there is one)
        fresh = [l for l in lines if l not in self.recent]
        return random.choice(fresh or lines)

    def play(self, kind, preview=False, loop=False):
        # windows plays one sound at a time, so a new one cuts off the last (music included)
        if (kind in self.muted or self.quiet()) and not preview:
            return
        if (self.sounds.get() or preview) and not self.hidden and self.volume.get() > 0:
            try:
                winsound.PlaySound(str(make_sound(kind, self.volume.get())),
                                   winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
                                   | (winsound.SND_LOOP if loop else 0))
                self.music = loop
            except Exception:
                log_error(f"playing the {kind} sound")

    def stop_music(self):
        if self.music:
            self.music = False
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass

    def warm_sounds(self):
        # makes the sound files in the background, so the first time one plays there's no hiccup
        if self.sounds.get() and self.volume.get() > 0:
            vol = self.volume.get()
            threading.Thread(target=lambda: [make_sound(k, vol) for k in SOUNDS], daemon=True).start()

    def toggle_sound(self, kind):
        # one sound on or off (from settings). switching one on plays it, so you know which it is.
        if kind in self.muted:
            self.muted.discard(kind)
            self.play(kind, preview=True)
        else:
            self.muted.add(kind)
            if kind == "dance":
                self.stop_music()
        self.save()

    def sounds_changed(self):
        if not self.sounds.get():
            self.stop_music()
        self.warm_sounds()
        self.changed()

    def volume_changed(self):
        self.play("pop", preview=True)   # a little sample at the new volume
        self.warm_sounds()
        self.save()

    def toast(self, title, body):
        if self.notify_on.get():
            notify(title, body)

    def creds_changed_at(self):
        try:
            return CREDENTIALS.stat().st_mtime
        except OSError:
            return 0.0

    def note_usage(self, now, hold):
        # tokens just went up somewhere: work (wizard time) for at least `hold` seconds
        self.working_until = max(self.working_until, now + hold)
        self.last_usage = now

    def mood_tick(self, now):
        # once a second: is claude working, should the pet say something
        if self.cc.last_growth > self.cc_growth_seen:
            self.cc_growth_seen = self.cc.last_growth
            self.note_usage(now, WORK_HOLD)
        rate = CHATTER[self.chatter.get()] or 1.0
        working = now < self.working_until
        if working and not self.was_working:
            self.work_started = now
            if self.state == "sleep":
                self.wake()
            self.say(self.pick(WORK_START), force=True)
            self.next_work_line = now + random.uniform(90, 180) / rate
        elif working and now >= self.next_work_line:
            self.say(self.pick(WORKING))
            self.next_work_line = now + random.uniform(90, 180) / rate
        elif not working and self.was_working and now - self.work_started > 45:
            self.say(self.pick(WORK_DONE), force=True)
        self.was_working = working
        reading = working and self.reading()   # the spell tome is out: claude is reading files
        if reading and not self.was_reading and self.state == "work" and random.random() < 0.5:
            self.say(self.pick(TOME_LINES))
        self.was_reading = reading
        if self.cc.last_error > self.error_seen:   # a claude code tool call just failed
            self.error_seen = self.cc.last_error
            if self.anim.get() and self.state != "sleep":
                self.worried_t = 3.0
                if random.random() < 0.6:
                    self.say(self.pick(OOPS_LINES))
        hour = datetime.datetime.now().hour
        present = idle_seconds() < 60
        today = datetime.date.today().isoformat()
        if present and 5 <= hour < 12 and self.greeted != today and self.state != "sleep":
            self.greeted = today   # first time at the computer this morning
            if self.say(self.pick(MORNING_LINES), force=True):
                self.wave_t = 1.4
        if present and hour < 5 and now >= self.next_late_line and not working:
            if self.say(self.pick(LATE_LINES)):
                self.next_late_line = now + random.uniform(40, 60) * 60
        self.fun_tick(now, present, working)
        if self.state == "sleep" and present and now >= self.next_chat:   # talks in its sleep
            if random.random() < 0.5:
                self.say(self.pick(SLEEP_LINES))
            self.next_chat = now + random.uniform(*CHAT_GAP) / rate
        if working or self.state == "sleep" or self.details.visible or not present:
            return   # busy, asleep, or nobody's there to listen
        if self.full():
            if now >= self.next_full_line and self.say(self.pick(FULL_LINES)):
                self.next_full_line = now + random.uniform(8, 15) * 60 / rate
            return
        if now - self.last_touch > ATTENTION_MIN * 60 and now >= self.next_attention:
            if self.say(self.pick(ATTENTION_LINES)):
                self.wave_t = 1.4
                self.next_attention = now + random.uniform(15, 25) * 60 / rate
            return
        if now - self.last_usage > IDLE_TALK_MIN * 60 and now >= self.next_idle_line:
            if self.say(self.pick(IDLE_LINES + BORED_LINES)):
                self.next_idle_line = now + random.uniform(8, 15) * 60 / rate
                self.next_chat = now + random.uniform(*CHAT_GAP) / rate
                if random.random() < 0.4 and self.state == "idle" and self.grounded():
                    self.start_dance()   # bored. might as well dance.
                return
        if now >= self.next_chat and self.grounded() and not self.held:
            if self.say(self.pick(self.small_talk())):
                self.next_chat = now + random.uniform(*CHAT_GAP) / rate

    def small_talk(self):
        # something to say about whatever it's up to right now
        if self.state == "dance":
            return DANCE_LINES
        if self.plat is not None and random.random() < 0.5:
            return HIGH_LINES
        if self.state == "walk" and self.walking_allowed() and random.random() < 0.6:
            return WALK_LINES
        return random.choice((QUOTES, CURIOUS_LINES))

    # reactions
    def greet(self):
        # you pointed at it: it wakes up, or stops and waves
        self.last_touch = time.time()
        if not self.anim.get():
            return
        if self.state == "sleep":
            self.wake()
        elif self.state not in ("work", "dance"):
            self.wave_t = 1.1
            if self.state == "walk":
                self.state, self.state_t = "idle", 2.0

    def poke(self):
        # you clicked it: squish, hop, happy face and a heart
        self.pokes += 1
        self.last_touch = time.time()
        self.play("pop")
        if self.pokes in POKE_COUNT:
            self.say(POKE_COUNT[self.pokes], force=True)
        elif random.random() < 0.6:
            self.say(self.pick(POKE_LINES), force=True)
        if not self.anim.get():
            return
        self.wake()
        self.happy_t = 1.1
        self.spawn("heart")
        if self.grounded() and self.squash_t <= 0:
            self.jump_now(HOP_HEIGHT * 0.7 * self.s())
        if self.state == "walk":
            self.state, self.state_t = "idle", 1.5

    def fall_asleep(self, reason):
        self.state, self.sleep_reason = "sleep", reason
        self.tally("naps")
        self.state_t = random.uniform(20, 60) if reason == "nap" else 0
        self.part_t, self.wave_t, self.look_t = 0.4, 0.0, 0.0
        if random.random() < 0.5:
            self.say("*yawn*", force=True)

    def wake(self, hop=True):
        if self.state != "sleep":
            return
        self.state, self.state_t, self.sleep_reason = "idle", 2.0, None
        self.stretch_t = 0.9   # a big stretch, both arms up
        self.parts = [p for p in self.parts if p["kind"] == "heart"]
        if hop:
            self.jump_now(HOP_HEIGHT * 0.5 * self.s())

    def check_away(self):
        if not (self.anim.get() and self.naps.get()) or self.hidden:
            return
        away = idle_seconds()
        if self.state == "sleep":
            if self.sleep_reason == "away" and away < 2:
                self.wake()          # you're back
                self.wave_t = 1.4
                self.say(self.pick(WAKE_LINES), force=True)
        elif (away >= SLEEP_AFTER_MIN * 60 and self.grounded() and not self.held and not self.details.visible
              and self.state != "work"):
            self.fall_asleep("away")

    def check_fullscreen(self):
        if self.hide_fs.get():
            try:
                self.fs = fullscreen_screens(self.screens)
            except OSError:
                self.fs = [False] * len(self.screens)
        else:
            self.fs = [False] * len(self.screens)
        self.set_hidden(self.fs[self.si] or self.user_hidden)

    def hand(self):
        # which row the wand hand is on while casting (it waves between two)
        return 0 if int(self.cast_t / 0.35) % 2 else 1

    def spawn(self, kind):
        s = self.s()
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        pb = max(1, round(2 * s))
        if kind == "heart":   # pops out just above the bubble so it never covers the numbers
            self.parts.append({"kind": "heart", "x": (18 * bw - 7 * pb) / 2 + random.uniform(-2, 2) * bw,
                               "y": self.bubble_top - 7 * pb, "vx": random.uniform(-10, 10) * s,
                               "vy": -30 * s, "life": 0.8, "c": 0})
        elif kind == "note":   # dancing
            self.parts.append({"kind": "note", "x": random.uniform(1, 14) * bw, "y": -5 * pb,
                               "vx": random.uniform(-15, 15) * s, "vy": -35 * s, "life": 1.0,
                               "c": random.randrange(len(NOTE_C))})
        elif kind == "spark":   # from the wand tip
            self.parts.append({"kind": "spark", "x": 17 * bw + 4 * pb, "y": self.hand() * bh - 8 * pb,
                               "vx": random.uniform(-25, 35) * s, "vy": random.uniform(-45, -5) * s,
                               "life": random.uniform(0.4, 0.8), "c": random.randrange(len(SPARK_C))})
        elif kind == "rune":   # glowing bits rising off the spell tome's pages
            self.parts.append({"kind": "rune", "x": random.uniform(6, 12) * bw, "y": 2 * bh - 3 * pb,
                               "vx": random.uniform(-12, 12) * s, "vy": random.uniform(-40, -20) * s,
                               "life": random.uniform(0.5, 0.9), "c": random.randrange(len(RUNE_C))})
        elif kind == "glint":   # a shiny mascot twinkles now and then
            self.parts.append({"kind": "spark", "x": random.uniform(3, 14) * bw, "y": random.uniform(0, 3) * bh,
                               "vx": 0.0, "vy": -6 * s, "life": 0.45, "c": 3})
        elif kind == "burst":   # new year's fireworks, high above its head
            cx, cy = random.uniform(-6, 24) * bw, self.bubble_top - random.uniform(30, 70) * s
            for i in range(10):
                a = i / 10 * 2 * math.pi
                self.parts.append({"kind": "spark", "x": cx, "y": cy, "vx": math.cos(a) * 45 * s,
                                   "vy": math.sin(a) * 45 * s, "life": 0.9, "c": random.randrange(len(SPARK_C))})
        elif kind == "straw":   # flying out of the hay pile
            self.parts.append({"kind": "straw", "x": random.uniform(0, 17) * bw, "y": 4 * bh,
                               "vx": random.uniform(-70, 70) * s, "vy": random.uniform(-150, -50) * s,
                               "life": random.uniform(0.35, 0.7), "c": random.randrange(len(HAY_C))})
        else:
            big = sum(p["kind"] == "Z" for p in self.parts) <= sum(p["kind"] == "z" for p in self.parts)
            self.parts.append({"kind": "Z" if big else "z", "x": 15 * bw, "y": bh - 4 * pb,
                               "vx": random.uniform(5, 9) * s, "vy": -20 * s, "life": 2.4, "c": 0})
