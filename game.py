
import pygame as pg
import numpy as np

import random

from game_util import *
from config import *


class Instance():
    def __init__(self, idx, initx, inity, controller = -1):
        self.idx = idx
        self.x = initx
        self.y = inity
        
        self.hp = CONFIG_HP_INITIAL
        self.hp_max = CONFIG_HP_MAX
        self.hp_decay_mode = CONFIG_HP_DECAY_MODE
        self.hp_decay_value = CONFIG_HP_DECAY_VALUE

        self.dmg_base = CONFIG_DMG_BASE
        self.dmg_coef_hp = CONFIG_DMG_COEF_HP
        self.dmg_coef_reflect = CONFIG_DMG_COEF_REFLECT
        
        self.cal_dmg = 0

        self.action_rev = ACTION_IDLE
        
        self.survived_turn = 0

        self.controller = controller # negative value for manual controll
        self.print_message("CREATED",1)
        self.print_info(mode = 0)
    
    def __del__(self):
        self.print_message("DELETED: Survived %d turns"%(self.survived_turn),1)

    # Check if it is alive
    def is_alive(self):
        return True if self.hp > 0 else False
    def is_dead(self):
        return False if self.hp > 0 else True
    
    def get_reward(self):
        # Simple model
        if self.is_dead():
            return -100
        res = 0
        res += self.cal_dmg/10
        self.cal_dmg = 0
        res += self.hp/self.hp_max
        return res

    # Prints basic information about instance
    def print_info(self, mode = 0):
        if mode == 0:
            print("    idx:%d, Controller:%d"%(self.idx, self.controller))
            print("    hp:%5d/%5d, dmg:%5d,%1.3f,%1.3f"%(self.hp, self.hp_max, self.dmg_base, self.dmg_coef_hp, self.dmg_coef_reflect))

    # Prints debug message
    def print_message(self, msg = "", lv = 0):
        if CONFIG_DEBUG_INSTANCE == 0 or CONFIG_DEBUG_INSTANCE >= lv:
            print("Inst.%d: %s"%(self.idx,msg))

    # Execute its turn
    def execute_turn(self, instances, area_resource, area_dim):
        if not self.is_alive():
            return None
        
        self.survived_turn += 1

        # Move or attack
        isMoveAvailable = True
        isAttack = False
        attackTarget = None
        if   self.action_rev == ACTION_MOVL: target = (self.x-1,self.y  )
        elif self.action_rev == ACTION_MOVR: target = (self.x+1,self.y  )
        elif self.action_rev == ACTION_MOVU: target = (self.x  ,self.y-1)
        elif self.action_rev == ACTION_MOVD: target = (self.x  ,self.y+1)
        else:                                   target = (self.x  ,self.y  )

        # Wall checking
        if target[0] < 0 or target[0] >= area_dim[0] or target[1] < 0 or target[1] >= area_dim[1]:
            isMoveAvailable = False
            self.print_message("MOVE CANCELLED by WALL", 3)
        # Object colliding
        else:
            for inst in instances:
                if inst.idx != self.idx and (inst.x == target[0] and inst.y == target[1]):
                    isMoveAvailable = False
                    isAttack = True
                    attackTarget = inst
                    self.print_message("MOVE CANCELLED by OBJ", 3)
                    break
        
        # Move to target position
        if isMoveAvailable:
            self.x = target[0]
            self.y = target[1]
        # Attack Enemy
        elif isAttack:
            attackTarget.hp -= int(self.hp*self.dmg_coef_hp)
            self.hp -= int(attackTarget.hp*self.dmg_coef_hp*self.dmg_coef_reflect)
        
        if not self.is_alive():
            return None
        
        # Gain resource
        self.hp+=area_resource[self.y,self.x]
        area_resource[self.y,self.x] = 0
        self.health_check()

        # Decay health
        if self.hp_decay_mode == 0:
            self.hp -= self.hp_decay_value
        self.health_check()

    # Cap health
    def health_check(self):
        if self.hp > self.hp_max:
            self.hp = self.hp_max
        elif self.hp <= 0:
            self.hp = 0 # Death


