bossbar set arena:king players @a[x=611,y=64,z=123,dx=22,dy=13,dz=22]
bossbar set arena:king visible true
execute store result bossbar arena:king value run data get entity @e[tag=zking,limit=1] Health
