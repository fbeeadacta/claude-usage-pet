# everything the mascot can say.


# ---- things it says ----
QUOTES = [
    "you got this!", "one step at a time.", "drink some water! I'll wait.",
    "have you tried turning it off and on again?", "I believe in you. mostly.",
    "fun fact: I'm made entirely of rectangles.", "bugs are just surprise features.",
    "stretch break? your back will thank you.", "I don't have hands, but high five anyway.",
    "ctrl+s is my love language.", "you're doing great, honestly.",
    "it's not a bug, it's a plot twist.", "posture check!", "small progress is still progress.",
    "blink twice if you need a break.", "I like it here on the taskbar.",
    "if it works, don't touch it. (touch it a little)", "today's forecast: 100% chance of shipping.",
    "I'd make you coffee but I'm 40 pixels tall.", "remember to eat something!",
    "you look like someone who writes great commit messages.", "fun fact: I have never once read the docs.",
    "tabs or spaces? careful, this is a test.", "every bug you fix makes me 1% prouder.",
    "I'm not saying you're a genius, but I'm not NOT saying it.", "keep going. I'm cheering quietly.",
    "your code is like me: small, orange and full of surprises.", "deep breath. you've got this.",

    'progress, not perfection.',
    "you're one commit away from greatness.",
    'take a break. the bugs will wait. they always do.',
    "you're doing better than your error messages say.",
    'be the semicolon you wish to see in the world.',
    'done is better than perfect. perfect is also nice though.',
    'trust the process. unless the process is a race condition.',
    'hydrate or diedrate!',
    'your future self will thank you for that comment.',
    'it works? ship it! (ok, test it first.)',
    'small steps. big dreams. medium-sized snacks.',
    'one bug at a time.',
    "you've got this. and if you don't, Claude's got this.",
    'a clean desk is nice. a clean diff is nicer.',
    'rest is productive too.',
    'even the best wizards misspell a spell sometimes.',
    'the best time to write a test was yesterday. the second best is now.',
    'every expert was once a beginner who kept going.',
    'you are the main character of this codebase.',
    "the code doesn't know you're tired. but I do. take five.",
]
WORK_START = ["*thinking*", "ooh, a new job!", "on it!", "let me cook.", "time for some magic.",
              "summoning tokens...", "wizard hat: on.", "a quest!",
    'the wizard is in.',
    "rolling up my sleeves. I don't have sleeves.",
    "spellbook: open. let's go!",
    'new task! *cracks knuckles*',
    'magic time!',
    "alright, let's do some wizarding.",
    "Claude's on it. I'm on Claude.",
    'abra-code-abra!',
]
WORKING = ["*thinking really hard*", "this is quite the job you got for me.",
           "abracadabra... *writes code*", "tokens go brrr.", "hmm, interesting...",
           "casting a big spell here.", "don't look, I'm concentrating.", "almost... maybe...",
           "my wand is getting warm.", "so many tokens. so little time.",
           "reading your files. no judging. ok, a little judging.", "*furious wand waving*",
           "if this works, I'm taking credit.",
    'the magic is flowing.',
    'so many tokens. so shiny.',
    '*concentrates in purple*',
    'this spell has a lot of syllables.',
    'almost there. probably. maybe.',
    'my hat is buzzing.',
    "keep going, Claude! you've got this!",
    "hold on, I'm channeling.",
    'brewing something good.',
    'if I stop waving the wand, does it stop working? not risking it.',
]
WORK_DONE = ["phew! done.", "that was a good one.", "*wipes forehead*", "ta-da!", "magic complete.", "another one bites the dust.",
             "done! that wand needs a nap.",
    'mischief managed.',
    'and... done! *bows*',
    'the spell is cast.',
    "job's done! hat off. (not really.)",
    'another quest completed!',
    'that went well. I think. it went well.',
    'phew. magic is tiring.',
    'finished! did you see that? that was magic.',
]
IDLE_LINES = ["it's quiet... too quiet.", "need anything? I'm just standing here.",
              "I could be useful, you know.", "my wand is getting dusty.", "*taps foot*",
              "zero tokens. a peaceful day.", "anyone? hello?", "I'm on standby. very professional.",
              "I alphabetised your desktop icons. in my head.", "nothing to do. this is fine.",
    'no tokens, no problems.',
    "I'm conserving energy. and tokens.",
    'standing by. very still. very alert.',
    'the wand is resting. so am I.',
    'peaceful. suspiciously peaceful.',
    'quiet day. I like quiet days. I think.',
]
POKE_LINES = ["hey!", "hehe", "that tickles!", "boop.", "yes?", "I'm awake, I'm awake!", "beep!",
              "do that again. no, wait.", "you rang?", "*giggles in pixels*", "personal space! (just kidding)",
              "that's my good side.", "poke detected. responding with joy.", "ow. (not really)",
    'boop received. boop returned.',
    'you found my tickle pixel!',
    "hey, that's my ticklish block!",
    '*happy rectangle noises*',
    'achievement unlocked: poked the mascot.',
    'careful, I bruise like a peach. a pixel peach.',
    "do it again and I'll... smile more, probably.",
    'poke me harder, I dare you. no wait, gently.',
    "that's not a button! (it's a little bit a button.)",
    'hello to you too!',
]
POKE_COUNT = {10: "that's 10 pokes. we're friends now.", 50: "poke #50! I'm keeping count.",
              100: "100 pokes. a true bond.", 500: "500 pokes?! are you okay?"}
