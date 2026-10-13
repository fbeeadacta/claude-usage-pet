# reading your login, asking the usage api, and turning the answer into numbers and times.
import datetime
import json
import os
import time
import urllib.request
import urllib.error

from .config import (AHEAD_BY, CREDENTIALS, FAKE_USAGE_ENV, IDLE_HOURS_WEEKLY, IDLE_MIN_5H, NICE, ONLY_KNOWN_LIMITS,
    SLOW_BELOW, URL, USER_AGENT)


# ---- talking to the api ----

class NoRedirects(urllib.request.HTTPRedirectHandler):
    # urllib would follow a redirect and send the login token along to wherever it points.
    # the token may only go to api.anthropic.com, so a redirect is treated as an error instead
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirects)


def read_login():
    # (token, when it expires as unix seconds or None). claude code writes expiresAt in milliseconds
    try:
        creds = json.loads(CREDENTIALS.read_text())["claudeAiOauth"]
        token = creds["accessToken"] or None
    except (OSError, ValueError, KeyError, TypeError):
        return None, None
    try:
        expires = float(creds.get("expiresAt")) / 1000
    except (TypeError, ValueError):
        expires = None
    return token, expires


def login_expired():
    # the saved login has run out (claude code renews it when it next runs). no network, no token kept
    token, expires = read_login()
    return bool(token) and expires is not None and time.time() >= expires


LOGIN_HELP = ("To fix it, Claude Code needs to log you in again:\n"
              "1. Press the Windows key, type cmd and press Enter. A black Command Prompt window opens.\n"
              "2. Type claude and press Enter.\n"
              "3. If it asks you to log in, follow the steps (type /login and press Enter if it doesn't ask). "
              "Your browser opens: sign in to your Claude account and click Authorize.\n"
              "4. When Claude Code shows its prompt, you're done. Close the window (type /exit or click X). "
              "The mascot notices the new login within a few seconds.\n"
              "If step 2 says 'claude' is not recognized, install Claude Code first from claude.com/claude-code.")
LOGIN_EXPIRED = ("login expired. The mascot can't see your usage until Claude Code renews it. Using Claude Code "
                 "in a terminal usually does that by itself; if not, log in again.\n\n" + LOGIN_HELP)
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


def fake_usage():
    # offline test mode (env PET_FAKE_USAGE): no network, no token read. "ok" = made-up numbers,
    # "offline" = no connection, "429" = a "slow down" with a one hour wait
    mode = os.environ.get(FAKE_USAGE_ENV, "").lower()
    LAST.clear()
    LAST.update(status="fake-" + mode)
    if mode == "offline":
        return None, "no connection (offline test mode)."
    if mode == "429":
        global RETRY_AFTER
        RETRY_AFTER = 3600
        return None, "rate limited."
    soon = lambda s: (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=s)).isoformat()
    return {"five_hour": {"utilization": 40.0, "resets_at": soon(2 * 3600)},
            "seven_day": {"utilization": 20.0, "resets_at": soon(3 * 86400)}}, None


def fetch_usage():
    # returns (data, error). error is a short plain message, never the token.
    # LAST keeps what the answer looked like (status, headers' names, a short error body) for data/pet_usage.log.
    if os.environ.get(FAKE_USAGE_ENV):
        return fake_usage()
    LAST.clear()
    token, expires = read_login()
    if not token:
        return None, "no login found. The mascot reads your login from Claude Code.\n\n" + LOGIN_HELP
    if expires is not None and time.time() >= expires:
        # the login ran out and claude code hasn't renewed it yet. asking anyway only earns 401s, and a few
        # of those in a row get an hour-long "slow down", so don't touch the network until it's renewed
        LAST.update(status="expired")
        return None, LOGIN_EXPIRED
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "anthropic-beta": "oauth-2025-04-20",
    })
    t0 = time.time()
    try:
        with OPENER.open(req, timeout=10) as r:
            body = r.read()
            LAST.update(status=r.status, took=round(time.time() - t0, 1))
    except urllib.error.HTTPError as e:
        LAST.update(status=e.code, headers=interesting_headers(e.headers), took=round(time.time() - t0, 1))
        if e.code == 401:
            return None, LOGIN_EXPIRED
        if e.code == 429:
            try:
                LAST["body"] = e.read(300).decode("utf-8", "replace").replace("\n", " ")
            except Exception:
                pass
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


LAST = {}   # the last answer's status, header names and (for a 429) the short error body: never the token


def interesting_headers(headers):
    # the rate-limit related headers of an answer, as name=value (none of these hold secrets)
    keep = ("retry-after", "x-should-retry", "anthropic-ratelimit", "x-ratelimit", "request-id", "cf-ray")
    try:
        return [f"{k.lower()}={v}" for k, v in headers.items() if k.lower().startswith(keep)]
    except Exception:
        return []


RETRY_AFTER = 0   # seconds the usage service asked us to wait, from its last "slow down"
SERVICE_CHANGED = ("the usage service changed. Its answer doesn't look like it used to, so the mascot can't read "
                   "your usage right now.\n\nThis usually needs an update to the mascot. data/pet_errors.log (in its "
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
