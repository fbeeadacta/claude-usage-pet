# Claude usage pet

A Windows desktop mascot that shows Claude plan usage. `claude_pet.py` starts it; the code is in `pet/`.
`pet/__init__.py` lists what each file does and where new things go, so only open the files a change needs.

## Start here
- Read `docs/PROJECT_NOTES.md` before making changes. It has the full spec, how things work, settings and known limits. The change log is in `docs/CHANGELOG.md`.
- After every change, update `docs/PROJECT_NOTES.md`: bump the version at the top, and add a change log entry in `docs/CHANGELOG.md`.
- Also read `CLAUDE.local.md` if it exists (personal, machine-specific notes; not in git).

## Rules
- Python standard library only (tkinter, urllib, ctypes, winsound, wave, ...). No pip installs.
- Never print, log or save the login token. It may only be sent to https://api.anthropic.com.
- Only commit or push when asked. Before pushing, if `CLAUDE.local.md` exists, run its pre-push check.
- Keep personal or machine-specific info out of the repo (it may go public). That belongs in `docs/LOCAL_NOTES.md` or `CLAUDE.local.md`, which are gitignored.
- Code comments: casual and lowercase, no doc-comment blocks. Match the surrounding code.
- Keep each file's imports explicit. `usage.RETRY_AFTER` changes at run time: read it through the module.

## Working on it
- Say plainly when something is untested or uncertain.
- Test with `SETTINGS_FILE` / `STATE_FILE` / `ERROR_LOG` / `CC_CACHE` pointed at a scratch folder, and `SUMMON_EVENT` set to another name, so tests don't clash with the user's running pet. Files import these names, so a test must patch a name in every `pet.*` module that has it, not just one.
- The running pet only loads new code after it's quit (right-click → Quit) and started again.
