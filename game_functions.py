import numpy as np

from game import *
from config import *


def instance_reward_model_basic(inst):
    # Simple model
    if inst.is_dead():
        return -10
    res = 0
    res += inst.cal_dmg/10
    inst.cal_dmg = 0
    res += inst.hp/inst.hp_max
    return res

def spawn_resources_basic(game):
    for x in range(GAME_AREA_WIDTH):
        for y in range(GAME_AREA_HEIGHT):
            if np.random.rand()<GAME_RESOURCE_SPAWN_RATE:
                game.area_resource[x,y] += 1

def state_basic(game, inst):
    sight = GAME_INSTANCE_SIGHT
    res_pad = np.zeros((GAME_AREA_WIDTH+2*sight, GAME_AREA_HEIGHT+2*sight))
    for w in range(GAME_AREA_WIDTH):
        for h in range(GAME_AREA_HEIGHT):
            res_pad[sight+w,sight+h] = game.area_resource[w,h]/GAME_RESOURCE_MAX

    res_info = []
    enm_info = []
    wall_info = []
    for w in range(inst.y,inst.y+sight*2+1):
        for h in range(inst.x,inst.x+sight*2+1):
            if inst.y+sight == w and inst.x+sight == h: continue
            res_info.append(res_pad[w,h])

    for x in range(inst.x-sight,inst.x+sight+1):
        for y in range(inst.y-sight,inst.y+sight+1):
            if x == inst.x and y == inst.y: continue
            inp = False
            for enm in game.instances:
                if x == enm.x and y == enm.y:
                    enm_info.append(1.0-enm.hp/enm.hp_max)
                    inp = True; break
            if not inp:
                enm_info.append(1.0)
            if x<0 or x>=GAME_AREA_WIDTH or y<0 or y>=GAME_AREA_HEIGHT:
                wall_info.append(1)
            elif game.area_wall[y,x] == True:
                wall_info.append(1)
            else:
                wall_info.append(0)
    inst_info = [inst.x/GAME_AREA_WIDTH, inst.y/GAME_AREA_HEIGHT, inst.hp/inst.hp_max]

    return res_info + enm_info + wall_info + inst_info



def get_state_text(ind):
    if   ind==ACTION_IDLE: return "IDLE"
    elif ind==ACTION_MOVL: return "MOVL"
    elif ind==ACTION_MOVR: return "MOVR"
    elif ind==ACTION_MOVU: return "MOVU"
    elif ind==ACTION_MOVD: return "MOVD"

def get_grid_rectange (xloc,yloc,padding=0,
        cell_w=DRAW_CELL_WIDTH, cell_h=DRAW_CELL_HEIGHT):
    return [[(xloc+0)*cell_w+padding,(yloc+0)*cell_h+padding],
        [(xloc+1)*cell_w-padding,(yloc+0)*cell_h+padding],
        [(xloc+1)*cell_w-padding,(yloc+1)*cell_h-padding],
        [(xloc+0)*cell_w+padding,(yloc+1)*cell_h-padding]]
