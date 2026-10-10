# Claude usage pet

A Windows desktop mascot (one file: `claude_pet.py`) that shows Claude plan usage.

## Start here
- Read `PROJECT_NOTES.md` before making changes. It has the full spec, how things work, settings, known limits and the change log.
- After every change, update `PROJECT_NOTES.md`: bump the version at the top and add a change log entry.
- Also read `CLAUDE.local.md` if it exists (personal, machine-specific notes; not in git).

## Rules
- Python standard library only (tkinter, urllib, ctypes, winsound, wave, ...). No pip installs.
- Never print, log or save the login token. It may only be sent to https://api.anthropic.com.
- Only commit or push when asked. Before pushing, run the personal-details check described in `CLAUDE.local.md`.
- Keep personal or machine-specific info out of the repo (it may go public). That belongs in `LOCAL_NOTES.md` or `CLAUDE.local.md`, which are gitignored.
- Code comments: casual and lowercase, no doc-comment blocks. Match the surrounding code.

## Working with the user
- Not comfortable with terminals: give step-by-step instructions.
- Say plainly when something is untested or uncertain.
- Test on the left monitor, with `SETTINGS_FILE` / `STATE_FILE` / `ERROR_LOG` pointed at a scratch folder, so tests don't clash with the user's running pet.
- The running pet only loads new code after it's quit (right-click → Quit) and started again.
