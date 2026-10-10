# Claude usage pet: project notes

A small Claude mascot that walks along the top of the Windows taskbar. A bubble above its head shows Claude plan usage. If any file here gets lost or corrupted, this note has enough detail to rebuild it. You can give this file to Claude and ask it to rebuild the project.

Last updated: 2026-10-10 (version 6.5)

## Files in this folder

| File | What it is |
| --- | --- |
| `claude_pet.py` | Starts the pet (the shortcut and "Start with Windows" point at it). Before loading anything it checks for Windows, Python 3.10+ and tkinter, and explains in a pop-up if one is missing. |
| `Start pet.bat` | Double-click to start the pet without a console window. Finds Python (the `py` launcher first, then `python`/`pythonw` on the path). If there's no Python it says so and opens python.org. |
| `.gitattributes` | Keeps `.bat` files in Windows line endings, which batch files need. |
| `pet/` | The pet's code, split into small parts. `pet/__init__.py` lists what each file does and where new things go. See "Code layout" below. |
| `README.md` | Short intro for the GitHub page. |
| `PROJECT_NOTES.md` | This file. |
| `.gitignore` | Tells git which files stay on this computer only. |
| `pet_settings.json` | Saved settings: size, toggles, position. Created the first time the pet runs. Safe to delete. Not on GitHub. |
| `pet_state.json` | The pet's memory: when each limit last moved, milestones it has already announced, and how many times you've poked it. Safe to delete (it just forgets). Not on GitHub. |
| `LOCAL_NOTES.md` | Details about this particular computer (paths, monitors, Python install). Not on GitHub. |
| `pet_errors.log` | What went wrong, if anything (Python error details, never the login token). Kept under about 200 KB. Safe to delete. Not on GitHub. |
| `docs/*.png` | Screenshots for the README, staged on a plain backdrop (nothing personal in them). |

## Code layout

The code is a package (`pet/`) started by `claude_pet.py`. Every file begins with a one-line summary and imports exactly what it uses from the others.

| File | What's in it |
| --- | --- |
| `pet/config.py` | Tweakable numbers: speeds, timings, limits, personalities (`PROFILES`), file locations, default shortcut keys. |
| `pet/lines.py` | Everything the mascot says. |
| `pet/tips.py` | The descriptions next to each setting. |
| `pet/art.py` | The mascot's pixel shapes and all colours. |
| `pet/usage.py` | Login token, the usage API call, parsing, time and date formatting, login help text. |
| `pet/cclog.py` | Claude Code's local logs: token counts, costs, stats. |
| `pet/storage.py` | The settings file (`DEFAULTS`), the memory file, the error log. |
| `pet/winapi.py` | Windows calls: monitors, windows, idle time, notifications, the shortcut thread, startup, single instance. |
| `pet/sounds.py` | Making the sound effects. |
| `pet/ui.py` | Shared drawing helpers: rounded boxes, smooth corners, fading, text wrapping. |
| `pet/mascot.py` | The `Pet` class: puts the parts below together; its settings and start-up. |
| `pet/screens.py`, `mouse.py`, `talk.py`, `data.py`, `movement.py`, `render.py` | The parts of the `Pet` (mixin classes): monitors, mouse handling, talking and reactions, data and ticks, physics and movement, drawing. They all share one `self`. |
| `pet/details.py` | The hover details panel. |
| `pet/menu.py` | The right-click menu. |
| `pet/settings_window.py` | The settings window. |

`pet/__init__.py` also says where new things go (a new setting, animation, sound, settings page or Pet part).

One thing to know: `usage.RETRY_AFTER` changes while the pet runs, so other files read it as `usage.RETRY_AFTER`, never by importing the name on its own.

## How to use it