DRAG_LINES = ["wheee!", "where are we going?", "put me down! (actually this is fun)", "is this a kidnapping?",
              "my legs are dangling!", "first class, please.", "careful, I'm fragile. ish.", "taxi!",
    'up, up and away!',
    'I can fly! (with assistance.)',
    'this is the best ride ever.',
    "I hope you know where you're going.",
    'please keep your hands and feet inside the cursor.',
    'my legs are doing the swimming thing.',
    'wheeeeeee... where to, boss?',
    'airborne mascot! everybody look!',
]
WAKE_LINES = ["welcome back!", "oh hi! I wasn't sleeping.", "you're back!",
              "I missed you! (I counted pixels.)", "there you are!",
    "you're back! the taskbar was so quiet.",
    'hello again! I guarded your desktop.',
    'welcome back! nothing happened. I checked twice.',
    'oh! hi! I was definitely awake.',
    'there you are! I was about to send a search party.',
    '*stretches* ready when you are!',
]
RESET_LINES = ["fresh limits! let's go!", "5-hour limit reset. I feel brand new."]
THROW_LINES = ["AAAAAAAAA!", "WHEEEEEEEE—", "I'M FLYIIIING!", "not the face, not the face!", "I CAN SEE MY HOUSE!", "TELL MY TOKENS I LOVE THEM!",
               "this is NOT in my job description!", "I regret nothing!",
    'I REGRET EVERYTHING!',
    'TO INFINITY AND— oh no.',
    'TELL THE TASKBAR I LOVED IT!',
    "I DIDN'T SIGN UP FOR THIS!",
    'YEET!',
    'WHY ARE YOU LIKE THIS?!',
    'MY PIXELS ARE SCATTERING!',
    'WORTH IT!',
]
DIZZY_LINES = ["@_@ everything is spinning...", "I see stars. pixel stars.", "who moved the taskbar?",
               "I'm fine. I'm fine. which way is up?", "why are there three of you?",
               "*wobbles*"]
CHUTE_LINES = ["good thing I packed a parachute.", "safety first!", "*floats majestically*",
               "enjoying the view up here.", "gently does it...", "*parachute noises*"]
FALL_LINES = ["geronimo!", "whoops—", "I meant to do that!", "taking the stairs. the fast way.",
              "bye-bye window!", "jumping is just falling with confidence.",
    'gravity, my old friend.',
    'this was not in the plan.',
    'falling with style!',
    'see you at the bottom!',
    'whoopsie daisy!',
]
DIVE_LINES = ["leap of faith!", "*eagle screech*", "I saw this in a game once.", "there'd better be hay down there.",
              "trust me, I'm a professional.", "swan dive!", "no stairs? no problem.", "see you at the bottom!"]
HAY_LINES = ["hay! right where I left it.", "*pfft* straw in my mouth.", "perfectly safe. totally planned.",
             "who leaves hay lying around? thank you, whoever you are.", "nailed it. itchy, but nailed it.",
             "10/10. would dive again.", "*emerges majestically*"]
SLAP_LINES = ["*splat*", "WALL.", "ow, my face.", "that window is harder than it looks.", "I'm ok!",
              "who put a wall there?", "*slides down slowly*", "nobody saw that. right?"]
