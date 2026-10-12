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
HAT = [                    # the wizard hat. # = hat, l / d = its lit and shady sides, m = moon, * = stars,
                           # y = gold band, o / b = the buckle, L = the brim's top. 23 wide, so it sits
                           # centred on the head (only the tip bends over to the right)
    "...............#d......",
    ".............##d.......",
    "............l#d........",
    "..........l#d..........",
    ".........l##*d.........",
    ".........l###d.........",
    "........l####*d........",
    ".......l####***d.......",
    ".......l#m###*dd.......",
    "......llmm#####dd......",
    ".....ll#mm#####*dd.....",
    ".....ll##m######dd.....",
    "....ll*##########dd....",
    "....yyyyyyobboyyyyy....",
    "..LLLLLLLLLLLLLLLLLLL..",
    "..dd###############dd..",
]

BUCKET = [                 # the minecraft bucket: h = handle, r = rim, w = what's in it (water, or e when
    "..hhhhhhhh..",        # it's empty), l / i / d = the iron's lit side, middle and shady side
    ".h........h.",
    ".rrrrrrrrrr.",
    "rwwwwwwwwwwr",
    "rwwwwwwwwwwr",
    ".rrrrrrrrrr.",
    ".liiiiiiidd.",
    ".liiiiiiidd.",
    "..liiiiidd..",
    "..lliiiddd..",
    "...lldddd...",
]

