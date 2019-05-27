import game

from config import *
from model import *

def print_config():
    print("="*50)
    print("Debug message level")
    print("    Main: %s"%(str(DEBUG_MAIN) if DEBUG_MAIN>=0 else "Off"))
    print("    Game: %s"%(str(DEBUG_GAME) if DEBUG_GAME>=0 else "Off"))
    print("    Inst: %s"%(str(DEBUG_INSTANCE) if DEBUG_INSTANCE>=0 else "Off"))
    print("="*50)
    print("Experiment Setup")
    print("="*50)
    print("="*50)

    print("="*50)
    print("Agent Setup")
    print("    Hidden Channel: %d, Batch size: %d"%(AGENT_HIDDEN_CHANNEL, AGENT_BATCH_SIZE))
    print("    Memory Length: %d"%(AGENT_MEMORY_LENGTH))
    print("    Is revivable?: %r, Revive cooltime: %d"%(AGENT_IS_REVIVABLE, AGENT_BASE_COOLTIME))
    print("    EPS start/end/decay: %f, %f, %f"%(AGENT_EPS_START, AGENT_EPS_END, AGENT_EPS_DECAY))
    print("    Gamma: %f, LR: %f"%(AGENT_GAMMA, AGENT_LR))
    print("="*50)

def printdm(msg ="", lv = 1):
    if DEBUG_MAIN == 0 or DEBUG_MAIN >= lv:
        print("Main:",msg)

if __name__ == "__main__":
    print_config()
    # statstics
    STAT_TURN = 0

    # game initialize
    g = game.Game()
    printdm("Game Initiated",1)

    # Temp agent
    agents = list()
    pl_count = 1 if GAME_PLAYER_ENABLE else 0
    cpu_count = GAME_INSTANCE_COUNT - pl_count
    for ind in range(cpu_count):
        agent = Agent(ind, ind+pl_count, True, AGENT_IS_REVIVABLE, AGENT_BASE_COOLTIME,
                len(g.return_state(0)), AGENT_HIDDEN_CHANNEL, ACTION_COUNT,
                AGENT_MEMORY_LENGTH,
                AGENT_EPS_START, AGENT_EPS_END, AGENT_EPS_DECAY, AGENT_GAMMA, AGENT_LR, AGENT_BATCH_SIZE)
        agents.append(agent)
    printdm("%d Agent Created"%len(agents),1)

    # instance linking
    for inst in g.instances:
        inst.controller = inst.idx - pl_count
        printdm("Agent %d linked to Inst %d"%(inst.controller, inst.idx))

    # Main loop
    while not g.is_done:
        if g.automatic:
            g.turn_check = True
        if g.turn_check:
            # Decrease cooltime
            for ag in agents:
                if ag.cooltime > 0:
                    ag.cooltime -= 1
                if ag.cooltime <= 0 and not ag.is_available:
                    # create instance and connect
                    ag.cooltime = 0
                    ag.is_available = True
                    idx = g.instance_create(ag.idx)
                    ag.inst_assigned = idx
                    printdm("Agent %d linked to Inst %d"%(ag.idx, idx))

            actions = list()
            states = list()
            for ind, ag in enumerate(agents):
                # Change ind to better
                if ag.is_available:
                    state = torch.FloatTensor([g.return_state(agents[ind].inst_assigned)])
                    states.append(state)
                    actions.append(ag.act(state))
                else:
                    states.append(torch.FloatTensor([0]))
                    actions.append(-1)


            # print(actions[0])
            # Should be changed
            next_states, rewards, is_deads = g.execute_turn(actions)

            # Training
            for ind, ag in enumerate(agents):
                if is_deads[ind] and ag.is_available == True:
                    printdm("Agent %d disconnected from Inst %d"%(ag.idx, ag.inst_assigned))
                    ag.inst_assigned = -1
                    ag.is_available = False
                    if ag.is_revivable:
                        ag.cooltime = ag.cooltime_base
                if ag.is_available:
                    ag.memorize(states[ind], actions[ind], rewards[ind], next_states[ind])
                    ag.learn()
                    # Handle dead things

            # state = next_states[0]
            STAT_TURN += 1
            if MAIN_PRINT_TURN_FREQUENCY >= 0 and STAT_TURN%MAIN_PRINT_TURN_FREQUENCY == 0:
                printdm("Turn %d Passed"%STAT_TURN)
            if STAT_TURN >= TEST_TURN_LENGTH:
                g.is_done = True

        g.clock.tick(TEST_STEP_PER_SECOND)
        g.draw()

    printdm("Ending the simulation")