SQUISH_LINES = ["hey! I was standing there!", "no room! going down!", "squished! see you on the taskbar.",
                "ok ok, I'll move. downstairs.", "rude. I had a lease on that spot.", "evicted!"]
# jumping to another window: before, after a good landing, after a bad one
LEAP_TRY = ["I can make that.", "hold my tokens.", "parkour!", "trust the process.", "3... 2... 1...",
            "ok. big jump. no big deal.", "calculating trajectory... roughly.", "watch this!",
            "I've done this before. in my dreams.", "yolo.", "for science!", "this is a terrible idea. here goes!",
    'watch and learn.',
    "this one's for the highlight reel.",
    'here goes nothing!',
    'I am a cat. I am a cat.',
    'physics, please be nice.',
]
LEAP_OK = ["nailed it.", "did you see that?!", "10/10 landing.", "and the crowd goes wild!", "too easy.",
           "*bows*", "gold medal, please.", "new personal best!", "smooth. like butter.", "I'm basically a ninja.",
    'stuck the landing!',
    'the judges give it a 10.',
    'did you film that?',
    'parkour master!',
    'nothing to it.',
]
LEAP_FAIL = ["that window moved. I swear.", "nobody saw that.", "I meant to do that.", "gravity: 1, me: 0.",
             "ow. my pixels.", "the floor came out of nowhere.", "practice run. it was a practice run.",
             "who put that gap there?", "I underestimated the distance. and overestimated me.",
             "still a 7/10 for style.", "let's never speak of this.",
    'I was aiming for the floor.',
    'that window dodged me.',
    'tactical fall.',
    'the wind took me. inside your house.',
    'gravity cheated.',
]
# things it says now and then, depending on what it's up to
WALK_LINES = ["going for a walk. don't wait up.", "left foot, right foot, left foot...", "on patrol.",
              "where am I going? no idea. very exciting.", "*whistles*", "inspecting the taskbar. looks solid.",
              "exploring! what's over here?", "these legs were made for walking. all four of them.",
              "daily steps: 37.", "just stretching my legs.", "I wonder what's on the other side of the screen.",
              "hey, is that a new icon?",
    "left, right, left... I'm basically a marathon runner now.",
    'I walk at exactly 28 pixels a second. I checked.',
    'every step is a tiny adventure.',
    'if I walk far enough, do I reach the internet?',
    'one small step for a crab, one giant leap for crab-kind.',
    'taskbar tour, stop one: the start button. very round.',
    'walking off my last token.',
    "I don't know where I'm going, but I'm making great time.",
    'this is my cardio for the week.',
    '*hums the walking song*',
    'patrolling for bugs. none here. suspicious.',
    'my legs are 4 pixels long and I use every single one.',
    'do the taskbar icons ever wave back?',
    "I'm a free-range mascot.",
    'is this the way to the recycle bin? asking for a friend.',
    'new personal best: three steps without tripping.',
    '*pretends to be busy*',
    "if anyone asks, I'm doing important research.",
    "I've walked this taskbar a hundred times. still beautiful.",
    'left foot... right foot... wait, how many feet do I have?',
    'going on a quest for the perfect standing spot.',
    'some say I walk too much. those people are the screen edges.',
    'strolling. sauntering. perambulating, even.',
    'I wonder if the mouse pointer wants to race.',
    "I'm not lost. I'm exploring with confidence.",
    "exercise is important. that's why I do it in tiny amounts.",
    "the floor is lava. just kidding. it's a taskbar.",
    'brb, inspecting that icon over there.',
    'a little walk clears the cache. my cache. I have a small cache.',
    "tip tap tip tap. that's my footsteps. you can't hear them. trust me.",
]
HIGH_LINES = ["the view from up here is amazing.", "king of the window!", "I can see my taskbar from here!",
              "this window is comfy. I'm staying.", "don't close this one, ok? I live here now.",
              "it's windy up here. metaphorically.", "I'm on top of things. literally.",
              "*sits on your window* hope you don't mind.", "ooh, high ground.",
    "I'm the tallest I've ever been.",
    'hello down there!',
    "don't minimise this window, ok? please?",
    "I've climbed a window. next: the moon.",
    "the air is thinner up here. it's still air. I think.",
    "I'm on top of the world. well, the window.",
    'is this what being a title bar feels like?',
    'I can see your whole taskbar from here. lovely.',
]
DANCE_LINES = ["*dances*", "can't stop, won't stop.", "this is my jam!", "busting a move!", "feel the rhythm!",
               "watch my legs go!", "♪ tokens, tokens, everywhere ♪", "dance break!",
    '*moonwalks badly*',
    "the robot! I'm a natural.",
    'these moves are 8-bit and proud.',
    "dance like nobody's watching. you're watching. still dancing.",
    'boogie mode activated.',
    '♪ do the crab, do the crab ♪',
    'my dance teacher was a screensaver.',
    '*funky pixel shuffle*',
]
SLEEP_LINES = ["zzz... five more tokens...", "zzz...", "*snore*", "mmm... rate limits... no...",
               "zzz... I'm a big model now...", "*mumbles about semicolons*", "zzz... the cache is warm...",
    'zzz... no... not the semicolons...',
    '*sleep-walks one pixel*',
    'zzz... five more minutes, Claude...',
    "zzz... I'm a big wizard now...",
    'mmm... crunchy tokens...',
    'zzz... git push... zzz...',
    '*snores in 8-bit*',
    'zzz... who left the cache on...',
]
CURIOUS_LINES = ["what does this button do? (I don't have buttons.)", "do windows dream of electric sheep?",
                 "I wonder how many tokens a hug costs.", "what's your favourite colour? mine's orange. obviously.",
                 "is the cursor alive? it moves on its own...", "if I jump high enough, can I reach the tabs?",
                 "why is it called a taskbar if there are no snacks?", "what happens if I walk off the screen? (please don't let me)",
                 "I've been thinking. mostly about rectangles.", "how many pixels tall are you?",
                 "what are we building today?", "does the mouse ever get tired?", "I heard there's a recycle bin. spooky.",
                 "can I have a window of my own one day?", "sometimes I count the windows. you have a lot.",
                 "what's the wifi password? asking for a friend.", "beep boop. I'm not a robot. I'm a crab. sort of.",
    "what's in all those folders? actually, don't tell me. privacy.",
    'why is there a key just for Scroll Lock?',
    'if a token falls in a forest and no one counts it, does it count?',
    "what does the cursor do when you're asleep?",
    "does the wallpaper know I'm standing on it?",
    "why is the save icon a floppy disk? I've never seen one.",
    'how many tabs do you have open? be honest.',
    'is Ctrl+Z time travel? asking scientifically.',
    "what's your favourite thing you've ever built?",
    'if I learned to code, would I code a smaller me?',
    'what does the start button start? everything?',
    'do monitors get lonely when you switch them off?',
    'where do deleted files go? a farm upstate?',
    'does Claude ever get tired of being helpful? asking for me.',
    'if two of me met, would we high-five?',
    'what would you name a pet rock? I vote Pebble McTokens.',
    'are tokens crunchy?',
    "is it weird that I've never seen my own back?",
    "what's the biggest number you've ever counted to?",
    'if I stand still long enough, do I become an icon?',
]
ATTENTION_LINES = ["psst... hey. got a minute?", "*polite cough*", "I'm still here, by the way!",
                   "a little poke would be nice. no pressure.", "hello? it's me, your tiny assistant.",
                   "I did a cool jump earlier. you missed it.",
    'hey. hey. hey. hi.',
    "I've been practising my wave. *waves*",
    "is it poke o'clock yet?",
    'you can hover over me, you know. I have stats.',
    '*stares at you lovingly*',
    "I'm right here! the little orange guy!",
]
BORED_LINES = ["I counted all the pixels on your taskbar. twice.", "bored. so bored.",
               "should I take up a hobby? knitting, maybe.", "no tokens today? I'll just... stand here.",
               "I've been practising my dance moves.", "is it home time yet?",
    'I tried counting to infinity. got bored at 47.',
    "I've named every pixel on the taskbar. this one's Gary.",
    "maybe I'll learn to juggle. I have no hands. challenge accepted.",
    '*sighs in rectangles*',
    "I'd read a book, but they're all in the spell tome and I only get that when Claude reads.",
    "if boredom were tokens, I'd be over my limit.",
    'playing I spy. I spy... something taskbar-coloured.',
    'anyone want to play fetch? (right-click me!)',
]
MORNING_LINES = ["good morning! ready when you are.", "morning! let's make today a good one.",
                 "rise and shine! (I've been up for ages)", "good morning! I kept your taskbar warm.",
    "good morning! the taskbar's been waiting for you.",
    'morning! I did my stretches.',
    "good morning! today's forecast: tokens, with a chance of magic.",
    'morning! coffee first, then code.',
]
LATE_LINES = ["it's late... maybe wrap up soon?", "past midnight. the code will still be here tomorrow.",
              "*yawn* aren't you sleepy?", "night owl mode. don't forget to sleep!",
    "the owls are proud of you. I'm a bit worried.",
    "it's very late. even my pixels are yawning.",
    'bedtime soon? the code will keep.',
    "night shift! I'll keep watch. but you should sleep.",
]
OOPS_LINES = ["oops, something went wrong in there.", "uh oh. a tool tripped over.",
              "that didn't work. Claude will try again!", "*winces* an error. it happens."]
