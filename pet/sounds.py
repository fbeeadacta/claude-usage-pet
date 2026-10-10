# the sound effects, made from maths (no sound files to ship).
import math
import os
import random
import struct
import tempfile
import threading
import wave
from pathlib import Path


SOUND_DIR = Path(tempfile.gettempdir()) / "claude_pet_sounds"


SOUND_LEVEL = 0.07   # how loud every sound is at 100% volume (average power; all sounds levelled to this)
SOUND_TRIM = {"eagle": 0.55, "scream": 0.6, "hay": 0.6, "spell": 0.8, "chime": 0.85, "dance": 0.75}   # by-ear adjustments
SOUND_VERSION = 5   # bump this when a sound changes, so old saved copies aren't used
# how the sounds are grouped and named in settings, where each one can be switched off
SOUND_GROUPS = (("Reactions", (("pop", "Poke"), ("boing", "Bounce"), ("scream", "Scream"), ("splat", "Wall splat"))),
                ("Adventures", (("whoosh", "Parachute"), ("eagle", "Eagle cry"), ("hay", "Hay landing"))),
                ("Moods", (("spell", "Wizard magic"), ("dance", "Dance music"), ("chime", "Milestones"))))
SOUNDS = ("pop", "boing", "scream", "chime", "whoosh", "eagle", "splat", "spell", "hay", "dance")


