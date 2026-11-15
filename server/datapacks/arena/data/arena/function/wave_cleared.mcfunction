execute if score #wave arena >= #max arena run return run function arena:victory
scoreboard players add #wave arena 1
scoreboard players set #state arena 1
scoreboard players set #timer arena 80
title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] subtitle {"text":"Next wave incoming...","color":"gray"}
title @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] title {"text":"Wave cleared!","color":"green","bold":true}
