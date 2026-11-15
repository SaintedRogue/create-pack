execute store result score #r arena run random value 0..3
execute if score #type arena matches 1 run function arena:mob/zombies
execute if score #type arena matches 2 run function arena:mob/skeletons
execute if score #type arena matches 3 run function arena:mob/spiders
execute if score #type arena matches 4 run function arena:mob/mixed
execute if score #type arena matches 5 run function arena:mob/nether
execute if score #type arena matches 6 run function arena:mob/illagers
scoreboard players remove #n arena 1
execute if score #n arena matches 1.. run function arena:spawn_loop
