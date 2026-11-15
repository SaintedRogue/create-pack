execute if score #state arena matches 0 run return run tellraw @s {"text":"No fight running. Pick one from the signs first.","color":"red"}
execute if score #state arena matches 3 run return run tellraw @s {"text":"That fight is already won!","color":"green"}
tp @s 622 66 127 0 0
tellraw @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] [{"selector":"@s","color":"yellow"},{"text":" joined the fight!","color":"gray"}]
