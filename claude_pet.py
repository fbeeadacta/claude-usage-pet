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
# run it:      double-click "Start pet.bat"   (finds python for you, no console window)
#              pythonw claude_pet.py          (no console window)
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

MIN_PYTHON = (3, 10)
PYTHON_PAGE = "https://www.python.org/downloads/windows/"


def problem(text, offer_download=False):
    # says what's wrong in a normal windows pop-up (works without a console), then quits.
    # plain old python only up here, so even a too-old python gets this far
    print(text, file=sys.stderr)
    if sys.platform == "win32":
        import ctypes
        if offer_download:
            text += "\n\nOpen the Python download page now?"
            if ctypes.windll.user32.MessageBoxW(None, text, "Claude usage pet", 0x34) == 6:   # yes/no + warning, 6 = yes
                import webbrowser
                webbrowser.open(PYTHON_PAGE)
        else:
            ctypes.windll.user32.MessageBoxW(None, text, "Claude usage pet", 0x30)
    sys.exit(1)


def check_setup():
    # the things the pet can't work without. checked before any of the pet's code loads
    if sys.platform != "win32":
        problem("Sorry, the Claude usage pet only works on Windows.")
    if sys.version_info < MIN_PYTHON:
        problem("The Claude usage pet needs Python %d.%d or newer, but this is Python %d.%d.\n\n"
                "Install a newer Python from python.org, then start the pet again."
                % (MIN_PYTHON + sys.version_info[:2]), offer_download=True)
    try:
        import tkinter
    except ImportError:
        problem("This Python is missing tkinter, the part that draws windows.\n\n"
                "Reinstall Python from python.org. If the installer has a \"tcl/tk and IDLE\" "
                "option, make sure it's ticked. Then start the pet again.", offer_download=True)


if __name__ == "__main__":
    check_setup()

    from pet.storage import log_error
    from pet.winapi import already_running, set_startup
    from pet.mascot import Pet

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
        if sys.stderr is None or not sys.stderr.isatty():   # no console (pythonw): say so in a pop-up
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, "The Claude usage pet stopped because of an error.\n\n"
                                             "The details are in pet_errors.log, in the pet's folder.",
                                             "Claude usage pet", 0x10)
        raise
