execute unless entity @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] run return run function arena:abort
scoreboard players remove #timer arena 1
execute if score #state arena matches 1 if score #timer arena matches 60 run title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title {"text":"3","color":"yellow","bold":true}
execute if score #state arena matches 1 if score #timer arena matches 40 run title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title {"text":"2","color":"gold","bold":true}
execute if score #state arena matches 1 if score #timer arena matches 20 run title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title {"text":"1","color":"red","bold":true}
execute if score #state arena matches 1 if score #timer arena matches ..0 run function arena:spawn_wave
execute if score #state arena matches 2 unless entity @e[tag=arena_mob] run function arena:wave_cleared
execute if score #state arena matches 3 if score #timer arena matches ..0 run function arena:finish
execute if entity @e[tag=zking] run function arena:kingbar
execute unless entity @e[tag=zking] run bossbar set arena:king visible false
