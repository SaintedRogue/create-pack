scoreboard players set #state arena 3
scoreboard players set #timer arena 200
title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] subtitle {"text":"Your loot comes with you in 10 seconds","color":"gray"}
title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title {"text":"VICTORY!","color":"gold","bold":true}
execute as @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] at @s run playsound minecraft:ui.toast.challenge_complete master @s
tellraw @a [{"selector":"@a[x=611,y=64,z=123,dx=22,dy=13,dz=22]","color":"yellow"},{"text":" beat ","color":"gray"},{"nbt":"name","storage":"arena:s","color":"gold","bold":true},{"text":" in the arena!","color":"gray"}]
