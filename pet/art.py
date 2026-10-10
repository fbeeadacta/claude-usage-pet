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

# seasonal outfits, worn on the head like the wizard hat (all made of the same small blocks)
PUMPKIN = [                # halloween: a jack-o'-lantern. o = pumpkin, # = glowing face, g = stem
    "......gg......",
    ".....gg.......",
    "...oooooooo...",
    ".oooooooooooo.",
    "oo##oooooo##oo",
    "ooo#oooooo#ooo",
    "oooooo##oooooo",
    "oo#oooooooo#oo",
    ".oo########oo.",
    "...oooooooo...",
]
SANTA = [                  # christmas. r = red, w = white fur
    "...............ww.......",
    "..............wwww......",
    "..............rww.......",
    "............rrr.........",
    "...........rrrr.........",
    "..........rrrrrr........",
    ".........rrrrrrrr.......",
    "........rrrrrrrrrr......",
    ".......rrrrrrrrrrrr.....",
    ".....wwwwwwwwwwwwwwwww..",
    ".....wwwwwwwwwwwwwwwww..",
]
PARTY = [                  # new year and its birthday. p / c / y = pink, cyan, yellow stripes
    "......yy......",
    ".....yyyy.....",
    "......yy......",
    "......pp......",
    ".....pppp.....",
    ".....cccc.....",
    "....cccccc....",
    "....yyyyyy....",
    "...yyyyyyyy...",
    "...pppppppp...",
    "..pppppppppp..",
    "..cccccccccc..",
    ".cccccccccccc.",
]
LOVE = [                   # valentine's day: two hearts on springs
    ".##.##.......##.##.",
    "#######.....#######",
    ".#####.......#####.",
    "..###.........###..",
    "...s...........s...",
    "...s...........s...",
    "...s...........s...",
]
# bedtime: an old-fashioned nightcap, flopped over to one side with a bobble on the end. about the wizard hat's size.
# S = the striped part (turned into blue and white stripes below), W = the white cuff, p = the bobble
NIGHTCAP = ["".join(("b" if (i + r) // 2 % 2 else "w") if ch == "S" else ch for i, ch in enumerate(line))
            for r, line in enumerate([
    "...........SSSS.........",
    "..........SSSSSSS.......",
    ".........SSSSSSSSSS.....",
    "........SSSSSSSSSSSSS...",
    ".......SSSSSSSSSS..SSS..",
    "......SSSSSSSSSSS...SS..",
    "......SSSSSSSSSSS..pppp.",
    ".....WWWWWWWWWWWWW.pppp.",
    ".....WWWWWWWWWWWWW..pp..",
])]
# the candle it carries at bedtime, in a little holder with a ring handle (held at the h on the right).
# f / o = the flame (two frames, so it flickers), k = wick, c = candle, d = wax drip, h = brass holder
CANDLE = [[".f......", "fff.....", "fof.....", "fof....."],
          ["..f.....", ".ff.....", "fof.....", "foff...."]]
CANDLE_BASE = [
    ".k......",
    "ccc.....",
    "cdc.....",
    "ccc.....",
    "ccc.....",
    "ccc..hh.",
    "hhhhhh.h",
    ".hhhh.hh",
]
CANDLE_C = {"f": "#ffd166", "o": "#ff8c3a", "k": "#2b1a14", "c": "#f3ead2", "d": "#ffffff", "h": "#d9a441"}
GLOW_C = "#ffe9a8"   # the candle's soft light
OUTFITS = {"halloween": (PUMPKIN, {"o": "#f28c28", "#": "#ffcf4d", "g": "#4f7a28"}),
           "christmas": (SANTA, {"r": "#d8343a", "w": "#f7f4ee"}),
           "newyear": (PARTY, {"p": "#ff6f8a", "c": "#5ad1e8", "y": "#ffe08a"}),
           "birthday": (PARTY, {"p": "#ff6f8a", "c": "#5ad1e8", "y": "#ffe08a"}),
           "valentine": (LOVE, {"#": "#ff6f8a", "s": "#2b1a14"}),
           "bedtime": (NIGHTCAP, {"b": "#3f6fc6", "w": "#f2efe8", "W": "#f7f4ee", "p": "#ffffff"})}
OUTFITS["bedtime_right"] = ([ln[::-1] for ln in NIGHTCAP], OUTFITS["bedtime"][1])   # heading right: bobble on the left
# the spell tome (reading files): two open spreads, so turning pages shows it reading on.
# c = leather cover, g = gold corners, p / P = page / page shadow, e / E = page edges, s = spine,
# r = red capital, i = ink, b = glowing sigil, y = its gold heart, m = ribbon bookmark
TOME = [
    [
        "..pppppppp......pppppppp..",
        ".ppppppppppPssPpppppppppp.",
        "gprrrpiipiiPssPppbbbbbpppg",
        "cprprppppppPssPpbbpppbbppc",
        "cprrpppiiipPssPpbppyppbppc",
        "cprprppppppPssPpbpyyypbppc",
        "cpiipiiiipiPssPpbbpppbbppc",
        "cppppppppppPssPppbbbbbpppc",
        "cppiiiippppPssPppppppppppc",
        "cpiiiipiiipPssPpiipiipippc",
        "cppppppppppPssPppppppppppc",
        "geEeEeEeEeEessEeEeEeEeEeEg",
        "ggeEeEeEeEeEsseEeEeEeEeEgg",
        ".gcccccccccccmccccccccccg.",
        ".............m............",
        "............m.m...........",
    ],
    [
        "..pppppppp......pppppppp..",
        ".ppipiiiipiPssPpppppppppp.",
        "gppppppppppPssPppppbpppppg",
        "cppiiiipiipPssPppppbpppppc",
        "cppppppppppPssPpppbpbppppc",
        "cpiiipiiiipPssPpppbybppppc",
        "cppppppppppPssPppbpypbpppc",
        "cpipiiiipppPssPppbpppbpppc",
        "cppppppppppPssPpbbbbbbbppc",
        "cpiiiipiiiiPssPppppppppppc",
        "cppppppppppPssPpiipiipippc",
        "geEeEeEeEeEessEeEeEeEeEeEg",
        "ggeEeEeEeEeEsseEeEeEeEeEgg",
        ".gcccccccccccmccccccccccg.",
        ".............m............",
        "............m.m...........",
    ],
]
TOME_C = {"c": "#4a2f80", "g": "#f2c14e", "p": "#f2efe8", "P": "#d9d1bf", "e": "#c9bfa9", "E": "#a99d84",
          "s": "#2e1c55", "r": "#d8343a", "i": "#5a4a7a", "b": "#4aa3ff", "y": "#ffe08a", "m": "#e5534b"}
SIGIL_GLOW = ("#4aa3ff", "#8fd0ff", "#c4e8ff")   # the sigil pulses through these
# the other wizard jobs (pet/magic.py draws them)
QUILL = [                  # writing: w = feather, v = its violet vane, g = gold nib (bottom left)
    ".....ww",
    "....wvw",
    "...wvw.",
    "..wvw..",
    ".wvw...",
    ".ww....",
    "g......",
]
QUILL_C = {"w": "#f7f4ee", "v": "#c9b8ff", "g": "#ffd166"}
SCROLL_C, ROLL_C, SCRIBBLE_C = "#f3e3b5", "#c9a865", "#3b3a6e"
RUNE_GLYPHS = [            # running commands: wizard runes falling like rain (the last one is a ">_" prompt)
    ["#.#", "##.", "#.#", "#..", "#.."], ["#.#", "#.#", ".#.", ".#.", ".#."], ["##.", "#.#", "##.", "#.#", "#.#"],
    [".#.", "#.#", ".#.", "#.#", "#.#"], ["#..", "##.", "#.#", "##.", "#.."], [".#.", "###", "#.#", ".#.", ".#."],
    ["#.#", "###", "#.#", "#.#", "#.#"], ["#..", ".#.", "#..", "...", "###"],
]
RAIN_C = ["#e9fff0", "#6ff0a0", "#2f9a5c", "#ffe08a", "#9fd3ff"]   # rune rain: brightest first, then dimmer.
                                                                    # (the last two: runes rising off the tome)
ORB_C = {"rim": "#2a1d5c", "top": "#8a9bff", "mid": "#5f68dd", "low": "#433fa8", "pink": "#ff9ad5",
         "cyan": "#8be9fd", "haze": "#7a6ee8", "glint": "#b9c4ff", "shine": "#ffffff", "gold": "#f2c14e",
         "bronze": "#b8862c"}
PORTAL_C = ["#b98cff", "#7ff3ff", "#ffffff"]
NOTES_C = [("#ffe58a", "#e8c45a"), ("#ff9ec7", "#e57aa8"), ("#a8f0a0", "#7fcf77"), ("#9fd3ff", "#73b2e8")]
QMARK = [                  # asking you: the "?" (its dot is drawn on its own, bouncing)
    "..#####..",
    ".#######.",
    "###...###",
    "###...###",
    "......###",
    ".....###.",
    "....###..",
    "...###...",
    "...###...",
]
QMARK_MINI = ["##.", "..#", ".#.", "...", ".#."]
QMARK_C, QMARK_BACK, QMARK_EDGE = "#ffd166", "#e0a83a", "#9c6b1c"
QMARK_TINTS = ("#8be9fd", "#ff9ad5", "#ffffff")
CIRCLE_C = ["#b98cff", "#7ff3ff", "#e9d8ff"]
RUNE_SMALL = [[".#.", "###", ".#."], ["#.#", ".#.", "#.#"], ["##.", ".##", "##."], [".#.", "#.#", ".#."]]
HOURGLASS_C = {"G": "#ffe39a", "g": "#f2c14e", "o": "#b8862c", "w": "#8b5a2b", "W": "#5e3a1a",
               "l": "#bfe3ff", "h": "#ffffff", "i": "#2c2350", "y": "#ffd166", "Y": "#e0a83a", "s": "#ffffff"}
# (thinking: gold caps, wooden posts and their rings, glass and its shine, the dark inside, sand, a twinkle)
MOTE_C = ["#ffe08a", "#8be9fd", "#ff9ad5", "#ffffff", "#b98cff", "#7ff3ff", "#6ff0a0", "#ffd166"]
# idle activities (pet/idle.py)
SMOKE_C = ["#c9c3b5", "#8e8a82"]   # smoke, and the dust it sweeps up
BRISTLE_C, TIE_C, DUST_C = "#e3b54a", "#d8343a", "#a8a39a"   # the broom's head and its red band, specks of dust
CANVAS_C, EASEL_C = "#f7f4ee", "#8b5a2b"
PAINT_C = {"k": "#2b1a14", "r": "#e5534b", "o": "#f28c28", "y": "#ffd166", "g": "#4f9a3a", "l": "#8fd16a",
           "b": "#4aa3ff", "c": "#8be9fd", "p": "#ff8fb8", "w": "#ffffff", "t": "#f3e3b5", "n": "#8b5a2b",
           "a": "#b4b4bc", "m": "#d77757"}
PAINTINGS = {              # the little pictures it paints (12 x 12, letters from PAINT_C, "." = bare canvas)
    "flower": ["............", "....pppp....", "...pppppp...", "..ppyyyypp..", "..ppyyyypp..", "...pppppp...",
               "....pppp....", ".....gg.....", "..ll.gg.....", "...llgg.ll..", ".....ggll...", "gggggggggggg"],
    "heart": ["............", "............", "..rrr..rrr..", ".rrwrrrrrrr.", ".rwrrrrrrrr.", ".rrrrrrrrrr.",
              "..rrrrrrrr..", "...rrrrrr...", "....rrrr....", ".....rr.....", "............", "............"],
    "sun": ["y....yy....y", ".y........y.", "....oooo....", "...oooooo...", "..oooooooo..", "yyokkookkoyy",
            "..oooooooo..", "..okooooko..", "...okkkko...", "....oooo....", ".y........y.", "y....yy....y"],
    "mushroom": ["............", "....rrrr....", "..rrwwrrrr..", ".rrrwwrrwwr.", ".rrrrrrrwwr.", "rrwwrrrrrrrr",
                 "rrwwrrrrrrrr", "...tttttt...", "...tkttkt...", "...tttttt...", "...tttttt...", "gggggggggggg"],
    "cat": ["............", "..a......a..", "..aa....aa..", "..aaaaaaaa..", ".aaaaaaaaaa.", ".aakaaaakaa.",
            ".aaaaaaaaaa.", ".aaaappaaaa.", "..aakaakaa..", "...aaaaaa...", "............", "............"],
    "fish": ["...........c", "..........c.", "............", ".....oooo...", "o..ooooooo..", "ooooooookoo.",
             "oooooooooooo", "o..ooooooo..", ".....oooo...", "............", "............", "cc..cc..cc.."],
    "house": ["y...........", ".....rr.....", "....rrrr....", "...rrrrrr...", "..rrrrrrrr..", ".rrrrrrrrrr.",
              "..tttttttt..", "..tbbtnntt..", "..tbbtnntt..", "..ttttnntt..", "gggggggggggg", "............"],
    "me": ["..........y.", ".........yyy", "..........y.", "..mmmmmmmm..", "..mkmmmmkm..", "..mkmmmmkm..",
           "mmmmmmmmmmmm", "..mmmmmmmm..", "..mmmmmmmm..", "..m.m..m.m..", "..m.m..m.m..", "............"],
    "rainbow": ["............", "............", "....rrrr....", "..rroooorr..", ".rooyyyyoor.", ".roy....yor.",
                "roy......yor", "roy......yor", "roy......yor", "ccc......ccc", ".c........c.", "............"],
}
ICE_C, WATER_C, RIPPLE_C, BOBBER_C = "#dff3ff", "#1d3b5a", "#4f7fae", ("#e5534b", "#ffffff")
CATCHES = {                # what comes up out of the fishing hole: (picture, colours)
    "fish": (["..####...#", ".######.##", "#k########", ".######.##", "..####...#"], {"#": "#7fb8e8", "k": "#2b1a14"}),
    "gold": (["..####...#", ".######.##", "#k########", ".######.##", "..####...#"], {"#": "#ffd166", "k": "#2b1a14"}),
    "boot": (["..###...", "..###...", "..###...", "..######", "########", "ssssssss"], {"#": "#8b5a2b", "s": "#3b2a1a"}),
    "crab": ([".#....#.", "##....##", ".######.", "##k##k##", ".######.", "#.#..#.#"], {"#": "#e5534b", "k": "#2b1a14"}),
    "bug": (["#....#", ".#..#.", "..##..", ".####.", "######", ".####.", "#....#"], {"#": "#4f9a3a"}),
    "sock": (["sss..", "###..", "sss..", "###..", "#####", "#####"], {"#": "#f2efe8", "s": "#e5534b"}),
}
BALLOON_C = [("#e5534b", "#ff9a92"), ("#4aa3ff", "#a8d4ff"), ("#ffd166", "#fff0b8"), ("#ff8fb8", "#ffd0e2"),
             ("#6fcf6a", "#bff0bc"), ("#b98cff", "#e2d1ff")]   # (balloon, its shine)
PLANE = [                  # a paper plane flying right. # = paper, s = its shaded underside
    "#...........",
    "###.........",
    ".######.....",
    "..sssss#####",
    "...sss##....",
]
PLANE_C = {"#": "#f7f4ee", "s": "#c9c3b5"}
# rare visitors
UFO = [                    # c = glass dome, w = shine, g = hull, l = blinking lights, d = feet
    "......cccccc......",
    ".....cwcccccc.....",
    "....cccccccccc....",
    "..gggggggggggggg..",
    "gglggglggglggglggg",
    "..gggggggggggggg..",
    "....dd......dd....",
]
UFO_C = {"c": "#8be9fd", "w": "#ffffff", "g": "#a7a9b4", "d": "#5b5d66"}
UFO_LIGHTS = ("#ffe08a", "#e5534b")
BEAM_C = "#fff3b0"
CAT_A = [                  # a cat walking right (flipped when it walks left). e = eyes
    "#.............#.#",
    "#.............###",
    "#.............e#e",
    ".#.###########.#.",
    "..##############.",
    "..#############..",
    "..#.#.......#.#..",
]
CAT_B = CAT_A[:6] + ["...#.#.....#.#..."]
CAT_C = {"#": "#b4b4bc", "e": "#7bd13f"}
BALL = [".rrrr.", "rwwrrr", "rwrrrr", "rrrrrr", "rrrrrd", ".rrdd."]
BALL_C = {"r": "#e5534b", "w": "#ffb3ad", "d": "#a8322c"}
SHINY = "#f0c75e"          # the rare colour

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