1. Double-click **Start pet.bat** in this folder.
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
6. **Right-click** the mascot for a small menu with **Refresh now**, **Settings** and **Quit**. It opens beside the mascot (not on top of it). A click anywhere else, or right-clicking the mascot again, closes it.
7. **Settings** opens a window in the same style as the details panel, with five tabs. Every option has a switch, buttons or a slider, plus a one-line description underneath. Changes apply straight away. Drag the title to move the window, and close it with × or Esc.
   - **Behaviour:** Walk around, Jump now and then, Take naps, Wizard when Claude works, Stand on windows, Animations
   - **Look:** Size (slider, 0.5x–4x), Bubble shows (both limits / 5-hour only / on hover), Bubble style (numbers / bars), Keep details open
   - **Sound:** Sound effects (master switch), Volume (slider, 0–100%; plays a sample when you let go), Which sounds (every sound as an on/off chip, in groups: Reactions = Poke, Bounce, Scream, Wall splat; Adventures = Parachute, Eagle cry, Hay landing; Moods = Wizard magic, Dance music, Milestones), Chatter (off / sometimes / a lot). Desktop notifications moved to System.
   - **Usage:** Refresh every (2, 3, 4 or 5 minutes), Warn when nearly full, Yellow ring from (70–85%), Red ring from (85–95%), Count tokens like the Claude app
   - **Shortcuts:** Keyboard shortcuts (on/off; off lets go of the keys so other apps can use them), then each shortcut with what it does and its keys as key caps (defaults: Ctrl + Alt + P shows or hides the mascot, Ctrl + Alt + D pins or closes the details panel). Click one and press the new keys; Esc cancels, Backspace clears it. Warnings appear if the keys have no Ctrl/Alt, are already used by the other shortcut, or another app already uses them. Reset to defaults.
   - **System:** Desktop notifications, Hide during full screen, Stay on one monitor, Start with Windows
8. **Ctrl + mouse wheel** over the mascot fine-tunes its size. This may only work after you've clicked the mascot once.

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
- **Standing on windows:** when it falls past the top of a window (dropped, thrown, or walking off an edge), it lands there. It follows the window smoothly if you drag it (its window is checked every frame), and falls off when the window closes, minimizes or maximizes. At a window's edge it either turns around or walks off (50/50).
- **Personality** (Settings → Behaviour; replaces the old "Walk around" and "Jump now and then" switches): Parkour! / Lively / Normal / Chill / Statue. Each is a row in `PROFILES`: how often it keeps walking, how long it stands about or walks, walking speed, how often it hops and jumps to windows, nap chance, and what it does at a window's edge. In a 3-minute simulation it walked 73% / 64% / 41% / 24% / 0% of the time. Statue = no walking, hops or jumps (it still reacts and talks). Old settings with walking off become Statue.
- **Coming up short:** a jump whose feet are still below a window's top when it reaches the window's side slaps into the side like a wall (`leap_wall`): a boing, a little bounce back and a tumble, dizzy stars, a line (`SLAP_LINES`), then it slides down beside the window with no parachute. Jumping straight up from in front of a window can't hit its side, so a failed one just lands back in front. The jump plan also slows down if it would otherwise reach the side of a higher window before its feet clear the top.
- **Leap of faith:** walking to the edge of a window, it may first look for another window that way to jump to (`edge_leap`), else take a leap of faith (`dive`) if the drop is at least `DIVE_MIN` (150 px): a little spring off the edge, it tips head first into a swan dive (no parachute), and lands in a pile of hay with straw flying. It sits in the hay for `HAY_TIME` (1.3 s), eyes peeking out, then pops out. Otherwise it turns around (`turn`) or walks off.
- **Jumping between windows:** about every 25 seconds (with Jump, Walk and Stand on windows all on) it looks for a window top it could reach: up to ~520 px sideways, from a bit below it to ~420 px above it, not covered by another window. It crouches, says something brave, and jumps. Its legs really manage about 300 px up, so higher targets always fail; it also eyeballs the sideways push (85–120%, and 15% of the time it badly misjudges it). Misses just plop down (no parachute), with an excuse. Settings: `LEAP_EVERY`, `LEAP_POWER`, `LEAP_REACH`.
- **Windows are solid:** a window in front of the one it stands on can't cover it. When one slides over it or is brought to the front, the pet gets pushed out the side it's nearer to (a quick scoot, not a jump). Pushed past the edge of its own window, it falls off. Cornered against the screen edge or another window, it drops straight through to the taskbar. The screen edges are hard walls, even when a window is dragged past them. Maximized windows count as walls too. On the taskbar, windows whose bottom edge ends on or above the taskbar push it aside too (it checks the windows within ~400 px of it). A window that goes down behind the taskbar is behind its floor, so it stands in front of it and isn't pushed; boxed in on the taskbar (a maximized window, say) it just carries on, since there's nowhere lower to go.
- **Time of day:** a "good morning" the first time you're at the computer after 5 AM. After midnight, a gentle "it's late, maybe wrap up?" about every 40–60 minutes. Between 11 PM and 6 AM it naps three times as often and walks slower.
- **Tool errors:** when a Claude Code tool call fails, it looks worried (raised eyebrows) for 3 seconds and sometimes says "oops".
- **Old numbers:** if the last successful check is more than 10 minutes old (and more than 3 refreshes), the bubble turns grey and says how old the numbers are, for example "15m old".
- **Login renewals:** it watches Claude Code's login file. When Claude Code renews your login after it expired, the pet checks again straight away.
- **Notifications** (if on): at 90% and 100% of a limit, when a nearly-used limit resets, and when your login expires.
- **Sounds** (if on): a pop when poked, a scream when thrown, a chime at milestones and resets.
- **Memory:** it remembers when each limit last moved, which milestones it has already announced, your poke count, and when it last said good morning, even after a restart.

