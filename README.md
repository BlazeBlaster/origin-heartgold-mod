# Origin HeartGold mod

A fan mod built on top of **Origin HeartGold v4.0.3 EN (rc8)**, a Pokémon HeartGold ROM hack. It adds new story events, disguised legendary starters, a baby Shadow Lugia with its own custom ability, and tougher trainers.

No ROM is included. You need your own copy of the game.

## Download and patch

Get the patches from the [Releases](../../releases) page. There are two; pick the one that matches the ROM you have.

| Patch | Apply it to | Base SHA-1 |
|---|---|---|
| `OHG_Lugiling_from_HeartGold_USA.xdelta` | Clean **Pokémon - HeartGold Version (USA)** | `4fcded0e2713dc03929845de631d0932ea2b5a37` |
| `OHG_Lugiling_from_OriginHG_rc8.xdelta` | **Origin HeartGold v4.0.3 EN (rc8)**, already patched | `a54a647599d59ed0060dfc4375c289d6e041318a` |

The patched ROM's SHA-1 is `51ddba2e9a3bfbba577fa2f0ebbf3af9f7276758`.

To apply a patch, use an xdelta tool such as [xdelta3](https://github.com/jmacd/xdelta-gpl/releases), Delta Patcher, or Rom Patcher JS:

```
xdelta3 -d -s "Pokemon - HeartGold Version (USA).nds" OHG_Lugiling_from_HeartGold_USA.xdelta ohg_mod.nds
```

Start a new game; saves from other versions are not supported.

## What's new

**Starters**
- Oak's "Pikachu" is really a **Latios** bending light, and his "Bulbasaur" is really a **Shaymin**. Both reveal themselves with an overworld flicker, and people around Kanto comment on them.
- The Charmander line gets a new ability, **Solar Flare**: it summons sun on entry and boosts Sp. Atk in sun, with no HP drain.

**Story events**
- An abandoned shiny Pokémon on Route 2 / Pewter City, on every starter path.
- **The Shadow of Route 5**: a Darkrai questline with a nightmare-eating Hypno and a young Riolu. Riolu and Lucario get a new ability, **Aura Guardian** (powers up aura and pulse moves).
- **The Sea Temple thread**: a Manaphy story from Cerulean to Route 25, where Manaphy calms a frightened baby Shadow Lugia and gains a new ability, **Azure Skin**.
- A Gracidea in Ilex Forest (Shaymin path), a hermit who teaches Nasty Plot, a Reshiram payoff and Blaine's Heat Rock (Charmander path), and the Route 9 Lum Berry restored on the non-Pikachu paths.

**Lugiling and Shadow Lugia**
- **Lugiling** is a new Pokémon: a baby Shadow Lugia (Psychic/Dark, 300 base stat total). It evolves into **Shadow Lugia** at Lv 40.
- Shadow Lugia is an offensive Lugia: 106 HP / 90 Atk / 100 Def / 140 Sp. Atk / 124 Sp. Def / 120 Spe.
- Both have a new ability, **Dark Tide**: it works like Dark Aura and also gives their own Water moves a 1.5x boost. The hidden ability is Shadow Shield.
- Aeroblast is held back for a future quest.
- Lugiling has its own battle sprites and a small following-Pokémon sprite, made from AI-generated pixel art.

**Difficulty**
- All trainers have max IVs, natures that fit their sets, and smarter AI. Levels are unchanged.
- Use the hack's own DIFFICULTY menu for the level cap and Exp. Share options.

## Known gaps

These were checked only in the code, not in game:
- Lugiling's evolution at Lv 40.
- Releasing Reshiram through Mr. Fuji when your party is full.
- Some townsfolk comment lines.

Lugiling uses Lugia's cry.

## Building from source

The `tools/` folder holds the Python build scripts that produce the patch. `tools/patch.py` runs four modules in order:
- `mod_code`: new script command and battle abilities
- `mod_species`: Shadow Lugia, Lugiling, ability and learnset edits
- `mod_story`: story events
- `mod_trainers`: trainer IVs, natures and AI

```
PYTHONIOENCODING=utf-8 python tools/patch.py rom/ohg.nds out/ohg_mod.nds
```

Requirements:
- Python 3 with Pillow.
- `rom/ohg.nds`: your own Origin HeartGold v4.0.3 EN (rc8) ROM. Not included.
- `ref/charmap.txt`: the text character map from the [pret/pokeheartgold](https://github.com/pret/pokeheartgold) decompilation. Not included.
- `ref/ohgrepo/script_cmds.json`: the script command list from the Origin HeartGold tools. Not included.

## Credits

- Origin HeartGold, by its original authors. This mod would not exist without their hack.
- Pokémon is © Nintendo / Creatures Inc. / GAME FREAK inc. This is a non-commercial fan project.
