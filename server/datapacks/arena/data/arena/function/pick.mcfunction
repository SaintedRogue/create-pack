scoreboard players operation #v arena = @s arena_pick
execute if score #v arena matches 99 run return run function arena:end_fight
execute if score #v arena matches 50 run return run function arena:join
execute unless score #v arena matches 1..9 run return 0
execute unless score #state arena matches 0 run return run tellraw @s [{"text":"A fight is already running! ","color":"red"},{"text":"Click JOIN FIGHT to jump in, or END FIGHT to stop it.","color":"gray"}]
scoreboard players operation #type arena = #v arena
scoreboard players set #wave arena 1
scoreboard players set #max arena 5
execute if score #type arena matches 7.. run scoreboard players set #max arena 1
function arena:names
function arena:reset_room
tp @s 622 66 127 0 0
scoreboard players set #state arena 1
scoreboard players set #timer arena 100
tellraw @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] [{"selector":"@s","color":"yellow"},{"text":" started ","color":"gray"},{"nbt":"name","storage":"arena:s","color":"gold","bold":true},{"text":"! Click JOIN FIGHT to help.","color":"gray"}]
title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] subtitle {"text":"Get ready...","color":"gray"}
title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title {"nbt":"name","storage":"arena:s","color":"gold","bold":true}
