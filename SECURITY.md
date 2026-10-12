# Security policy

## Reporting a problem

If you find a security or privacy problem, please **don't open a public issue**. Report it privately instead:

1. Go to the [Security tab](https://github.com/have-you-tried-restarting/claude-usage-pet/security) of this repository.
2. Click **Report a vulnerability** and describe what you found.

Only the maintainer can see these reports. This is a hobby project, so there's no fixed response time, but security reports come first.

Only the latest version on the `main` branch gets fixes.

## What the pet can access

So you know what's at stake:

| What | How it's used |
| --- | --- |
| Your Claude Code login token (`~/.claude/.credentials.json`) | Read on your computer and sent **only** to `https://api.anthropic.com/api/oauth/usage`, over HTTPS with certificate checks, to get your usage numbers. Redirects are refused, so it can't be sent anywhere else. Never printed, logged or saved. |
| Claude Code's logs (`~/.claude/projects`) | Only numbers, times, model names, tool names and project folder names are read. Never the text of your conversations. Nothing from the logs leaves your computer. |
| Its own `data` folder | Settings, its memory, a cache of the log numbers, and two small logs. The error log replaces your user folder with `~`. |
| PowerShell | Used only to show Windows notifications and to make the "Start with Windows" shortcut. The text passed in is escaped. |

The pet uses only Python's standard library: it has no third-party packages and downloads nothing.

## Things worth reporting

- Any way the login token could reach anything other than `api.anthropic.com`, or end up in a file or on screen.
- Any way text from Claude Code's logs or another program could make the pet run commands.
- Anything that leaks personal details into the files the pet writes.