Only one pet runs at a time. Starting it again while it's already running does nothing, so **quit the old one first** (right-click → Quit) after updating the file.

## Fixing problems

- **The pet acts strangely or won't start:** delete `pet_settings.json` and start it again. All settings go back to their defaults.
- **The pet won't start at all:** to see the error message, open this folder in File Explorer, click the address bar, type `cmd`, press Enter, then type `py claude_pet.py` and press Enter. The error appears in that window.
- **Nothing happens when you start it:** a pet is probably already running. It may be hidden because something is full-screen, or sitting on your other monitor.
- **"Rate limited" / the bubble says "slow down":** the usage service answered "too many requests". This used to happen with the old 30-second and 1-minute refresh settings, and can still happen after restarting the pet several times in a row (each start checks straight away). Your last numbers stay on screen. It waits 3 minutes, then 6, 12 and so on (up to 30, or longer if the service asks), and goes back to normal after the next successful check.
- **The bubble says "login expired":** open Claude Code once so it refreshes your login. The pet notices the renewed login file and checks again straight away.
- **Something seems broken:** look in `pet_errors.log` in this folder, or send it to Claude. It never contains your login token.
- **A keyboard shortcut does nothing:** another app may already use Ctrl + Alt + P or D. `pet_errors.log` will say so. Settings → Shortcuts shows "Another app already uses these keys" under it; click it and pick different keys.
- **The bubble says "no login":** Claude Code isn't signed in on this computer. Run `claude` once and sign in.
- **It hides when it shouldn't, or doesn't hide during full screen:** turn off "Hide during full screen" (Settings → System), then tell Claude which app caused it.
- **"Start with Windows" stops working after a Python update:** turn it off and on again in Settings → System. (New shortcuts use the `pyw` launcher, which follows Python updates; only computers without the launcher point at one Python version.)
- **Two pets start with Windows:** an old version may have left its own startup shortcut. Press Windows + R, type `shell:startup` and press Enter, then delete `Claude Usage Widget` if it's there.

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
- **Polling:** every 2 minutes by default (Settings → Usage → Refresh every, 2 to 5 min). After a 429 ("slow down") it waits 3 minutes, doubling each time it repeats (up to 30 minutes), or the service's `Retry-After` if that's longer.

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
- **Gotcha:** Tk window positions must be written `+x+y`, even when x is negative, for example `"123x87+-1022+945"`. Writing `-1022` means "1022 pixels from the right edge" and sends a window on a monitor left of the main one to the wrong place.
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
- Frame rate: a steady 60 fps while moving (`FPS`). Each frame is aimed at the next 1/60 s mark, and while moving the pet asks Windows for a 1 ms timer (`timeBeginPeriod(1)`), handing it back when it stops. Windows' normal 15.6 ms clock made some frames take 31 ms, and that was the jitter in throws. Otherwise: 33 fps while waving or showing hearts or z's, 12 fps while standing, and 2 fps while hidden. The canvas is only redrawn when something visible changes. Walking just moves the window.

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
- `say()` has a 20 s cooldown for chit-chat (8 s on "a lot"). Lines about something that just happened skip the cooldown.
- Small talk comes every 45–120 s (`CHAT_GAP`, divided by the chatter rate), picked by `small_talk()` from what it's doing: walking, dancing, standing on a window, or quotes and curious questions. While napping it sometimes talks in its sleep.
- `pick()` avoids the last 25 lines it said.
- No talking when chatter is off or the pet is hidden.
- Random lines and quiet-time comments only happen when someone has touched the mouse or keyboard in the last minute, and not while it's working, asleep or showing the panel.
- "Chatter" changes how often: sometimes = ×1, a lot = ×2.5.
- All the lines are lists in `pet/lines.py` (`QUOTES`, `CURIOUS_LINES`, `WALK_LINES`, `HIGH_LINES`, `DANCE_LINES`, `SLEEP_LINES`, `FALL_LINES`, `LEAP_TRY`, `LEAP_OK`, `LEAP_FAIL`, `SQUISH_LINES`, `WORK_START`, `WORKING`, `WORK_DONE`, `IDLE_LINES`, `POKE_LINES`, `POKE_COUNT`, `DRAG_LINES`, `WAKE_LINES`, `RESET_LINES`, `MILESTONES` and more).

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
- Also `greeted` (the date of the last "good morning").
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
- 320 base units wide, with two tabs. It opens just above the bubble. If there isn't room (the mascot is high up on a window), it opens below the mascot, and if there's no room there either, beside it. It never covers the mascot or its bubble.
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
- On release, the speed comes from the mouse movement over the last 0.12 s. It's heavy: mouse speeds under 250 px/s (`THROW_MIN`) just drop it, and faster ones keep 38% (`THROW_KEEP`) of the mouse speed, up to 1500 px/s (`THROW_MAX`). Air drag is 150% per second (`THROW_DRAG`) and ground friction is 1600 px/s² (`GROUND_FRICTION`). Measured: a quick 70 px flick travels about 120 px, and a big 300 px throw about 670 px.
  - It bounces off screen edges, losing half its speed each time.
  - It bounces once off the floor if it lands faster than 700 px/s (35% bounce).
  - It bonks on the top of the screen.
  - The tilt springs back upright the short way.
