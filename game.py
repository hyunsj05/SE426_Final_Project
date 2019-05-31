import pygame as pg
import numpy as np

import random

from config import *
from game_functions import *

import matplotlib.pyplot as plt
class Instance():
    def __init__(self, idx, initx, inity, controller = -1):
        self.idx = idx
        self.x = initx
        self.y = inity
        self.hp_history=[]
        self.attack_num=0
        self.hp = INSTANCE_HP_INITIAL
        self.hp_max = INSTANCE_HP_MAX
        self.hp_decay_mode = INSTANCE_DECAY_MODE
        self.hp_decay_value = INSTANCE_DECAY_VALUE

        self.dmg_base = INSTANCE_DAMAGE_BASE
        self.dmg_per_hp = INSTANCE_DAMAGE_PERCENT_HP
        self.dmg_per_reflect = INSTANCE_DAMAGE_PERCENT_REFLECT
        self.dmg_per_vampire = INSTANCE_DAMAGE_PERCENT_VAMPIRE

        # For calculating reward
        self.cal_dmg = 0

        # Stats
        self.survived_turn = 0
        # Reserved action
        self.action_rev = ACTION_IDLE

        # Controller - Negative value for manual control
        self.controller = controller

        self.printd("CREATED",1)

    def __del__(self):
        self.printd("DELETED: Survived %d turns"%(self.survived_turn),1)
    # Prints debug message
    def printd(self, msg = "", lv = 0):
        if DEBUG_INSTANCE == 0 or DEBUG_INSTANCE >= lv:
            print("Inst.%d: %s"%(self.idx,msg))

    # Check if it is alive
    def is_alive(self):
        return True if self.hp > 0 else False
    def is_dead(self):
        return False if self.hp > 0 else True

    def get_reward(self):
        rm = INSTANCE_REWARD_MODEL
        # ================================================
        # Add your custom reward function call here
        if rm == "basic":
            return instance_reward_model_basic(self)

        # ===============================================

    # Execute its turn
    def execute_turn(self, instances, area_resource, area_wall, area_dim):
        self.hp_history.append(self.hp)
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
            self.printd("MOVE CANCELLED by outer wall", 3)
        elif area_wall[target[1], target[0]] == True:
            isMoveAvailable = False
            self.printd("MOVE CANCELLED by inner wall", 3)

        # Object colliding
        else:
            for inst in instances:
                if inst.idx != self.idx and (inst.x == target[0] and inst.y == target[1]):
                    isMoveAvailable = False
                    isAttack = True
                    attackTarget = inst
                    self.printd("MOVE CANCELLED by other instance", 3)
                    break

        # Move to target position
        if isMoveAvailable:
            self.x = target[0]
            self.y = target[1]
        # Attack Enemy
        elif isAttack:
            self.attack_num+=1
            dmg = int(self.dmg_base + self.hp * self.dmg_per_hp)
            attackTarget.hp -= dmg
            self.hp -= int(dmg * attackTarget.dmg_per_reflect)
            # Vampire!
            attackTarget.hp -= int(dmg * self.dmg_per_vampire)
            self.hp -= int(dmg * self.dmg_per_vampire)
        self.health_check()

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



