import game

from config import *
from model import *

if __name__ == "__main__":
    print("="*50)
    print("Debug message level")
    if CONFIG_DEBUG_MAIN >= 0:
        print("    Global:", CONFIG_DEBUG_MAIN)
    if CONFIG_DEBUG_GAME >= 0:
        print("    Game:", CONFIG_DEBUG_GAME)
    if CONFIG_DEBUG_INSTANCE >= 0:
        print("    Instance:", CONFIG_DEBUG_INSTANCE)
    print("="*50)
    print_config()
    print("="*50)
    # statstics
    STAT_TURN = 0

    # game initialize
    g = game.Game()

    # Temp agent
    agents = list()
    pl_count = 1 if CONFIG_PLAYER_ENABLE else 0
    cpu_count = CONFIG_INSTANCE_COUNT - pl_count
    for ind in range(cpu_count):
        agent = Agent(ind, ind+pl_count, True, True, 10, len(g.return_state(0)), 256, 5)
        agents.append(agent)
        
    # instance linking
    for inst in g.instances:
        inst.controller = inst.idx - pl_count
        print("Main: Agent %d linked to Inst %d"%(inst.controller, inst.idx))
    
    # Main loop
    while not g.is_done:
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
                    print("Main: Agent %d linked to Inst %d"%(ag.idx, idx))

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
                    print("Main: agent %d disconnected from Inst %d"%(ag.idx, ag.inst_assigned))
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

        g.clock.tick(60) #If simualtion is slow, touch this maybe...
        g.draw()

