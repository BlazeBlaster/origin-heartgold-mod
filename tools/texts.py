# All dialogue changes. Each entry: (bank, index, old_substring, new_substring) for edits,
# or appended lines via NEW_LINES.  Line-break codes: \n new line, \f scroll, \r new box.

EDITS = [
    # --- Latios starter ---
    (66, 67, "partner, Pikachu.", "partner, a “Pikachu” that turned out\\fto be Latios."),
    # --- Soul Dew send-off gift ---
    (439, 29, "I found this a couple of days ago while I\\nwas fixing the wiring at home. It should\\fcome in handy on your journey. Here,\\ftake it!",
              "Oh! Is that the Pikachu from Prof. Oak’s\\nlab? I heard it’s really a Latios!\\rI found this orb washed up on the\\nbeach a few days ago. They say it has\\fa bond with the Eon Pokémon.\\fIt should come in handy. Here,\\ftake it!"),
    (439, 30, "a Light Ball", "a Soul Dew"),
    # --- Shiny Charmander story ---
    (314, 16, "been sitting there for ages. I wonder if\\fit’s wild.",
              "been sitting there for ages. Its color\\fis so strange... I wonder if it’s wild."),
    (314, 36, "Charmander looks very weak. Try to\\ncatch it?",
              "This Charmander’s scales are an odd\\ngolden color... It looks very weak.\\fTry to catch it?"),
    (314, 42, "You worthless piece of trash.", "You worthless, off-color trash."),
    (314, 52, "There. This little one will be just fine\\nnow.",
              "There. This little one will be just fine\\nnow.\\rWhat lovely golden scales... I’ve never\\nseen a shiny Charmander before!\\fTake good care of it."),
    (456, 17, "My Charmander is garbage.\\nIt couldn’t do a thing against\\fthe Rock-type Gym Leader.",
              "My Charmander is garbage. Its scales\\nare some freaky gold color, and it\\fcouldn’t do a thing against\\fthe Rock-type Gym Leader."),
    (456, 18, "Charmander seems to like you a lot. It\\nwants to go on a journey with you.",
              "Charmander’s shiny golden scales\\nsparkle. It seems to like you a lot.\\fIt wants to go on a journey with you."),
    # --- Darkrai instead of Bulbasaur (Route 5 raid, Route 5 house, Route 11) ---
    (322, 5, "Bulbasaur: Bul! Ba! Saur!", "Darkrai: Kraaai!"),
    (322, 12, "This Bulbasaur looks decent too.", "This Darkrai looks decent too."),
    (322, 14, "Bulbasaur: Bu...", "Darkrai: Krai..."),
    (322, 18, "Bulbasaur!", "Darkrai!"),
    (322, 21, "Bulbasaur...", "Darkrai..."),
    (322, 35, "Bulbasaur: Bulba-saur!", "Darkrai: Dark-raaai!"),
    (326, 1, "They took Bulbasaur away", "They took Darkrai away"),
    (326, 3, "Bulbasaur", "Darkrai"),
    (326, 5, "Bulbasaur", "Darkrai"),
    (326, 7, "Bulbasaur: Bulba-saur!", "Darkrai: Dark-raaai!"),
    (326, 8, "Bulbasaur", "Darkrai"),
    (326, 10, "Bulbasaur", "Darkrai"),
    (326, 13, "Bulbasaur", "Darkrai"),
    (326, 15, "Bulbasaur", "Darkrai"),
    (326, 16, "Bulbasaur", "Darkrai"),
    (326, 21, "Bulbasaur", "Darkrai"),
    (326, 35, "Bulbasaur", "Darkrai"),
    (339, 84, "Bulbasaur", "Darkrai"),
    (339, 85, "Bulbasaur", "Darkrai"),
]

# Pokémon Ranger quest for the Manaphy Egg. Keys are names used by the scripts.
MIRA = {  # Pallet Town shore, bank 439
    'intro': "Mira: Oh, a Trainer! I’m Mira, a\\nPokémon Ranger on sea patrol.\\rThis morning a Pokémon Egg washed\\nup on this shore. It’s glowing blue...\\rMy Capture Styler says it’s a Manaphy\\nEgg, all the way from the Sea Temple!\\rRangers protect Pokémon, but we don’t\\nraise them in Poké Balls. This Egg\\fneeds a Trainer to hatch it.\\rFirst I need my partner Theo to\\napprove it. He’s on patrol in\\fViridian City.\\rCould you take him my mission report?\\nI can’t leave the Egg alone.\\r{0103:0} took Mira’s mission report.",
    'remind': "Mira: My partner Theo is on patrol in\\nViridian City. Please give him my\\fmission report!",
    'nostarter': "Mira: I’m Mira, a Pokémon Ranger on\\nsea patrol.\\rYou don’t have a Pokémon yet? Prof.\\nOak’s lab is just up the road!",
    'give': "Mira: Theo approved it? Wonderful!\\rThe Egg seems to like you, too. It’s\\nglowing even brighter now.\\rPlease take good care of it.\\nMission clear!",
    'received': "{0103:0} received a Pokémon Egg!",
    'after': "Mira: Keep the Egg in your party as\\nyou travel. It will hatch after you’ve\\fwalked with it for a while.",
    'full': "Mira: Your party is full! Make room\\nfor the Egg, then come back to me.",
    'done': "Mira: How is the Manaphy doing?\\rWherever it goes, the sea will always\\nbe its home.",
}
THEO = {  # Viridian City, bank 445
    'report': "Theo: Hi! I’m Theo, a Pokémon Ranger.\\nWhat’s this? A mission report from\\fMira?\\r...A Manaphy Egg washed up in\\nPallet Town?!\\rManaphy is called the Prince of the\\nSea. Its Egg must have drifted here\\ffrom the Sea Temple.\\rThe Ranger Union would want it raised\\nby a kind Trainer. Mira trusts you,\\fso I do too.\\rMission approved! Please go tell Mira\\nin Pallet Town.",
    'idle': "Theo: I’m Theo, a Pokémon Ranger.\\nI keep watch over the Pokémon around\\fViridian City.",
    'waiting': "Theo: Mira is waiting for you on the\\nPallet Town shore. Hurry back to her!",
    'done': "Theo: So the Egg is with you now.\\nTake good care of it, Trainer!",
}

# Oak's lab disguise reveals (bank 444)
STARTERS = {
    'flicker': "...Huh?\\nThe Pikachu is flickering strangely...",
    'latios_cry': "???: Laaa-tiiiooos!",
    'latios_oak': "Prof. Oak: Wh-what?!\\nThat’s no Pikachu!\\rIt’s Latios, the Eon Pokémon!\\rLatios can bend light with its feathers\\nto change how it looks.\\fIt must have been hiding among my\\fPokémon, disguised as a Pikachu!\\rProf. Oak: ...It doesn’t seem to want\\nto leave your side, {0103:0}.\\rA Pokémon like that chooses its own\\nTrainer. Take good care of it!",
    'bloom': "...Huh?\\nFlowers are blooming around the\\fBulbasaur...",
    'shaymin_cry': "???: Shaaa-miiin!",
    'shaymin_oak': "Prof. Oak: Wh-what?!\\nThat’s no Bulbasaur!\\rIt’s Shaymin, the Gratitude Pokémon!\\rIn its Land Forme it’s a small,\\ngreen thing, just like a Bulbasaur...\\fI never even noticed!\\rThey say Shaymin can purify polluted\\nland and make flowers bloom.\\rProf. Oak: It seems very fond of you,\\n{0103:0}. Take good care of it!",
}
