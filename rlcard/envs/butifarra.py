'''
    File name: envs/butifarra.py
    Author: William Hale
    Date created: 11/26/2021
'''

import numpy as np
from collections import OrderedDict

from rlcard.envs import Env

from rlcard.games.butifarra import Game

from rlcard.games.butifarra.game import ButifarraGame
from rlcard.games.butifarra.utils.action_event import ActionEvent
from rlcard.games.butifarra.utils.butifarra_card import ButifarraCard
from rlcard.games.butifarra.utils.move import CallMove, PlayCardMove

#   [] Why no_bid_action_id in bidding_rep ?
#       It allows the bidding always to start with North.
#       If North is not the dealer, then he must call 'no_bid'.
#       Until the dealer is reached, 'no_bid' must be the call.
#       I think this might help because it keeps a player's bid in a fixed 'column'.
#       Note: the 'no_bid' is only inserted in the bidding_rep, not in the actual game.
#
#   [] Why current_player_rep ?
#       Explanation here.
#
#   [] Note: hands_rep maintain the hands by N, E, S, W.
#
#   [] Note: trick_rep maintains the trick cards by N, E, S, W.
#      The trick leader can be deduced since play is in clockwise direction.
#
#   [] Note: is_bidding_rep can be deduced from bidding_rep.
#      I think I added is_bidding_rep before bidding_rep and thus it helped in early testing.
#      My early testing had just the player's hand: I think the model conflated the bidding phase with the playing phase in this situation.
#      Although is_bidding_rep is not needed, keeping it may improve learning.
#
#   [] Note: bidding_rep uses the action_id instead of one hot encoding.
#      I think one hot encoding would make the input dimension significantly larger.
#


