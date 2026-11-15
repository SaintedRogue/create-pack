execute if score #state arena matches 0 run return run tellraw @s {"text":"No fight running.","color":"gray"}
tellraw @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] [{"selector":"@s","color":"yellow"},{"text":" ended the fight.","color":"gray"}]
tp @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] 622 66 119 0 0
function arena:cleanup
