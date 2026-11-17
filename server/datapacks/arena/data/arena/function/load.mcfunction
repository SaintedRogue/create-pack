scoreboard objectives add arena dummy
scoreboard objectives add arena_pick trigger
scoreboard players set #two arena 2
execute unless score #state arena matches 0.. run scoreboard players set #state arena 0
execute unless score #diff arena matches 1.. run scoreboard players set #diff arena 100
execute unless data storage arena:s diff run data modify storage arena:s diff set value "Normal 1x"
bossbar add arena:king {"text":"Zombie King","color":"dark_red","bold":true}
bossbar set arena:king color red
bossbar set arena:king max 150
bossbar set arena:king visible false
