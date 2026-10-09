# Claude usage pet: project notes

A small Claude mascot that walks along the top of the Windows taskbar. A bubble above its head shows Claude plan usage. If any file here gets lost or corrupted, this note has enough detail to rebuild it. You can give this file to Claude and ask it to rebuild the project.

Last updated: 2026-10-09 (version 5)

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
| `pet_state.json` | The pet's memory: when each limit last moved, milestones it has already announced, and how many times you've poked it. Safe to delete (it just forgets). Not on GitHub. |
| `LOCAL_NOTES.md` | Details about this particular computer (paths, monitors, Python install). Not on GitHub. |
| `pet_errors.log` | What went wrong, if anything (Python error details, never the login token). Kept under about 200 KB. Safe to delete. Not on GitHub. |
| `docs/*.png` | Screenshots for the README, staged on a plain backdrop (nothing personal in them). |

## How to use it

1. Double-click **Start Claude Pet** in this folder.
2. The mascot appears on top of the taskbar. The first numbers can take a few seconds to show up.
3. **Hover** over the mascot or its bubble:
   - It waves, and after a moment the details panel fades in above it.
   - The panel has two tabs:
     - **Plan:** pace bars, reset times (as countdowns and clock times), tips, a chart of your usage across the current window with the pace line (switch between 5-hour and Week), a forecast ("at this pace you'll run out around 23:40" or "you'll use about 60% by the reset"), and Claude Code tokens used today.
     - **Claude Code:** stats read from your Claude Code logs. "Overview" shows sessions, messages, total tokens, active days, peak hour, favourite model, a 26-week activity grid and a book comparison. "Models" shows tokens per model plus the input/output/cache split. Each view can show all time, 30 days or 7 days.
   - Move the mouse onto the panel and it stays open, so you can click the tabs. Move away and it fades out.
   - The panel is the same height on every tab, so the tabs never move when you switch.
4. **Click** the mascot to poke it. It squishes, hops, makes a happy face and pops a heart.
5. **Drag** the mascot to pick it up. It hangs from the spot you grabbed and swings as you move. Its legs wiggle.
   - **Throw it** by letting go while moving. It keeps your speed, screams, bounces off screen edges and the floor, and slides to a stop. From high up it opens a parachute. A hard landing leaves it dizzy.
