# Kid mode: scale max health, then fill the boss up to the new maximum.
attribute @s minecraft:generic.max_health modifier add arena:kid_mode -0.5 add_multiplied_total
execute store result entity @s Health float 1 run attribute @s minecraft:generic.max_health get
tag @s remove kid_new
