# reading your login, asking the usage api, and turning the answer into numbers and times.
import datetime
import json
import urllib.request
import urllib.error

from .config import (AHEAD_BY, CREDENTIALS, IDLE_HOURS_WEEKLY, IDLE_MIN_5H, NICE, ONLY_KNOWN_LIMITS,
    SLOW_BELOW, URL, USER_AGENT)


# ---- talking to the api ----

def read_token():
    try:
        creds = json.loads(CREDENTIALS.read_text())
        return creds["claudeAiOauth"]["accessToken"] or None
    except (OSError, ValueError, KeyError, TypeError):
        return None


LOGIN_HELP = ("To fix it, Claude Code needs to log you in again:\n"
              "1. Press the Windows key, type cmd and press Enter. A black Command Prompt window opens.\n"
              "2. Type claude and press Enter.\n"
              "3. If it asks you to log in, follow the steps (type /login and press Enter if it doesn't ask). "
              "Your browser opens: sign in to your Claude account and click Authorize.\n"
              "4. When Claude Code shows its prompt, you're done. Close the window (type /exit or click X). "
              "The mascot notices the new login within a few seconds.\n"
              "If step 2 says 'claude' is not recognized, install Claude Code first from claude.com/claude-code.")
CLOCK = {"24h": False, "mmdd": False}   # how times and dates are shown (settings: Clock, Dates)


def fmt_time(dt):
    # 3:05 PM, or 15:05 on the 24-hour clock
    return f"{dt:%H:%M}" if CLOCK["24h"] else f"{dt:%I:%M %p}".lstrip("0")


def fmt_day(dt):
    # Fri 16/10, or Fri 10/16
    return f"{dt:%a} {dt.month}/{dt.day}" if CLOCK["mmdd"] else f"{dt:%a} {dt.day}/{dt.month}"


def fmt_when(dt, key):
    # the 5-hour limit resets today, so just the time. the weekly one gets the day too.
    return fmt_time(dt) if key == "five_hour" else f"{fmt_day(dt)} {fmt_time(dt)}"


def fetch_usage():
    # returns (data, error). error is a short plain message, never the token.
    token = read_token()
    if not token:
        return None, "no login found. The mascot reads your login from Claude Code.\n\n" + LOGIN_HELP
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "anthropic-beta": "oauth-2025-04-20",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None, "login expired. The mascot can't see your usage until you log in again.\n\n" + LOGIN_HELP
        if e.code == 429:
            global RETRY_AFTER
            try:
                RETRY_AFTER = int(e.headers.get("Retry-After") or 0)   # the service's own "try again in"
            except (TypeError, ValueError):
                RETRY_AFTER = 0
            return None, "rate limited."
        return None, f"api error {e.code}."
    except Exception as e:
        return None, f"no connection ({type(e).__name__})."
    try:
        return json.loads(body), None
    except ValueError:
        return None, SERVICE_CHANGED


RETRY_AFTER = 0   # seconds the usage service asked us to wait, from its last "slow down"
SERVICE_CHANGED = ("the usage service changed. Its answer doesn't look like it used to, so the mascot can't read "
                   "your usage right now.\n\nThis usually needs an update to the mascot. pet_errors.log (in its "
                   "folder) lists the names of what the service sent back, which helps fix it. It keeps trying.")


def looks_right(data):
    # the usage answer still has the shape we know: a dict with a 5-hour or weekly limit in it
    return isinstance(data, dict) and ("five_hour" in data or "seven_day" in data)


def short_error(err):
    # a few words for the bubble. the details panel shows the whole message.
    for start, short in (("no login", "no login"), ("login expired", "login expired"),
                         ("rate limited", "slow down"), ("no connection", "offline"),
                         ("the usage service changed", "service changed")):
        if err.startswith(start):
            return short
    return err.rstrip(".")


def nice_name(key):
    if key in NICE:
        return NICE[key]
    return key.replace("seven_day_", "weekly ").replace("_", " ").strip()


def parse_rows(data):
    # api answer -> [{key, label, pct, resets}], most important first
    rows = []
    if not isinstance(data, dict):
        return rows
    for key, v in data.items():
        if isinstance(v, dict) and v.get("utilization") is not None and v.get("resets_at"):
            if ONLY_KNOWN_LIMITS and period_seconds(key) is None:
                continue   # a field the api lists that is not a 5-hour or weekly limit
            rows.append({"key": key, "label": nice_name(key),
                         "pct": float(v["utilization"]), "resets": v["resets_at"]})
    order = {"five_hour": 0, "seven_day": 1}
    rows.sort(key=lambda r: (order.get(r["key"], 9), r["key"]))
    return rows


def parse_time(iso):
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def same_window(a, b):
    # two resets_at values for the same limit window (they can wobble by a few seconds)
    ta, tb = parse_time(a), parse_time(b)
    return ta is not None and tb is not None and abs((ta - tb).total_seconds()) < 600


def reset_text(iso, now=None):
    reset = parse_time(iso)
    if reset is None:
        return ""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    mins = max(0, int((reset - now).total_seconds() // 60))
    if mins >= 24 * 60:
        return f"resets in {mins // 1440}d {(mins % 1440) // 60}h"
    return f"resets in {mins // 60}h {mins % 60:02d}m"


def period_seconds(key):
    # how long the window is, or None when we do not know
    if key == "five_hour":
        return 5 * 3600
    if key.startswith("seven_day"):
        return 7 * 24 * 3600
    return None


def elapsed_pct(key, resets_iso, now):
    # how far through the window the clock is, 0 to 100 (None if unknown)
    period, reset = period_seconds(key), parse_time(resets_iso)
    if not period or reset is None:
        return None
    remaining = max(0.0, (reset - now).total_seconds())
    return min(100.0, max(0.0, (period - remaining) / period * 100))


def forecast(key, pct, resets_iso, now):
    # where this pace ends up: (projected % at the reset, unix time it runs out or None), or None if
    # it's too early in the window to say
    el, reset = elapsed_pct(key, resets_iso, now), parse_time(resets_iso)
    if el is None or reset is None or el < 3 or pct <= 0:
        return None
    proj = pct / el * 100
    out = None
    if proj >= 100 and pct < 100:
        start = reset.timestamp() - period_seconds(key)
        out = start + (now.timestamp() - start) * 100 / pct
    return proj, out


def pace_info(key, pct, resets_iso, now, unchanged_seconds):
    # returns (elapsed_pct_or_None, message_or_None, kind) where kind is 'fast', 'slow' or None.
    # compares what you used with how much time has passed.
    el = elapsed_pct(key, resets_iso, now)
    if el is None or el < 10:   # too early in the window to say anything
        return el, None, None
    idle_limit = (IDLE_MIN_5H * 60) if key == "five_hour" else (IDLE_HOURS_WEEKLY * 3600)
    if unchanged_seconds >= idle_limit and pct < el:
        return el, "no usage lately. put it to work!", "slow"
    if pct >= el + AHEAD_BY:
        # used more than the clock allows, so at this rate it runs out before the reset
        return el, "ahead of pace. may hit the limit early", "fast"
    if el >= 20 and pct <= el * SLOW_BELOW:
        return el, "way under pace. use more!", "slow"
    return el, None, None


def bar_color(p):
    return "#e5534b" if p >= 85 else "#d9a441" if p >= 60 else "#4caf7d"
