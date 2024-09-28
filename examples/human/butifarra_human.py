''' A toy example of playing against rule-based bot on UNO
'''

import rlcard
from rlcard import models
from rlcard.agents.human_agents.butifarra_human_agent import HumanAgent, _print_action

from rlcard.utils import (
    get_device
)
import torch
        
# Make environment
model_path = "experiments/butifarra-amics/agent1/model.pth"
env = rlcard.make('butifarra')
human_agent = HumanAgent(env.num_actions)

m1 = torch.load(model_path, map_location=get_device())
m1.set_device(get_device())

m2 = torch.load(model_path, map_location=get_device())
m2.set_device(get_device())

m3 = torch.load(model_path, map_location=get_device())
m3.set_device(get_device())


env.set_agents([
    m1,
    m2,
    human_agent,
    m3
])

print(">> Buti!")

while (True):
    print(">> Start a new game")

    trajectories, payoffs = env.run(is_training=False)
    # If the human does not take the final action, we need to
    # print other players action


    print('===============     Result     ===============')
    if payoffs[0] > 0:
        print('You win!')
    else:
        print('You lose!')

    print(payoffs)
    print('')
    input("Press any key to continue...")
