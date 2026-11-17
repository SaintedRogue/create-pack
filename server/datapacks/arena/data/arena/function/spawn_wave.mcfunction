scoreboard players set #state arena 2
title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] subtitle {"text":"FIGHT!","color":"red","bold":true}
execute if score #max arena matches 1 run title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title {"nbt":"name","storage":"arena:s","color":"dark_red","bold":true}
execute if score #max arena matches 5 run title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title [{"text":"Wave ","color":"gold"},{"score":{"name":"#wave","objective":"arena"}},{"text":" of 5"}]
playsound minecraft:event.raid.horn master @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] 622 70 134 4 1
execute if score #type arena matches 1..6 run function arena:spawn_horde
execute if score #type arena matches 7 run function arena:boss/zombie_king
execute if score #type arena matches 8 run function arena:boss/ravager
execute if score #type arena matches 9 run function arena:boss/wither
execute if score #type arena matches 10 run function arena:boss/cm_ignis
execute if score #type arena matches 11 run function arena:boss/cm_monstrosity
execute if score #type arena matches 12 run function arena:boss/cm_harbinger
execute if score #type arena matches 13 run function arena:boss/cm_ender_guardian
execute if score #type arena matches 14 run function arena:boss/cm_maledictus
execute if score #type arena matches 15 run function arena:boss/cm_remnant
execute if score #type arena matches 16 run function arena:boss/cm_kobolediator
execute as @e[tag=kid_new] run function arena:kidhp
execute as @e[tag=diff_new] run function arena:diffscale
spreadplayers 622 137 1 6 under 75 false @e[tag=arena_new]
tag @e[tag=arena_new] remove arena_new
