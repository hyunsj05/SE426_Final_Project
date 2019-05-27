

# Source from https://github.com/keon/3-min-pytorch/blob/master/10-DQN-Learns-From-Environment/01-cartpole-dqn.py
import random, math

import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
import torch.nn.functional as F
import numpy as np
# Import deque for learning
from collections import deque

EPISODES = 50
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 200
GAMMA = 0.8
LR = 0.001
BATCH_SIZE = 32


class Agent:
    def __init__(self, idx, inst_assigned, is_available, is_revivable,cooltime_base, in_channel, hid_channel, out_channel):
        self.model = nn.Sequential(
                nn.Linear(in_channel, hid_channel),
                nn.ReLU(),
                nn.Linear(hid_channel, hid_channel),
                nn.ReLU(),
                nn.Linear(hid_channel, out_channel)
        )
        self.num_states = out_channel
        self.memory = deque(maxlen=10000)
        self.optimizer = optim.Adam(self.model.parameters(), LR)
        self.steps_done = 0

        self.idx = idx
        self.inst_assigned = inst_assigned
        self.is_available = is_available
        self.is_revivable = is_revivable
        self.cooltime_base = cooltime_base
        self.cooltime = self.cooltime_base

    def act(self, state):
        eps_threshold = EPS_END + (EPS_START - EPS_END)* math.exp(-1. * self.steps_done / EPS_DECAY)
        self.steps_done += 1
        if random.random() > eps_threshold:
            return self.model(state).data.max(1)[1].view(1, 1)
        else:
            return torch.LongTensor([[random.randrange(self.num_states)]])

    def memorize(self, state, action, reward, next_state):
        self.memory.append((state, action, torch.FloatTensor([reward]), torch.FloatTensor([next_state])))

    def learn(self):
        if len(self.memory) < BATCH_SIZE:
            return None
        batch = random.sample(self.memory, BATCH_SIZE)
        states, actions, rewards, next_states = zip(*batch)

        states = torch.cat(states)
        actions = torch.cat(actions)
        rewards = torch.cat(rewards)
        next_states = torch.cat(next_states)

        current_q = self.model(states).gather(1, actions)
        max_next_q = self.model(next_states).detach().max(1)[0]
        expected_q = rewards + (GAMMA * max_next_q)

        loss = F.mse_loss (current_q.squeeze(), expected_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
