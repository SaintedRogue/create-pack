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
MOB = 'Tags:["arena_mob","arena_new"],PersistenceRequired:1b'

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
    bossbar add arena:king {"text":"Zombie King","color":"dark_red","bold":true}
    bossbar set arena:king color red
    bossbar set arena:king max 150
    bossbar set arena:king visible false
""")

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
""")

# #state: 0 idle, 1 countdown, 2 fighting, 3 victory lap
fn("pick", f"""
    scoreboard players operation #v arena = @s arena_pick
    execute if score #v arena matches 99 run return run function arena:end_fight
    execute if score #v arena matches 50 run return run function arena:join
    execute unless score #v arena matches 1..9 run return 0
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
    tellraw @a[{ALL}] [{{"selector":"@s","color":"yellow"}},{{"text":" started ","color":"gray"}},{{"nbt":"name","storage":"arena:s","color":"gold","bold":true}},{{"text":"! Click JOIN FIGHT to help.","color":"gray"}}]
    title @a[{A}] subtitle {{"text":"Get ready...","color":"gray"}}
    title @a[{A}] title {{"nbt":"name","storage":"arena:s","color":"gold","bold":true}}
""")

names = ["Zombie Horde", "Skeleton Squad", "Spider Swarm", "Mixed Horde", "Nether Raiders",
         "Illager Gang", "The Zombie King", "Ravager Raid", "THE WITHER"]
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
    execute store result bossbar arena:king value run data get entity @e[tag=zking,limit=1] Health
""")

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
    summon zombie 622 66 140 {{{MOB[:-len(',PersistenceRequired:1b')].replace('"arena_new"]', '"arena_new","zking"]')},PersistenceRequired:1b,CanBreakDoors:0b,CustomName:'{{"text":"Zombie King","color":"dark_red","bold":true}}',CustomNameVisible:1b,Health:150f,attributes:[{{id:"minecraft:generic.max_health",base:150d}},{{id:"minecraft:generic.scale",base:2d}},{{id:"minecraft:generic.attack_damage",base:9d}},{{id:"minecraft:generic.knockback_resistance",base:0.8d}}],ArmorItems:[{{id:"minecraft:diamond_boots",count:1}},{{id:"minecraft:diamond_leggings",count:1}},{{id:"minecraft:diamond_chestplate",count:1}},{{id:"minecraft:golden_helmet",count:1}}],HandItems:[{{id:"minecraft:diamond_sword",count:1}},{{}}],ArmorDropChances:[0f,0f,0f,0f],HandDropChances:[0f,0f]}}
    summon zombie 620 66 138 {{{MOB},IsBaby:1b}}
    summon zombie 624 66 138 {{{MOB},IsBaby:1b}}
    summon zombie 620 66 142 {{{MOB},IsBaby:1b}}
    summon zombie 624 66 142 {{{MOB},IsBaby:1b}}
""")
fn("boss/ravager", f"""
    summon ravager 622 66 140 {{{MOB},CustomName:'{{"text":"Ravager","color":"dark_red","bold":true}}',CustomNameVisible:1b,Passengers:[{{id:"minecraft:vindicator",Tags:["arena_mob"],PersistenceRequired:1b}}]}}
    summon pillager 618 66 140 {{{MOB}}}
    summon pillager 626 66 140 {{{MOB}}}
    summon pillager 622 66 143 {{{MOB}}}
""")
fn("boss/wither", f"summon wither 622 68 140 {{{MOB}}}")

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
    title @a[{A}] subtitle {{"text":"Grab your loot! Back to the gallery in 10 seconds","color":"gray"}}
    title @a[{A}] title {{"text":"VICTORY!","color":"gold","bold":true}}
    execute as @a[{A}] at @s run playsound minecraft:ui.toast.challenge_complete master @s
    tellraw @a [{{"selector":"@a[{A}]","color":"yellow"}},{{"text":" beat ","color":"gray"}},{{"nbt":"name","storage":"arena:s","color":"gold","bold":true}},{{"text":" in the arena!","color":"gray"}}]
""")
fn("finish", f"""
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
