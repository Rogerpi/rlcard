from rlcard.games.butifarra.utils.print_card import print_cards
from rlcard.games.butifarra.utils.butifarra_card import ButifarraCard
from rlcard.games.butifarra.utils.action_event import ActionEvent, CantarAction

class HumanAgent(object):
    ''' A human agent for Leduc Holdem. It can be used to play against trained models
    '''

    def __init__(self, num_actions):
        ''' Initilize the human agent

        Args:
            num_actions (int): the size of the ouput action space
        '''
        self.use_raw = False
        self.num_actions = num_actions

        print("puta espanya")

    @staticmethod
    def step(state):
        ''' Human agent will display the state and make decisions through interfaces

        Args:
            state (dict): A dictionary that represents the current state

        Returns:
            action (int): The action decided by human
        '''
        _print_state(state)
        action = int(input('>> You choose action (integer): '))
        while action < 0 or action >= len(state['legal_actions']):
            print('Action illegal...')
            action = int(input('>> Re-choose action (integer): '))
        return state['raw_legal_actions'][action]

    def eval_step(self, state):
        ''' Predict the action given the curent state for evaluation. The same to step here.

        Args:
            state (numpy.array): an numpy array that represents the current state

        Returns:
            action (int): the action predicted (randomly chosen) by the random agent
        '''
        return self.step(state), {}

def _print_state(state):
    ''' Print out the state of a given player

    Args:
        player (int): Player id
    '''
    print('\n================== INFO =================')
    trumfo_rep = state['obs'][-9:-4]
    trumfo_list = [ActionEvent.from_action_id(i+1) for i, x in enumerate(trumfo_rep) if x == 1]
    trumfo = trumfo_list[0] if len(trumfo_list)==1 else None

    if trumfo is not None:
            print(f'Trumfo {trumfo}')


    print('\n=============== Your Hand ===============')
    hand_rep = state['obs'][0:48]
    hand = [ButifarraCard.card(i) for i, x in enumerate(hand_rep) if x == 1]
    #print(hand)
    print_cards(hand)
    print('\n')
    print('======== Actions You Can Choose =========')
    #print(state['legal_actions'])
    for i, action in enumerate(state['legal_actions']):
        print(str(i)+': ', end='')
        print(ActionEvent.from_action_id(action))
        if i < len(state['legal_actions']) - 1:
            print(', ', end='')
    print('\n')

def _print_action(action):
    ''' Print out an action in a nice form

    Args:
        action (str): A string a action
    '''
    print(ActionEvent.from_action_id(action))