LEFT_WAVE = (((2, 1), (1, 1)), ((2, 1), (1, 0)))   # the left arm, mirror of WAVE
NOTE = ["..##", "..#.", "..#.", "###.", "###."]   # a music note, for dancing
# the parachute: a dome with red and white stripes
CHUTE = ["".join(("r" if (i // 4) % 2 == 0 else "w") if abs(i - 17.5) < w / 2 else "." for i in range(36))
         for w in (12, 20, 26, 30, 34, 36)]

# seasonal outfits, worn on the head like the wizard hat, and drawn the same way: a lit left side, a shady
# right side, highlights, and no dark edge round them
PUMPKIN = [                # halloween: a ribbed jack-o'-lantern with a glowing face.
                           # o / l / L / d = pumpkin, its lit side, shine, shady side. r = ribs.
                           # # / y = the glow. g / G / v / V = stem and leaf
    "...........gg.v.....",
    "..........gG.vv.....",
    ".........gG.vVv.....",
    ".....lllllllldd.....",
    "..llLLrooooooroodd..",
    ".llLo#roooooor#oodd.",
    "lloo#y#oooooo#y#oodd",
    "llooooroo##ooroooodd",
    "lloooorooooooroooodd",
    "lloo###o####o###oodd",
    ".llood##yyyy##doodd.",
    "..lloorooooooroodd..",
    ".....lddddddddd.....",
]
PUMPKIN_C = {"o": "#f28c28", "l": "#ffa94a", "L": "#ffd08a", "d": "#c25e17", "r": "#d8701f", "#": "#ffbf3a",
             "y": "#fff0a0", "g": "#6f9e36", "G": "#4a7024", "v": "#93c957", "V": "#6f9e36"}
SANTA = [                  # christmas: the tip flops over to a fluffy bobble.
                           # r / l / d = red, lit, shady. W / w / f = white fur, lit, shady
    "..........lrrd..........",
    ".........lrrrrdd........",
    "........lrrrrrrrdd......",
    "........lrrrrrrrrrdd.Ww.",
    ".......lrrrrrrrrrrrdWWww",
    ".......lrrrrrrrrrrrd.wwf",
    "......lrrrrrrrrrrrrdd.f.",
    ".....llrrrrrrrrrrrrrdd..",
    "....llrrrrrrrrrrrrrrrdd.",
    "..WWWWwwwwwwwwwwwwwwwwf.",
    "..Wwwwwwwwwwwwwwwwwwwff.",
    "..fffwwwwfwwwwfwwwwffff.",
]
SANTA_C = {"r": "#d8343a", "l": "#ef5b5f", "d": "#a8222a", "W": "#ffffff", "w": "#f2eee8", "f": "#cfc9c0"}
TOPHAT = [                 # new year: a glossy top hat with a gold band, a sparkle and confetti.
                           # k / L / K / d = black, its lit edge, sheen, shade.
                           # y / Y / b = gold band, glint, shade. p / c = confetti
    "..p.................c.",
    "..........*...........",
    ".......LKkkkkkkkd...y.",
    ".c.....LKkkkkkkkd.....",
    ".......LKkkkkkkkd.....",
    ".......LKkkkkkkkd..p..",
    "...y...LKkkkkkkkd.....",
    ".......LKkkkkkkkd.....",
    ".......yyyyyYyyyy.....",
    ".......bbbbbbbbbb.....",
    "...LLLLkkkkkkkkkkdd...",
    "...dddddddddddddddd...",
]
TOPHAT_C = {"k": "#2e2e38", "L": "#56566a", "K": "#46465a", "d": "#1b1b22", "y": "#f2c14e", "Y": "#fff3b0",
            "b": "#c9952e", "*": "#fff3b0", "p": "#ff6f8a", "c": "#5ad1e8"}
PARTY = [                  # birthday: a polka dot party hat with a pompom.
                           # c / l / d = cone, lit, shady. y = dots. P / p / q = pompom. F / f = the frill
    ".......PP.......",
    "......PPpq......",
    ".......pq.......",
    ".......lcd......",
    "......lcyd......",
    "......lccdd.....",
    ".....lccccd.....",
    ".....lycccyd....",
    "....lcccccdd....",
    "....lccyccccd...",
    "...lyccccccydd..",
    "...lcccccyccdd..",
    "..lccyccccccccd.",
    "..lccccccyccccd.",
    ".FFfFFfFFfFFfFFf",
]
PARTY_C = {"P": "#ffb3c6", "p": "#ff6f8a", "q": "#d94a6a", "c": "#5ad1e8", "l": "#9be6f4", "d": "#2fa8c4",
           "y": "#ffe08a", "F": "#ff8fab", "f": "#d94a6a"}
LOVE = [                   # valentine's day: two hearts on springs, on a headband.
                           # L / H / d = shine, heart, shade. s = spring. b / B = headband
    ".LH.HH.........LH.HH.",
    "LHHHHHd.......LHHHHHd",
    "HHHHHHd.......HHHHHHd",
    ".HHHHd.........HHHHd.",
    "..HHd...........HHd..",
    "...s.............s...",
    "..s...............s..",
    "...s.............s...",
    "..s...............s..",
    "...s.............s...",
    "bbbbbbbbbbbbbbbbbbbbB",
]
LOVE_C = {"L": "#ffd1dc", "H": "#ff5c7c", "d": "#d6375a", "s": "#c9c3bb", "b": "#e5466a", "B": "#b8304f"}
# bedtime: an old-fashioned nightcap, flopped over to one side with a bobble on the end. about the wizard hat's size.
NIGHTCAP = [               # b / w = blue and white stripes, B / c = their lit edge, D / x = their shady side,
                           # W / V / X = the cuff, its lit end and shade. p / P / q = the bobble, its shine and shade
    "...........Bwwb.........",
    "..........Bwwbbww.......",
    ".........Bwwbbwwbbw.....",
    "........Bwwbbwwbbwwbb...",
    ".......Bwwbbwwbbw..bww..",
    "......Bwwbbwwbbww...xD..",
    "......cwbbwwbbwxD..Pppq.",
    ".....VWWWWWWWWWWWW.pppq.",
    ".....XXXXXXXXXXXXX..qq..",
]
NIGHTCAP_C = {"b": "#3f6fc6", "B": "#5f8ce0", "D": "#2c5096", "w": "#f2efe8", "c": "#ffffff", "x": "#cfcac0",
              "W": "#f7f4ee", "V": "#ffffff", "X": "#d6d0c6", "p": "#f4f1ea", "P": "#ffffff", "q": "#c9c3b8"}
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
OUTFITS = {"halloween": (PUMPKIN, PUMPKIN_C), "christmas": (SANTA, SANTA_C), "newyear": (TOPHAT, TOPHAT_C),
           "birthday": (PARTY, PARTY_C), "valentine": (LOVE, LOVE_C), "bedtime": (NIGHTCAP, NIGHTCAP_C)}
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
SUMMON_C = ["#b98cff", "#7ff3ff", "#ffffff"]   # the summoning circle (PORTAL_C further down is the portal trip's)
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
# getting to another monitor (pet/travel.py)
HOOK = [                   # a grappling hook: three prongs on top, the ring the rope ties to at the bottom. m = metal
    ".mmmmm.",
    "mm.m.mm",
    "m..m..m",
    "...m...",
    "...m...",
    "..m.m..",
    "...m...",
]
HOOK_C = {"m": "#b8bcc6"}
ROPE_C = {"a": "#c9a46a", "b": "#a07a45"}   # two shades, so it looks twisted
WINGS = {                  # a right wing (the left is the same, flipped): (picture, the row it's attached at)
    "up": ([
        "..............##",
        "............####",
        "..........#####.",
        "........######..",
        "......#######...",
        "...#########....",
        "############....",
        "##########......",
        ".#.#.#.#........",
    ], 6),
    "down": ([
        "#########.......",
        "############....",
        ".##############.",
        "...############.",
        ".....#########..",
        "........###.##..",
        "..........#..#..",
    ], 1),
    "small": ([            # just sprouted, or folding away
        "....##",
        "..####",
        "######",
        "####..",
        ".#....",
    ], 2),
}
WING_C = {"#": "#f7f4ee"}
GUN = [                    # the portal gun, pointing right. t = the tip, in the colour it's about to shoot
    "..ggg...",
    "wwwwwwwt",
    "wwwwww..",
    ".gg.....",
]
GUN_C = {"w": "#f2efe8", "g": "#8e8e93"}
PORTAL_C = {               # l = bright rim, o = the portal, d = deep inside, w = a glint going round
    "blue": {"l": "#bfe3ff", "o": "#3d9bff", "d": "#123a6b", "w": "#ffffff"},
    "orange": {"l": "#ffd9a8", "o": "#ff8a1f", "d": "#6b3210", "w": "#ffffff"},
}
HATCH_C = ("#7a5230", "#1a120c")   # the trapdoor: wood, and the dark hole under it
LADDER_C = ("#b07a43", "#d9a066")                # rails, rungs
STALK_C = ("#4f9a3a", "#3d7d2c", "#7fd16a")      # the beanstalk: stalk, its darker streak, leaves
SOIL_C = ("#6b4a2b", "#8b6239")
BOX_C = ("#c79a5b", "#a97c42", "#e8cf9a")        # cardboard: front, the lid's edge, tape
CANNON_C = ("#34343a", "#5b5d66", "#7a5230", "#a87445")   # barrel, its rings, wheel, wheel's hub
FLASH_C = ("#fff3b0", "#ffd166", "#ff8a1f")      # muzzle flash, rocket flames
JET_C = ("#a7a9b4", "#e5534b", "#5b5d66")        # jetpack: tank, stripe, nozzle
# coding jokes (pet/gags.py): little pictures, no dark edges
PHONE = ["kkkkk", "ksssk", "ksssk", "ksssk", "ksssk", "kkbkk"]   # a phone (s = screen, lit brighter while it rings)
PHONE_C = {"k": "#2b2b30", "s": "#7fc7ff", "b": "#8e8e93"}
COOKIE = ["..ooo..", ".oocoo.", "ooooooo", "oooocoo", "ocooooo", ".ooooc.", "..ooo.."]   # c = chocolate chips
COOKIE_C = {"o": "#d9a05b", "c": "#5a3a22"}
DUCK = ["...yyy..", "..yyeyo.", "..yyyyoo", "y.yyy...", "yyyyyyyy", "yyyyyyyy", ".yyyyyy."]   # a rubber duck
DUCK_C = {"y": "#ffd84a", "o": "#ff8a1f", "e": "#2b1a14"}
BULB = [".www.", "wwwww", "wwwww", "wwwww", ".www.", ".ggg.", ".ggg."]   # an idea
BULB_C = {"w": "#fff3b0", "g": "#a7a9b4"}
MUG = ["mccm..", "mmmmhh", "ssss.h", "mmmmhh", "mmmm..", ".mm..."]   # c = coffee, s = a red stripe, h = handle
MUG_C = {"m": "#f2efe8", "c": "#5a3a22", "s": "#e5534b", "h": "#f2efe8"}
# ---- pet/finds.py: digging up a 404, the bug hunt, the lost semicolon ----
SHOVEL = [                 # an upright shovel: g / G = the D-grip, l / w = the wooden shaft (lit, shady),
    "..gGGg..",            # c / C = the steel socket, L / m / D = the blade (lit, steel, shady)
    ".g....G.",
    ".g....G.",
    "..gGGg..",
    "...lw...",
    "...lw...",
    "...lw...",
    "...lw...",
    "...lw...",
    "...lw...",
    "..cCCc..",
    "..cCCc..",
    ".LmmmmD.",
    "LLmmmmmD",
    "LmmmmmmD",
    "LmmmmmmD",
    "LmmmmmmD",
    ".LmmmmD.",
    "..LmmD..",
    "...mD...",
]
SHOVEL_C = {"g": "#5a3a1e", "G": "#3f2814", "l": "#c9925a", "w": "#9a6535", "c": "#9aa1ab", "C": "#6d737d",
            "L": "#e9eef4", "m": "#bcc4cf", "D": "#858e9b"}
DIRT_C = ("#8b6239", "#6b4a2b", "#a8794a", "#5a3d22", "#3a2716", "#1f150c")   # soil, its shade, its lit side,
                           # clods, the hole's sides, the hole's dark bottom
CHEST = [                  # a treasure chest: L / w / D = wood (lit, middle, shady), b / B = iron bands,
    "..LLLLLLLLLLLL..",    # y / Y = the brass lock and its shine, k = the keyhole
    ".LwwwwwwwwwwwwD.",
    "LwwwwwwwwwwwwwwD",
    "bbbbbbbbbbbbbbbB",
    "LwwwwwwyywwwwwwD",
    "LwwwwwyYYywwwwwD",
    "LwwwwwyykywwwwwD",
    "LwwwwwwyywwwwwwD",
    "bbbbbbbbbbbbbbbB",
    "LwwwwwwwwwwwwwwD",
    "LwwwwwwwwwwwwwwD",
    "DDDDDDDDDDDDDDDD",
]
CHEST_OPEN = [             # the same chest with its lid thrown back (i = the lid's dark inside, G = the glow)
    "..DDDDDDDDDDDD..",
    ".DiiiiiiiiiiiiD.",
    "DiiiiiiiiiiiiiiD",
    "bGGGGGGGGGGGGGGB",
] + CHEST[4:]
CHEST_C = {"L": "#c98a4e", "w": "#a86b35", "D": "#73441d", "b": "#5b606a", "B": "#3c4047", "y": "#e8b84a",
           "Y": "#fff0a0", "k": "#2b1a14", "i": "#3a2414", "G": "#ffe9a0"}
PAGE_C = {"p": "#f7f4ee", "l": "#ffffff", "d": "#d6d0c6", "f": "#e3ddd2", "r": "#e5534b", "t": "#b9b3a8"}
BEETLE = [                 # a shiny green beetle, heading right: L / s / D = its shell (lit, green, the seam),
    "........a.",          # d = its underside, h = head, E = eye, a = feelers. the last row is its legs,
    "..LLss.a..",          # in two frames
    ".LLssssh..",
    "LssssDshEh",
    "sssDDsshhh",
    ".dddddd...",
    (".k.k.k....", "k.k.k....."),
]
BEETLE_WINGS = ("...WW.WW..", "..W..W....")   # its wings, flapping, when it flies off (a row above it)
BEETLE_C = {"L": "#b8f5a8", "s": "#58c45c", "D": "#2f8a3a", "d": "#23692c", "h": "#2b2b33", "E": "#ffffff",
            "a": "#2b2b33", "k": "#2b2b33", "W": "#e8f6ff"}
NET_C = {"h": "#9a6535", "H": "#6e4426", "r": "#8e939c", "R": "#c9ced8", "w": "#f2efe8"}   # handle, hoop, mesh
SEMI_SMALL = [".y", "..", ".y", "yd"]   # the lost semicolon, lying on the floor
SEMI_BIG = [               # the semicolon up close (in the magnifying glass, and held up): y / Y / d = gold,
    ".yyy..",              # its shine and its shade
    "yYYyd.",
    "yYyyd.",
    ".ydd..",
    "......",
    "......",
    ".yyy..",
    "yYyyd.",
    "yyyyd.",
    ".yydd.",
    "..yd..",
    ".yd...",
]
SEMI_C = {"y": "#f2c14e", "Y": "#fff3b0", "d": "#b8862b", "W": "#ffffff"}
CHECK = ["........gg", ".......ggd", "......ggd.", "gg...ggd..", "dgg.ggd...", ".dgggd....", "..dgd....."]   # it compiles
CHECK_C = {"g": "#5fd16a", "d": "#2f8a3a"}
SHEEP = [".wwwww..", "wwwwwwff", "wwwwwwff", "wwwwww..", ".l..l..."]   # f = face, l = legs
SHEEP_C = {"w": "#f7f4ee", "f": "#3b3b40", "l": "#3b3b40"}
FENCE = ["b.....b", "bbbbbbb", "b.....b", "bbbbbbb", "b.....b"]
FENCE_C = {"b": "#a87445"}
FORTUNE = ["..oooo..", ".oooooo.", "oooddooo", "oo....oo"]   # a fortune cookie
FORTUNE_C = {"o": "#e8b86b", "d": "#c9944a"}
MERGE_IN, MERGE_OUT = [".k.k", "k.k.", ".k.k"], ["k.k.", ".k.k", "k.k."]   # << and >> on the sticky notes
DIGITS = {"4": ["k.k", "k.k", "kkk", "..k", "..k"], "0": ["kkk", "k.k", "k.k", "k.k", "kkk"]}
UNDO = [".k..", "kkkk", ".k.k", "...k", ".kk."]   # ctrl+z
GAG_C = {"note_in": "#ffd166", "note_out": "#8be9fd", "fold": "#e0b94c", "fold2": "#6cc8dc", "ink": "#2b1a14",
         "wood": "#8b5a2b", "metal": "#a7a9b4", "dark": "#3a3a3c", "key": "#8e8e93", "lit": "#ffe08a",
         "code": "#6ff0a0", "glass": "#bfe3ff", "frame": "#d4a64a", "plate": "#f2efe8", "plate2": "#c9c3b5",
         "cake": "#f2c27a", "cake2": "#c98a3e", "butter": "#ffe9a0", "syrup": "#8b4a1c", "paper": "#f7f4ee",
         "red": "#e5534b", "hole": "#1a120c", "soil": "#6b4a2b", "soil2": "#8b6239", "sign": "#c9944a",
         "net": "#f2efe8", "semi": "#ffc23a",
         "brass": "#d9a441", "brass_lit": "#f4d27a", "brass_dark": "#a8741f", "lens": "#bfe3ff", "lens_edge": "#9fd2f2",
         "lens_shine": "#e3f4ff", "grip": "#4a2c18", "grip2": "#6e4426"}   # the magnifying glass
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
MC_WATER = ["#2c55b8", "#3f76e4", "#8fb3f7", "#d6e4ff"]   # minecraft water: deep, base, surface, glint
BUCKET_C = {"h": "#4a4a4a", "r": "#d6d6d6", "w": MC_WATER[1], "e": "#2e2e2e", "l": "#ececec", "i": "#a8a8a8",
            "d": "#6c6c6c"}
CORD_C = ["#f5c518", "#fff2a6", "#cfd2d8", "#6e5206", "#1c1d22", "#4a4d57", "#c9980f", "#8e9199"]   # bungee
                           # cord: yellow, its shine, the metal (clamp, ring, ferrule, clip), its dark edge, the
                           # black sleeve on the thick end and its sheen, the braid marks, the metal's shady side
HARNESS_C = ["#16171b", "#3e414a", "#d9dce2"]   # the bungee harness: black webbing, its sheen, the silver ring
ZIP_C = ["#e6e1d6", "#4a4a4f", "#9a9aa0", "#e5534b"]   # zipline: cable, its dark edge and straps, posts, trolley
GRIP_C = "#a8553a"   # the crease under its hands and feet as they grip the pole
POLE_C = ["#e3b04b", "#fff1c4", "#a8741f", "#7c7f86", "#b83a3a", "#e06464", "#55585e"]   # fireman's pole: brass,
                           # its shine, its shady side, the steel bracket, the red landing mat, its top, steel shade
WEB_C = ["#fafafa", "#aab3c2"]   # spider web: the strand, its grey edge
WOOD_C = ["#c08a4e", "#8a5a2b", "#5e3b1a"]   # the bungee plank: top, underside, the gaps between boards
CHUTE_R, CHUTE_W, STRING_C = "#e5534b", "#f2efe8", "#d9d4c7"
HAT_C, BAND_C, STAR_C, WAND_C = "#6c4ab6", "#f2c14e", "#ffe08a", "#8b5a2b"
HAT_COLOURS = {"#": HAT_C, "l": "#8b6ad6", "d": "#4e3391", "L": "#8461cf", "m": "#fff3b0", "*": STAR_C,
               "y": BAND_C, "o": "#d9a43a", "b": "#7a5a1e"}
SPARK_C = ["#ffe08a", "#8be9fd", "#ff9ad5", "#ffffff"]
DIM, RED, TRACK = "#8e8e93", "#e5534b", "#3a3a3c"
IDLE_C = "#b48cff"   # sleepy lavender: checks are slowed down because nothing is using claude
KEY = "#010203"            # this exact colour becomes see-through (and click-through)
PARK = -32000              # hidden windows are parked way off screen
