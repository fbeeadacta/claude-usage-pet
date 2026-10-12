# Contributing

Thanks for your interest in the Claude usage pet!

## Bug reports and ideas: yes please

[Open an issue](https://github.com/have-you-tried-restarting/claude-usage-pet/issues/new/choose) and pick the form that fits. For bugs, these help the most:

- Your Windows version, your Python version (`py --version`), and your display scaling (Settings → System → Display).
- What you did, what you expected, and what happened instead.
- The relevant part of `data/pet_errors.log` from the pet's folder, if there is one. It never contains your login token, and it replaces your user folder with `~`.

**Never paste your `.credentials.json`, a login token, or anything that starts with `sk-ant-`.** Nobody here will ever ask for them.

Found a security problem? Please follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Code changes

This project doesn't accept pull requests. It's a personal project kept to one person's taste, and changes come from the maintainer. If you'd like to see something changed, an issue describing it is the best way to get it in.

You're welcome to **fork it** and make it your own under the [MIT licence](LICENSE). If you do, please keep the note that it's unofficial and not affiliated with Anthropic.

## If you work on a fork

- **Python's standard library only** (tkinter, urllib, ctypes, winsound, wave...). No pip installs, so it stays a double-click to run.
- **Never print, log or save the login token**, and never send it anywhere except `https://api.anthropic.com`.
- **Don't hammer the usage service while testing.** It throttles hard: a "slow down" can last up to an hour. Set `PET_FAKE_USAGE=ok` (or `offline`, or `429`) before starting the pet to use made-up numbers with no network at all:

  ```powershell
  $env:PET_FAKE_USAGE = "ok"; py claude_pet.py
  ```

- `pet/__init__.py` lists what each file does. `docs/PROJECT_NOTES.md` explains how everything works, including the hidden dev mode (press Ctrl + Shift + D with the settings window open), which plays any animation on demand.
