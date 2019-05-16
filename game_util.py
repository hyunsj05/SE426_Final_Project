
from config import *

def get_state_text(ind):
    if   ind==STATE_IDLE: return "IDLE"
    elif ind==STATE_MOVL: return "MOVL"
    elif ind==STATE_MOVR: return "MOVR"
    elif ind==STATE_MOVU: return "MOVU"
    elif ind==STATE_MOVD: return "MOVD"
    # elif ind==STATE_ATKL: return "ATKL"
    # elif ind==STATE_ATKR: return "ATKR"
    # elif ind==STATE_ATKU: return "ATKU"
    # elif ind==STATE_ATKD: return "ATKD"

def get_grid_rectange (xloc,yloc,padding=0,cell_w=CONFIG_CELL_W, cell_h=CONFIG_CELL_H):
    return [[(xloc+0)*cell_w+padding,(yloc+0)*cell_h+padding],
        [(xloc+1)*cell_w-padding,(yloc+0)*cell_h+padding],
        [(xloc+1)*cell_w-padding,(yloc+1)*cell_h-padding],
        [(xloc+0)*cell_w+padding,(yloc+1)*cell_h-padding]]