def print_debug_main(msg ="", lv = 0):
    if CONFIG_DEBUG_GAME == 0 or CONFIG_DEBUG_GAME >= lv:
        print("Game:",msg)

class Game():
    def __init__(self):
        # init pygame
        pg.init()
        
        self.area_w = CONFIG_AREA_W
        self.area_h = CONFIG_AREA_H
        self.cell_w = CONFIG_CELL_W
        self.cell_h = CONFIG_CELL_H 
        
        # define game area
        self.size = [self.cell_w*self.area_w, self.cell_h*self.area_h+self.cell_h]
        self.scr = pg.display.set_mode(self.size)

        # set basic fonts
        self.f_b20 = pg.font.SysFont("comicsansms", 20)
        self.f_b12 = pg.font.SysFont("comicsansms", 12)

        pg.display.set_caption("Simulation")

        self.is_done = False
        self.turn_check = False
        self.clock = pg.time.Clock()
        
        self.area_resource = np.zeros((self.area_w,self.area_h),dtype=int)
        self.instances = list()
        self.total_instances = 0

        self.turn = 0
        self.player_idx = -1

        # Instance creation
        if CONFIG_PLAYER_ENABLE:
            inst = Instance(self.total_instances, 1, 1)
            self.total_instances += 1
            self.instances.append(inst)
            self.player_idx = 0

        controlidx = 0
        for instanceSpawnCounter in range(CONFIG_INSTANCE_COUNT-len(self.instances)):
            self.instance_create(controlidx)
            controlidx += 1

    def instance_create (self, controlidx):
        isSpawnPossible = False
        while (not isSpawnPossible):
            isSpawnPossible = True
            locx = random.randrange(self.area_w)
            locy = random.randrange(self.area_h)
            # Check if instance collides
            for inst in self.instances:
                if inst.x == locx and inst.y == locy:
                    isSpawnPossible = False
                    break
        # Spawn instance
        inst = Instance(self.total_instances, locx, locy, controlidx)
        self.total_instances += 1
        self.instances.append(inst)
        return self.total_instances - 1

    def spawn_resource_basic(self):
        for x in range(self.area_w):
            for y in range(self.area_h):
                if np.random.rand()<CONFIG_RESOURCE_SPAWN_RATE:
                    self.area_resource[x,y] += 1

    def execute_turn(self, actions):  
        print_debug_main("Turn %d: Initiated"%(self.turn),1)
        
        # Assign actions
        for ind, act in enumerate(actions):
            for inst in self.instances:
                if inst.controller == ind:
                    inst.action_rev = actions[ind]

        # Shuffle order
        print_debug_main("Turn %d: Order shuffled"%(self.turn),3)
        order = []
        for i in range(len(self.instances)):
            order.append(i)
        random.shuffle(order)
        
        # Execute instance turn
        print_debug_main("Turn %d: Execute instance turn"%(self.turn),3)
        for instidx in order:
            self.instances[instidx].execute_turn(self.instances, self.area_resource, [self.area_w, self.area_h])
        
        # Delete instances
        print_debug_main("Turn %d: Instance death"%(self.turn),3)
        instances_new = []
        for inst in self.instances:
            if inst.hp > 0: instances_new.append(inst)
            else:
                if inst.controller < 0: self.player_idx = -1
                del inst
        self.instances = instances_new

        # Spawn resources
        print_debug_main("Turn %d: Spawn Resources"%(self.turn),3)
        if CONFIG_RESOURCE_SPAWN_METHOD == 0:
            self.spawn_resource_basic()
        
        # Cap resources
        for x in range(self.area_w):
            for y in range(self.area_h):
                if self.area_resource[x,y] > CONFIG_RESOURCE_MAX:
                    self.area_resource[x,y] = CONFIG_RESOURCE_MAX;
        
        # Increase turn
        self.turn += 1
        
        # return next states - need to think about instance count
        res_reward = list()
        res_is_dead = list()
        res_states = list()
        for ind in range(len(actions)):
            is_enrolled = False
            for inst in self.instances:
                if inst.controller == ind:
                    res_states.append(self.return_state(inst.idx))
                    res_reward.append(inst.get_reward())
                    res_is_dead.append((not inst.is_alive()))
                    is_enrolled = True
                    break
            if not is_enrolled:
                res_states.append(list())
                res_reward.append(list())
                res_is_dead.append(True)
        
        # print(res_states)
        # print(res_reward)
        # print(res_is_dead)
        return res_states, res_reward, res_is_dead

    def return_state(self, idx):
        if idx == -1: # return all states
            res = list()
            for inst in self.instances:
                res.append(self.return_state(inst.idx))
            return res
        # return one instance
        inst = None
        for ind in self.instances:
            if ind.idx == idx:
                inst = ind; break
        if inst == None:
            print("Game: return_state: Instance error: %d"%idx)
            return list()
        sight = 2
        res_pad = np.zeros((self.area_w+2*sight, self.area_h+2*sight))
        for w in range(self.area_w):
            for h in range(self.area_h):
                res_pad[sight+w,sight+h] = self.area_resource[w,h]/CONFIG_RESOURCE_MAX

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
                for enm in self.instances:
                    if x == enm.x and y == enm.y:
                        enm_info.append(1.0-enm.hp/enm.hp_max)
                        inp = True; break
                if not inp:
                    enm_info.append(1.0)
                if x<0 or x>self.area_w or y<0 or y>self.area_h:
                    wall_info.append(1)
                else:
                    wall_info.append(0)
        inst_info = [inst.x/self.area_w, inst.y/self.area_h, inst.hp/inst.hp_max]

        return res_info + enm_info + inst_info

    def draw(self):
        self.turn_check = False
        # keydown event handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.is_done = True
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.is_done = True
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = STATE_IDLE
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_LEFT: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = STATE_MOVL
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_RIGHT: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = STATE_MOVR
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_UP: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = STATE_MOVU
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_DOWN: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = STATE_MOVD
                self.turn_check = True
        self.scr.fill(COL_WHITE)
        text = self.f_b20.render("Turn:{}".format(self.turn), True, COL_BLACK)
        self.scr.blit(text, (20,self.cell_h*self.area_h+10))
        
        # draw grid
        for xi,line in enumerate(self.area_resource):
            for yi, elem in enumerate(line):
                pg.draw.polygon(self.scr, COL_BLACK, get_grid_rectange(yi,xi,0),4)
                text = self.f_b20.render(str(self.area_resource[xi,yi]), True, COL_GREEN)
                self.scr.blit(text, (yi*self.cell_w+5,xi*self.cell_h+5))
                
        # draw instances
        for ii, inst in enumerate(self.instances):
            pg.draw.polygon(self.scr,COL_RED,get_grid_rectange(inst.x,inst.y,3),3)
            text = self.f_b12.render(get_state_text(inst.action_rev), True, COL_BLUE)
            self.scr.blit(text, (inst.x*self.cell_w+20,inst.y*self.cell_h+0))
            text = self.f_b12.render(str(inst.hp), True, COL_RED)
            self.scr.blit(text, (inst.x*self.cell_w+20,inst.y*self.cell_h+10))
            text = self.f_b12.render(str(inst.x)+","+str(inst.y), True, COL_RED)
            self.scr.blit(text, (inst.x*self.cell_w+20,inst.y*self.cell_h+20))
            text = self.f_b12.render(str(inst.controller), True, COL_RED)
            self.scr.blit(text, (inst.x*self.cell_w+20,inst.y*self.cell_h+30))
        
        pg.display.flip()
        


