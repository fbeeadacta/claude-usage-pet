# Claude usage pet: change log

Newest first. The spec and how everything works are in `PROJECT_NOTES.md`.

- **2026-10-11 (version 7.8): subfolders no longer show up as their own projects.**
  - The Projects view named a project after the last folder in the session's working directory, so a session that worked in `pet/` or `docs/` showed up as a separate project. `cclog.project_name()` now walks up to the folder that has `.git` and uses that name (falling back to the plain folder name outside a repo). Results are cached per folder.
  - `CACHE_VERSION` went to 2, so the log cache is rebuilt once on the next start and old rows get the new names.
  - Tested: the name lookup (repo root, two subfolders, no folder, a missing folder, a non-repo folder). Not tested on the running pet until it's restarted.

- **2026-10-10 (version 7.7): one copy of the data, fewer pictures.**
  - Copies of the data files left in the main folder are now always cleaned up on start: if the main-folder copy is newer than the one in `data/`, it replaces it; if it's older, it's deleted. Before, a leftover copy stayed forever once `data/` had its own. (These leftovers came from a pet still running the pre-7.6 code, which writes to the main folder until it's restarted.)
  - Screenshots: only the wizard jobs sheet is kept, moved to `screenshots/wizard-jobs.png`. The other README pictures and `docs/jobs/` are removed, and the README no longer shows them.
  - Tested: the move/cleanup logic in a scratch folder (newer root copy, older root copy, no data copy). Not tested on the running pet until it's restarted.

- **2026-10-10 (version 7.6): tidier folder.**
  - The change log moved out of `PROJECT_NOTES.md` into `docs/CHANGELOG.md`, so the notes are quicker to read.
  - The notes (`PROJECT_NOTES.md`, `LOCAL_NOTES.md`) moved into `docs/`. `README.md`, `CLAUDE.md` and `CLAUDE.local.md` stay in the main folder.
  - Everything the pet writes (`pet_settings.json`, `pet_state.json`, `pet_cc_cache.json.gz`, `pet_errors.log`) now lives in `data/`, made on first run. `config.py` has `DATA_DIR` and `ERROR_LOG`; `storage.py` imports `ERROR_LOG` from there. On start, any old copies next to `claude_pet.py` are moved into `data/` once. `.gitignore` just lists `data/`.
  - Removed the unused `OPTIMIZE_PROMPT.md` and the `usage_widget_pos.json` ignore line (nothing writes it).
  - Messages that mentioned `pet_errors.log` now say `data/pet_errors.log`.

- **2026-10-10 (version 7.5): no more slumping at 100%, and pajamas at bedtime.**
  - At 100% the mascot no longer sits still, slumped with tired eyes. It walks, hops, dances and does its idle activities as usual. The black ring and the occasional 100% line stay. (One line, "I'm exhausted. clocking out until the reset.", was swapped for one that fits.) The "tired" eyes are gone from the drawing code.
  - New: Pajamas at bedtime (Settings → Appearance → Mascot), on by default from 11 PM until 6 AM: a striped nightcap and a candle (see "Pajamas at bedtime" above). "Bedtime from" (8 PM to 1 AM) only shows while the toggle is on.
  - Tested (test pet, scratch files, left monitor, 3x, bedtime forced on): screenshots awake (cap, candle in hand, rays) and asleep (cap, candle on the floor), heading left and heading right; the on/off hours for 8 PM, 11 PM, midnight and 1 AM. Not tested: the settings rows on screen (they use the same show/hide as Apprentices), the bedtime line, and it switching on by itself at the real hour.

- **2026-10-10 (version 7.4): fixed the memory leak on Python 3.15.**
  - The pet kept using more memory the longer it ran (about 1 MB every 4 seconds, faster during rune rain). Python 3.15 comes with Tk 9.0, and Tk 9.0 leaks a little memory (around 80 bytes) for every canvas item that's deleted, whatever kind it is (rectangles, lines, polygons, ovals, text; images don't). The pet redraws everything up to 60 times a second by deleting all items and making new ones, so it leaked all the time. Rune rain draws the most pieces per frame, so it leaked fastest. Tk 8.6 (Python 3.14) doesn't leak, and the pet's own Python memory stayed flat throughout.
  - Fix: every canvas is now `ui.Canvas`, which reuses its items. `delete("all")` only hides them (one call), and the next `create_*` of the same kind with the same option names takes a hidden one back: new coordinates, new options, shown and raised to the top, so the drawing order is the same as before. Embedded widgets (the settings search box) are still made and deleted for real. Nothing else in the drawing code changed.
  - Tested (test pets with scratch files on the left monitor, every wizard job and idle activity forced in turn for 30 s each, 3.14 and 3.15 side by side): before the fix, 3.15 grew about 95 MB in 5 minutes while 3.14 stayed flat. After it, both stay flat apart from one-off steps (the first full read of Claude Code's logs, a new font size, the 5-minute cache save). CPU and frame rate were the same on both. A screenshot of the fixed pet looked right. Not tested: the settings window and details panel over a long time (they also use `ui.Canvas` now, but only redraw when something changes).

- **2026-10-10 (version 7.3): new things to do when idle.**
  - Stargazing, the practice spell and the book are gone. In their place: sweeping, painting, fishing through a hole in the taskbar, blowing up balloons that pop, and throwing a paper plane (see "Idle activities" above). Each one is equally likely (the plane only when none is out already). `ACT_CHANCE` is unchanged.
  - The paper plane is a new little window (`Sprite`), turned to match its heading in 15° steps.
  - Particles can now fall (`"g"`), and there's a `"dot"` particle in any colour (paint, ice, splashes, balloon bits, dust).
  - The diary's three old counts are replaced by five new ones (old counts stay in `pet_state.json` but aren't shown).
  - Tested (test pet, scratch files, left monitor, plain backdrop, 1x and 2x, both sides): each activity started directly, with screenshots of each stage; the diary counts; and the plane's flight checked over many simulated throws (median about 550 px at 1x, 2–6 s in the air, about 1 in 7 loops). Not tested: them starting on their own timers, the plane bonking off screen edges on screen, and fishing or sweeping on top of a window.

