# Sign clicks run /trigger arena_pick set <n>; only honoured from inside the gallery.
scoreboard players enable @a arena_pick
execute as @a[scores={arena_pick=1..},x=611,y=64,z=116,dx=22,dy=7,dz=5] at @s run function arena:pick
scoreboard players set @a[scores={arena_pick=1..}] arena_pick 0
# Containment failsafe: any arena mob outside the arena is deleted (no loot).
execute as @e[tag=arena_mob] unless entity @s[x=611,y=60,z=123,dx=22,dy=17,dz=22] run function arena:void
# Sneak on the bedrock pad to leave.
execute as @a[x=612,y=65,z=124,dx=2,dy=2,dz=2,predicate=arena:sneaking] run function arena:leave
execute unless score #state arena matches 0 run function arena:running
execute if block 630 67 116 #minecraft:buttons[powered=true] unless score #diff arena matches 50 run function arena:diff/easy
execute if block 631 67 116 #minecraft:buttons[powered=true] unless score #diff arena matches 100 run function arena:diff/normal
execute if block 632 67 116 #minecraft:buttons[powered=true] unless score #diff arena matches 175 run function arena:diff/hard