FULL_LINES = ["100%. that's what I call a hard day's work.", "we used ALL of it. I'm so proud.",
              "the tank is empty. see you after the reset!", "*collapses dramatically*",
              "all used up. I'll keep you company till the reset.", "not a single token left. legendary."]
# early pace warning ({when} = when it runs out at this pace, {reset} = when the limit resets)
PACE_LINES = {
    "five_hour": ["at this pace you'll hit the 5-hour limit around {when}. it resets {reset}. maybe pace yourself?",
                  "heads up: we're burning fast. 100% around {when}, reset at {reset}.",
                  "this pace runs out around {when}, before the {reset} reset. just saying!"],
    "seven_day": ["at this pace the weekly limit runs out {when}. it resets {reset}. careful!",
                  "heads up: the week's limit is going fast. empty by {when}, reset {reset}."],
}
# when it's called over (shortcut, tray icon, starting the pet again)
COME_LINES = ["coming!", "on my way!", "you called?", "here I am!", "*sprints*", "reporting for duty!"]
DROP_IN_LINES = ["incoming!", "special delivery!", "did someone call?", "dropping in!"]
# quiet mode
QUIET_LINES = ["shh. I'll be quiet.", "*zips mouth*", "quiet mode. I'll just wave."]
# first start: a short tour, one line after another
TOUR_LINES = ["hi! I'm your little Claude usage buddy.",
              "the bubble over my head shows how much of your Claude plan you've used.",
              "hover over me for the details: reset times, a chart and Claude Code stats.",
              "click me to say hi. you can drag me around too, or even throw me!",
              "right-click me for settings. that's the tour. nice to meet you!"]