def make_sound(kind, volume=100):
    # little sound effects, made from maths the first time they're needed (no sound files to ship).
    # windows' simple sound player has no volume knob, so each volume gets its own quieter copy.
    volume = max(0, min(100, int(volume)))
    path = SOUND_DIR / f"{kind}_{volume}_v{SOUND_VERSION}.wav"   # a new version = fresh files
    if path.exists():
        return path
    rate, buf, at = 22050, [], [0.0]
    rng = random.Random(kind)   # the same sound every time it's made

    def wav(dur, f0, f1, vol=0.5, wobble=0.0, shape="sine", attack=0.01, decay=1.5, vib=7):
        # one note: a pitch slide from f0 to f1, a wave shape, a quick fade in and a fade out
        n, out, phase = int(rate * dur), [], 0.0
        for i in range(n):
            k = i / n
            f = f0 + (f1 - f0) * k + (math.sin(i / rate * 2 * math.pi * vib) * wobble if wobble else 0)
            phase += 2 * math.pi * f / rate
            if shape == "noise":
                v = rng.uniform(-1, 1)
            elif shape == "saw":
                v = ((phase / math.pi) % 2) - 1
            elif shape == "square":
                v = 0.6 if math.sin(phase) >= 0 else -0.6
            elif shape == "tri":
                v = 2 * abs(((phase / math.pi) % 2) - 1) - 1
            else:
                v = math.sin(phase)
            out.append(v * min(1.0, i / (rate * attack)) * (1 - k) ** decay * vol)
        return out

    def soft(samples, a=0.2):
        # takes the hiss off noise (a simple low-pass), for thuds and rustles
        y, out = 0.0, []
        for x in samples:
            y += a * (x - y)
            out.append(y * 2)
        return out

    def mix(when, samples):
        i0 = int(when * rate)
        if len(buf) < i0 + len(samples):
            buf.extend([0.0] * (i0 + len(samples) - len(buf)))
        for j, v in enumerate(samples):
            buf[i0 + j] += v

    def tone(dur, f0, f1, **kw):   # one after another
        mix(at[0], wav(dur, f0, f1, **kw))
        at[0] += dur

    if kind == "pop":
        tone(0.09, 700, 1400)
    elif kind == "boing":
        tone(0.35, 160, 520, wobble=60)
    elif kind == "scream":
        tone(0.75, 950, 480, vol=0.35, wobble=40, shape="saw")
    elif kind == "chime":
        tone(0.16, 880, 880)
        tone(0.28, 1320, 1320)
    elif kind == "eagle":   # a long raspy hawk cry as it leaps off: a short rising "kee", a long falling
        # "eeeeeerrr" that holds before it trails away, a breathy edge, and an echo off the mountains
        cry = [0.0] * int(2.6 * rate)

        def put(when, samples):
            i0 = int(when * rate)
            for j, v in enumerate(samples[:len(cry) - i0]):
                cry[i0 + j] += v

        put(0.0, wav(0.16, 2100, 2900, 0.22, wobble=140, shape="saw", attack=0.02, decay=0.6, vib=42))
        put(0.13, wav(0.55, 3050, 2600, 0.3, wobble=220, shape="saw", attack=0.03, decay=0.15, vib=34))
        put(0.66, wav(1.25, 2600, 1300, 0.3, wobble=240, shape="saw", attack=0.002, decay=1.6, vib=30))
        put(0.13, soft(wav(1.6, 0, 0, 0.13, shape="noise", attack=0.05, decay=1.4), 0.55))
        for delay, gain in ((0.0, 1.0), (0.22, 0.32), (0.45, 0.14)):   # the echo
            mix(delay, [v * gain for v in cry[:int(2.15 * rate)]])
    elif kind == "splat":   # face meets window: a dull thud and a wet slap
        mix(0.0, wav(0.2, 150, 45, 0.5, attack=0.002, decay=2.0))
        mix(0.0, soft(wav(0.22, 0, 0, 0.5, shape="noise", attack=0.001, decay=2.5), 0.25))
        mix(0.03, wav(0.1, 700, 250, 0.12, shape="saw", attack=0.002, decay=2.5))
    elif kind == "spell":   # magic: a quick sparkly run up the scale with a shimmer
        for i, note in enumerate((1047, 1319, 1568, 2093, 2637, 3136)):
            mix(i * 0.05, wav(0.4, note, note, 0.16, wobble=note * 0.012, attack=0.003, decay=2.2, vib=9))
        mix(0.0, soft(wav(0.6, 0, 0, 0.05, shape="noise", attack=0.1, decay=1.2), 0.6))
    elif kind == "hay":   # landing in a haystack: a soft "tsssshh" of straw, a faint thump under it
        hiss = wav(0.75, 0, 0, 0.55, shape="noise", attack=0.008, decay=2.2)
        low = soft(hiss, 0.35)
        mix(0.0, [(h - l) * 0.65 for h, l in zip(hiss, low)])   # keeps only the hissy top end: tsss
        mix(0.0, soft(wav(0.3, 0, 0, 0.25, shape="noise", attack=0.004, decay=2.5), 0.25))   # body of the straw
        mix(0.0, wav(0.1, 90, 50, 0.18, attack=0.002, decay=2.0))
    elif kind == "dance":   # a bouncy little chiptune that loops while it dances (2 bars at 150 bpm)
        step = 0.2   # one eighth note
        c5 = 523.25
        tune = (0, None, 7, 4, 9, 7, 4, None, 2, 4, 7, None, 12, 9, 7, 4)
        bass = (-24, -24, -29, -29, -27, -27, -31, -29)   # C C G G A A F G, a quarter note each
        for i, n in enumerate(tune):
            if n is not None:
                f_ = c5 * 2 ** (n / 12)
                mix(i * step, wav(step * 0.9, f_, f_, 0.12, shape="square", attack=0.005, decay=1.2))
        for i, n in enumerate(bass):
            f_ = c5 * 2 ** (n / 12)
            mix(i * 2 * step, wav(step * 1.8, f_, f_, 0.2, shape="tri", attack=0.005, decay=0.8))
        for i in range(16):   # drums: a kick on the beat, a hi-hat in between
            if i % 2 == 0:
                mix(i * step, wav(0.1, 120, 50, 0.28, attack=0.002, decay=2.0))
            else:
                mix(i * step, soft(wav(0.04, 0, 0, 0.1, shape="noise", attack=0.001, decay=2.0), 0.9))
        loop = int(16 * step * rate)
        buf[:] = (buf + [0.0] * loop)[:loop]   # exactly two bars, so the loop doesn't stumble
    else:   # whoosh: the parachute opening. a deep "floom", like a big sheet of cloth catching the air
        n = int(0.7 * rate)
        air = soft(soft(wav(0.7, 0, 0, 1.0, shape="noise", attack=0.001, decay=0.0), 0.06), 0.12)   # deep rumble
        body = []
        for i, v in enumerate(air):
            k = i / n
            swell = min(1.0, k / 0.12) * (1 - k) ** 1.8          # fills up fast, then settles
            flap = 1 + 0.35 * math.sin(i / rate * 2 * math.pi * 13) * (1 - k)   # the cloth fluttering
            body.append(v * swell * flap)
        mix(0.0, body)
        mix(0.02, wav(0.5, 85, 50, 0.3, attack=0.06, decay=1.8))   # the low "oom" as it fills
    # every sound is levelled to about the same loudness (measured as its average power, not its loudest
    # peak), then trimmed by ear: high, buzzy sounds like the scream and the eagle seem louder than they
    # measure, so they get turned down a bit more.
    if buf:
        rms = math.sqrt(sum(v * v for v in buf) / len(buf)) or 1.0
        gain = SOUND_LEVEL * SOUND_TRIM.get(kind, 1.0) / rms
        peak = max(abs(v) for v in buf) * gain
        if peak > 0.9:
            gain *= 0.9 / peak   # never so loud it clips
        buf = [v * gain for v in buf]
    soft_all = 1.0
    frames = [int(max(-1.0, min(1.0, v)) * soft_all * volume / 100 * 32767) for v in buf]
    SOUND_DIR.mkdir(exist_ok=True)
    tmp = path.with_name(f"{path.stem}_{threading.get_ident()}.tmp")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack(f"<{len(frames)}h", *frames))
    os.replace(tmp, path)   # (written aside first, so a half-made file never gets played)
    return path
