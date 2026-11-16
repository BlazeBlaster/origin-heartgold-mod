# Builds the ARM9 code changes: a compact ScrCmd_GiveMon plus a shiny hook in the freed space.
# Script use: GiveMon with a species value that has bit 15 set (0x8000|species, passed through a var)
# creates that species with a shiny personality that matches the player's own trainer ID.
import struct
from thumb import Asm

SCRCMD_GIVEMON   = 0x0204C594   # table entry 137 points here (+1)
SCRCMD_END       = 0x0204C65C   # next function starts here
SCRIPT_READ_HW   = 0x0203F534
SCRIPT_GET_VAR   = 0x0203FAE8
SCRIPT_GET_VPTR  = 0x0203FAB0
MAPSEC_OF_MAP    = 0x0203A800
GIVEMON          = 0x02053380
CREATEMON        = 0x0206D0C0
GET_TRAINER_ID   = 0x02029414
GEN_SHINY_PID    = 0x0206F458
GIVEMON_CALLSITE = 0x020533A8   # 22 bytes: arg setup + bl CreateMon
GIVEMON_CALL_END = 0x020533BE

def build():
    a = Asm(SCRCMD_GIVEMON)
    a.push_r4_r7_lr(); a.sub_sp(0x28)
    a.mov('r4', 'r0')                 # ctx
    a.adds8('r0', 0x80); a.ldr('r5', 'r0', 0)   # fieldSystem = ctx->fieldSystem
    a.ldr('r0', 'r5', 0x20); a.ldr('r0', 'r0', 0)
    a.bl(MAPSEC_OF_MAP); a.mov('r6', 'r0')      # mapsec
    a.movs('r7', 0)
    a.label('loop')                   # species, level, item, form, ability -> sp+0x14..0x24
    a.mov('r0', 'r4'); a.bl(SCRIPT_READ_HW)
    a.mov('r1', 'r0'); a.mov('r0', 'r5'); a.bl(SCRIPT_GET_VAR)
    a.add_rd_sp('r1', 0x14); a.lsls('r2', 'r7', 2); a.str_reg('r0', 'r1', 'r2')
    a.adds8('r7', 1); a.cmp('r7', 5); a.bcond('lt', 'loop')
    a.mov('r0', 'r4'); a.bl(SCRIPT_READ_HW)
    a.mov('r1', 'r0'); a.mov('r0', 'r5'); a.bl(SCRIPT_GET_VPTR)
    a.mov('r4', 'r0')                 # result pointer
    a.ldr_sp('r0', 0x20); a.str_sp('r0', 0)   # form
    a.ldr_sp('r0', 0x24); a.str_sp('r0', 4)     # ability
    a.ldr_sp('r0', 0x1C); a.str_sp('r0', 8)     # held item
    a.str_sp('r6', 0xC)                         # mapsec
    a.movs('r0', 0x18); a.str_sp('r0', 0x10)    # encounter type
    a.ldr_sp('r3', 0x18)   # level
    a.ldr_sp('r2', 0x14)                        # species (may carry 0x8000)
    a.ldr('r1', 'r5', 0xC)                      # save data
    a.movs('r0', 0xB)                           # heap id
    a.bl(GIVEMON)
    a.strh('r0', 'r4', 0)
    a.movs('r0', 0); a.add_sp(0x28); a.pop_r4_r7_pc()
    # ---- hook(mon, species, level, profile) -> CreateMon(...) ----
    a.label('hook'); hook = a.pc()
    a.push_r4_r7_lr(); a.sub_sp(0x10)
    a.mov('r4', 'r0'); a.mov('r5', 'r1'); a.mov('r6', 'r2'); a.mov('r7', 'r3')
    a.movs('r0', 0)
    for off in (0, 4, 8, 0xC): a.str_sp('r0', off)
    a.lsls('r0', 'r5', 16); a.bcond('pl', 'normal')   # bit 15 of species -> shiny request
    a.lsls('r5', 'r5', 17); a.lsrs('r5', 'r5', 17)     # strip the marker
    a.mov('r0', 'r7'); a.bl(GET_TRAINER_ID)
    a.str_sp('r0', 0xC)                                 # fixedOtId = player's ID
    a.bl(GEN_SHINY_PID)                                 # r0 still = trainer ID
    a.str_sp('r0', 4)                                   # fixedPersonality
    a.movs('r0', 1); a.str_sp('r0', 0); a.str_sp('r0', 8)   # hasFixedPersonality, otIdType=PRESET
    a.label('normal')
    a.mov('r0', 'r4'); a.mov('r1', 'r5'); a.mov('r2', 'r6'); a.movs('r3', 0x20)
    a.bl(CREATEMON)
    a.add_sp(0x10); a.pop_r4_r7_pc()
    # ---- Manaphy egg icon / palette helpers (entered by bl from inside the two icon functions,
    # whose own {r3, lr} frame they pop to return). r0 = species on entry.
    a.label('icon'); icon = a.pc()
    a.movs('r2', 0xB5); a.lsls('r2', 'r2', 4); a.h(0x3A07)   # subs r2,#7 -> 0xB49 (plain egg icon)
    a.movs('r3', 0); a.bcond('al', 'common')
    a.label('pal'); pal = a.pc()
    a.movs('r2', 0); a.movs('r3', 1)                            # plain egg palette 1
    a.label('common')
    a.movs('r1', 0xF5); a.lsls('r1', 'r1', 1)                   # 490 = Manaphy
    a.h(0x1A40)                                                 # subs r0, r0, r1
    a.h(0x4240)                                                 # negs r0, r0  (C=1 only if species was Manaphy)
    a.h(0x4153)                                                 # adcs r3, r2  -> r3 = r3 + r2 + C
    a.adds3('r0', 'r3', 0)
    a.h(0xBD08)                                                 # pop {r3, pc}
    code = a.assemble()
    assert SCRCMD_GIVEMON + len(code) <= SCRCMD_END, hex(len(code))
    code += b'\xc0\x46' * ((SCRCMD_END - SCRCMD_GIVEMON - len(code)) // 2)
    # ---- call site inside GiveMon ----
    c = Asm(GIVEMON_CALLSITE)
    c.ldr_sp('r2', 0x10)   # level
    c.ldr_sp('r3', 0x18)   # profile
    c.mov('r0', 'r4')      # mon
    c.mov('r1', 'r7')      # species
    c.bl(hook)
    while c.pc() < GIVEMON_CALL_END: c.nop()
    site = c.assemble(); assert len(site) == GIVEMON_CALL_END - GIVEMON_CALLSITE
    # egg branch of the icon-index function: was "ldr r0,=0xB49; pop {r3,pc}"
    i = Asm(0x0207309A); i.bl(icon)
    # egg branch of the icon-palette function: was "movs r0,#1; pop {r3,pc}"
    p = Asm(0x02073146); p.bl(pal)
    return [(SCRCMD_GIVEMON, code), (GIVEMON_CALLSITE, site),
            (0x0207309A, i.assemble()), (0x02073146, p.assemble())], hook

# original bytes expected at each patched address (safety check)
EXPECT = {0x0207309A: bytes.fromhex('0748 08bd'.replace(' ', '')),
          0x02073146: bytes.fromhex('0120 08bd'.replace(' ', ''))}