6. **Right-click** the mascot to open the menu. **Settings…** at the top opens a window with every option and a short description of each. The menu has:
   - Refresh now
   - Refresh every (2, 3, 4 or 5 minutes; 2 is the default. Faster settings got "slow down" answers, so they were removed.)
   - Keep details open (the panel stays until you close it with ×)
   - Count tokens like the Claude app (on by default; off shows the real count, see below)
   - Walk around (on/off)
   - Jump now and then (on/off)
   - Take naps (on/off)
   - Wizard when Claude works (on/off)
   - Warn when nearly full (on/off; the coloured ring around the usage bubble)
   - Warning levels (yellow ring from 70/75/80/85%, red ring from 85/90/95%)
   - Animations (on/off; off makes it completely still and switches off the fades and typing)
   - Chatter (off, sometimes, or a lot)
   - Size (0.75x to 3x)
   - Bubble (both limits, 5-hour only, or only when you hover; and show numbers or show bars)
   - Accessory (the ones you've unlocked; locked ones say how to get them)
   - Stand on windows (on/off)
   - Sound effects (off by default)
   - Desktop notifications (on/off)
   - Keyboard shortcuts (on/off: Ctrl + Alt + P hides or shows the pet, Ctrl + Alt + D pins or closes the details panel)
   - Hide during full screen (on/off)
   - Stay on one monitor (on/off)
   - Start with Windows (on/off)
   - Quit

   Hover any menu item for a tooltip: what it does, then what happens when it's on or off (or its choices).
7. **Ctrl + mouse wheel** over the mascot fine-tunes its size. This may only work after you've clicked the mascot once.

### Things it does on its own

- **Two or more monitors:** it walks from one screen to the next. If the next screen's taskbar is lower, it drops down. If it's higher, it jumps up (up to 400 px at 1x). If it's higher than that, it turns around. Turn on "Stay on one monitor" to keep it on one screen. You can still drag it to another screen.
- **Full screen:** when a video, game or anything else is full-screen on its monitor, it fades away. It comes back when you leave full screen. A monitor that's showing something full-screen counts as a wall, so it won't walk onto it.
- **Sleep:** if you haven't touched the mouse or keyboard for 5 minutes, it lies down, closes its eyes and floats z's. When you come back, it wakes up with a hop and a wave. It also takes short naps (20–60 seconds) now and then. Hovering or clicking wakes it up.
- **Usage warning:** when a limit reaches 80%, the usage bubble (and its little tail) gets a yellow ring. From 90% the ring turns red. At 100% it turns black with a silver edge. Change the yellow and red levels under "Warning levels", or switch the ring off with "Warn when nearly full" in the menu. When the 5-hour limit resets, it celebrates with three happy hops and hearts.
- **Idle habits:** it blinks, glances left and right, hops about every 30 seconds, and now and then breaks into a little dance with music notes.
- **Waking up:** a big stretch, both arms up.
- **Limit used up (100%):** it slumps with tired eyes, stops walking and hopping, and says "hard day's work" lines.
- **Wizard mode:** when tokens are going up, it puts on a wizard hat and casts sparkles with a wand. It notices Claude Code within about 3 seconds, by reading its logs. It notices claude.ai chat and other apps when the 5-hour % goes up, which is checked every 2 minutes.
- **Talking:** speech bubbles type themselves out above the usage bubble. It says:
  - an encouraging or silly line every 4–10 minutes ("Sometimes"), but only when you're at the computer
  - something when work starts, now and then while it's working, and when a long job finishes
  - bored comments after 30 minutes with no token usage at all (and sometimes it dances to pass the time)
  - a polite request for attention after 20 minutes without a hover, poke or drag
  - screams when thrown, parachute lines, and dizzy lines after a hard landing
  - special lines when a limit hits 100%
  - milestones at 50%, 75%, 90% and 100% of each limit
  - a cheer when the 5-hour limit resets
  - replies to some pokes, plus poke-count milestones (10, 50, 100, 500)
  - "wheee!" when you pick it up, a yawn before sleeping, and a hello when you come back
  - a warning if your login expires
- **Standing on windows:** when it falls past the top of a window (dropped, thrown, or walking off an edge), it lands there. It rides along if you move the window, and falls off when the window closes, minimizes or maximizes. At a window's edge it either turns around or walks off (50/50).
- **Time of day:** a "good morning" the first time you're at the computer after 5 AM. After midnight, a gentle "it's late, maybe wrap up?" about every 40–60 minutes. Between 11 PM and 6 AM it naps three times as often and walks slower.
- **Tool errors:** when a Claude Code tool call fails, it looks worried (raised eyebrows) for 3 seconds and sometimes says "oops".
- **Accessories:** a party hat at 10 pokes, sunglasses at 50, a crown at 100, and a scarf the first time a limit reaches 100%. Pick one in Settings or right-click → Accessory.
- **Old numbers:** if the last successful check is more than 10 minutes old (and more than 3 refreshes), the bubble turns grey and says how old the numbers are, for example "15m old".
- **Login renewals:** it watches Claude Code's login file. When Claude Code renews your login after it expired, the pet checks again straight away.
- **Notifications** (if on): at 90% and 100% of a limit, when a nearly-used limit resets, when your login expires, and when you unlock an accessory.
- **Sounds** (if on): a pop when poked, a scream when thrown, a chime at milestones and resets.
- **Memory:** it remembers when each limit last moved, which milestones it has already announced, your poke count, unlocked accessories, and when it last said good morning, even after a restart.

Only one pet runs at a time. Starting it again while it's already running does nothing, so **quit the old one first** (right-click → Quit) after updating the file.

## Fixing problems

- **The pet acts strangely or won't start:** delete `pet_settings.json` and start it again. All settings go back to their defaults.
- **The pet won't start at all:** to see the error message, open this folder in File Explorer, click the address bar, type `cmd`, press Enter, then type `py claude_pet.py` and press Enter. The error appears in that window.
- **Nothing happens when you start it:** a pet is probably already running. It may be hidden because something is full-screen, or sitting on your other monitor.
- **"Rate limited" / the bubble says "slow down":** the usage service answered "too many requests". This used to happen with the old 30-second and 1-minute refresh settings, and can still happen after restarting the pet several times in a row (each start checks straight away). Your last numbers stay on screen. It waits 3 minutes, then 6, 12 and so on (up to 30, or longer if the service asks), and goes back to normal after the next successful check.
- **The bubble says "login expired":** open Claude Code once so it refreshes your login. The pet notices the renewed login file and checks again straight away.
- **Something seems broken:** look in `pet_errors.log` in this folder, or send it to Claude. It never contains your login token.
- **A keyboard shortcut does nothing:** another app may already use Ctrl + Alt + P or D. `pet_errors.log` will say so. Turn "Keyboard shortcuts" off, or change `HOTKEY_PET` / `HOTKEY_DETAILS` near the top of `claude_pet.py`.
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
- **What the numbers cover:** they're for the whole plan, so they include claude.ai chat, the desktop app and Claude Code together.
- **Polling:** every 2 minutes by default (menu: Refresh every, 2 to 5 min). After a 429 ("slow down") it waits 3 minutes, doubling each time it repeats (up to 30 minutes), or the service's `Retry-After` if that's longer.

**Claude Code token counts** come from its local logs:
- Files: `~/.claude/projects/**/*.jsonl`, one JSON object per line.
- Assistant lines have `message.usage` (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`), plus `message.model`, `message.id`, `requestId`, `timestamp` (UTC), `sessionId` and `uuid`.
- **Each answer is logged several times** (once per content block, with the same usage repeated).
- **"Count tokens like the Claude app" (default):** adds up every copy, like the Claude desktop app, and "Peak hour" is the hour most sessions *start* in (that's what matches the app).
- **Switched off (real count):** each `(message.id, requestId)` pair is counted once, about 3× lower, and "Peak hour" is the hour with the most messages.
- "Messages" counts every user and assistant line (each `uuid` once), which matches Claude Code's own count.
- "Total tokens" is input + output + cache write + cache read.
- Only numbers are kept from the logs (times, session ids, model names and token counts), never message text.
- Claude.ai chat has no local token log, so there are no token numbers for chat. Only the plan % covers it.
- **Cost estimate:** what the same tokens would cost on the pay-as-you-go API (your plan covers them, so it's only for comparison). Always counted once per answer, whichever counting mode is on. Prices are in `PRICES` near the top of `claude_pet.py` (dollars per million: input, output, cache read). Cache writes cost 1.25× input for the 5-minute cache and 2× for the 1-hour cache, using the 1-hour amount the logs record. Models with no price are left out, and the panel says so.
- **Projects:** each answer's `cwd` (the folder Claude Code was working in). The Projects view shows the top 5 by tokens, with session counts.
- **Tool errors:** user lines whose `message.content` has a `tool_result` with `is_error: true`.

## How it's built (to rebuild from scratch)

**Rules:**
- Python standard library only (`tkinter`, `urllib`, `ctypes`). No pip installs.
- Windows only.
- Casual lowercase code comments, no docstrings.

**The window:**
- Borderless and always on top, with no taskbar button.
- The whole window is filled with one "key" colour, `#010203`. `-transparentcolor` makes that colour see-through, and clicks go through it to whatever is behind.
- The mascot and the little pictures (hearts, z's, sparks) are drawn as solid rectangles, not text, so their edges stay sharp. The small pictures get a 1-block dark shadow so they show on any wallpaper.
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

**Rounded boxes:**
- Three rectangles plus four corner images, all on whole pixels.
- Each corner is made once and reused. It's sampled 4×4 per pixel.
- In the details panel the edge is blended into the panel colour, which makes it smooth.
- On the see-through window, each pixel is either fully in or fully out, because blending into the key colour would leave a coloured fringe.

**Little pictures** (each block is 2 px at 1x):

| Picture | Pattern | Behaviour |
| --- | --- | --- |
| Heart | `.##.##. / ####### / ####### / .#####. / ..###.. / ...#...` | Pops out above the bubble. |
| Z | `#### / ..#. / .#.. / ####` | Two sizes. Drifts up behind the bubble. |
| Spark | `.#. / ### / .#.` | Shoots from the wand tip in gold, cyan, pink or white, and drifts behind the bubbles. |
| Wizard hat | 24×11 blocks: a purple cone leaning right, a star of `*` in the middle, a gold band and a wide brim (see `HAT` in the code) | Sits on the head while working. |

**Wizard pose:**
- The right arm swaps between (15,1)+(16,1) and (15,1)+(16,0) every 0.35 s.
- A 5-block brown wand goes diagonally up and right from the hand, with a 2×2 gold tip.
- The eyes look toward the wand.
- The usage bubble moves up to make room for the hat.

**Colours:**

| What | Colour |
| --- | --- |
| Mascot | `#d77757` |
| Eyes and shadows | `#2b1a14` |
| Cheeks | `#f4a08f` |
| Heart | `#ff6f8a` |
| Z's | `#f2efe8` |
| Warning ring | `#f2c14e` (yellow), `#e5534b` (red) |
| Bubble | `#1f1e1d` |
| Bubble text | `#f2efe8` |
| Speech bubble | `#f2efe8`, with text `#2b1a14` |
| Hat, band, star | `#6c4ab6`, `#f2c14e`, `#ffe08a` |
| Wand | `#8b5a2b` |
| Activity grid | `#2c2c2e` for an empty day, then `#173c6e`, `#1f57a6`, `#2b74e0`, `#5aa2ff` from quiet to busy |
| Usage dots | green `#4caf7d` under 60%, amber `#d9a441` under 85%, red `#e5534b` from 85% |

**Window layout (bottom to top):**
1. The mascot.
2. Room for the hat (only while working).
3. A 2 px gap and the bubble's tail.
4. The usage bubble.
5. The speech bubble (only while talking).
6. 40 px of empty space at 1x for hearts.

There's also 30 px of side space for z's and sparks.

**Usage bubble, "bars" style:**
- One row per limit: a small label (`5h`, `wk`), then a 56×5 px bar in the usage colour on a `#3a3a3c` track.
- A red dot in the corner when the last check failed.
- With no data yet, it falls back to the numbers style.

**Talking:**
- Speech is wrapped to 190 px at 1x and types out at 30 letters a second. It stays up for 2.6 s + typing time + 0.03 s per letter.
- `say()` has a 25 s cooldown for chit-chat. Lines about something that just happened skip the cooldown.
- No talking when chatter is off or the pet is hidden.
- Random lines and quiet-time comments only happen when someone has touched the mouse or keyboard in the last minute, and not while it's working, asleep or showing the panel.
- "Chatter" changes how often: sometimes = ×1, a lot = ×2.5.
- All the lines are lists near the top of `claude_pet.py` (`QUOTES`, `WORK_START`, `WORKING`, `WORK_DONE`, `IDLE_LINES`, `POKE_LINES`, `POKE_COUNT`, `DRAG_LINES`, `WAKE_LINES`, `RESET_LINES`, `MILESTONES`).

**Working (wizard) detection:**
- A background thread reads only the new bytes of each log file every 3 s.
- New output tokens mean it keeps working for 20 more seconds.
- A rise in the 5-hour % (after the first check of each run) means it keeps working for 130 more seconds, which covers the next 2-minute check.
- No napping while working. If it was asleep, it wakes up for work.

**Milestones:** announced once per limit window, with the window identified by `resets_at` (±10 minutes). On the very first run, levels already passed are recorded quietly instead of announced.

**Plan tab chart:**
- Plots `history` points that fall inside the current window (window start = `resets_at` minus 5 hours or 7 days) plus the current %, against a dashed pace line from 0% at the start to 100% at the reset.
- Forecast: projected % at reset = used % ÷ elapsed % × 100. If that's 100 or more, the run-out time is start + elapsed × 100 ÷ used %.
- **Before the pet's first check in the window** there's no real %, so that stretch is estimated and drawn dotted ("dotted = estimate"). Claude Code's token use from the window start up to the first real point becomes a running total, weighted roughly by cost (input ×1, output ×5, cache write ×1.25, cache read ×0.1). It's then scaled so it ends exactly at the first real %. With no Claude Code activity in that stretch, it's a straight dotted line. Claude.ai chat use isn't in the logs, so the estimate's shape only reflects Claude Code.
- With no data and no estimate it shows "the line fills in as I check your usage". The real history only grows while the pet is running.

**Memory file (`pet_state.json`):**
- Holds `seen` (per limit: %, when it last changed, `resets_at`), `last_5h`, `pokes`, `milestones`, `last_usage` and `history`.
- Also `unlocked` (accessories) and `greeted` (the date of the last "good morning").
- `history` is `[time, 5-hour %, weekly %]` from each successful check: every check for the last 6 hours, then one per 10 minutes, kept for 8 days.
- Saved every 60 s and when you quit.
- Bad values are ignored.

**Sleep:**
- Away for `SLEEP_AFTER_MIN` (5) minutes, measured with `GetLastInputInfo`. It wakes when there's any input again.
- Random naps: a 6% chance whenever it stops walking.

**Celebration:** happens when the 5-hour % drops by 15 points or more from a value of at least 15.

**Hover:**
- Checked 10 times a second by comparing the mouse position (`winfo_pointerxy`) with the mascot and bubble rectangles. Enter/Leave events aren't used because they're unreliable on see-through windows.
- The panel opens after 0.3 s of hovering. It closes 0.35 s after the mouse leaves the mascot, bubble and panel, unless it's pinned.

**Details panel:**
- 320 base units wide, opened just above the bubble, with two tabs.
- Its height is the tallest of Plan, Claude Code Overview and Claude Code Models (each is drawn once to measure it), so the tab buttons stay put. Shorter tabs leave space at the bottom.
- The **Plan** tab is the old widget's panel: bars, a pace tick, reset times and pace messages, plus "Claude Code today".
- The **Claude Code** tab has "Overview" and "Models" views, and "All", "30d" and "7d" ranges. The selected tab, view and range are remembered.
- The activity grid is 26 weeks × 7 days with Sunday at the top. Each day's colour level is 1 + min(3, int(4 × day ÷ busiest day)).
- The book comparison picks the biggest book from a list that the total is at least twice the size of (book sizes are rough token counts).
- It fades in and out over 0.18 s with an ease-out curve, sliding up 10 px as it appears.
- Windows 11 gives it rounded corners (`DwmSetWindowAttribute` 33 = round).
- The mascot stops walking while the panel is open.
- Pace messages:
  - "ahead of pace" when used ≥ elapsed + 10.
  - "way under pace" when elapsed ≥ 20 and used ≤ half of elapsed.
  - "no usage lately" when the number hasn't changed for 45 minutes (5-hour) or 12 hours (weekly).
  - Nothing during the first 10% of a window.

**Dragging and throwing:**
- On press it remembers where on the body you grabbed (`grab_local`). While held, it tilts so its middle hangs straight below that spot (`hang_angle`), plus a swing from how fast you move sideways. A spring pulls the tilt toward that target.
- Tilted, every block is drawn as a turned square (polygon) around the turning point. The usage bubble steps aside, and speech sits just above the body.
- **The mascot's window is one fixed size in every state** (worked out from the size setting only, with room for the parachute, bubbles, 4 lines of speech and a fully tilted body). It's always placed by the body: window x = body centre − `center_x`, window y = feet − `feet_win`. Resizing or shifting the window when switching states (tilted, standing, parachute) made Windows flash a dark box or the mascot flicker for a frame, because moving a window and redrawing it don't happen at the same instant. Tilting turns the body around its middle.
- The window reaches about 20 px below its feet into the taskbar area. That part is see-through and click-through, so it doesn't get in the way.
- On release, the speed comes from the mouse movement over the last 0.1 s (capped at 2600 px/s at 1x). It keeps that speed, with air drag of 60% per second.
  - It bounces off screen edges, losing half its speed each time.
  - It bounces once off the floor if it lands faster than 700 px/s (35% bounce).
  - It slides with friction of 900 px/s² until it stops.
  - It bonks on the top of the screen.
  - The tilt springs back upright the short way.
- Thrown faster than 900 px/s: a scream. Landing faster than 1100 px/s: dizzy for 2.4 s (stars circle its head).
- **Parachute:** opens when falling faster than 150 px/s with more than 260 px (`CHUTE_HEIGHT`) still to go. It then falls at 110 px/s, drifting side to side. The 36-block red and white canopy has 4 strings to its raised hands and head.

**Standing on windows:**
- `list_platforms()` lists visible, normal app windows front to back (not minimized, maximized, cloaked, tool windows, click-through overlays, the desktop or taskbar, or the pet's own), at least 150×100 px. It uses the compositor's visible edges (`DwmGetWindowAttribute` 9) because `GetWindowRect` includes invisible borders.
- The list is refreshed every 0.2 s while it's falling, held, or standing on a window.
- While falling, if it passes a window's top edge with its middle more than 12 px inside the window (and nothing in front covers that spot), that window becomes its floor (`plat`, `plat_box`). Each refresh moves it with the window. If the window is gone, or it walks or slides past the edge, it falls.
- The parachute decision measures to the next ledge below, not the taskbar.

**Accessories:** `ACCESSORIES` and the `PARTY` / `CROWN` pictures in the code. The sunglasses and scarf are body blocks, so they turn with it when it's tilted. Hats are drawn on the head (not while tilted, not in wizard mode).

**Worried face:** open eyes plus two short slanted eyebrows on the lower half of row 0.

**Per-monitor scaling:** `GetDpiForMonitor` gives each screen's scaling (`Screen.dpi`), and the size used is `scale × that screen's dpi`. Moving to a monitor with different scaling resizes it once.

**Keyboard shortcuts:** a background thread registers them with `RegisterHotKey` and runs its own message loop. Presses come back to the main thread through a queue.

**Notifications:** a Windows toast sent through PowerShell (`Windows.UI.Notifications`), in the background, with no console window.

**Sounds:** made the first time they're needed, using maths (sine sweeps, a wobbly sawtooth scream, a noise whoosh), into `%TEMP%\claude_pet_sounds\*.wav`. Played with `winsound`, asynchronously.

**Error log:** `log_error()` appends a time stamp and traceback to `pet_errors.log`, trimming to the newest half when it's over `ERROR_LOG_KB`. Tk callback errors, log-reading errors, notification and sound errors, and crashes all go there.

**Settings window:** a normal window (dark title bar via `DwmSetWindowAttribute` 20) with two columns. Each option uses the same Tk variables and commands as the menu, so both stay in sync. The descriptions come from `TIPS`.

**Dancing:** a 5% chance whenever it stops walking (or when it's bored). It lasts 3.5–6 s. The beat is 0.25 s: arms up left, down, up right, both up. It bops down on beats 2 and 4 and sways half a block, with music notes floating up.

**Menu tooltips:** Windows draws the right-click menu itself, so tooltips use `<<MenuSelect>>` (which item is highlighted). It then finds the open menu's position (window class `#32768`) and shows a small dark window beside it, on the left, or on the right when there's no room, after 0.35 s. The texts are in `TIPS` in the code. The tooltip is moved with `SetWindowPos` if Tk holds the move back while the menu is open.

**Single instance:** a named mutex, `claude-usage-pet`.

**Settings file:**
- `pet_settings.json` holds:
  - `scale`, `x` and `y`
  - on/off switches: `walk`, `jump`, `naps`, `anim`, `wizard`, `warn`, `cc_app`, `hide_fs`, `one_monitor`
  - `poll`, the refresh time in seconds (120/180/240/300)
  - `notify`, `sounds`, `hotkeys`, `platforms` (on/off) and `accessory` ("none" or an unlocked one)
  - `warn_at` (70/75/80/85) and `panic_at` (85/90/95), the yellow and red ring levels
  - `bubble` ("both" / "5h" / "hover") and `bubble_style` ("numbers" / "bars")
  - `chatter` ("off" / "some" / "lots")
  - the panel's `panel_tab`, `plan_chart` ("5h" / "7d"), `cc_view` and `cc_range`
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
1. ~~Pick a license.~~ Done: MIT (`LICENSE`), covering the code only. The README says the Claude name and mascot belong to Anthropic.
2. Re-read `README.md`, especially the unofficial and not-affiliated note. The mascot design belongs to Anthropic.
3. Check that no personal details have slipped into tracked files. Search for your Windows username and your email.
4. On GitHub, go to Settings → General → Danger Zone → Change visibility.

## Status

**Tested on 2026-10-09** with fake numbers and screenshots on the real screens:
- See-through background, standing on the taskbar, walking frames.
- Details panel fading in, with rounded corners.
- Poke: heart, happy face and hop.
- Sleeping with z's.
- Sweat drop at 90% (replaced in version 3.1 by the warning sign and red ring, tested at 90% and 96%).
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

**Version 4, tested on 2026-10-09** (left monitor, fake plan numbers):
- Grabbed by the arm, it hangs sideways (90°) and swings.
- A throw from the left monitor onto the main one, with a scream.
- The parachute opening on a long fall.
- Dizzy stars after a hard landing.
- Dancing.
- 100%: black ring with silver edge, slumped with tired eyes.
- Panel the same height (320×343) on both tabs.
- Refresh setting saved.
- The earlier speech, wizard, milestone, memory and monitor tests still pass.

**Version 3, tested on 2026-10-09:**
- Speech bubbles: typing out, wrapping, and staying above the usage bubble.
- Wizard hat, wand and sparkles, with working mode starting and stopping on its own.
- Bars-style bubble.
- Claude Code tab: Overview and Models, read from the real logs.
- Plan tab with the "today" line.
- 50% milestone line.
- Reset cheer with three hops.
- 10th-poke line.
- Memory saved, reloaded and checked.
- No errors.

**Version 5, tested on 2026-10-09** (left monitor):
- Landing on a real window from another program, riding it when it moved, and falling when it closed.
- The parachute only on long drops.
- All four accessories.
- Unlocking the party hat at 10 pokes.
- Worried face after a tool error.
- Faded "15m old" bubble.
- An immediate re-check when the login file changes.
- Error log.
- Generating all 5 sounds (not played).
- Ctrl + Alt + P hiding and showing.
- The settings window.
- Projects view and cost line.
- One real notification.
- Both monitors read as 100% scaling.
- The earlier throw, parachute, monitor, speech, wizard and memory tests still pass.

**Not tested yet:**
- Real API data inside the pet.
- Wizard mode triggered by real Claude Code activity (it was tested by calling it directly).
- The quiet-time comments and random quotes on their real timers.
- Right-click menu clicks.
- Real mouse hover, click, drag and throw. These were tested with pretend mouse events.
- Hovering the menu tooltips with the mouse (they were tested with the keyboard).
- Sounds actually playing, the "good morning" and late-night lines (time-dependent), and a monitor at a different scaling.
- Ctrl + mouse wheel.
- Start with Windows.
- Real YouTube, Netflix or game full screen. This was tested with a stand-in full-screen window.
- Display scaling above 100%.
- An auto-hiding taskbar.
- A taskbar on the side of the screen.

**Known limits:**
- It sits at the bottom of the screen if the taskbar auto-hides.
- If a monitor has different display scaling, the pet keeps its size in real pixels, so it looks smaller or bigger there.
- No automatic login refresh: the pet only notices when Claude Code renews the login. Doing the renewal itself would mean sending the refresh token to Anthropic's login server (not api.anthropic.com) and could clash with Claude Code, so it's left out unless you decide otherwise.
- Claude Code stats only cover this computer's logs. If Claude Code deletes old logs, they disappear from the stats too.

**Ideas for later:**
- Dim the bubble when the data is stale.

## Change log

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
