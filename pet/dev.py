# part of the Pet: dev mode (a hidden settings page: ctrl + shift + D while settings is open). makes the mascot
# play any animation right now, or every one of them in a row, for testing. nothing it does here goes in the diary.
import time

from .config import CHUTE_HEIGHT, HOP_HEIGHT
from .gags import GAGS

GAG_NAMES = {"phone": "Phone call", "cookie": "Cookie", "duck": "Rubber duck", "coffee": "Coffee", "bughunt": "Bug hunt",
             "loop": "Infinite loop", "pancakes": "Pancake stack", "sheep": "Counting sheep", "fortune": "Fortune cookie",
             "merge": "Merge conflict", "recursion": "Recursion", "semicolon": "Lost semicolon", "dig": "Digging a 404",
             "keyboard": "Tiny keyboard"}
# every animation, in groups, as (key, name). the order here is the order "play all" goes in.
DEV_GROUPS = (
    ("Moves", (("walk", "Walk"), ("hop", "Hop"), ("wave", "Wave"), ("poke", "Poked"), ("party", "Party hops"),
               ("look", "Look around"), ("stretch", "Stretch"), ("worried", "Worried"), ("dizzy", "Dizzy"),
               ("dance", "Dance"), ("nap", "Nap"), ("throw", "Thrown"), ("chute", "Parachute"),
               ("come", "Called over"), ("fetch", "Fetch"), ("leap", "Leap to a window"), ("dive", "Leap of faith"),
               ("bucket", "Water bucket"), ("bungee", "Bungee jump"),
               ("zipline", "Zipline"), ("pole", "Pole slide"), ("web", "Web swing"),
               ("zipline_x", "Zipline to next monitor"), ("web_x", "Web swing to next monitor"))),
    ("Idle activities", (("sweep", "Sweep"), ("paint", "Paint"), ("fish", "Fish"), ("balloon", "Balloons"),
                         ("plane", "Paper plane"))),
    ("Coding jokes", tuple((k, GAG_NAMES.get(k, k.title())) for k in GAGS)),
    ("Wizard", (("job:wand", "Wand"), ("job:read", "Tome"), ("job:write", "Quill"), ("job:bash", "Rune rain"),
                ("job:web", "Crystal ball"), ("job:agent", "Summoning"), ("job:plan", "Sticky notes"),
                ("job:ask", "Question mark"), ("job:mcp", "Rune circle"), ("job:think", "Hourglass"),
                ("job:compact", "Rolling scroll"), ("job:helpers", "Apprentices"))),
    ("Trips", tuple((f"trip:{k}", n) for k, n in (
        ("rope", "Rope"), ("ladder", "Ladder"), ("beanstalk", "Beanstalk"), ("boxes", "Boxes"), ("wings", "Wings"),
        ("jetpack", "Jetpack"), ("balloon", "Balloons"), ("ufo", "UFO"), ("cannon", "Cannon"), ("portal", "Portals"),
        ("teleport", "Teleport"), ("hatch", "Trapdoor")))),
    ("Visitors", (("ufo", "UFO abduction"), ("cat", "Cat"), ("shiny", "Shiny colours"))),
    ("Outfits", (("look:halloween", "Halloween"), ("look:christmas", "Christmas"), ("look:newyear", "New year"),
                 ("look:birthday", "Birthday"), ("look:valentine", "Valentine"), ("look:bedtime", "Pajamas"))),
)
DEV_NAMES = {k: n for _, items in DEV_GROUPS for k, n in items}
DEV_ORDER = [k for _, items in DEV_GROUPS for k, _ in items]
TIMEOUT = 45.0   # (play all) gives up waiting on one after this long and goes on to the next
GAP = 0.9        # (play all) a breather between two


