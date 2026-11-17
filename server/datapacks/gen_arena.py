"""Generate the 'arena' datapack (MC 1.21.1, pack_format 48) into ~/create-pack/server/datapacks/arena."""
import json, os, textwrap
ROOT = os.path.expanduser("~/create-pack/server/datapacks/arena")
F = {}

# ---- geometry (keep in sync with the in-world build) ----
A   = "x=611,y=64,z=123,dx=22,dy=13,dz=22"     # arena incl. barrier liner
GAL = "x=611,y=64,z=116,dx=22,dy=7,dz=5"       # gallery (controls work only here)
ALL = "x=611,y=60,z=115,dx=22,dy=17,dz=30"     # gallery + arena (for messages)
KEEP = "x=611,y=60,z=123,dx=22,dy=17,dz=22"    # mobs outside this get removed
PAD = "x=612,y=65,z=124,dx=2,dy=2,dz=2"        # bedrock exit pad (NW corner)
IN, OUT = "622 66 127 0 0", "622 66 119 0 0"   # arena entry / gallery return (facing south)
MOB = 'Tags:["arena_mob","arena_new","diff_new"],PersistenceRequired:1b'

# Difficulty buttons (gallery north wall, right of the door). Multiplies every arena mob's max health
# and melee attack damage; stacks on top of KID_MODE for Cataclysm bosses. Applies to mobs as they spawn.
DIFFS = [  # (percent, key, label, button x, modifier, colour, note pitch)
    (50, "easy", "Easy 1/2x", 630, -0.5, "green", 0.8),
    (100, "normal", "Normal 1x", 631, 0.0, "yellow", 1.0),
    (175, "hard", "Hard 1.75x", 632, 0.75, "red", 1.4),
]
DIFF_Y, DIFF_Z, DIFF_HEADER = 67, 116, "631 69 116"

# Cataclysm bosses (fight types 10-16), arena "kid mode": max health scaled by KID_MODE.
# Every one of these has reinforced_deepslate, barrier, bedrock and light in its cataclysm:*_immune
# block tag (checked in 3.33), so they can't break the arena shell. Extra NBT wakes the ones that
# otherwise sleep until a player triggers their altar/throne.
KID_MODE = 0.5
CATACLYSM = [  # (type, key, entity, name, summon y, extra NBT)
    (10, "ignis", "cataclysm:ignis", "Ignis", 66, ""),
    (11, "monstrosity", "cataclysm:netherite_monstrosity", "Netherite Monstrosity", 66, ",is_Awaken:1b"),
    (12, "harbinger", "cataclysm:the_harbinger", "The Harbinger", 68, ",Is_Act:1b"),
    (13, "ender_guardian", "cataclysm:ender_guardian", "Ender Guardian", 66, ""),
    (14, "maledictus", "cataclysm:maledictus", "Maledictus", 67, ""),
    (15, "remnant", "cataclysm:ancient_remnant", "Ancient Remnant", 66, ",has_necklace:1b"),
    (16, "kobolediator", "cataclysm:kobolediator", "Kobolediator", 66, ",Awaken:1b"),
]
LAST_TYPE = CATACLYSM[-1][0]

