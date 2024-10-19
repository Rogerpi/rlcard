''' Wrrapers of pretrained models.
'''
import os

import rlcard
from rlcard.agents import DQNAgent
from rlcard.models.model import Model
import torch

# Root path of pretrianed models

class ButifarraDQNModel(Model):
    ''' A pretrained model on Leduc Holdem with CFR (chance sampling)
    '''
    def __init__(self):
        ''' Load pretrained model
        '''
        env = rlcard.make('butifarra')
        model_path = "/home/roger/libraries/butifarra/rlcard/experiments/butifarra-newstate/checkpoint_dqn.pt"
        self.agent = DQNAgent.from_checkpoint(checkpoint=torch.load(model_path))
    @property
    def agents(self):
        ''' Get a list of agents for each position in a the game

        Returns:
            agents (list): A list of agents

        Note: Each agent should be just like RL agent with step and eval_step
              functioning well.
        '''
        return [self.agent, self.agent, self.agent, self.agent]