# claude code session wrap-ups. {what} = "34 min on Token Tracker, 58 messages, 2.1M tokens"
RECAP_LINES = ["session wrap-up: {what}. nice work!", "that session's done: {what}.",
               "and that's a wrap: {what}.", "session report: {what}. *takes notes*"]
AWAY_RECAP = "while you were away, {n} sessions wrapped up: {tokens} tokens in all. hover me for the list."
# reading files: the wizard opens its spell tome
TOME_LINES = ["*flips through the spell tome*", "let me look that up.", "reading, reading...",
              "ah, chapter 3: your code.", "hmm, says here... interesting.", "studying the ancient scrolls. your files."]
# seasons and special days
SEASON_LINES = {
    "halloween": ["happy halloween! boo!", "trick or treat? I'll take tokens.", "spooky season! *wobbles a pumpkin*"],
    "christmas": ["merry christmas! ho ho ho.", "I'm on the nice list. probably.", "festive mode: on."],
    "newyear": ["happy new year! new year, new tokens.", "let's make this year a good one!"],
    "birthday": ["it's my birthday! I'm made of rectangles and I'm one year older.", "party hat on! it's my birthday!"],
    "valentine": ["happy valentine's day! you're my favourite user.", "I ♥ you. and your tokens."],
}
BEDTIME_LINES = ["*puts on nightcap* bedtime mode.", "I found a candle. it's getting late!",
                 "pajamas on. you should think about bed too.", "*lights a candle* night shift begins."]
# rare events
SHINY_LINES = ["whoa. I feel... shiny today.", "is it me, or am I sparkly?"]
UFO_LINES = ["uh oh.", "wait, what's that light?", "hey! put me down!"]
UFO_BACK_LINES = ["they gave me back. said I'm 'too orange'.", "I've seen things. rectangular things.",
                  "the aliens say hi.", "...did that just happen?"]
