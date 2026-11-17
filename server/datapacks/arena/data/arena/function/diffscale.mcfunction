execute if score #diff arena matches 50 run attribute @s minecraft:generic.max_health modifier add arena:difficulty -0.5 add_multiplied_total
execute if score #diff arena matches 50 run attribute @s minecraft:generic.attack_damage modifier add arena:difficulty -0.5 add_multiplied_total
execute if score #diff arena matches 175 run attribute @s minecraft:generic.max_health modifier add arena:difficulty 0.75 add_multiplied_total
execute if score #diff arena matches 175 run attribute @s minecraft:generic.attack_damage modifier add arena:difficulty 0.75 add_multiplied_total
execute store result entity @s Health float 1 run attribute @s minecraft:generic.max_health get
tag @s remove diff_new
