execute as @e[tag=arena_mob] run function arena:void
execute as @e[x=611,y=64,z=123,dx=22,dy=13,dz=22,type=!player,type=!item,type=!experience_orb] run function arena:void
scoreboard players set #state arena 0
bossbar set arena:king visible false