class Game():
    def __init__(self):
        # init pygame
        pg.init()
        # define game area
        self.size = [DRAW_CELL_WIDTH*GAME_AREA_WIDTH, DRAW_CELL_HEIGHT*GAME_AREA_HEIGHT+DRAW_CELL_HEIGHT]
        self.scr = pg.display.set_mode(self.size)
        self.g_w=round((GAME_INSTANCE_COUNT+2)/2)
        # set basic fonts
        self.f_big = pg.font.SysFont("comicsansms", DRAW_FONT_SIZE_BIG)
        self.f_small = pg.font.SysFont("comicsansms", DRAW_FONT_SIZE_SMALL)
        self.all_resource_history=[]
        pg.display.set_caption("Simulation")

        self.is_done = False
        self.turn_check = False
        self.clock = pg.time.Clock()
        self.automatic = TEST_AUTOMATIC

        self.area_resource = np.zeros((GAME_AREA_WIDTH,GAME_AREA_HEIGHT),dtype=int)
        self.area_wall = np.zeros((GAME_AREA_WIDTH,GAME_AREA_HEIGHT),dtype=bool)
        for i in range(GAME_AREA_WIDTH):
            for j in range(GAME_AREA_HEIGHT):
                self.area_wall[i,j] = False
        self.instances = list()
        self.total_instances = 0

        self.turn = 0
        self.player_idx = -1

        # Instance creation
        if GAME_PLAYER_ENABLE:
            inst = Instance(self.total_instances, 1, 1)
            self.total_instances += 1
            self.instances.append(inst)
            self.player_idx = 0

        controlidx = 0
        for instanceSpawnCounter in range(GAME_INSTANCE_COUNT-len(self.instances)):
            self.instance_create(controlidx)
            controlidx += 1
    # Prints debug message
    def printd(self, msg ="", lv = 0):
        if DEBUG_GAME == 0 or DEBUG_GAME >= lv:
            print("Game:",msg)

    # Instance creation
    def instance_create (self, controlidx):
        isSpawnPossible = False
        while (not isSpawnPossible):
            isSpawnPossible = True
            locx = random.randrange(GAME_AREA_WIDTH)
            locy = random.randrange(GAME_AREA_HEIGHT)
            # Check if instance collides
            for inst in self.instances:
                if inst.x == locx and inst.y == locy:
                    isSpawnPossible = False
                    break
        # Spawn instance
        inst = Instance(self.total_instances, locx, locy, controlidx)
        self.total_instances += 1
        self.instances.append(inst)
        self.printd("Instance %d Created. Ctrl: %d. Inst Count(Alive/Total): %d/%d"%(inst.idx,controlidx,len(self.instances),self.total_instances))
        return self.total_instances - 1


    def spawn_resources(self):
        rm = GAME_RESOURCE_METHOD
        # ================================================
        # Add your custom resource spawn function call here
        if rm == "basic":
            spawn_resources_basic(self)
        # ================================================


    def execute_turn(self, actions):
        self.printd("Turn %d: Initiated"%(self.turn),1)

        # Assign actions
        for ind, act in enumerate(actions):
            for inst in self.instances:
                if inst.controller == ind:
                    inst.action_rev = actions[ind]

        # Shuffle order
        self.printd("Turn %d: Order shuffled"%(self.turn),3)
        order = []
        for i in range(len(self.instances)):
            order.append(i)
        random.shuffle(order)

        # Execute instance turn
        self.printd("Turn %d: Execute instance turn"%(self.turn),3)
        for instidx in order:
            self.instances[instidx].execute_turn(self.instances, self.area_resource, self.area_wall, [GAME_AREA_WIDTH, GAME_AREA_HEIGHT])

        # Delete instances
        self.printd("Turn %d: Instance death"%(self.turn),3)
        instances_new = []
        for inst in self.instances:
            if inst.hp > 0: instances_new.append(inst)
            else:
                if inst.controller < 0: self.player_idx = -1
                del inst
        self.instances = instances_new

        # Spawn resources
        self.printd("Turn %d: Spawn Resources"%(self.turn),3)
        self.spawn_resources()

        # Cap resources
        for x in range(GAME_AREA_WIDTH):
            for y in range(GAME_AREA_HEIGHT):
                if self.area_resource[x,y] > GAME_RESOURCE_MAX:
                    self.area_resource[x,y] = GAME_RESOURCE_MAX;

        # Increase turn
        self.turn += 1
        all_resource=0
        for i in range(GAME_AREA_HEIGHT):
            for j in range(GAME_AREA_WIDTH):
                all_resource+=self.area_resource[i,j]
        self.all_resource_history.append(all_resource)
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

        return res_states, res_reward, res_is_dead

    def return_state(self, idx):
        inst = None
        for ind in self.instances:
            if ind.idx == idx:
                inst = ind; break
        if inst == None:
            print("ERROR: Game.return_state: Instance error: %d, returning list()"%idx)
            return list()
        rm = GAME_STATE_METHOD
        # ================================================
        # Add your custom state function call here
        if rm == "basic":
            return state_basic(self, inst)
        # ================================================

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
                    self.instances[self.player_idx].state_reserved = ACTION_IDLE
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_LEFT: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = ACTION_MOVL
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_RIGHT: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = ACTION_MOVR
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_UP: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = ACTION_MOVU
                self.turn_check = True
            if event.type == pg.KEYDOWN and event.key == pg.K_DOWN: # Temp
                if self.player_idx >= 0:
                    self.instances[self.player_idx].state_reserved = ACTION_MOVD
                self.turn_check = True
        self.scr.fill(DRAW_COL_WHITE)
        text = self.f_big.render("Turn:{}".format(self.turn), True, DRAW_COL_BLACK)
        self.scr.blit(text, (20,DRAW_CELL_HEIGHT*GAME_AREA_HEIGHT+10))

        # draw grid
        for xi,line in enumerate(self.area_resource):
            for yi, elem in enumerate(line):
                pg.draw.polygon(self.scr, DRAW_COL_BLACK, get_grid_rectange(yi,xi,0),4)
                text = self.f_big.render(str(self.area_resource[xi,yi]), True, DRAW_COL_GREEN)
                self.scr.blit(text, (yi*DRAW_CELL_WIDTH+5,xi*DRAW_CELL_HEIGHT+5))

        # draw instances
        for ii, inst in enumerate(self.instances):
            pg.draw.polygon(self.scr,DRAW_COL_RED,get_grid_rectange(inst.x,inst.y,3),3)
            text = self.f_small.render(get_state_text(inst.action_rev), True, DRAW_COL_BLUE)
            self.scr.blit(text, (inst.x*DRAW_CELL_WIDTH+20,inst.y*DRAW_CELL_HEIGHT+0))
            text = self.f_small.render(str(inst.hp), True, DRAW_COL_RED)
            self.scr.blit(text, (inst.x*DRAW_CELL_WIDTH+20,inst.y*DRAW_CELL_HEIGHT+10))
            text = self.f_small.render(str(inst.x)+","+str(inst.y), True, DRAW_COL_RED)
            self.scr.blit(text, (inst.x*DRAW_CELL_WIDTH+20,inst.y*DRAW_CELL_HEIGHT+20))
            text = self.f_small.render(str(inst.controller), True, DRAW_COL_RED)
            self.scr.blit(text, (inst.x*DRAW_CELL_WIDTH+20,inst.y*DRAW_CELL_HEIGHT+30))
        if (self.turn%GRID_GRAPH_TURN)==0:
            plt.clf()
            plt.subplots_adjust(hspace = 2, wspace = 0.6)
            attack_list=[]
            xlabel=[]
            for i in range(len(self.instances)):
                plt.subplot(self.g_w,2,i+1)
                plt.xlabel("live turn: %s"%len(self.instances[i].hp_history))
                plt.ylabel("hp")
                plt.title("%d"%self.instances[i].idx)
                plt.ylim(0, 100)
                plt.plot(range(len(self.instances[i].hp_history)),self.instances[i].hp_history)
                attack_list.append(self.instances[i].attack_num/len(self.instances[i].hp_history))
                xlabel.append(self.instances[i].idx)
            plt.subplot(self.g_w, 2, self.g_w*2-1)
            plt.bar(range(len(attack_list)),attack_list)
            plt.xticks(range(len(attack_list)),xlabel)
            plt.title("aggression")
            plt.subplot(self.g_w, 2, self.g_w*2)
            plt.plot(range(self.turn), self.all_resource_history)
            plt.title("all_resource_graph")
            plt.xlabel("turn")
            plt.show(block=False)
            plt.pause(0.0000001)
        pg.display.flip()