class DevMixin:
    def dev_setup(self, on):
        self.dev_on = on               # dev mode: the hidden settings page
        self.dev_now = None            # the animation being forced right now
        self.dev_queue, self.dev_total, self.dev_skipped = [], 0, []   # play all
        self.dev_started = self.dev_hold = self.dev_next = 0.0
        self.dev_job = None            # (until, kind, apprentices): a pretend wizard job
        self.dev_outfit = None         # an outfit worn whatever the date or time
        self.dev_restore, self.dev_note, self.dev_tick_job = None, None, None

    # ---- what the settings page asks for ----
    def dev_play(self, key, seq=False):
        # plays one animation now. returns why it can't, or None.
        if not seq:
            self.dev_queue, self.dev_total = [], 0   # (one on its own stops "play all")
            if key.startswith("look:"):   # outfits and the shiny colour just switch on and off
                look = key[5:]
                self.dev_outfit = None if self.dev_outfit == look else look
                self.redraw()
                return None
            if key == "shiny":
                self.shiny = not self.shiny
                self.redraw()
                return None
        why = ("Animations are off (Settings → Mascot)." if not self.anim.get()
               else "It's hidden right now." if self.hidden else "Put it down first." if self.held else None)
        if not why:
            self.dev_finish(next_up=False)
            self.dev_reset()
            now = time.time()
            self.dev_now, self.dev_started, self.dev_hold = key, now, now + 0.5
            why = self.dev_start(key, seq)
            if why:
                self.dev_now = None
        self.dev_note = (key, why) if why else None
        if why and seq:
            self.dev_skipped.append(DEV_NAMES[key])
        self.dev_schedule()
        return why

    def dev_play_all(self):
        self.dev_stop()
        self.dev_queue, self.dev_total, self.dev_skipped = list(DEV_ORDER), len(DEV_ORDER), []
        self.dev_next = 0.0
        self.dev_schedule()

    def dev_stop(self):
        # stops everything dev mode started, and it stands where it is
        self.dev_queue, self.dev_note = [], None
        self.dev_finish(next_up=False)
        if self.anim.get() and not self.held:
            self.dev_reset()
        self.dev_outfit = None
        self.redraw()

    def dev_leave(self):
        self.dev_stop()
        self.dev_on = False
        self.save()

    def dev_status(self):
        # (what the settings page shows) the name playing now, and how far through "play all" it is
        done = self.dev_total - len(self.dev_queue)
        now = DEV_NAMES.get(self.dev_now)
        return now, (done, self.dev_total) if self.dev_queue or (self.dev_now and self.dev_total) else None

    # ---- starting each one ----
    def dev_start(self, key, seq):
        s, sc = self.s(), self.screens[self.si]
        if key.startswith("job:"):   # the wizard, as if claude were busy with this
            kind, until = key[4:], time.time() + 10
            self.dev_job = (until, None if kind in ("wand", "helpers") else kind, 3 if kind == "helpers" else 0)
            self.working_until = max(self.working_until, until)
            self.cur_job, self.job_since = self.dev_job[1], time.time()
            return None
        if key.startswith("trip:"):
            return self.dev_trip(key[5:])
        if key.startswith("look:") or key == "shiny":   # (play all) on for a few seconds, then back how it was
            if key == "shiny":
                was = self.shiny
                self.shiny, self.dev_restore = True, lambda: setattr(self, "shiny", was)
            else:
                self.dev_outfit, self.dev_restore = key[5:], lambda: setattr(self, "dev_outfit", None)
            self.dev_hold = time.time() + 3.5
            self.redraw()
            return None
        if key in GAGS or key in ("sweep", "paint", "fish", "balloon", "plane"):
            if key == "plane" and self.plane is not None:
                return "A paper plane is still out. Wait for it to land."
            return None if self.start_act(key) else "It needs to be standing still on something."
        if key == "walk":
            if not self.walking_allowed():
                return "Walking is off (the Statue personality, or the details panel is open)."
            self.state, self.state_t = "walk", 4.0
            self.dev_hold = time.time() + 4
        elif key == "hop":
            self.jump_now(HOP_HEIGHT * s)
        elif key == "wave":
            self.wave_t = 1.4
        elif key == "poke":   # (like a click, without counting the poke)
            self.play("pop")
            self.happy_t = 1.1
            self.spawn("heart")
            self.jump_now(HOP_HEIGHT * 0.7 * s)
        elif key == "party":
            self.celebrate = 3
        elif key == "look":
            self.look_d, self.look_t = -self.dir, 1.4
        elif key == "stretch":
            self.stretch_t = 0.9
        elif key == "worried":
            self.worried_t = 3.0
        elif key == "dizzy":
            self.dizzy_t = 2.4
        elif key == "dance":
            self.start_dance()
        elif key == "nap":
            self.fall_asleep("nap")
            self.state_t = 6.0
        elif key == "throw":
            self.plat, self.through = None, False
            self.vx, self.vy, self.spin = self.dir * 650 * s, -600 * s, self.dir * 10.0
        elif key == "chute":   # dropped from high up
            self.plat, self.through = None, True
            self.y = max(sc.mt + self.pet_px[1] + 20 * s, sc.wb - (CHUTE_HEIGHT + 120) * s)
            self.vy = 200 * s
        elif key == "come":
            self.come_here()
        elif key == "fetch":
            self.start_fetch()
        elif key == "leap":
            if not self.platforms.get():
                return "Standing on windows is off (Settings → Mascot)."
            if not self.try_leap():
                return "There's no window close enough to jump to."
        elif key == "dive":
            if self.plat is None:
                return "It needs to be standing on a window. Try Leap to a window first."
            if not self.start_dive():
                return "Not a big enough drop off this window, or the screen edge is in the way."
        elif key == "bucket":
            if self.plat is None:
                return "It needs to be standing on a window. Try Leap to a window first."
            if not self.start_bucket():
                return "Not a big enough drop off this window, or the screen edge is in the way."
        elif key in ("zipline_x", "web_x"):
            if self.plat is None:
                return "It needs to be standing on a window. Try Leap to a window first."
            if not getattr(self, "start_" + key[:-2])(cross=True):
                return ("It needs a window higher than the next monitor's taskbar, facing that monitor, with "
                        "Stay on one monitor off.")
        elif key in ("bungee", "zipline", "pole", "web"):
            if self.plat is None:
                return "It needs to be standing on a window. Try Leap to a window first."
            if not getattr(self, "start_" + key)():
                return "Not a big enough drop off this window, or the screen edge is in the way."
        elif key == "ufo":
            if self.plat is not None:
                return "It needs to be on the taskbar, not on a window."
            self.start_ufo()
        elif key == "cat":
            self.start_cat()
        return None

    def dev_trip(self, how):
        # off to another monitor that way, or else up onto a high window. the first spot it can go that way wins.
        # (after one trip it's often somewhere no trip goes from, like the higher monitor: then it's popped over
        # to another monitor's taskbar first, and goes from there)
        if self.plat is None and self.dev_trip_from_here(how):
            return None
        si, x, y, plat = self.si, self.x, self.y, self.plat
        for i, o in enumerate(self.screens):
            if i != si:
                self.si, self.x, self.y, self.plat = i, (o.wl + o.wr) / 2, o.wb, None
                if self.dev_trip_from_here(how):
                    return None
        self.si, self.x, self.y, self.plat = si, x, y, plat
        return self.dev_trip_window(how)

    def dev_trip_from_here(self, how):
        return any(to != self.si and self.start_trip(to, how, exact=True) for to in range(len(self.screens)))

    def dev_trip_window(self, how):
        s, sc = self.s(), self.screens[self.si]
        self.update_platforms()
        for i, w in enumerate(self.plats):
            _, left, top, right, _ = w
            if w[0] == self.plat or not sc.mt + self.pet_px[1] + 20 * s < top < self.y - 120 * s:
                continue
            tx = min(max(self.x, left + 30 * s), right - 30 * s)
            if not sc.wl <= tx <= sc.wr or any(o[1] <= tx < o[3] and o[2] <= top - 2 < o[4] for o in self.plats[:i]):
                continue
            if self.start_trip(self.si, how, win=w, tx=tx, exact=True):
                return None
        if how == "hatch":
            return "The trapdoor needs a monitor below this one."
        return "Nowhere to go that way from here. Try another monitor, or a window higher up."

    # ---- keeping an eye on it ----
    def dev_reset(self):
        # stops whatever it was doing and stands it on its feet, so the next one starts cleanly
        self.end_trip()
        self.stop_fetch()
        self.wake(hop=False)
        if self.ufo and not self.ufo.get("dropped"):
            self.ufo = None
        self.dev_job = None
        self.bucket_stop()
        self.bungee_stop()
        self.stunt_stop()
        self.goto_x = self.goto_why = None
        self.state, self.state_t, self.act = "idle", 3.0, None
        self.leap_plan = self.leaping = None
        self.diving = self.chute = self.dropping_in = self.ufo_fall = False
        self.squash_t = self.pending_v = 0.0
        self.celebrate = 0
        self.vx = self.vy = self.walk_v = self.angle = self.spin = 0.0
        self.y = self.floor()

    def dev_free(self):
        # done with it: back on its feet, nothing going on
        key, now = self.dev_now, time.time()
        if now < self.dev_hold or self.dev_job is not None:
            return False
        if self.state not in ("idle", "walk") or self.trip or self.ufo or self.goto_x is not None:
            return False
        if not self.grounded() or self.squash_t > 0 or self.pending_v or self.hay_t > 0 or self.celebrate:
            return False
        if max(self.wave_t, self.happy_t, self.dizzy_t, self.stretch_t, self.worried_t, self.look_t) > 0:
            return False
        return not ((key == "fetch" and self.ball) or (key == "cat" and self.cat) or (key == "plane" and self.plane)
                    or (key == "dive" and self.hay_show) or self.bucket or self.water
                    or self.bungee or self.stunt)

    def dev_finish(self, next_up=True):
        if self.dev_restore:
            self.dev_restore()
            self.dev_restore = None
            self.redraw()
        if self.dev_now is None:
            return
        self.dev_now = None
        self.dev_job = None
        self.state_t = max(self.state_t, 3.0)   # (a moment before it does its own thing again)
        if next_up and self.dev_queue:
            self.dev_next = time.time() + GAP

    def dev_schedule(self):
        if self.dev_tick_job is None and (self.dev_now or self.dev_queue or self.dev_job):
            self.dev_tick_job = self.root.after(150, self.dev_tick)

    def dev_tick(self):
        self.dev_tick_job = None
        now = time.time()
        if self.dev_job is not None and now >= self.dev_job[0]:
            self.dev_job = None
        if self.dev_now and (self.dev_free() or now - self.dev_started > TIMEOUT):
            self.dev_finish()
        if self.dev_queue and not self.dev_now and now >= self.dev_next:
            key = self.dev_queue.pop(0)
            if self.dev_play(key, seq=True):   # (couldn't: straight on to the next)
                self.dev_next = now
        if self.dev_total and not self.dev_queue and not self.dev_now:   # that was the end of "play all"
            skipped = self.dev_skipped
            self.dev_note = ("all", f"All done. Skipped {len(skipped)}: {', '.join(skipped)}." if skipped
                             else "All done. Every one played.")
            self.dev_total = 0
        self.dev_schedule()

    # ---- the hooks the other parts ask ----
    def wizard_casting(self):
        # is it doing wizard things? a dev job says so; otherwise claude working does (but not mid dev animation)
        if self.dev_job is not None:
            return time.time() < self.dev_job[0]
        return bool(self.wizard.get()) and time.time() < self.working_until and not self.dev_now
