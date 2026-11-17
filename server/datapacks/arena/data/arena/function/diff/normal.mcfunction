scoreboard players set #diff arena 100
data modify storage arena:s diff set value "Normal 1x"
data modify block 631 69 116 front_text.messages[2] set value '{"text":"now: Normal 1x","color":"yellow","bold":true}'
tellraw @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] [{"text":"Arena difficulty: ","color":"gray"},{"text":"Normal 1x","color":"yellow","bold":true},{"text":" (normal strength, starting with the next mobs to spawn)","color":"gray"}]
playsound minecraft:block.note_block.pling master @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] 631 67 116 1 1.0
