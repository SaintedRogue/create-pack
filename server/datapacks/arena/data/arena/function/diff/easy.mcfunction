scoreboard players set #diff arena 50
data modify storage arena:s diff set value "Easy 1/2x"
data modify block 631 69 116 front_text.messages[2] set value '{"text":"now: Easy 1/2x","color":"green","bold":true}'
tellraw @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] [{"text":"Arena difficulty: ","color":"gray"},{"text":"Easy 1/2x","color":"green","bold":true},{"text":" (weaker mobs, starting with the next mobs to spawn)","color":"gray"}]
playsound minecraft:block.note_block.pling master @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] 630 67 116 1 0.8
