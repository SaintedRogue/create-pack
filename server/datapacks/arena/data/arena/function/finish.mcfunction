# Won fight: bring the loot and XP out to the gallery too, so nothing valuable is left behind
# (reset_room wipes the arena at the start of the next fight).
tp @e[x=611,y=64,z=123,dx=22,dy=13,dz=22,type=item] 622 66 119
tp @e[x=611,y=64,z=123,dx=22,dy=13,dz=22,type=experience_orb] 622 66 119
tp @a[x=611,y=64,z=123,dx=22,dy=13,dz=22] 622 66 119 0 0
function arena:cleanup
