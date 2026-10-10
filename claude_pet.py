# claude usage pet: a tiny claude mascot that lives on your taskbar and shows your
# plan usage (5-hour and weekly limits) in a bubble above its head.
#
# the numbers are for your whole plan, so they include claude.ai chat, the desktop app
# and claude code. they come from https://api.anthropic.com/api/oauth/usage, an
# undocumented endpoint that can change or stop working without notice.
# claude code's own token counts are read from its local logs (~/.claude/projects).
# only numbers are taken from those logs (times, token counts, model names), never text.
#
# your login token is read from ~/.claude/.credentials.json (claude code puts it there).
# it is only ever sent to api.anthropic.com. it is never printed, logged or saved.
#
# run it:      pythonw claude_pet.py          (no console window)
#              python claude_pet.py           (with a console, to see errors)
# start with windows:   right click the mascot > start with windows
#                       (or: python claude_pet.py --startup / --no-startup)
# hover the mascot for details. click it to poke it. right click for the menu.
# drag it to pick it up. ctrl + mouse wheel over the mascot changes its size.
# no pip installs needed. it only uses python's standard library.
#
# the code lives in the pet/ folder next to this file; see pet/__init__.py for what's where.

import sys
import argparse

from pet.storage import log_error
from pet.winapi import already_running, set_startup
from pet.mascot import Pet


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--startup", action="store_true", help="start the pet when you sign in to windows")
    ap.add_argument("--no-startup", action="store_true", help="stop starting with windows")
    a = ap.parse_args()
    if a.startup or a.no_startup:
        print(set_startup(a.startup))
        sys.exit(0)
    if already_running():
        sys.exit(0)
    try:
        Pet().root.mainloop()
    except Exception:
        log_error("the pet stopped")
        raise
