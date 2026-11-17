scoreboard players set #diff arena 175
data modify storage arena:s diff set value "Hard 1.75x"
data modify block 631 69 116 front_text.messages[2] set value '{"text":"now: Hard 1.75x","color":"red","bold":true}'
tellraw @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] [{"text":"Arena difficulty: ","color":"gray"},{"text":"Hard 1.75x","color":"red","bold":true},{"text":" (tougher mobs, starting with the next mobs to spawn)","color":"gray"}]
playsound minecraft:block.note_block.pling master @a[x=611,y=60,z=115,dx=22,dy=17,dz=30] 632 67 116 1 1.4
