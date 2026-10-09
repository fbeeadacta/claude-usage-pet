# Claude usage pet: project notes

A small Claude mascot that walks along the top of the Windows taskbar. A bubble above its head shows Claude plan usage. If any file here gets lost or corrupted, this note has enough detail to rebuild it. You can give this file to Claude and ask it to rebuild the project.

Last updated: 2026-10-09 (version 2)

## Files in this folder

| File | What it is |
| --- | --- |
| `claude_pet.py` | The pet. This is the main program. |
| `README.md` | Short intro for the GitHub page. |
| `PROJECT_NOTES.md` | This file. |
| `usage_widget.py` | The original panel-style widget, kept as a backup. It still works on its own. |
| `.gitignore` | Tells git which files stay on this computer only. |
| `Start Claude Pet.lnk` | Double-click to start the pet without a console window. Made for this computer, so it's not on GitHub. |
| `pet_settings.json` | Saved settings: size, toggles, position. Created the first time the pet runs. Safe to delete. Not on GitHub. |
| `LOCAL_NOTES.md` | Details about this particular computer (paths, monitors, Python install). Not on GitHub. |

## How to use it

1. Double-click **Start Claude Pet** in this folder.
2. The mascot appears on top of the taskbar. The first numbers can take a few seconds to show up.
3. **Hover** over the mascot or its bubble:
   - It waves, and after a moment the details panel fades in above it (reset times, pace bars, tips).
   - Move the mouse onto the panel and it stays open. Move away and it fades out.
4. **Click** the mascot to poke it. It squishes, hops, makes a happy face and pops a heart.
5. **Drag** the mascot to pick it up. Its legs wiggle, and when you let go it falls back down.
6. **Right-click** the mascot to open the menu:
   - Refresh now
   - Keep details open (the panel stays until you close it with ×)
   - Walk around (on/off)
   - Jump now and then (on/off)
   - Take naps (on/off)
   - Animations (on/off; off makes it completely still and switches off the fades)
   - Size (0.75x to 3x)
   - Bubble (both limits, 5-hour only, or only when you hover)
   - Hide during full screen (on/off)
   - Stay on one monitor (on/off)
   - Start with Windows (on/off)
   - Quit
7. **Ctrl + mouse wheel** over the mascot fine-tunes its size. This may only work after you've clicked the mascot once.

### Things it does on its own

- **Two or more monitors:** it walks from one screen to the next. If the next screen's taskbar is lower, it drops down. If it's higher, it jumps up (up to 400 px at 1x). If it's higher than that, it turns around. Turn on "Stay on one monitor" to keep it on one screen. You can still drag it to another screen.
- **Full screen:** when a video, game or anything else is full-screen on its monitor, it fades away. It comes back when you leave full screen. A monitor that's showing something full-screen counts as a wall, so it won't walk onto it.
- **Sleep:** if you haven't touched the mouse or keyboard for 5 minutes, it lies down, closes its eyes and floats z's. When you come back, it wakes up with a hop and a wave. It also takes short naps (20–60 seconds) now and then. Hovering or clicking wakes it up.
- **Usage moods:** it sweats (a little blue drop) when a limit is at 85% or more. When the 5-hour limit resets, it celebrates with three happy hops and hearts.
- **Idle habits:** it blinks, glances left and right, and hops about every 30 seconds.

Only one pet runs at a time. Starting it again while it's already running does nothing, so **quit the old one first** (right-click → Quit) after updating the file.

## Fixing problems

- **The pet acts strangely or won't start:** delete `pet_settings.json` and start it again. All settings go back to their defaults.
- **The pet won't start at all:** to see the error message, open this folder in File Explorer, click the address bar, type `cmd`, press Enter, then type `py claude_pet.py` and press Enter. The error appears in that window.
- **Nothing happens when you start it:** a pet is probably already running. It may be hidden because something is full-screen, or sitting on your other monitor.
- **The bubble says "login expired":** open Claude Code once so it refreshes your login. The pet picks up the new login by itself.
- **The bubble says "no login":** Claude Code isn't signed in on this computer. Run `claude` once and sign in.
- **It hides when it shouldn't, or doesn't hide during full screen:** turn off "Hide during full screen" in the menu, then tell Claude which app caused it.
- **The double-click shortcut stops working after a Python update:** the shortcut points to one specific Python version's `pythonw.exe`. Rebuild it using the settings in `LOCAL_NOTES.md`, or ask Claude to fix it.
- **Two pets start with Windows:** the old widget may have its own startup shortcut. Run `py usage_widget.py --no-startup` once to remove it.

