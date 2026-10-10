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
]
WORK_START = ["*thinking*", "ooh, a new job!", "on it!", "let me cook.", "time for some magic.",
              "summoning tokens...", "wizard hat: on.", "a quest!"]
WORKING = ["*thinking really hard*", "this is quite the job you got for me.",
           "abracadabra... *writes code*", "tokens go brrr.", "hmm, interesting...",
           "casting a big spell here.", "don't look, I'm concentrating.", "almost... maybe...",
           "my wand is getting warm.", "so many tokens. so little time.",
           "reading your files. no judging. ok, a little judging.", "*furious wand waving*",
           "if this works, I'm taking credit."]
WORK_DONE = ["phew! done.", "that was a good one.", "*wipes forehead*", "ta-da!", "magic complete.", "another one bites the dust.",
             "done! that wand needs a nap."]
IDLE_LINES = ["it's quiet... too quiet.", "need anything? I'm just standing here.",
              "I could be useful, you know.", "my wand is getting dusty.", "*taps foot*",
              "zero tokens. a peaceful day.", "anyone? hello?", "I'm on standby. very professional.",
              "I alphabetised your desktop icons. in my head.", "nothing to do. this is fine."]
POKE_LINES = ["hey!", "hehe", "that tickles!", "boop.", "yes?", "I'm awake, I'm awake!", "beep!",
              "do that again. no, wait.", "you rang?", "*giggles in pixels*", "personal space! (just kidding)",
              "that's my good side.", "poke detected. responding with joy.", "ow. (not really)"]
POKE_COUNT = {10: "that's 10 pokes. we're friends now.", 50: "poke #50! I'm keeping count.",
              100: "100 pokes. a true bond.", 500: "500 pokes?! are you okay?"}
DRAG_LINES = ["wheee!", "where are we going?", "put me down! (actually this is fun)", "is this a kidnapping?",
              "my legs are dangling!", "first class, please.", "careful, I'm fragile. ish.", "taxi!"]
WAKE_LINES = ["welcome back!", "oh hi! I wasn't sleeping.", "you're back!",
              "I missed you! (I counted pixels.)", "there you are!"]
RESET_LINES = ["fresh limits! let's go!", "5-hour limit reset. I feel brand new."]
THROW_LINES = ["AAAAAAAAA!", "WHEEEEEEEE—", "I'M FLYIIIING!", "not the face, not the face!", "I CAN SEE MY HOUSE!", "TELL MY TOKENS I LOVE THEM!",
               "this is NOT in my job description!", "I regret nothing!"]
DIZZY_LINES = ["@_@ everything is spinning...", "I see stars. pixel stars.", "who moved the taskbar?",
               "I'm fine. I'm fine. which way is up?", "why are there three of you?",
               "*wobbles*"]
CHUTE_LINES = ["good thing I packed a parachute.", "safety first!", "*floats majestically*",
               "enjoying the view up here.", "gently does it...", "*parachute noises*"]
FALL_LINES = ["geronimo!", "whoops—", "I meant to do that!", "taking the stairs. the fast way.",
              "bye-bye window!", "jumping is just falling with confidence."]
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
            "I've done this before. in my dreams.", "yolo.", "for science!", "this is a terrible idea. here goes!"]
LEAP_OK = ["nailed it.", "did you see that?!", "10/10 landing.", "and the crowd goes wild!", "too easy.",
           "*bows*", "gold medal, please.", "new personal best!", "smooth. like butter.", "I'm basically a ninja."]
LEAP_FAIL = ["that window moved. I swear.", "nobody saw that.", "I meant to do that.", "gravity: 1, me: 0.",
             "ow. my pixels.", "the floor came out of nowhere.", "practice run. it was a practice run.",
             "who put that gap there?", "I underestimated the distance. and overestimated me.",
             "still a 7/10 for style.", "let's never speak of this."]
