# the mascot's pixel shapes and all the colours.


# the mascot. same shape as claude code's welcome screen:
#    ▐▛███▜▌
#   ▝▜█████▛▘
#     ▘▘ ▝▝
# every terminal character is 2x2 small blocks, so it is 18 blocks wide and 5 tall.
# each block is a solid rectangle (not text) so the edges stay sharp on a see-through window.
BODY = [
    "...############...",
    "...############...",
    "..##############..",
    "...############...",
]
ARMS = ((1, 2), (16, 2))
WAVE = (((15, 1), (16, 1)), ((15, 1), (16, 0)))   # right arm, two waving frames
LEGS_STAND = (4, 6, 11, 13)
LEGS_STEP = (5, 7, 10, 12)
LEGS_AIR = (3, 5, 12, 14)
EYES = (5, 12)             # columns on row 1
BLUSH = (4, 13)            # columns on row 2, when it's happy
BLOCK_W, BLOCK_H = 4, 8    # one block at 1x. terminal blocks are twice as tall as wide.

# little pictures made of small square blocks (2 px at 1x)
HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
ZZZ = ["####", "..#.", ".#..", "####"]
SPARK = [".#.", "###", ".#."]
HAT = [                    # the wizard hat. # = hat, y = gold band, * = star
    "...............##.......",
    ".............###........",
    "............####........",
    "...........#####........",
    "..........#######.......",
    ".........####*####......",
    "........####***####.....",
    "........#####*#####.....",
    ".......#############....",
    ".......yyyyyyyyyyyyy....",
    "....###################.",
]

LEFT_WAVE = (((2, 1), (1, 1)), ((2, 1), (1, 0)))   # the left arm, mirror of WAVE
NOTE = ["..##", "..#.", "..#.", "###.", "###."]   # a music note, for dancing
# the parachute: a dome with red and white stripes
CHUTE = ["".join(("r" if (i // 4) % 2 == 0 else "w") if abs(i - 17.5) < w / 2 else "." for i in range(36))
         for w in (12, 20, 26, 30, 34, 36)]

ORANGE, EYE, BLUSH_C = "#d77757", "#2b1a14", "#f4a08f"
BUBBLE, BUBBLE_TEXT = "#1f1e1d", "#f2efe8"
SPEECH, SPEECH_TEXT = "#f2efe8", "#2b1a14"
HEART_C, ZZZ_C, SHADOW = "#ff6f8a", "#f2efe8", "#2b1a14"
WARN_C, PANIC_C = "#f2c14e", "#e5534b"
FULL_C, FULL_EDGE = "#0d0d0d", "#c8c8cd"   # the ring at 100%: black with a silver edge
NOTE_C = ["#ff9ad5", "#8be9fd", "#ffe08a"]
HAY_C = ["#e3b54a", "#f4d77c", "#b8862c"]   # hay: base, light straw, dark straw
CHUTE_R, CHUTE_W, STRING_C = "#e5534b", "#f2efe8", "#d9d4c7"
HAT_C, BAND_C, STAR_C, WAND_C = "#6c4ab6", "#f2c14e", "#ffe08a", "#8b5a2b"
SPARK_C = ["#ffe08a", "#8be9fd", "#ff9ad5", "#ffffff"]
DIM, RED, TRACK = "#8e8e93", "#e5534b", "#3a3a3c"
KEY = "#010203"            # this exact colour becomes see-through (and click-through)
PARK = -32000              # hidden windows are parked way off screen