F["pack.mcmeta"] = json.dumps({"pack": {"pack_format": 48, "description": "Ahrendt arena: pick-a-fight mob arena"}}, indent=2)
F["data/minecraft/tags/function/load.json"] = json.dumps({"values": ["arena:load"]})
F["data/minecraft/tags/function/tick.json"] = json.dumps({"values": ["arena:tick"]})
F["data/arena/predicate/sneaking.json"] = json.dumps(
    {"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"flags": {"is_sneaking": True}}}, indent=2)

def fn(name, body): F[f"data/arena/function/{name}.mcfunction"] = textwrap.dedent(body).strip() + "\n"

fn("load", """
    scoreboard objectives add arena dummy
    scoreboard objectives add arena_pick trigger
    scoreboard players set #two arena 2
    execute unless score #state arena matches 0.. run scoreboard players set #state arena 0
    execute unless score #diff arena matches 1.. run scoreboard players set #diff arena 100
    execute unless data storage arena:s diff run data modify storage arena:s diff set value "Normal 1x"
    bossbar add arena:king {"text":"Zombie King","color":"dark_red","bold":true}
    bossbar set arena:king color red
    bossbar set arena:king max 150
    bossbar set arena:king visible false
""")

DIFF_POLL = "\n    ".join(f"execute if block {x} {DIFF_Y} {DIFF_Z} #minecraft:buttons[powered=true] unless score #diff arena matches {p} run function arena:diff/{k}" for p, k, _, x, *_ in DIFFS)
fn("tick", f"""
    # Sign clicks run /trigger arena_pick set <n>; only honoured from inside the gallery.
    scoreboard players enable @a arena_pick
    execute as @a[scores={{arena_pick=1..}},{GAL}] at @s run function arena:pick
    scoreboard players set @a[scores={{arena_pick=1..}}] arena_pick 0
    # Containment failsafe: any arena mob outside the arena is deleted (no loot).
    execute as @e[tag=arena_mob] unless entity @s[{KEEP}] run function arena:void
    # Sneak on the bedrock pad to leave.
    execute as @a[{PAD},predicate=arena:sneaking] run function arena:leave
    execute unless score #state arena matches 0 run function arena:running
    {DIFF_POLL}
""")

# #state: 0 idle, 1 countdown, 2 fighting, 3 victory lap
fn("pick", f"""
    scoreboard players operation #v arena = @s arena_pick
    execute if score #v arena matches 99 run return run function arena:end_fight
    execute if score #v arena matches 50 run return run function arena:join
    execute unless score #v arena matches 1..{LAST_TYPE} run return 0
    execute unless score #state arena matches 0 run return run tellraw @s [{{"text":"A fight is already running! ","color":"red"}},{{"text":"Click JOIN FIGHT to jump in, or END FIGHT to stop it.","color":"gray"}}]
    scoreboard players operation #type arena = #v arena
    scoreboard players set #wave arena 1
    scoreboard players set #max arena 5
    execute if score #type arena matches 7.. run scoreboard players set #max arena 1
    function arena:names
    function arena:reset_room
    tp @s {IN}
    scoreboard players set #state arena 1
    scoreboard players set #timer arena 100
    tellraw @a[{ALL}] [{{"selector":"@s","color":"yellow"}},{{"text":" started ","color":"gray"}},{{"nbt":"name","storage":"arena:s","color":"gold","bold":true}},{{"text":" on ","color":"gray"}},{{"nbt":"diff","storage":"arena:s","color":"yellow"}},{{"text":"! Click JOIN FIGHT to help.","color":"gray"}}]
    title @a[{A}] subtitle [{{"text":"Get ready... ","color":"gray"}},{{"nbt":"diff","storage":"arena:s","color":"yellow"}}]
    title @a[{A}] title {{"nbt":"name","storage":"arena:s","color":"gold","bold":true}}
""")

names = ["Zombie Horde", "Skeleton Squad", "Spider Swarm", "Mixed Horde", "Nether Raiders",
         "Illager Gang", "The Zombie King", "Ravager Raid", "THE WITHER"] + [c[3] for c in CATACLYSM]
fn("names", "\n".join(f'execute if score #type arena matches {i} run data modify storage arena:s name set value "{n}"'
                      for i, n in enumerate(names, 1)))

fn("join", f"""
    execute if score #state arena matches 0 run return run tellraw @s {{"text":"No fight running. Pick one from the signs first.","color":"red"}}
    execute if score #state arena matches 3 run return run tellraw @s {{"text":"That fight is already won!","color":"green"}}
    tp @s {IN}
    tellraw @a[{ALL}] [{{"selector":"@s","color":"yellow"}},{{"text":" joined the fight!","color":"gray"}}]
""")

fn("running", f"""
    execute unless entity @a[{A}] run return run function arena:abort
    scoreboard players remove #timer arena 1
    execute if score #state arena matches 1 if score #timer arena matches 60 run title @a[{A}] title {{"text":"3","color":"yellow","bold":true}}
    execute if score #state arena matches 1 if score #timer arena matches 40 run title @a[{A}] title {{"text":"2","color":"gold","bold":true}}
    execute if score #state arena matches 1 if score #timer arena matches 20 run title @a[{A}] title {{"text":"1","color":"red","bold":true}}
    execute if score #state arena matches 1 if score #timer arena matches ..0 run function arena:spawn_wave
    execute if score #state arena matches 2 unless entity @e[tag=arena_mob] run function arena:wave_cleared
    execute if score #state arena matches 3 if score #timer arena matches ..0 run function arena:finish
    execute if entity @e[tag=zking] run function arena:kingbar
    execute unless entity @e[tag=zking] run bossbar set arena:king visible false
""")

fn("kingbar", f"""
    bossbar set arena:king players @a[{A}]
    bossbar set arena:king visible true
    execute store result bossbar arena:king max run attribute @e[tag=zking,limit=1] minecraft:generic.max_health get
    execute store result bossbar arena:king value run data get entity @e[tag=zking,limit=1] Health
""")

CM_DISPATCH = "\n    ".join(f"execute if score #type arena matches {t} run function arena:boss/cm_{k}" for t, k, *_ in CATACLYSM)
fn("spawn_wave", f"""
    scoreboard players set #state arena 2
    title @a[{A}] subtitle {{"text":"FIGHT!","color":"red","bold":true}}
    execute if score #max arena matches 1 run title @a[{A}] title {{"nbt":"name","storage":"arena:s","color":"dark_red","bold":true}}
    execute if score #max arena matches 5 run title @a[{A}] title [{{"text":"Wave ","color":"gold"}},{{"score":{{"name":"#wave","objective":"arena"}}}},{{"text":" of 5"}}]
    playsound minecraft:event.raid.horn master @a[{A}] 622 70 134 4 1
    execute if score #type arena matches 1..6 run function arena:spawn_horde
    execute if score #type arena matches 7 run function arena:boss/zombie_king
    execute if score #type arena matches 8 run function arena:boss/ravager
    execute if score #type arena matches 9 run function arena:boss/wither
    {CM_DISPATCH}
    execute as @e[tag=kid_new] run function arena:kidhp
    execute as @e[tag=diff_new] run function arena:diffscale
    spreadplayers 622 137 1 6 under 75 false @e[tag=arena_new]
    tag @e[tag=arena_new] remove arena_new
""")

fn("spawn_horde", """
    # wave n spawns 2n+1 mobs: 3, 5, 7, 9, 11
    scoreboard players operation #n arena = #wave arena
    scoreboard players operation #n arena *= #two arena
    scoreboard players add #n arena 1
    function arena:spawn_loop
""")
fn("spawn_loop", """
    execute store result score #r arena run random value 0..3
    execute if score #type arena matches 1 run function arena:mob/zombies
    execute if score #type arena matches 2 run function arena:mob/skeletons
    execute if score #type arena matches 3 run function arena:mob/spiders
    execute if score #type arena matches 4 run function arena:mob/mixed
    execute if score #type arena matches 5 run function arena:mob/nether
    execute if score #type arena matches 6 run function arena:mob/illagers
    scoreboard players remove #n arena 1
    execute if score #n arena matches 1.. run function arena:spawn_loop
""")
P = "622 66 137"
def mobs(name, table):
    fn(f"mob/{name}", "\n".join(f"execute if score #r arena matches {r} run summon {m} {P} {{{MOB}{extra}}}" for r, m, extra in table))
mobs("zombies",   [("0..1", "zombie", ""), ("2", "husk", ""), ("3", "zombie", ",IsBaby:1b")])
mobs("skeletons", [("0..2", "skeleton", ""), ("3", "stray", "")])
mobs("spiders",   [("0..2", "spider", ""), ("3", "cave_spider", "")])
mobs("mixed",     [("0", "zombie", ""), ("1", "skeleton", ""), ("2", "spider", ""), ("3", "creeper", "")])
# Wither skeletons use the plain skeleton loot table: no wither skulls, so nobody can build a Wither at home.
mobs("nether",    [("0..2", "wither_skeleton", ',DeathLootTable:"minecraft:entities/skeleton"'), ("3", "blaze", "")])
mobs("illagers",  [("0..1", "vindicator", ""), ("2..3", "pillager", "")])

fn("boss/zombie_king", f"""
    summon zombie 622 66 140 {{{MOB[:-len(',PersistenceRequired:1b')].replace('"diff_new"]', '"diff_new","zking"]')},PersistenceRequired:1b,CanBreakDoors:0b,CustomName:'{{"text":"Zombie King","color":"dark_red","bold":true}}',CustomNameVisible:1b,Health:150f,attributes:[{{id:"minecraft:generic.max_health",base:150d}},{{id:"minecraft:generic.scale",base:2d}},{{id:"minecraft:generic.attack_damage",base:9d}},{{id:"minecraft:generic.knockback_resistance",base:0.8d}}],ArmorItems:[{{id:"minecraft:diamond_boots",count:1}},{{id:"minecraft:diamond_leggings",count:1}},{{id:"minecraft:diamond_chestplate",count:1}},{{id:"minecraft:golden_helmet",count:1}}],HandItems:[{{id:"minecraft:diamond_sword",count:1}},{{}}],ArmorDropChances:[0f,0f,0f,0f],HandDropChances:[0f,0f]}}
    summon zombie 620 66 138 {{{MOB},IsBaby:1b}}
    summon zombie 624 66 138 {{{MOB},IsBaby:1b}}
    summon zombie 620 66 142 {{{MOB},IsBaby:1b}}
    summon zombie 624 66 142 {{{MOB},IsBaby:1b}}
""")
fn("boss/ravager", f"""
    summon ravager 622 66 140 {{{MOB},CustomName:'{{"text":"Ravager","color":"dark_red","bold":true}}',CustomNameVisible:1b,Passengers:[{{id:"minecraft:vindicator",Tags:["arena_mob","diff_new"],PersistenceRequired:1b}}]}}
    summon pillager 618 66 140 {{{MOB}}}
    summon pillager 626 66 140 {{{MOB}}}
    summon pillager 622 66 143 {{{MOB}}}
""")
fn("boss/wither", f"summon wither 622 68 140 {{{MOB}}}")
for t, k, ent, nm, y, extra in CATACLYSM:
    # Not tagged arena_new: big bosses stay centred instead of being spread toward the walls.
    fn(f"boss/cm_{k}", f'summon {ent} 622 {y} 138 {{Tags:["arena_mob","kid_new","diff_new"],PersistenceRequired:1b{extra}}}')
# The Harbinger's death laser ignores barrier (invisible) and broke the arena's outer bricks and
# gallery glass in testing (2026-11-16, 70 blocks). Cataclysm decides what each boss may break from
# its cataclysm:*_immune block tags, so add the arena's outer materials to every boss's immune list.
# Effect outside the arena: Cataclysm bosses also can't break these four blocks in the wild.
ARENA_SHELL = ["minecraft:deepslate_bricks", "minecraft:deepslate_tiles", "minecraft:glass", "minecraft:polished_blackstone_bricks"]
for tag in ("harbinger_immune", "ignis_immune", "netherite_monstrosity_immune", "leviathan_immune",
            "maledictus_immune", "remnant_immune", "scylla_immune", "clawdian_immune"):
    F[f"data/cataclysm/tags/block/{tag}.json"] = json.dumps({"replace": False, "values": ARENA_SHELL}, indent=2)

fn("diffscale", "\n".join(
    [f"execute if score #diff arena matches {p} run attribute @s minecraft:generic.{a} modifier add arena:difficulty {m} add_multiplied_total"
     for p, _, _, _, m, *_ in DIFFS if m for a in ("max_health", "attack_damage")]
    + ["execute store result entity @s Health float 1 run attribute @s minecraft:generic.max_health get", "tag @s remove diff_new"]))
for p, k, label, x, m, col, pitch in DIFFS:
    what = "normal strength" if not m else ("weaker mobs" if m < 0 else "tougher mobs")
    fn(f"diff/{k}", f"""
    scoreboard players set #diff arena {p}
    data modify storage arena:s diff set value "{label}"
    data modify block {DIFF_HEADER} front_text.messages[2] set value '{{"text":"now: {label}","color":"{col}","bold":true}}'
    tellraw @a[{ALL}] [{{"text":"Arena difficulty: ","color":"gray"}},{{"text":"{label}","color":"{col}","bold":true}},{{"text":" ({what}, starting with the next mobs to spawn)","color":"gray"}}]
    playsound minecraft:block.note_block.pling master @a[{ALL}] {x} {DIFF_Y} {DIFF_Z} 1 {pitch}
""")

fn("kidhp", f"""
    # Kid mode: scale max health, then fill the boss up to the new maximum.
    attribute @s minecraft:generic.max_health modifier add arena:kid_mode {KID_MODE - 1} add_multiplied_total
    execute store result entity @s Health float 1 run attribute @s minecraft:generic.max_health get
    tag @s remove kid_new
""")

fn("wave_cleared", f"""
    execute if score #wave arena >= #max arena run return run function arena:victory
    scoreboard players add #wave arena 1
    scoreboard players set #state arena 1
    scoreboard players set #timer arena 80
    title @a[{A}] subtitle {{"text":"Next wave incoming...","color":"gray"}}
    title @a[{A}] title {{"text":"Wave cleared!","color":"green","bold":true}}
""")
fn("victory", f"""
    scoreboard players set #state arena 3
    scoreboard players set #timer arena 200
    title @a[{A}] subtitle {{"text":"Your loot comes with you in 10 seconds","color":"gray"}}
    title @a[{A}] title {{"text":"VICTORY!","color":"gold","bold":true}}
    execute as @a[{A}] at @s run playsound minecraft:ui.toast.challenge_complete master @s
    tellraw @a [{{"selector":"@a[{A}]","color":"yellow"}},{{"text":" beat ","color":"gray"}},{{"nbt":"name","storage":"arena:s","color":"gold","bold":true}},{{"text":" in the arena!","color":"gray"}}]
""")
fn("finish", f"""
    # Won fight: bring the loot and XP out to the gallery too, so nothing valuable is left behind
    # (reset_room wipes the arena at the start of the next fight).
    tp @e[{A},type=item] 622 66 119
    tp @e[{A},type=experience_orb] 622 66 119
    tp @a[{A}] {OUT}
    function arena:cleanup
""")
fn("abort", f"""
    tellraw @a[{ALL}] {{"text":"Nobody left in the arena, so the fight is over.","color":"gray"}}
    function arena:cleanup
""")
fn("end_fight", f"""
    execute if score #state arena matches 0 run return run tellraw @s {{"text":"No fight running.","color":"gray"}}
    tellraw @a[{ALL}] [{{"selector":"@s","color":"yellow"}},{{"text":" ended the fight.","color":"gray"}}]
    tp @a[{A}] {OUT}
    function arena:cleanup
""")
fn("leave", f"""
    tp @s {OUT}
    tellraw @s {{"text":"You left the arena.","color":"gray"}}
""")
fn("cleanup", f"""
    execute as @e[tag=arena_mob] run function arena:void
    execute as @e[{A},type=!player,type=!item,type=!experience_orb] run function arena:void
    scoreboard players set #state arena 0
    bossbar set arena:king visible false
""")
# Removing mobs: drop them into the void first so their loot is lost (no free Nether stars from abandoned fights).
fn("void", """
    tp @s 622 -300 134
    kill @s
""")
lights = [(x, z) for x in (614, 618, 622, 626, 630) for z in (126, 130, 134, 138, 142)]
fn("reset_room", f"""
    execute as @e[{A},type=!player] run function arena:void
    fill 612 66 124 632 75 144 minecraft:air replace minecraft:fire
""" + "\n".join(f"execute if block {x} 74 {z} minecraft:air run setblock {x} 74 {z} minecraft:light[level=15]" for x, z in lights))

for path, body in F.items():
    p = os.path.join(ROOT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(body)
print(f"wrote {len(F)} files to {ROOT}")