class ButifarraEnv(Env):
    ''' Butifarra Environment
    '''
    def __init__(self, config):
        self.name = 'butifarra'
        self.game = Game()
        super().__init__(config=config)
        self.butifarraPayoffDelegate = DefaultButifarraPayoffDelegate()
        self.butifarraStateExtractor = DefaultButifarraStateExtractor()
        state_shape_size = self.butifarraStateExtractor.get_state_shape_size()
        self.state_shape = [[1, state_shape_size] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def get_payoffs(self):
        ''' Get the payoffs of players.

        Returns:
            (list): A list of payoffs for each player.
        '''
        return self.butifarraPayoffDelegate.get_payoffs(game=self.game)

    def get_perfect_information(self):
        ''' Get the perfect information of the current state

        Returns:
            (dict): A dictionary of all the perfect information of the current state
        '''
        return self.game.round.get_perfect_information()

    def _extract_state(self, state):  # wch: don't use state 211126
        ''' Extract useful information from state for RL.

        Args:
            state (dict): The raw state

        Returns:
            (numpy.array): The extracted state
        '''
        return self.butifarraStateExtractor.extract_state(game=self.game)

    def _decode_action(self, action_id):
        ''' Decode Action id to the action in the game.

        Args:
            action_id (int): The id of the action

        Returns:
            (ActionEvent): The action that will be passed to the game engine.
        '''
        return ActionEvent.from_action_id(action_id=action_id)

    def _get_legal_actions(self):
        ''' Get all legal actions for current state.

        Returns:
            (list): A list of legal actions' id.
        '''
        raise NotImplementedError  # wch: not needed


class ButifarraPayoffDelegate(object):

    def get_payoffs(self, game: ButifarraGame):
        ''' Get the payoffs of players. Must be implemented in the child class.

        Returns:
            (list): A list of payoffs for each player.

        Note: Must be implemented in the child class.
        '''
        raise NotImplementedError


class DefaultButifarraPayoffDelegate(ButifarraPayoffDelegate):

    def __init__(self):
        pass

    def get_payoffs(self, game: ButifarraGame):
        ''' Get the payoffs of players.

        Returns:
            (list): A list of payoffs for each player.
        '''
        cantar_move = game.round.cantar_move
        if cantar_move:
            declarer = cantar_move.player
            won_bases_counts = game.round.won_bases_counts
            won_cards = game.round.won_cards
            declarer_won_bases_count = won_bases_counts[declarer.player_id % 2]
            defender_won_bases_count = won_bases_counts[(declarer.player_id + 1) % 2]
            declarer_valor_bases = sum([x.get_valor() for x in won_cards[declarer.player_id % 2]])
            defender_valor_bases = sum([x.get_valor() for x in won_cards[(declarer.player_id +1 )% 2]])

            declarer_punts = (declarer_valor_bases + declarer_won_bases_count) - 36
            defender_punts = (defender_valor_bases + defender_won_bases_count) - 36
            
            multiplicador = game.round.doubling_cube
            if game.round.is_butifarra:
                multiplicador *= 2
            declarer_payoff = declarer_punts * multiplicador
            defender_payoff = defender_punts * multiplicador

            payoffs = []
            for player_id in range(4):
                payoff = declarer_payoff if player_id % 2 == declarer.player_id % 2 else defender_payoff
                payoffs.append(payoff)
        else:
            payoffs = [0, 0, 0, 0]
        return np.array(payoffs)


class ButifarraStateExtractor(object):  # interface

    def get_state_shape_size(self) -> int:
        raise NotImplementedError

    def extract_state(self, game: ButifarraGame):
        ''' Extract useful information from state for RL. Must be implemented in the child class.

        Args:
            game (ButifarraGame): The game

        Returns:
            (numpy.array): The extracted state
        '''
        raise NotImplementedError

    @staticmethod
    def get_legal_actions(game: ButifarraGame):
        ''' Get all legal actions for current state.

        Returns:
            (OrderedDict): A OrderedDict of legal actions' id.
        '''
        legal_actions = game.judger.get_legal_actions()
        legal_actions_ids = {action_event.action_id: None for action_event in legal_actions}
        return OrderedDict(legal_actions_ids)


class DefaultButifarraStateExtractor(ButifarraStateExtractor):

    def __init__(self):
        super().__init__()

    def get_state_shape_size(self) -> int:
        state_shape_size = 0
        state_shape_size +=  48  # hand_rep
        state_shape_size += 4 * 48  # bases_rep
        #state_shape_size += 48  # hidden_cards_rep_
        state_shape_size += 4  # delegar_rep
        state_shape_size += 4  # cantar_rep
        state_shape_size += 5  # trumfo
        state_shape_size += 3  # contrar, recontrar, stvicenç
        state_shape_size += 1  #cantant
        state_shape_size += 4 # current player

        return state_shape_size

    def extract_state(self, game: ButifarraGame):
        ''' Extract useful information from state for RL.

        Args:
            game (ButifarraGame): The game

        Returns:
            (numpy.array): The extracted state
        '''
        extracted_state = {}
        legal_actions: OrderedDict = self.get_legal_actions(game=game)
        raw_legal_actions = list(legal_actions.keys())
        current_player = game.round.get_current_player()
        current_player_id = current_player.player_id

        # construct hands_rep of hands of players
        hand_rep = np.zeros(48, dtype=int)
        if not game.is_over():
            for card in game.round.players[current_player_id].hand:
                hand_rep[card.card_id] = 1

        # construct trick_pile_rep
        bases_pila = [np.zeros(48, dtype=int) for _ in range(4)]
        if game.round.is_bidding_over() and not game.is_over():
            trick_moves = game.round.get_bases_moves()
            for move in trick_moves:
                player = move.player
                card = move.card
                bases_pila[player.player_id][card.card_id] = 1

        # construct current_player_rep
        current_player_rep = np.zeros(4, dtype=int)
        current_player_rep[current_player_id] = 1

        # construct is_bidding_rep
        is_bidding_rep = np.array([1] if game.round.is_bidding_over() else [0])

        delegar_rep = np.zeros(4, dtype=int)
        if not game.is_over() and game.round.delegar_move is not None:
            delegar_rep[game.round.delegar_move.player.player_id] = 1
        
        cantar_rep = np.zeros(4, dtype=int)
        if  not game.is_over() and game.round.cantar_move is not None:
            cantar_rep[game.round.cantar_move.player.player_id] = 1

        multiplicadors_rep = np.zeros(3, dtype=int)
        if  not game.is_over():
            if game.round.doubling_cube == 8:
                multiplicadors_rep[2] = 1
            if game.round.doubling_cube >= 4:
                multiplicadors_rep[1] = 1
            if game.round.doubling_cube >= 2:
                multiplicadors_rep[0] = 1

        
        trump_suit_rep = np.zeros(5, dtype=int)
        if game.round.is_bidding_over() and not game.is_over():
            trump_suit_rep[game.round.cantar_move.action.pal_id] = 1


        rep = []
        rep.append(hand_rep)
        rep += bases_pila
        # amagades
        rep.append(delegar_rep)
        rep.append(cantar_rep)
        rep.append(multiplicadors_rep)
        rep.append(is_bidding_rep)
        rep.append(trump_suit_rep)
        rep.append(current_player_rep)

        obs = np.concatenate(rep)
        extracted_state['obs'] = obs
        extracted_state['legal_actions'] = legal_actions
        extracted_state['raw_legal_actions'] = raw_legal_actions
        extracted_state['raw_obs'] = obs
        return extracted_state