## Where the numbers come from

- `GET https://api.anthropic.com/api/oauth/usage` is an **undocumented** endpoint, so it can change or break without notice.
- Request headers:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
  - `User-Agent: usage-widget/0.1` (if that's ever refused, try `claude-code/2.1.204`)
  - `anthropic-beta: oauth-2025-04-20`
- The token comes from `~/.claude/.credentials.json`, at `claudeAiOauth.accessToken`. That file only exists because Claude Code is installed and signed in.
- **Token rule:** the token is never printed, logged or saved. It's only ever sent to `https://api.anthropic.com`.
- **Response:** `five_hour`, `seven_day`, `seven_day_sonnet` and so on, each shaped like `{utilization, resets_at}`. Unknown extra fields also appear (for example `iguana_necktie`). They're hidden unless they're a 5-hour or 7-day window (setting: `ONLY_KNOWN_LIMITS`).
- **What the numbers cover:** they're for the whole plan, so they include claude.ai chat, the desktop app and Claude Code together. Raw token counts are only available for Claude Code, from its local logs in `~/.claude/projects/`. That isn't built yet.
- **Polling:** every 120 seconds. After a 429 ("slow down") it waits 180 seconds instead.

## How it's built (to rebuild from scratch)

**Rules:**
- Python standard library only (`tkinter`, `urllib`, `ctypes`). No pip installs.
- Windows only.
- Casual lowercase code comments, no docstrings.

**The window:**
- Borderless and always on top, with no taskbar button.
- The whole window is filled with one "key" colour, `#010203`. `-transparentcolor` makes that colour see-through, and clicks go through it to whatever is behind.
- The mascot and the little pictures (hearts, z's, sweat drop) are drawn as solid rectangles, not text, so their edges stay sharp. The small pictures get a 1-block dark shadow so they show on any wallpaper.
- Text only ever sits on the solid dark bubble.

**Screens:**
- `EnumDisplayMonitors` and `GetMonitorInfoW` list every monitor's full area and its "work area" (the area without the taskbar). This is checked again every 5 seconds.
- The pet's position is its centre `x` and its feet `y`, in real screen pixels. The floor is the bottom of the work area of the screen it's on.
- The process uses `SetProcessDpiAwareness(2)` (per-monitor) so positions are correct on every screen.
- **Gotcha:** Tk window positions must be written `+x+y`, even when x is negative, for example `"123x87+-1022+945"`. Writing `-1022` means "1022 pixels from the right edge" and sends a window on the left monitor to the wrong place.
- Hidden windows (the pet during full screen, the closed panel) are parked at (-32000, -32000) instead of using withdraw/deiconify, which would steal keyboard focus.

**Full-screen detection (twice a second):**
- `EnumWindows` goes through windows front to back.
- It skips:
  - invisible or minimized windows
  - the pet's own windows
  - click-through overlays (`WS_EX_TRANSPARENT`) and tool windows (`WS_EX_TOOLWINDOW`)
  - cloaked windows (`DwmGetWindowAttribute` 14)
  - the desktop and taskbar classes
- For each screen, the first window that touches it decides:
  - **Full screen:** the window covers the whole monitor and isn't a normal maximized window (a window counts as normal-maximized when `IsZoomed` and it has a title bar).
  - **Not full screen:** the window covers at least 85% of the screen.

**Movement:**
- Walk speed is 28 px/s.
- A hop is 34 px high, about once every 30 seconds. Gravity is 1150 px/s². All of these are multiplied by the size.
- The air curve uses the exact formula (`y += vy·dt + ½·g·dt²`), so the height is right at any frame rate.
- Every jump starts with a 0.08 s crouch. A hard landing gives a 0.07 s squish. Holding the mouse button down squishes it too.
- Frame rate: about 60 fps while moving, 33 fps while waving or showing hearts or z's, 12 fps while standing, and 2 fps while hidden. The canvas is only redrawn when something visible changes. Walking just moves the window.

**Monitor edges:**
- A neighbour is a screen whose edge touches this one and overlaps it vertically. It doesn't count if "Stay on one monitor" is on, or if that screen is showing something full-screen.
- The pet crosses once its centre passes the edge. A lower floor means it falls. A higher one means it jumps by (height + 12 px), up to 400 px at 1x. Anything higher, or no neighbour at all, means it turns around.

**The mascot:**
- It copies the Claude Code welcome-screen shape:

  ```
   ▐▛███▜▌
  ▝▜█████▛▘
    ▘▘ ▝▝
  ```

- Each terminal character is 2×2 blocks, so the mascot is 18 blocks wide and 5 blocks tall.
- One block is 4×8 pixels at 1x.

  ```
  row 0  ...############...   (asleep: breathing narrows this row every 1.4 s)
  row 1  ...############...   eyes: dark blocks at columns 5 and 12
  row 2  ..##############..   arms: blocks at (1,2) and (16,2)
  row 3  ...############...
  row 4  legs   standing: 4, 6, 11, 13
                walking:  5, 7, 10, 12  (alternates with standing every 0.18 s)
                in air:   3, 5, 12, 14  (held: wiggles between air and walking)
  ```

**Faces and poses:**

| Pose | How it's drawn |
| --- | --- |
| Blink or asleep | Each eye becomes a thin line in the lower half. |
| Happy | The eye line moves to the top, plus pink cheeks at (4,2) and (13,2). |
| Glancing or walking | The eyes shift one column. |
| Waving | The right arm moves to (15,1)+(16,1) or (15,1)+(16,0), swapping every 0.18 s. |
| Lying down (asleep) | The body sinks one block and the legs are hidden. |
| Squished | The body sinks half a block. |

**Little pictures** (each block is 2 px at 1x):

| Picture | Pattern | Behaviour |
| --- | --- | --- |
| Heart | `.##.##. / ####### / ####### / .#####. / ..###.. / ...#...` | Pops out above the bubble. |
| Z | `#### / ..#. / .#.. / ####` | Two sizes. Drifts up behind the bubble. |
| Sweat | `.#. / ### / ### / .#.` | Sits left of the head and bobs. |

**Colours:**

| What | Colour |
| --- | --- |
| Mascot | `#d77757` |
| Eyes and shadows | `#2b1a14` |
| Cheeks | `#f4a08f` |
| Heart | `#ff6f8a` |
| Z's | `#f2efe8` |
| Sweat | `#7cc4ff` |
| Bubble | `#1f1e1d` |
| Bubble text | `#f2efe8` |
| Usage dots | green `#4caf7d` under 60%, amber `#d9a441` under 85%, red `#e5534b` from 85% |

**Window layout (bottom to top):**
1. The mascot.
2. A 2 px gap and the bubble's tail.
3. The bubble.
4. 40 px of empty space at 1x for hearts.

There's also 22 px of side space for the sweat drop and z's.

**Sleep:**
- Away for `SLEEP_AFTER_MIN` (5) minutes, measured with `GetLastInputInfo`. It wakes when there's any input again.
- Random naps: a 6% chance whenever it stops walking.

**Celebration:** happens when the 5-hour % drops by 15 points or more from a value of at least 15.

**Hover:**
- Checked 10 times a second by comparing the mouse position (`winfo_pointerxy`) with the mascot and bubble rectangles. Enter/Leave events aren't used because they're unreliable on see-through windows.
- The panel opens after 0.3 s of hovering. It closes 0.35 s after the mouse leaves the mascot, bubble and panel, unless it's pinned.

**Details panel:**
- The old widget's panel, opened just above the bubble: bars, a pace tick, reset times and pace messages.
- It fades in and out over 0.18 s with an ease-out curve, sliding up 10 px as it appears.
- Windows 11 gives it rounded corners (`DwmSetWindowAttribute` 33 = round).
- The mascot stops walking while the panel is open.
- Pace messages:
  - "ahead of pace" when used ≥ elapsed + 10.
  - "way under pace" when elapsed ≥ 20 and used ≤ half of elapsed.
  - "no usage lately" when the number hasn't changed for 45 minutes (5-hour) or 12 hours (weekly).
  - Nothing during the first 10% of a window.

**Single instance:** a named mutex, `claude-usage-pet`.

**Settings file:**
- `pet_settings.json` holds `scale`, `walk`, `jump`, `naps`, `anim`, `bubble` ("both" / "5h" / "hover"), `hide_fs`, `one_monitor`, `x` and `y`.
- It's written to a temporary file first, then swapped in, so a crash can't leave half a file.
- Bad or missing values fall back to the defaults.

**Start with Windows:**
- Makes a shortcut named `Claude Usage Pet.lnk` in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.
- The shortcut targets `pythonw.exe` with the script path as its argument.

## Setup

- Windows 10 or 11 (tested on Windows 11).
- Python 3 with tkinter (tested with Python 3.14). No pip installs.
- Claude Code installed and signed in on the same computer.
- The development computer has two 1920×1080 monitors side by side, with the taskbar at the bottom of both.
- Everything specific to one computer (paths, the shortcut's settings, the Python install) goes in `LOCAL_NOTES.md`, which git ignores.

## GitHub

- The repo is `claude-usage-pet`. It's **private** for now.
- Commits use the GitHub no-reply email, set for this repo only, so no personal email is in the history.

**Before making the repo public:**
1. Pick a license. With no license file, others can look at the code but legally can't reuse it. MIT is the usual simple choice.
2. Re-read `README.md`, especially the unofficial and not-affiliated note. The mascot design belongs to Anthropic.
3. Check that no personal details have slipped into tracked files. Search for your Windows username and your email.
4. On GitHub, go to Settings → General → Danger Zone → Change visibility.

## Status

**Tested on 2026-10-09** with fake numbers and screenshots on the real screens:
- See-through background, standing on the taskbar, walking frames.
- Details panel fading in, with rounded corners.
- Poke: heart, happy face and hop.
- Sleeping with z's.
- Sweat at 90%.
- Waving on hover.
- Panel opening on hover and closing after the mouse leaves (with a pretend mouse position).
- Hover-only bubble.
- Animations off.
- Error bubble at 2x.
- Jump height (exactly 34 px).
- Frame timing: steady at about 60 fps, about 0.1 ms of work per frame.
- Hiding during full screen on the left monitor and coming back afterwards.
- Walking from the left monitor onto the main one.
- Seven simulated monitor layouts: level, lower, higher, too high, one-monitor mode, full-screen neighbour, and a bigger monitor on the left.
- CPU: about 4% of one core while walking, about 2% while standing.

**Not tested yet:**
- Real API data inside the pet.
- Right-click menu clicks.
- Real mouse hover, click and drag. These were tested with a pretend mouse position and direct calls.
- Ctrl + mouse wheel.
- Start with Windows.
- Real YouTube, Netflix or game full screen. This was tested with a stand-in full-screen window.
- Display scaling above 100%.
- An auto-hiding taskbar.
- A taskbar on the side of the screen.

**Known limits:**
- It sits at the bottom of the screen if the taskbar auto-hides.
- If a monitor has different display scaling, the pet keeps its size in real pixels, so it looks smaller or bigger there.
- No automatic login refresh.
- "No usage lately" tracking resets when the pet restarts.

**Ideas for later:**
- Claude Code token totals from local logs.
- Dim the bubble when the data is stale.
- Small speech lines ("70% used!") at usage milestones.
- Mute effects during Do Not Disturb.
- Remember naps and moods across restarts.

## Change log

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