CAT_LINES = ["a cat!", "kitty!", "here kitty kitty!", "who's a good... cat."]
# fetch
FETCH_START = ["fetch! fetch!", "ooh, a ball!", "I'll get it!", "*zoomies*"]
FETCH_GOT = ["got it!", "mine!", "*proudly holds the ball*"]
FETCH_BACK = ["again! again!", "here you go! throw it again?", "that was fun!", "best game ever."]
# breaking the fourth wall (mixed into small talk)
FOURTH_WALL = [
    "hi. yes, you. the one reading this bubble.", "I know you can see me. I can't see you. that's weird, right?",
    "I live in a Python script. it's cozy.", "somewhere, someone wrote this line hoping you'd smile. did it work?",
    "I'm technically just rectangles that someone told to be cute.",
    "don't tell anyone, but I'm redrawn about 60 times a second when I move.",
    "if you quit me, do I dream? (please don't.)", "my whole personality is in a file called lines.py.",
    "the writers gave me a lot of lines. this is one of them.", "this bubble is 190 pixels wide. I'm keeping it short.",
    "breaking the fourth wall: hello! it's very thin.", "I'm not allowed to read your files. Claude is. I just wear the hat.",
    "you've been looking at the screen a while. so have I. I don't have a choice.",
    "according to my code, now is a good time to say something. so: something.",
    "you can turn my chatter down in settings. you won't, though. right?", "I have a diary. it's mostly about you poking me.",
    "I was made with zero pip installs. I'm very proud of that.", "if you're reading this on GitHub: hi! take me home!",
    "every time you hover over me, a little panel is born.", "they said I'd be a usage tracker. nobody said I'd have to dance.",
    "some mascots get a whole screen. I get a taskbar. I love it.", "this line was picked at random. lucky you.",
    "I'm the only crab-shaped thing on your computer. probably.", "I'm not real. but my enthusiasm is.",
    "the developer tested me by throwing me. a lot.", "I know about the right-click menu. do you?",
]
# when the pet starts (not the very first time: that's the tour). by time of day, and any time.
WELCOME_LINES = {
    "morning": ["good morning! I kept the taskbar warm for you.", "morning! the pixels are fresh today.",
                "rise and shine! I'm wide awake. mostly."],
    "day": ["hey, welcome back!", "you're back! I was just standing here. professionally."],
    "evening": ["evening! one more session before dinner?", "good evening! the night shift begins."],
    "late": ["back at this hour? I respect it. and I'm a little worried.", "a late-night session? I'll get the wizard hat."],
    "any": ["welcome back! I missed you. (I counted pixels.)", "oh hi! good to see you again.",
            "*waves enthusiastically* welcome back!", "reboot complete. mascot online. hello!",
            "hello again! did you miss me? I missed me.", "and we're back! ready when you are."],
}
# then about the last claude code session's project. {project}, and {days} for old ones.
CONTINUE_LINES = {
    "warm": ["shall we keep going on {project}? it's still warm.", "back to {project}? I saved your spot. in spirit.",
             "{project} again? let's finish what we started!"],
    "recent": ["shall we continue working on {project} today?", "{project} misses you. probably.",
               "want to pick up {project} where we left off?", "how about a bit more {project} today?"],
    "old": ["it's been {days} days since {project}. shall we dust it off?", "remember {project}? {days} days ago. good times.",
            "{project} has been waiting {days} days. just saying."],
}
# claude code's tools, as wizard jobs (said now and then when one starts)
JOB_LINES = {
    "write": ["*quill scribbling intensifies*", "writing it down. in my fanciest handwriting.", "edits, edits everywhere.",
              "the quill knows what to write. I just hold the magic."],
    "bash": ["running commands. the runes are falling!", "casting terminal spells.", "the command line speaks in runes today.",
             "sudo make me a sandwich. just kidding. mostly."],
    "web": ["consulting the crystal ball... I mean, the internet.", "wingardium... webiosa!",
            "the crystal ball shows... cats. mostly cats.", "looking it up in the great crystal ball."],
    "agent": ["summoning a helper!", "rise, little me!", "I've called for backup.", "a tiny apprentice appears!"],
    "plan": ["making a plan. with sticky notes. lots of sticky notes.", "to-do list: levitate it. done.",
             "planning things out. magically."],
    "ask": ["Claude has a question for you!", "psst, Claude's waiting for your answer.", "question time! over to you."],
    "mcp": ["drawing a rune circle. an add-on is helping.", "calling on outside magic.", "the circle glows. help from beyond!"],
    "think": ["*thinking very hard*", "hmm... let me think.", "the gears are turning. magically."],
    "compact": ["tidying up the conversation. squish!", "shrinking the scroll so it fits.", "making room for more thoughts."],
}
# idle activities
SWEEP_LINES = ["*sweep sweep*", "tidy taskbar, tidy mind.", "so many crumbs. who's eating at the computer?",
               "dusting the taskbar. nobody else does it.", "where does all this dust come from?",
               "a little spring cleaning. in any season."]
