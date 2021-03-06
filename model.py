# Model.py
# Containing deep-learning agent code

# Source from https://github.com/keon/3-min-pytorch/blob/master/10-DQN-Learns-From-Environment/01-cartpole-dqn.py
# Essentials
import random, math
import numpy as np

# Importing torch
import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
import torch.nn.functional as F
# Import deque for memory
from collections import deque

class Agent:
    def __init__(self, 
            idx, inst_assigned, is_available, is_revivable, cooltime_base, 
            in_channel, hid_channel, out_channel,
            memory_length,
            eps_start, eps_end, eps_decay, gamma, lr, batch_size):
        self.model = nn.Sequential(
                nn.Linear(in_channel, hid_channel),
                nn.ReLU(),
                nn.Linear(hid_channel, hid_channel),
                nn.ReLU(),
                nn.Linear(hid_channel, out_channel)
        )
        self.memory = deque(maxlen=memory_length)
        self.optimizer = optim.Adam(self.model.parameters(), lr)
        self.steps_done = 0

        self.idx = idx
        self.inst_assigned = inst_assigned
        self.is_available = is_available
        self.is_revivable = is_revivable
        self.cooltime_base = cooltime_base
        self.cooltime = self.cooltime_base
        self.num_actions = out_channel

        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.gamma = gamma
        self.lr = lr
        self.batch_size = batch_size

    def act(self, state):
        eps_threshold = self.eps_end + (self.eps_start - self.eps_end)* math.exp(-1. * self.steps_done / self.eps_decay)
        self.steps_done += 1
        if random.random() > eps_threshold:
            return self.model(state).data.max(1)[1].view(1, 1)
        else:
            return torch.LongTensor([[random.randrange(self.num_actions)]])

    def memorize(self, state, action, reward, next_state):
        self.memory.append((state, action, torch.FloatTensor([reward]), torch.FloatTensor([next_state])))

    def learn(self):
        if len(self.memory) < self.batch_size:
            return None
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states = zip(*batch)

        states = torch.cat(states)
        actions = torch.cat(actions)
        rewards = torch.cat(rewards)
        next_states = torch.cat(next_states)

        current_q = self.model(states).gather(1, actions)
        max_next_q = self.model(next_states).detach().max(1)[0]
        expected_q = rewards + (self.gamma * max_next_q)

        loss = F.mse_loss (current_q.squeeze(), expected_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
