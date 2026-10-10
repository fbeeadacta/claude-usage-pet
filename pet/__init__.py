# the claude usage pet, in parts. claude_pet.py (one folder up) starts it.
#
#   config.py            settings you can tweak: speeds, timings, limits, personalities, file locations, shortcut keys.
#   lines.py             everything the mascot can say.
#   tips.py              the descriptions shown next to each option in settings.
#   art.py               the mascot's pixel shapes and all the colours.
#   usage.py             reading your login, asking the usage api, and turning the answer into numbers and times.
#   cclog.py             reading claude code's local logs for token counts, costs and stats (only numbers, never text).
#   storage.py           the settings file, the memory file and the error log.
#   winapi.py            windows bits through ctypes: screens, windows, idle time, notifications, shortcuts, startup.
#   sounds.py            the sound effects, made from maths (no sound files to ship).
#   ui.py                small drawing helpers shared by every window: rounded boxes, smooth corners, fading, wrapping.
#   screens.py           part of the Pet: which monitor it's on, the work areas, hiding.
#   mouse.py             part of the Pet: hovering, poking, dragging and throwing.
#   talk.py              part of the Pet: speech bubbles, sounds, moods and reactions.
#   data.py              part of the Pet: fetching usage, milestones, keyboard shortcuts and the regular ticks.
#   movement.py          part of the Pet: walking, jumping, physics, standing on windows.
#   render.py            part of the Pet: drawing the mascot, its bubbles and effects.
#   fun.py               part of the Pet: being called over, quiet mode, seasons, session wrap-ups, the tour,
#                        the diary, the tray icon, fetch, and rare visitors (shiny, ufo, cat).
#   tray.py              the tray icon (its own thread and hidden window).
#   sprites.py           little see-through windows for things away from the mascot: the ball, the cat.
#   mascot.py            the Pet itself: puts the parts together, its settings, and starting it up.
#   details.py           the details panel that shows when you hover the mascot (plan and claude code tabs).
#   menu.py              the small right-click menu.
#   settings_window.py   the settings window (sidebar, pages, search, keyboard control).
#
# where new things go:
#   a new setting       its default in storage.py (DEFAULTS), a row in settings_window.py (sections), a line in
#                       tips.py, and the behaviour in the Pet part it belongs to.
#   a new animation     the state in movement.py, how it looks in render.py (frame + draw).
#   new things to say   lines.py, then pick them in talk.py.
#   a new sound         make it in sounds.py (and add it to SOUNDS / SOUND_GROUPS), play it with self.play(...).
#   a new settings page a name in SettingsWindow.PAGES and its sections in settings_window.py.
#   a new part of the Pet: a new file with a class FooMixin, added to the list in mascot.py's class Pet(...).
#
# the parts of the Pet share one object (self), so a method in one part can call a method in any other.