SWEEP_DONE = ["*sweeps it under the taskbar*", "there. spotless. don't look under the taskbar.", "all clean! mostly.",
              "found a stray semicolon in there. I kept it."]
PAINT_LINES = ["art time!", "I feel inspired.", "*sets up the easel*", "painting something. no peeking.",
               "hold still, I'm painting you. kidding."]
PAINT_DONE = {
    "flower": ["I call it: 'Flower'. deep, right?", "a flower for you. this one never wilts."],
    "heart": ["it's a heart. for you. don't make it weird.", "I call it: 'Love, in 12 pixels'."],
    "sun": ["the sun, but cooler. it has sunglasses.", "I call it: 'Mr Sunshine'."],
    "mushroom": ["a mushroom. the friendly kind, I think.", "I call it: 'Fun Guy'."],
    "cat": ["portrait of the cat. she wouldn't sit still.", "I call it: 'Cat, Judging You'."],
    "fish": ["a fish. am I hungry? maybe.", "I call it: 'Still Life With Fish'."],
    "house": ["my dream house. it has a door AND a window.", "I call it: 'Home Sweet Taskbar'."],
    "me": ["self-portrait. I nailed the eyes.", "it's me! the resemblance is uncanny."],
    "rainbow": ["a rainbow! I ran out of blue.", "I call it: 'After the Rain'."],
}
FISH_LINES = ["*cuts a hole in the taskbar* fishing time.", "taskbar fishing! the fish here are very rare.",
              "I bet there are fish under the taskbar.", "gone fishing. back in a bit.", "shh. you'll scare the fish."]
CATCH_LINES = {
    "fish": ["got one! I'll let it go.", "a fish! hello, fish. bye, fish.", "look how big! ...ish."],
    "gold": ["a GOLDEN fish!! make a wish!", "a golden one! that's the rarest catch there is."],
    "boot": ["...a boot. again.", "a boot! whose boot is this?", "one boot. still waiting for the other one."],
    "crab": ["a little crab! hi, cousin.", "a crab! it looks a bit like me."],
    "bug": ["I caught a bug! good thing it wasn't in your code.", "a bug! I'll tell Claude about it."],
    "sock": ["one sock. so this is where they go.", "a sock! the other one's down there somewhere."],
}
BALLOON_LINES = ["*blows up a balloon*", "balloon time!", "a party for one!", "watch how big I can make it."]
POP_LINES = ["pop!", "bye, balloon.", "that one had a weak spot.", "ok. one more.",
             "balloons don't last. fun does."]
PLANE_LINES = ["*folds a paper plane*", "flight test number... I lost count.", "this one's going to fly so far.",
               "paper plane! stand clear!"]
PLANE_LAND = ["nice landing!", "and it sticks the landing!", "did you see that?", "the pilot is fine. there was no pilot."]
PLANE_FAR = ["whoa, all the way over there!", "new record! probably.", "that went further than I've ever walked."]
PLANE_FLOP = ["...it was a test flight.", "aerodynamics is hard.", "plop.", "I meant to do that."]
MILESTONES = {
    "five_hour": {50: "halfway through your 5-hour limit!", 75: "75% of the 5-hour limit used. pace yourself!",
                  90: "90%! almost out of 5-hour juice.",
                  100: "100% of the 5-hour limit. what a shift. time for a break."},
    "seven_day": {50: "halfway through the weekly limit.", 75: "75% of the weekly limit is gone.",
                  90: "90% of the week used. careful!",
                  100: "the whole week's limit. legendary effort."},
}