- Thrown faster than 900 px/s: a scream. Landing faster than 1100 px/s: dizzy for 2.4 s (stars circle its head).
- **Parachute:** opens when falling faster than 150 px/s with more than 260 px (`CHUTE_HEIGHT`) still to go. It then falls at 110 px/s, drifting side to side. The 36-block red and white canopy has 4 strings to its raised hands and head.

**Standing on windows:**
- `list_platforms()` lists visible, normal app windows front to back (not minimized, maximized, cloaked, tool windows, click-through overlays, the desktop or taskbar, or the pet's own), at least 150×100 px. It uses the compositor's visible edges (`DwmGetWindowAttribute` 9) because `GetWindowRect` includes invisible borders.
- The list is refreshed every 0.2 s while it's falling, held, or standing on a window.
- While falling, if it passes a window's top edge with its middle more than 12 px inside the window (and nothing in front covers that spot), that window becomes its floor (`plat`, `plat_box`). Each refresh moves it with the window. If the window is gone, or it walks or slides past the edge, it falls.
- The parachute decision measures to the next ledge below, not the taskbar.

**Worried face:** open eyes plus two short slanted eyebrows on the lower half of row 0.

**Per-monitor scaling:** `GetDpiForMonitor` gives each screen's scaling (`Screen.dpi`), and the size used is `scale × that screen's dpi`. Moving to a monitor with different scaling resizes it once.

**Keyboard shortcuts:** a background thread registers them with `RegisterHotKey` and runs its own message loop. Presses come back to the main thread through a queue.

**Notifications:** a Windows toast sent through PowerShell (`Windows.UI.Notifications`), in the background, with no console window.

**Sounds:** made the first time they're needed, using maths (sine sweeps, a wobbly sawtooth scream, a noise whoosh), into `%TEMP%\claude_pet_sounds\<sound>_<volume>.wav`. Played with `winsound`, asynchronously. Windows' simple player has no volume control, so each volume level gets its own quieter copy of the file.

**Error log:** `log_error()` appends a time stamp and traceback to `pet_errors.log`, trimming to the newest half when it's over `ERROR_LOG_KB`. Tk callback errors, log-reading errors, notification and sound errors, and crashes all go there.

**Settings window:** a borderless window drawn on one canvas, in the details panel's style (same colours, Segoe UI sizes, pill buttons, rounded corners).
- Five tabs; every tab gets the height of the tallest one, so the tabs never move. The "Changes apply straight away" note sits at the bottom.
- Each option is a row from `rows()`:
  - **Switches** are a pill-shaped track (orange when on) with a round knob; the whole row is clickable.
  - **Choices** are pill buttons.
  - **Sliders** have an orange fill and a round knob you drag.
- The descriptions come from `TIPS`. The window moves when you drag its title.

**Right-click menu:** a small borderless window drawn the same way (`PopupMenu`): Refresh now, Settings, a divider, Quit. It highlights the row under the mouse. When you right-click the mascot, it opens to the mascot's right (or left if there's no room), level with its feet, so it never covers the mascot. Opening it closes an unpinned details panel, and hovering doesn't open the panel while the menu is open (the panel used to pop up over the menu and catch its clicks). It's moved with `move_window()`, which checks the window really arrived and uses `SetWindowPos` if Tk held the move back (that was why the menu only worked once). Ten times a second it checks for a mouse press outside itself (`GetAsyncKeyState`) and closes if it finds one. Esc closes it too.

**Dancing:** a 5% chance whenever it stops walking (or when it's bored). It lasts 3.5–6 s. The beat is 0.25 s: arms up left, down, up right, both up. It bops down on beats 2 and 4 and sways half a block, with music notes floating up.

**Single instance:** a named mutex, `claude-usage-pet`.

**Settings file:**
- `pet_settings.json` holds:
  - `scale`, `x` and `y`
  - on/off switches: `walk`, `jump`, `naps`, `anim`, `wizard`, `warn`, `cc_app`, `hide_fs`, `one_monitor`
  - `poll`, the refresh time in seconds (120/180/240/300)
  - `notify`, `sounds`, `hotkeys`, `platforms` (on/off) and `volume` (0–100)
  - `warn_at` (70/75/80/85) and `panic_at` (85/90/95), the yellow and red ring levels
  - `bubble` ("both" / "5h" / "hover") and `bubble_style` ("numbers" / "bars")
  - `chatter` ("off" / "some" / "lots")
  - the panel's `panel_tab`, `plan_chart` ("5h" / "7d"), `cc_view` and `cc_range`
- It's written to a temporary file first, then swapped in, so a crash can't leave half a file.
- Bad or missing values fall back to the defaults.

**Start with Windows:**
- Makes a shortcut named `Claude Usage Pet.lnk` in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.
- The shortcut targets the `pyw` launcher if it's on the path (it picks the newest Python, so it survives Python updates), otherwise this Python's `pythonw.exe`. The script path is its argument.

## Setup

- Windows 10 or 11 (tested on Windows 11).
- Python 3.10 or newer with tkinter (tested with Python 3.14). No pip installs. The code's syntax was checked against 3.8 to 3.14, but it has only been run on 3.14.
- Claude Code installed and signed in on the same computer.
- The development computer has two 1920×1080 monitors side by side, with the taskbar at the bottom of both.
- Everything specific to one computer (paths, monitors, the Python install) goes in `LOCAL_NOTES.md`, which git ignores.

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
- Hiding during full screen on the second monitor and coming back afterwards.
- Walking from the second monitor onto the main one.
- Seven simulated monitor layouts: level, lower, higher, too high, one-monitor mode, full-screen neighbour, and a bigger monitor on the left.
- CPU: about 4% of one core while walking, about 2% while standing.

**Version 4, tested on 2026-10-09** (second monitor, fake plan numbers):
- Grabbed by the arm, it hangs sideways (90°) and swings.
- A throw from the second monitor onto the main one, with a scream.
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

**Version 5, tested on 2026-10-09** (second monitor):
- Landing on a real window from another program, riding it when it moved, and falling when it closed.
- The parachute only on long drops.
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

**Version 5.1, tested on 2026-10-09:**
- The new right-click menu: opening upward, hover highlight, "Settings" opening the window, closing on an outside click.
- All five settings tabs.
- A switch, a choice button and the volume slider, each changed and saved, with the sample file made at 25%.

**Version 5.4, tested on 2026-10-09** (second monitor, real windows from a second program):
- Dragging the window it stands on: it stayed exactly in place on the window, 0 px drift per frame.
- A window sliding over it: pushed along, at most 4 px overlap for a frame.
- Cornered at the screen edge: dropped through to the taskbar.
- A window suddenly brought to the front over it: scooted out the nearer side within 0.4 s.
- Not tested: dragging a real app's window by its title bar with the mouse (the test moved windows by code).

**Version 5.5, tested on 2026-10-09** (second monitor, real windows):
- Jumps from the taskbar: easy window (150 px up) 5/6 made it, medium (280 up) 5/6, too high (390 up) 0/6, each with a line before and an excuse or a brag after.
- Window to window (220 px up): 4/5 made it.
- Small talk over 20 simulated minutes at "Sometimes": about 16 lines, matching what it's doing (walking, dancing, standing on a window, idle), with no repeats.
- The version 5.4 window tests still pass.

**Version 5.6, tested on 2026-10-09** (second monitor, real windows):
- Taskbar: a window sliding in pushed it from x −1220 to −1450 (at most 17 px overlap for a frame); squeezed into the screen edge it stayed put on the floor.
- Leap of faith off a window 520 px up: dove head first, landed in hay, popped out onto the floor (screenshots checked).
- Personalities over 3 simulated minutes: Parkour! 73% walking / 15 hops / 0 naps, Lively 64% / 10 / 0, Normal 41% / 7 / 3, Chill 24% / 4 / 6, Statue 0% / 0.
- Settings: the Personality row (five pills) fits and switches.
- The 5.4 and 5.5 window and jump tests still pass.

**Version 5.7, tested on 2026-10-09** (second monitor, real windows):
- Jumping for a window that's too high, from beside it: hit the side every time (8/8), for windows that end above the taskbar and ones that go behind it, then landed beside it with no overlap.
- The same jump from in front of a window that goes behind the taskbar: landed back in front and stayed (not pushed).
- A window ending exactly at the taskbar slid over it: pushed. One that goes behind the taskbar: not pushed.
- Success rates now that the side counts: 150 px up 10/10, 280 px up 7/12, 390 px up 0/6. Window to window 5/5.

**Not tested yet:**
- Real API data inside the pet.
- Wizard mode triggered by real Claude Code activity (it was tested by calling it directly).
- The quiet-time comments and random quotes on their real timers.
- Real mouse hover, click, drag and throw. These were tested with pretend mouse events.
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