- **2026-10-10 (version 7.2): three things to do when idle.**
  - Stargazing at night, a practice spell that backfires, and reading a little book (see "Idle activities" above). New Pet part: `pet/idle.py`; new lines in `pet/lines.py`; three more counts in the diary.
  - The usage bubble makes room for the hat during the practice spell, like it does for the wizard.
  - Tested (test pet, scratch files, second monitor, 2x, plain backdrop): each activity started directly, with screenshots of the feet-up stargazing with stars, moon and a shooting star, the spell before and after the poof, and the book; the diary counts; and the earlier scenarios still pass. Not tested: them starting on their own timers (a 10% chance each time it finishes standing about).

- **2026-10-10 (version 7.1): the wizard's jobs, a new-look panel, a welcome back, and lots more to say.**
  - **Details panel redone** in the Claude desktop app's style (the same palette and controls as the settings window): a Plan / Claude Code switch, sections as headings over cards, rounded bars, a chart in a dark well, the overview as six tiles in one card. Sessions moved into Claude Code, beside Overview, Models and Projects.
  - **Welcome back** on every start after the first: a greeting for the time of day, and an offer to carry on with the last Claude Code session's project.
  - **Wizard jobs** for every kind of Claude Code tool, plus thinking and shortening the conversation (see "Wizard jobs" above, and `docs/wizard-jobs.png`). New Pet part: `pet/magic.py`. The reading tome is redrawn in much more detail and floats beside the mascot now.
  - **Much more to say:** about 300 new lines across walking (42 now), quotes, curious questions, pokes, drags, throws, dances, windows, sleep, waking, jumps, work, attention, mornings and late nights, plus 26 that break the fourth wall. A new chatter level, **Non-stop** (5× as often), and it avoids its last 60 lines.
  - Tested (test pet, scratch files, made-up logs, second monitor): every job at 2x (screenshots in `docs/`), the page turn's five stages, the job each tool name maps to (including `mcp__` tools, thinking blocks and compact lines), the welcome with a made-up last project, every panel view, and CPU while working: roughly 8–18% of one core with the rune rain and 7–12% with the crystal ball across runs (each animates at about 25 frames a second; it drops back when Claude stops). The earlier scenarios still pass. Not tested: real Claude Code activity driving the jobs live.
  - **Ideas for when it's idle** (proposed, not built):
    - stargazing at night: lies on its back, little stars twinkle above
    - practising spells that go wrong: a tiny puff of smoke, singed hat
    - reading a pocket book on its own, turning a page now and then
    - fishing off the edge of a window into the taskbar
    - juggling three little pixels
    - building a tiny sandcastle out of taskbar pixels, then knocking it over
    - stretching and doing push-ups (badly)
    - chasing its own tail (it doesn't have one; it checks)
    - waving at the mouse pointer and pretending to talk to it
    - painting a little picture on an easel, then holding it up
    - a cup of tea: blows on it, sips, little steam squiggles
    - knitting a scarf that slowly gets longer over the day
    - tapping along to the system clock, or "conducting" while you type
    - peeking over the top of the window it's standing on
    - hide and seek: hides behind a window edge, peeks out when you look
    - blowing bubbles that pop on the screen edges
    - a paper aeroplane thrown off a window, landing somewhere on the taskbar
    - sleepwalking a few steps during a nap
    - writing in its diary (the Pet diary) with the quill
    - polishing its wand, or adjusting its hat in a little mirror

- **2026-10-10 (version 7.0): a big batch of improvements, quality-of-life and fun.**
  - **Technical:**
    - The usage service changing shape is spotted and explained ("service changed"), with only the names it sent written to the error log.
    - Claude Code's log numbers are cached in `pet_cc_cache.json.gz`, so a restart only reads new lines; logs are read 4 MB at a time.
    - An auto-hiding taskbar is handled: the floor follows it up and down.
    - The notes are brought up to date: the settings window's real pages, where `PRICES` lives, and an idea that was already done.
  - **Quality of life:**
    - A tray icon with your usage in its tooltip; click to call the mascot, right-click for the menu.
    - Call the mascot over with Ctrl + Alt + H, the tray icon, or by starting the pet again. It runs to your mouse or parachutes in.
    - Quiet mode: for an hour from the menu, quiet hours, and following Do Not Disturb.
    - An early pace warning when you'd run out well before the reset.
    - Session wrap-ups in a speech bubble, and a new Sessions tab recapping the latest five sessions.
    - A short tour on the very first start, replayable from settings.
  - **Fun:**
    - Seasonal outfits (Halloween, Christmas, New Year, its birthday, Valentine's Day) and New Year fireworks.
    - Its eyes follow your mouse pointer.
    - A floating spell tome while Claude reads files.
    - Apprentice wizards for parallel Claude Code sessions.
    - A pet diary counting everything it gets up to.
    - Play fetch.
    - Rare surprises: a shiny colour, a UFO abduction, and a cat (with a meow).
  - New files: `pet/fun.py`, `pet/tray.py`, `pet/sprites.py`. The settings window's version is now 7.0.

- **2026-10-10 (version 6.6): tested on Python 3.15.**
  - Python 3.15 comes with Tk 9.0 (3.14 has Tk 8.6). Ran the real pet on both, on the second monitor with scratch settings and made-up usage numbers: the pet, both details panel tabs, the settings window, speech bubbles and the menu look the same, and nothing was logged as an error. All pet files load on 3.15 with warnings turned into errors.
  - `Start pet.bat` and the startup shortcut picked up 3.15 on their own once it was installed. No code changes were needed.

- **2026-10-10 (version 6.5): tidy-up.**
  - `Start pet.bat` replaces the hand-made `Start Claude Pet` shortcut, which pointed at one Python version.
  - Removed `usage_widget.py`, the original widget kept as a backup (it's still in the git history).

- **2026-10-10 (version 6.4): easier to install for someone new.**
  - New `Start pet.bat`: double-click to start the pet with no console. It finds Python, and if there's none it explains and opens the python.org download page.
  - `claude_pet.py` checks for Windows, Python 3.10+ and tkinter before loading anything, and says what to fix in a pop-up (with a button to open the download page). If the pet crashes while starting without a console, a pop-up points to `pet_errors.log`.
  - "Start with Windows" now uses the `pyw` launcher when there is one, so the shortcut keeps working after Python updates.
  - README: a step-by-step install section for people who don't use terminals, and a short troubleshooting list.
  - Tested: the checks (old Python, no tkinter, not Windows) with fake pop-ups; `Start pet.bat` with the launcher, with only `python` on the path, and with no Python, in a folder with spaces and brackets in its name; the startup shortcut opening through `pyw`; the crash pop-up. Not tested: a real older Python, Windows 10, Microsoft Store Python, and the security prompt for a `.bat` from a downloaded ZIP.

- **2026-10-10 (version 6.3): getting ready to go public.**
  - Removed a code comment that suggested sending Claude Code's user agent. The pet always identifies itself as `usage-widget/0.1`.
  - Personal working notes moved out of `CLAUDE.md` into the gitignored `CLAUDE.local.md`. Test notes say "second monitor" instead of describing one desk.
  - Fixed an old author email in the git history so every commit uses the same GitHub address.

- **2026-10-10 (version 6.2): the code is split into small files.**
  - `claude_pet.py` (about 4,900 lines) became a 45-line starter plus the `pet/` package (20 files, mostly 100–400 lines; the biggest is the settings window at about 1,000). Nothing about how the pet looks or behaves changed. The shortcut, "Start with Windows" and the settings, memory and error-log files are all where they were.
  - The `Pet` class is split into themed parts (mixins) that combine into one class.
  - Done by a script that cut the file at its section lines and worked out each file's imports. It then checked that no line of code went missing, no name is unresolved, there are no import loops and no method is defined twice.
  - Tested old and new side by side: sounds and dance music, small talk, times and dates, the login help, shortcuts (including a real key press), the whole settings window, the details panel placement, riding and being pushed by windows, jumps, wall slaps, the leap of faith, personalities, poking, dragging, throwing, the menu and refresh. Results matched; the only differences were random ones.

- **2026-10-10 (version 6.1):**
  - Sounds are levelled to about the same loudness: each is scaled to the same average power (`SOUND_LEVEL`), not its loudest peak, and never clips. High, buzzy or hissy sounds seem louder than they measure, so the eagle cry, scream and hay are trimmed further by ear (`SOUND_TRIM`). Measured average power is now 4–7% for every sound; the eagle and scream were the loudest-sounding before. `SOUND_VERSION` is now 5.

- **2026-10-10 (version 6.0): the settings window, redesigned to look and work like the Claude desktop app's settings.**
  - **Layout:**
    - a darker sidebar on the left with icons (Windows' own Segoe MDL2 icon font) and the page names
    - on the right, the page title, then each section as a small heading over a rounded card
    - each setting has its label and description on the left and its control on the right
    - warm greys and Claude's orange
  - **Pages:**
    - Mascot (movement, behaviour)
    - Appearance (live preview, size, usage bubble, time and date)
    - Sound & talking (sound effects and volume, which sounds, chatter)
    - Usage & alerts (checking, warnings and notifications, Claude Code)
    - Shortcuts
    - System (startup, screens)
    - About & stats (Claude login, performance, about)
  - **Controls:** choices are segmented controls (the chosen option on a lighter tab inside a dark well), right beside the label when there's room, below it when there isn't.
  - **Settings that only matter sometimes stay hidden until they do:**
    - the ring levels only show while warnings are on
    - volume and the sound chips only show while sound effects are on
    - the shortcut list only shows while shortcuts are on
  - **Live previews:**
    - Appearance starts with a picture of the mascot and its bubble at the real chosen size and style, with your real numbers.
    - Each sound chip has a ▶ to hear it without switching it.
  - **Search:** a "Search settings" box at the top of the sidebar (Ctrl + F) shows every matching setting from every page, working right there, under "Page › Section" headings. Esc clears it.
  - **Login status card** on About & stats:
    - a status dot: connected, login expired, not logged in, or can't check
    - when it last checked and when it will check next
    - a "Check now" button
    - the step-by-step login help when it's needed
  - **Reset per section:** a small "Reset" beside each section heading puts just that section back to its defaults (`reset_section`).
  - **Keyboard:**
    - Tab / Shift + Tab or the arrow keys move through the pages and settings, with an orange focus ring; it scrolls into view.
    - Space or Enter switches or presses the focused setting.
    - Left / Right change choices and sliders, or play a sound chip.
    - Ctrl + F jumps to search.
  - **Saved note:** the always-there "Changes apply straight away" line is gone; a small ✓ Saved appears in the corner for a moment after each change.
  - Still resizable (now 580–1100 wide, from 420 tall up to the screen's height) and scrolls. The size is remembered.
  - Version 6.0 (`VERSION`), with a link to the project on GitHub (opens in your browser).
  - Tested: screenshots of every page, the preview at 2x, search, keyboard focus and Space switching a setting, a section reset, the saved note, the login card with an expired login, and the smallest size.

- **2026-10-10 (version 5.17):**
  - Stats: CPU, Memory and Frame rate each have a small area graph of the last 3 minutes (`PERF_POINTS` = 90 samples, one every 2 s), right under their header. The scale grows to fit; the dotted line is the top of the scale.
  - The settings window can be resized:
    - drag the bottom-right grip, the right edge or the bottom edge (the cursor shows resize arrows)
    - size limits: 370–760 wide, 400 tall up to the screen's height
    - the size is remembered (`settings_size`)
  - The title and tabs stay fixed at the top and the "Changes apply straight away" line at the bottom. The content scrolls between them with the mouse wheel, with a slim scrollbar. Tabs wrap onto a second line when the window is narrow. Every tab now uses the window's height instead of all tabs being as tall as the tallest one.

- **2026-10-10 (version 5.16):**
  - New Settings tab, Stats: live performance of the pet itself, updated every 2 seconds while open:
    - CPU (of the whole processor, and of one core)
    - memory
    - frame rate
    - usage checks ok / failed and the last check time
    - how long reading new Claude Code log lines took
    - windows watched
    - sound files on disk
    - how long it's been running
  - CPU, memory and usage checks get a green / amber / red dot. CPU and memory come from Windows' own process counters (`own_usage`, using GetProcessTimes and K32GetProcessMemoryInfo).
  - Measured in testing: about 0.1% CPU (2% of one core) and 48 MB while standing still.

- **2026-10-10 (version 5.15):**
  - Windows no longer push the mascot while it's on the taskbar (`TASKBAR_PUSH = False`): maximized and half-screen windows were shoving it about when they shouldn't. The code is still there; set it to True to bring it back. Windows still push it when it's standing on another window.

- **2026-10-10 (version 5.14):**
  - All sounds are half as loud as before at the same volume setting (`soft_all` in `make_sound`). `SOUND_VERSION` is now 4, so the quieter copies are made fresh.

- **2026-10-10 (version 5.13):**
  - Login expired / no login: the details panel now shows step-by-step help (`LOGIN_HELP`) for someone who has never used a terminal: open Command Prompt, type claude, log in through the browser, close it. The problem line is red; the steps are plain text. The speech line and notification point to the panel.
  - Times show as 3:05 PM by default, with a 24-hour option (Settings → Look → Clock).
  - Dates show as Fri 16/10 (day/month) by default, with a month/day option (Settings → Look → Dates). Used everywhere a reset time, chart label or run-out forecast is shown (`fmt_time`, `fmt_day`, `fmt_when`).
  - Saved as `clock` ("12h" / "24h") and `dates` ("ddmm" / "mmdd").

- **2026-10-10 (version 5.12):**
  - New Settings tab, Shortcuts:
    - the on/off switch (moved from System)
    - each shortcut with what it does and its keys drawn as key caps
    - click a shortcut, press new keys (Esc cancels, Backspace clears)
    - clear warnings for keys without Ctrl/Alt, keys the other shortcut uses, and keys another app has taken
    - Reset to defaults
  - Saved as `keys` in `pet_settings.json` (`[modifiers, key code]` per shortcut, or null).
  - The shortcut thread now re-registers whenever they change, lets go of them while you're typing a new one, and lets go completely when shortcuts are switched off.
  - Tested: recording, all three warnings (another app, here the already-running pet holding Ctrl + Alt + P / D), changing to Ctrl + Alt + F9 and a real key press of it hiding the pet, Backspace clearing, saving, reset, and screenshots.

- **2026-10-10 (version 5.11):**
  - Every sound can be switched on or off on its own (Settings → Sound → Which sounds).
    - Each sound is a chip: warm with a filled orange dot when on, plain with an empty ring when off.
    - Switching one on plays it, so you know which it is.
    - While the main Sound effects switch is off, the chips dim and the line above them says none of them will play.
  - Saved as `muted` in `pet_settings.json`: the list of sounds switched off, so any sound added later starts switched on.
  - Desktop notifications moved from the Sound tab to System.
  - Tested: toggling chips, the sample on switching on, saving, a muted sound not playing, and screenshots of all on, some off, and the main switch off.

- **2026-10-10 (version 5.10):**
  - The parachute sound is now a deep "floom", like a big sheet of cloth catching the air: a low rumble that swells in, flutters, and settles, with a low tone under it (it was a plain hiss). `SOUND_VERSION` is now 3.

- **2026-10-10 (version 5.9):**
  - Sound effects are on by default. A settings file saved earlier with them off keeps them off until switched on in Settings → Sound.
  - The eagle cry is longer (about 2.2 s, plus an echo): a rising "kee", a held cry, then a long falling, raspy tail.
  - Landing in hay is now a soft "tsss" of straw instead of a thump and rustle.
  - Dances last 8–12 s (were 3.5–6 s); the music loops for the whole dance.
  - Sound files now carry a version number (`SOUND_VERSION`), so changed sounds are remade instead of reusing old saved copies.
  - Note: Windows plays one sound at a time, so on a short drop the hay "tsss" cuts the eagle cry off when it lands.

- **2026-10-10 (version 5.8):**
  - New sounds, all made from maths in `make_sound` (no sound files), which now mixes several notes at once:
    - `eagle`: a raspy hawk-like screech when it takes a leap of faith.
    - `hay`: a whump and rustle when it lands in the hay.
    - `splat`: a thud and slap when it hits a window's side.
    - `spell`: a sparkly run of notes when wizard mode starts, then every 12–25 s.
    - `dance`: a 3.2 s chiptune loop (C major, 150 bpm, lead + bass + drums) that plays while it dances and stops when the dance ends.
  - The scream when thrown hard, the whoosh when the parachute opens and the boing on a bouncy landing were made but never played; they play now.
  - Sound files are made in the background at start-up and when the volume changes, so there's no hiccup the first time.
  - Windows plays one sound at a time, so any new sound cuts off the dance music.
  - Tested: every sound generated with nothing clipping (levels balanced, 24–81% peak), the dance loop starting and stopping with the dance, and the spell sound on wizard start. Not listened to by Claude.

- **2026-10-09 (version 5.7):**
  - Jumps that come up short slap into the side of the window and slide down it, instead of passing through.
  - Windows that go down behind the taskbar don't push it; it stands in front of them. Windows ending on or above the taskbar still do.

- **2026-10-09 (version 5.6):**
  - Personalities: Parkour!, Lively, Normal, Chill, Statue.
  - Livelier personalities walk more, nap less, and jump to nearby windows more often.
  - Leap of faith off window edges, landing in a pile of hay.
  - Windows push it aside on the taskbar too.

- **2026-10-09 (version 5.5):**
  - Jumps over to windows nearby. It's brave, and not always right.
  - Much chattier: small talk every minute or two at "Sometimes" (it was every 4–10 minutes), about whatever it's doing. New lines for walking, dancing, standing on windows, sleep-talking, falling off edges, jumps, plus curious questions. More lines everywhere else too, and it doesn't repeat its last 25 lines.

- **2026-10-09 (version 5.4):**
  - It follows a dragged window smoothly instead of jumping every few frames.
  - Windows in front of it are solid: they push it aside, and if it's cornered it drops through to the taskbar.
  - The screen edges are hard limits while it's riding a window.

- **2026-10-09 (version 5.3):**
  - The details panel opens below or beside the mascot when there's no room above it.
  - Smooth, steady 60 fps while moving (fixed jittery throws).

- **2026-10-09 (version 5.2):**
  - Fixed the right-click menu only working once.
  - The menu opens beside the mascot, and right-clicking again closes it.
  - Throws are heavier: small flicks just drop it, and big throws keep 38% of the mouse speed.

- **2026-10-09 (version 5.1):**
  - Removed accessories.
  - The right-click menu is now a small dark menu in the panel's style, with just Refresh now, Settings and Quit (it replaces the long Windows menu and its tooltips).
  - New settings window: panel style, five tabs, switches, pills and sliders, and a sound volume slider.

- **2026-10-09 (version 5):**
  - Error log.
  - Per-monitor scaling.
  - Old numbers fade in the bubble.
  - Cost estimate at API prices.
  - Projects view.
  - Worried face on Claude Code tool errors.
  - Desktop notifications.
  - Keyboard shortcuts (Ctrl + Alt + P / D).
  - Time-of-day behaviour.
  - Standing on (and riding) windows.
  - Unlockable accessories.
  - Optional sound effects.
  - Settings window.
  - Re-checks straight away when Claude Code renews the login.
  - README screenshots.

- **2026-10-09 (version 4.2):**
  - Fixed the dark box flash and the flicker when switching between dragged/thrown and other states: the window now never resizes or jumps.
  - The plan chart fills in the time before the pet started, estimated from Claude Code's logs (dotted).
  - Removed the 30-second and 1-minute refresh options.

- **2026-10-09 (version 4.1):**
  - Plan tab: usage chart for the current window (5-hour or Week) with the pace line, a forecast, and reset clock times.
  - Friendlier "slow down" handling: a clear message, waits that grow while it repeats, and it follows the service's `Retry-After`.
  - Fixed the dark outline flicker while it tumbles, by keeping the window one size.

- **2026-10-09 (version 4):**
  - Throwing: it keeps its speed, bounces and slides.
  - It hangs from where you grab it and swings.
  - New animations: parachute, dizzy stars, dancing with notes, wake-up stretch, slumped and tired at 100%.
  - New lines: screams, attention-seeking, bored, dizzy, parachute, and 100% lines.
  - The 100% ring is black with a silver edge.
  - "Refresh every" setting.
  - Roomier details panel with a wrapped footer, and the same height on every tab so the tabs never move.
- **2026-10-09 (version 3.3):**
  - Claude Code numbers count like the Claude desktop app by default, with an option for the real count.
  - Tooltips on every menu item.

- **2026-10-09 (version 3.2):**
  - Removed the warning sign.
  - The warning ring now also goes around the bubble's tail. It's yellow from 80% and red from 90%, and both levels can be changed in the menu ("Warning levels").

- **2026-10-09 (version 3.1):**
  - Rounded boxes are drawn with smooth corner images, so their corners are clean (anti-aliased in the panel, step-free on the mascot's see-through window).
  - The activity grid uses whole pixels, so every square is the same size.
  - Replaced the sweat drop with a warning sign plus a red ring around the bubble. It can be switched off with "Warn when nearly full".

- **2026-10-09 (version 3):**
  - Speech bubbles: encouraging and silly quotes, plus lines about work, quiet times, milestones, resets, pokes, dragging, sleeping and waking. A "Chatter" setting controls how often.
  - Wizard mode while tokens are going up: hat, wand and sparkles.
  - The bubble can show bars instead of numbers.
  - New Claude Code tab in the details panel, with real token counts from the local logs, an overview, models, and 7-day, 30-day and all-time ranges.
  - Remembers moods, milestones and pokes across restarts (`pet_state.json`).
- **2026-10-09:** Put the project in a private GitHub repo. Added `README.md` and `.gitignore`. Moved this computer's details into `LOCAL_NOTES.md`, which git ignores.
- **2026-10-09 (version 2):**
  - Hides during full screen.
  - Hovering shows the details panel, which fades and slides in and out smoothly.
  - Walks across monitors, with a "Stay on one monitor" option.
  - Higher, smoother jumps: 34 px, with lighter gravity and the exact air curve.
  - New animations: sleeping (when you're away and random naps), poke reaction with hearts, waving, glancing, sweating at high usage, celebrating resets, and wiggling legs while held.
  - Fixed: windows on a monitor to the left of the main one were placed wrongly.
  - Clicking now pokes the mascot instead of opening the details panel.
- **2026-10-09 (version 1):** Turned the panel widget (`usage_widget.py`) into the walking pet (`claude_pet.py`). Default size is 1x. Added the double-click shortcut and this notes file.
