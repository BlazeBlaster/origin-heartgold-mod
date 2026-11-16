# Story sub-module brief (shared by all story agents)

Project: personal mod of Origin HeartGold v4.0.3 EN (Pokémon HeartGold hack). Root: the repository folder. Python, set PYTHONIOENCODING=utf-8. Never modify rom/ohg.nds. Full plan: CHANGES.md (read it; "Revisions" at the bottom override earlier entries).

## Your file
You write ONE module `tools/story_<name>.py` with `apply(ctx)`. It is called by tools/mod_story.py after the base story edits. Do not edit other files except where your task explicitly allows. Other agents work concurrently on mod_code.py (ARM code), mod_species.py (data) and the other story_*.py modules.

Test: `STORY_ONLY=story_<name> python tools/patch.py rom/ohg.nds out/test_<name>.nds mod_story` then check with `python tools/vdump.py out/test_<name>.nds <script> <bank> [from] [to]` (disassembles a script from the built ROM with its texts).

## Tools / data
- rom/msgs.txt: every text line as `bank.index<TAB>text` (escapes: \n newline, \r new box, \f scroll, {0103:0} player name, {0100:N} buffered species). Line width ~38 chars.
- rom/scrmap.json: script file -> [[text bank, zone, area, map]]. `python tools/sdump.py <script> <bank>` dumps an original script with texts.
- tools/scr.py: command table C {opcode: [name, arg sizes]} (from ref/ohgrepo/script_cmds.json). Jumps are relative to the end of the instruction. GoToIf/CallIf cond: 0 <, 1 ==, 2 >, 3 <=, 4 >=, 5 !=.
- tools/patch.py: ctx API — ctx.script(f) -> Script (set_arg(pc, name, argi, value, expect), append_script(builder) -> new script number, append_code(builder) -> offset, goto_at(pc, length, target): overwrite `length` bytes (even, >=6, no jump targets inside) with GoTo+Noops); Code(base) assembler: op(name,*args), label, goto_if(cond,label), call_if, goto(label), call(label), goto_abs(offset), build(); msg(c, idx) = NPCMsg+WaitButton+CloseMsg. ctx.bank(b) list of strings, ctx.add_text(b, s) -> index (NPCMsg takes a u8 index: must be < 256!), ctx.edit_text, ctx.set_text, ctx.narc(name) cached entries, ctx.log.
- tools/mod_story.py helpers you can import: edit_obj(ctx, event_file, obj_id, sprite=, newid=, shiny=), add_obj(ctx, event_file, sprite, script, x, z, copy_y_from, move=15, flag=0) -> new obj id, objs_off, give_mon_ex(c, species, level, nature=RANDOM, flags=F_IV31, ability_slot=RANDOM), set_party_ability(c, slot, ability), NATURE dict, SHINY_OBJ_ID=230, shiny_sprite(ctx, sprite), VAR_RESULT.
- Map events: narc a/0/3/2 (layout: u32 nBG + 20B each, u32 nObj + 32B each [id, sprite, move, type, flag, script, facing, param0..2 (param2 at +18), xRange, yRange, x, z (u16), y (i32)], warps 12B, coords 16B). tools/events.py, tools/mapgrid.py help view maps. Map object visibility flag: object hidden while its flag is SET.
- Shiny map Pokémon: edit_obj(..., shiny=True) swaps the sprite for a clone whose model has the shiny palette baked in (shiny_sprite, uses placeholder rows of the arm9 overworld table). Do NOT use object ids >= 0xF0: the map loader drops them on a real map load.
- Pokémon overworld sprite id for species S: pokemon_overworld_info.narc[S] u16 sprite → map-object sprite id = sprite+428 (e.g. Darkrai 973, Lugia 282+428=710). Verify per species.

## ModCmd (script command 62, implemented by the code agent)
`ModCmd sub a1..a6` (all u16, literal or var). sub 0 GiveMonEx(species, level, nature 0–24 or 0xFFFF, flags bit0 shiny bit1 IVs31, ability slot 0/1/2(hidden)/0xFFFF, result var). sub 1 SetPartyMonAbility(party slot, ability id, 0,0,0,0). Use the helpers give_mon_ex / set_party_ability. After giving, set moves with `SetMonMove partySlot moveSlot move` (party slot = GetPartyCount-1 for the newest mon). Old GiveMon also still works and species|0x8000 makes it shiny.

## Starter flags
1288 = Pikachu ball (Latios path), 1289 = Bulbasaur ball (Shaymin path), 1287 = set on the Charmander branch. 106 = has a starter.

## Free event flags (verify unused before relying on them: scan all scripts for Set/Clear/CheckFlag)
2600–2602 Ranger quest (taken). Ranges reserved per agent: story_gifts 2610–2619, story_darkrai 2620–2639, story_seatemple 2640–2659, story_comments 2660–2669. Free vars: use 0x4100+ only after checking they're unused.

## Rules
- Keep dialogue in the hack's tone, correct line widths, NPCMsg index < 256 (if a bank is too big, use a different bank the map's script can show? — no: NPCMsg uses the map's bank, so keep additions few or reuse/replace unused lines).
- Report concisely at the end: what you changed (scripts/pcs/banks/flags/objects), how you verified, what's untested or risky. Don't paste big dumps.
