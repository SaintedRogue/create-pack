"""Gladiator arena at ~622,66,118 (CreateMC01). Floor y65, players stand at y66.

Arena  : interior x612-632, z124-144, y66-75. Reinforced-deepslate floor + ceiling,
         barrier liner (x611/633, z123/145) inside deepslate-brick outer walls (x610/634, z122/146).
         Bedrock exit pad x612-614 z124-126. Light blocks y74 (re-laid by the datapack each fight).
Gallery: interior x611-633, z116-121, y66-70; door at 622,66,115; window = arena north wall z122.
"""
import sys
from range import run, FILL, SET, TEST

cmds = []
f = lambda c: cmds.append((c, FILL))
s = lambda c: cmds.append((c, SET))

# --- terrain ---
f("fill 609 66 114 635 80 147 minecraft:air")
f("fill 609 58 114 635 64 147 minecraft:dirt replace #minecraft:replaceable")
f("fill 609 65 114 635 65 147 minecraft:grass_block replace #minecraft:replaceable")

# --- arena shell ---
f("fill 610 65 122 634 65 146 minecraft:reinforced_deepslate")       # floor
f("fill 612 65 124 614 65 126 minecraft:bedrock")                     # exit pad
for c in ("610 66 122 610 75 146", "634 66 122 634 75 146", "610 66 146 634 75 146", "610 66 122 634 75 122"):
    f(f"fill {c} minecraft:deepslate_bricks")                        # outer walls
f("fill 612 67 122 632 70 122 minecraft:glass")                       # gallery window
f("fill 610 76 122 634 76 146 minecraft:reinforced_deepslate")       # ceiling
for c in ("611 66 123 633 75 123", "611 66 145 633 75 145", "611 66 124 611 75 144", "633 66 124 633 75 144"):
    f(f"fill {c} minecraft:barrier")                                 # unbreakable liner
for x in (614, 618, 622, 626, 630):
    for z in (126, 130, 134, 138, 142):
        s(f"setblock {x} 74 {z} minecraft:light[level=15]")          # arena lighting
for x in (614, 622, 630):
    for z in (126, 134, 142):
        s(f"setblock {x} 77 {z} minecraft:light[level=15]")          # stop mobs spawning on the roof

# --- gallery ---
f("fill 610 65 115 634 65 121 minecraft:polished_blackstone_bricks")
f("fill 610 66 115 634 70 115 minecraft:deepslate_tiles")
f("fill 610 66 115 610 70 121 minecraft:deepslate_tiles")
f("fill 634 66 115 634 70 121 minecraft:deepslate_tiles")
f("fill 610 71 115 634 71 121 minecraft:deepslate_tiles")
s("setblock 622 66 115 minecraft:oak_door[facing=south,half=lower,hinge=left]")
s("setblock 622 67 115 minecraft:oak_door[facing=south,half=upper,hinge=left]")
for x in (614, 622, 630):
    s(f"setblock {x} 70 118 minecraft:lantern[hanging=true]")
s("setblock 621 68 114 minecraft:wall_torch[facing=north]")           # light outside the door
s("setblock 623 68 114 minecraft:wall_torch[facing=north]")

# --- signs (waxed, click runs /trigger) ---
def sign(pos, facing, lines, pick=None, color="black"):
    msgs = []
    for i, (txt, col, bold) in enumerate(lines):
        comp = f'{{"text":"{txt}","color":"{col}","bold":{str(bold).lower()}'
        if pick is not None and i == 1:
            comp += f',"clickEvent":{{"action":"run_command","value":"/trigger arena_pick set {pick}"}}'
        comp += "}"
        msgs.append(f"'{comp}'")
    nbt = f"{{front_text:{{messages:[{','.join(msgs)}],has_glowing_text:1b,color:\"{color}\"}},is_waxed:1b}}"
    s(f"setblock {pos} minecraft:dark_oak_wall_sign[facing={facing}]{nbt}")

B = lambda t, c="white": (t, c, True)
N = lambda t, c="gray": (t, c, False)
E = ("", "white", False)
# West wall: wave fights (signs at x611 facing east)
sign("611 69 118", "east", [E, B("WAVE FIGHTS", "gold"), N("5 waves each"), E])
sign("611 68 117", "east", [E, B("Zombie Horde", "green"), N("click to start"), E], 1)
sign("611 68 118", "east", [E, B("Skeleton Squad", "white"), N("click to start"), E], 2)
sign("611 68 119", "east", [E, B("Spider Swarm", "red"), N("click to start"), E], 3)
sign("611 67 117", "east", [E, B("Mixed Horde", "yellow"), N("creepers too!"), E], 4)
sign("611 67 118", "east", [E, B("Nether Raiders", "gold"), N("click to start"), E], 5)
sign("611 67 119", "east", [E, B("Illager Gang", "aqua"), N("click to start"), E], 6)
# East wall: bosses (signs at x633 facing west)
sign("633 69 118", "west", [E, B("BOSS FIGHTS", "dark_red"), N("one big fight"), E])
sign("633 68 119", "west", [E, B("Zombie King", "green"), N("+ minions"), E], 7)
sign("633 68 118", "west", [E, B("Ravager Raid", "gold"), N("+ pillagers"), E], 8)
sign("633 68 117", "west", [E, B("THE WITHER", "light_purple"), N("good luck..."), E], 9)
# North wall by the door (signs at z116 facing south)
sign("620 67 116", "south", [E, B("JOIN FIGHT", "green"), N("jump in"), E], 50)
sign("624 67 116", "south", [E, B("END FIGHT", "red"), N("stops everything"), E], 99)
sign("622 68 116", "south", [N("To leave the", "white"), N("arena: crouch on", "white"), B("the BEDROCK", "aqua"), N("in the corner", "white")])

checks = [
    "execute if block 622 65 134 minecraft:reinforced_deepslate",
    "execute if block 613 65 125 minecraft:bedrock",
    "execute if block 622 76 134 minecraft:reinforced_deepslate",
    "execute if block 611 70 134 minecraft:barrier",
    "execute if block 633 70 134 minecraft:barrier",
    "execute if block 622 70 123 minecraft:barrier",
    "execute if block 622 70 145 minecraft:barrier",
    "execute if block 622 68 122 minecraft:glass",
    "execute if block 634 70 134 minecraft:deepslate_bricks",
    "execute if block 622 70 134 minecraft:air",
    "execute if block 622 74 134 minecraft:light",
    "execute if block 622 65 118 minecraft:polished_blackstone_bricks",
    "execute if block 622 66 115 minecraft:oak_door",
    "execute if block 622 71 118 minecraft:deepslate_tiles",
    "execute if block 611 68 117 minecraft:dark_oak_wall_sign",
    "execute if block 633 68 117 minecraft:dark_oak_wall_sign",
    "execute if block 624 67 116 minecraft:dark_oak_wall_sign",
    "execute if block 622 74 134 #minecraft:wither_immune",
    "execute if block 622 65 134 #minecraft:wither_immune",
    "execute if block 611 70 134 #minecraft:wither_immune",
]
cmds += [(c, TEST) for c in checks]

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for c, p in cmds:
        if only == "check" and p != TEST: continue
        print(f"{c[:100]}\n   -> {run(c, p)}", flush=True)
