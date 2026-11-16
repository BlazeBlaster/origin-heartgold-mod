# ModCmd (script command 62)

Implemented in `tools/mod_code.py` (`build_modcmd`), Thumb code at arm9 `0x02040914` to `0x02040A5C`.
The free cave runs to `0x02040A64`, so 8 bytes are left. Script-command table: `0x020F793C`. Entry 62 (`0x020F7A34`)
already pointed at `0x02040915`, the start of the old dead ScrCmd_062, so only the body is replaced.
Script-side helpers: `give_mon_ex` / `set_party_ability` in `tools/mod_story.py`. `tools/scr.py` registers `C[62] = ModCmd` with seven u16 args.

## Encoding
`u16 62, u16 sub, u16 a0, a1, a2, a3, a4, a5` (16 bytes).
- Each arg is resolved with the normal script var getter (`VarGet` `0x0203FAE8`): values below 0x4000 are literals, and 0x4000+ / 0x8000+ are vars.
- Exceptions: **0xFFFF is always a literal** (it would otherwise be read as an out-of-range special var), and **a5 is never resolved** (it is the result var).
- Returns 0 (script continues), and the command doesn't wait.

### sub 0: GiveMonEx(species, level, nature, flags, ability_slot, result_var)
- `nature`: 0 to 24 is stored in the hack's nature-override field (mon data 0xBE = nature+1). 0xFFFF (or anything ≥ 25) leaves the nature from the personality.
- `flags`: bit0 = shiny (personality generated for the player's trainer ID, same as the GiveMon shiny hook). bit1 = all six IVs 31 (CreateMon `ivs` arg = 31).
- `ability_slot`: 0 or 1 sets mon data 0xBC (the slot bit). 2 sets mon data 0x71 (the hidden-ability flag). After either, the code calls `BoxMon_SetAbility` `0x02071524`. 0xFFFF (or anything > 2) keeps CreateMon's random slot.
- `result_var`: set to 1 if the mon was added to the party, 0 if the party was full. On a full party nothing is created; the mon is **not** sent to the PC.
- Otherwise it follows ScrCmd_GiveMon / GiveMon (`0x02053380`): heap 0xB, met data with Poké Ball (4), the current map's mapsec, encounter type 0x18, no held item, form 0. It then calls `0x0206D4DC(mon, 3)` (three random IVs set to 31, as every GiveMon gift gets, then a stats recalculation) and registers the mon in the Pokédex.
- The ability slot also survives evolution: the ability is recomputed from 0x71 / 0xBC, not from the personality.

### sub 1: SetPartyMonData(slot, field, value, 0, 0, 0)
- Calls SetMonData(field, &value) on party mon `slot`. Does nothing if `slot` ≥ party count.
- `set_party_ability(c, slot, ability)` in mod_story.py emits two of these: field 0x71 (hidden-ability flag) = 1, then field 0x0A (ability) = ability. With the flag set, `BoxMon_SetAbility` (called by form changes etc.) recomputes the personal hidden ability, so only use it for the species' hidden ability (Manaphy's hidden ability is Azure Skin 318).

## How this hack stores abilities (found in CreateBoxMon `0x0206D158` / `BoxMon_SetAbility` `0x02071524`)
- mon data **0xBC**: ability slot 0/1. CreateBoxMon sets it at random (50 %), not from the personality.
- mon data **0x71**: hidden-ability flag. If non-zero, ability = personal hidden ability (personal field 0x1A).
- ability = hidden if 0x71 is set, else ability 2 if 0xBC is set, else ability 1. A missing ability 2 or hidden ability falls back to ability 1. Personal fields 0x18/0x19/0x1A are read per form (field 0x70).
- mon data **0xBE**: nature override (0 = use personality % 25, n = nature n−1). Read by `GetBoxMonNature` `0x0206F1A0`.
- GiveMon (`0x02053380`) args: heap, save, species, level, [form, ability id (0 = default), held item, mapsec, encounter type].
