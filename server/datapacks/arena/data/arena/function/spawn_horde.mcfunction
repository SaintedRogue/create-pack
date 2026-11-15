# wave n spawns 2n+1 mobs: 3, 5, 7, 9, 11
scoreboard players operation #n arena = #wave arena
scoreboard players operation #n arena *= #two arena
scoreboard players add #n arena 1
function arena:spawn_loop