# things it says now and then, depending on what it's up to
WALK_LINES = ["going for a walk. don't wait up.", "left foot, right foot, left foot...", "on patrol.",
              "where am I going? no idea. very exciting.", "*whistles*", "inspecting the taskbar. looks solid.",
              "exploring! what's over here?", "these legs were made for walking. all four of them.",
              "daily steps: 37.", "just stretching my legs.", "I wonder what's on the other side of the screen.",
              "hey, is that a new icon?"]
HIGH_LINES = ["the view from up here is amazing.", "king of the window!", "I can see my taskbar from here!",
              "this window is comfy. I'm staying.", "don't close this one, ok? I live here now.",
              "it's windy up here. metaphorically.", "I'm on top of things. literally.",
              "*sits on your window* hope you don't mind.", "ooh, high ground."]
DANCE_LINES = ["*dances*", "can't stop, won't stop.", "this is my jam!", "busting a move!", "feel the rhythm!",
               "watch my legs go!", "♪ tokens, tokens, everywhere ♪", "dance break!"]
SLEEP_LINES = ["zzz... five more tokens...", "zzz...", "*snore*", "mmm... rate limits... no...",
               "zzz... I'm a big model now...", "*mumbles about semicolons*", "zzz... the cache is warm..."]
CURIOUS_LINES = ["what does this button do? (I don't have buttons.)", "do windows dream of electric sheep?",
                 "I wonder how many tokens a hug costs.", "what's your favourite colour? mine's orange. obviously.",
                 "is the cursor alive? it moves on its own...", "if I jump high enough, can I reach the tabs?",
                 "why is it called a taskbar if there are no snacks?", "what happens if I walk off the screen? (please don't let me)",
                 "I've been thinking. mostly about rectangles.", "how many pixels tall are you?",
                 "what are we building today?", "does the mouse ever get tired?", "I heard there's a recycle bin. spooky.",
                 "can I have a window of my own one day?", "sometimes I count the windows. you have a lot.",
                 "what's the wifi password? asking for a friend.", "beep boop. I'm not a robot. I'm a crab. sort of."]
ATTENTION_LINES = ["psst... hey. got a minute?", "*polite cough*", "I'm still here, by the way!",
                   "a little poke would be nice. no pressure.", "hello? it's me, your tiny assistant.",
                   "I did a cool jump earlier. you missed it."]
BORED_LINES = ["I counted all the pixels on your taskbar. twice.", "bored. so bored.",
               "should I take up a hobby? knitting, maybe.", "no tokens today? I'll just... stand here.",
               "I've been practising my dance moves.", "is it home time yet?"]
MORNING_LINES = ["good morning! ready when you are.", "morning! let's make today a good one.",
                 "rise and shine! (I've been up for ages)", "good morning! I kept your taskbar warm."]
LATE_LINES = ["it's late... maybe wrap up soon?", "past midnight. the code will still be here tomorrow.",
              "*yawn* aren't you sleepy?", "night owl mode. don't forget to sleep!"]
OOPS_LINES = ["oops, something went wrong in there.", "uh oh. a tool tripped over.",
              "that didn't work. Claude will try again!", "*winces* an error. it happens."]
FULL_LINES = ["100%. that's what I call a hard day's work.", "we used ALL of it. I'm so proud.",
              "the tank is empty. see you after the reset!", "*collapses dramatically*",
              "I'm exhausted. clocking out until the reset.", "not a single token left. legendary."]
MILESTONES = {
    "five_hour": {50: "halfway through your 5-hour limit!", 75: "75% of the 5-hour limit used. pace yourself!",
                  90: "90%! almost out of 5-hour juice.",
                  100: "100% of the 5-hour limit. what a shift. time for a break."},
    "seven_day": {50: "halfway through the weekly limit.", 75: "75% of the weekly limit is gone.",
                  90: "90% of the week used. careful!",
                  100: "the whole week's limit. legendary effort."},
}
