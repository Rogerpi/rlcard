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
from rlcard.games.butifarra.utils.move import CallMove, PlayCardMove, PlayerMove, CantarAction

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
        self.butifarraStateExtractor = DefaultHiddenButifarraStateExtractor()
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
        return ActionEvent.from_action_id(action_id=action_id) # todo: not sure if correct, made me make changes to how it is saved in web db

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
    
class V1ButifarraPayoffDelegate(ButifarraPayoffDelegate):

    def __init__(self):
        pass

    def get_payoffs(self, game: ButifarraGame):
        ''' Get the payoffs of players.

        Returns:
            (list): A list of payoffs for each player.
        '''

        if not game.is_over():
            raise Exception("game is not over")
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
            
            punts_ma = [0,0,0,0]
            multiplicador = [0,0,0,0]
            for p in range(4):
                player_moves = [x for x in game.round.move_sheet if isinstance(x, PlayerMove) and x.player.player_id == p]
                punts_ma[p] = sum([c.card.get_valor() for c in player_moves if isinstance(c, PlayCardMove)])
                
                for m in player_moves:
                    if m.action.action_id >= m.action.first_play_card_action_id:
                        break
                    elif m.action.action_id == m.action.contrar_action_id:
                        multiplicador[p] = 2
                    elif m.action.action_id == m.action.recontrar_action_id:
                        multiplicador[p] = 4
                    elif m.action.action_id == m.action.sant_vicenc_action_id:
                        multiplicador[p] = 8

            declarer_punts_ma = punts_ma[declarer.player_id] + punts_ma[(declarer.player_id + 2) % 2 ]
            defender_punts_ma = punts_ma[(declarer.player_id + 1) % 2] + punts_ma[(declarer.player_id + 3) % 2 ]
                  
            #declarer_mult = max(multiplicador[declarer.player_id], multiplicador[(declarer.player_id + 2) % 2])
            #defender_mult = max(multiplicador[(declarer.player_id + 1) % 2], multiplicador[(declarer.player_id + 3) % 2])
           
            declarer_payoff = declarer_valor_bases - declarer_punts_ma + declarer_won_bases_count
            defender_payoff = defender_valor_bases - defender_punts_ma + defender_won_bases_count

            payoffs = []
            for player_id in range(4):
                payoff = declarer_payoff if player_id % 2 == declarer.player_id % 2 else defender_payoff
                
                punts = declarer_punts if player_id % 2 == declarer.player_id % 2 else defender_punts

                extra = 0
                if punts < 0:
                    extra = 2 * multiplicador[p] * punts # penalty
                else:
                    extra = multiplicador[p] * punts # gain
                
                payoffs.append(payoff + extra)

            # print("-----------------")
            # print("payoffs", payoffs)
            # print("punts", [declarer_punts, defender_punts])
            # print("punts_ma", punts_ma)
            # print("multiplicador", multiplicador)
            # print("-----------------")

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

        state_names = ['hand',
                        'cartes_jugades_jo',
                        'cartes_jugades_company', 
                        'cartes_jugades_dreta', 
                        'cartes_jugades_esquerra',
                        'cartes_amagades',
                        'basa_actual',
                        'ordre_basa',
                        'estem_cantant'
                        'delegar_qui',
                        'cantar_qui',
                        'contrar',
                        'recontrar',
                        'stvicenc',
                        'trumfo',
                        'current_player'
                        ] # idees: nombre bases guanyades, nombre bases consecutives
        
        state_sizes = [48, # 'hand',  
                            48, # 'cartes_jugades_jo'
                            48, # 'cartes_jugades_company', 
                            48, # 'cartes_jugades_dreta', 
                            48, # 'cartes_jugades_esquerra',
                            48, # 'cartes_amagades',
                            4, # 'basa_actual',
                            4, # 'ordre_basa',
                            1, # 'estem_cantant'
                            4, # 'delegar_qui',
                            4, # 'cantar_qui',
                            1, # 'contrar',
                            1, # 'recontrar',
                            1, # 'stvicenc',
                            5, # 'trumfo',
                            4 # current_player
                            ]
        
        self.state_size = sum(state_sizes)
        self.state_idxs = {}
        last_idx = 0
        for i in range(len(state_names)):
            new_idx = last_idx + state_sizes[i]
            self.state_idxs[state_names[i]] = [last_idx, new_idx]
            last_idx = new_idx


    def get_state_shape_size(self) -> int:
        return self.state_size

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

        for card in game.round.players[current_player_id].hand:
            hand_rep[card.card_id] = 1

        # construct trick_pile_rep

        cartes_jugades_jo = np.zeros(48, dtype=int) 
        cartes_jugades_company = np.zeros(48, dtype=int) 
        cartes_jugades_dreta = np.zeros(48, dtype=int) 
        cartes_jugades_esquerra = np.zeros(48, dtype=int) 

        cartes_amagades = np.zeros(48, dtype=int)

        basa_actual = np.ones(4, dtype=int) * -1
        basa_jugadors = np.ones(4, dtype=int) * -1

        if game.round.is_bidding_over():
            trick_moves = game.round.get_bases_moves()
            for move in trick_moves:
                player = move.player
                card = move.card
                if player.player_id == current_player_id: 
                    # es jo
                    cartes_jugades_jo[card.card_id] = 1

                elif player.player_id == ((current_player_id + 2) % 4): 
                    # es company
                    cartes_jugades_company[card.card_id] = 1

                elif player.player_id == ((current_player_id + 1) % 4): 
                    # es dreta
                    cartes_jugades_dreta[card.card_id] = 1

                elif player.player_id == ((current_player_id + 3) % 4): 
                    # es esquerra
                    cartes_jugades_esquerra[card.card_id] = 1

                else:
                    raise Exception("Jugador inexistent")
                
            
            cartes_visibles = hand_rep + cartes_jugades_jo + cartes_jugades_company + cartes_jugades_dreta + cartes_jugades_esquerra
            for i in range(48):
                if cartes_visibles[i] == 1:
                    cartes_amagades[i] = 0 
                elif cartes_visibles[i] == 0:
                    cartes_amagades[i] = 1
                else:
                    raise Exception("mes d'una mateixa carta apareix")
                
            cartes_basa = game.round.get_bases_moves()

            for i in range(len(cartes_basa)):
                move = cartes_basa[i]
                basa_actual[i] = move.card.card_id

            primer_jugador = cartes_basa[0].player.player_id if len(cartes_basa) > 0 else current_player_id
            for i in range(4):
                basa_jugadors[i] = (primer_jugador + i ) % 4

   
 
        # construct current_player_rep
        current_player_rep = np.zeros(4, dtype=int)
        current_player_rep[current_player_id] = 1

        # construct is_bidding_rep
        estem_cantant = np.array([1] if game.round.is_bidding_over() else [0])

        delegar_rep = np.zeros(4, dtype=int)
        if game.round.delegar_move is not None:
            id = game.round.delegar_move.player.player_id

            if id == current_player_id: 
                    # es jo
                delegar_rep[0] = 1

            elif id == ((current_player_id + 2) % 4): 
                # es company
                delegar_rep[1] = 1

            elif id == ((current_player_id + 1) % 4): 
                # es dreta
                delegar_rep[2] = 1

            elif id == ((current_player_id + 3) % 4): 
                # es esquerra
                delegar_rep[3] = 1

            else:
                raise Exception("what?")
            

        cantar_rep = np.zeros(4, dtype=int)
        if game.round.cantar_move is not None:
            id = game.round.cantar_move.player.player_id

            if id == current_player_id: 
                    # es jo
                cantar_rep[0] = 1

            elif id == ((current_player_id + 2) % 4): 
                # es company
                cantar_rep[1] = 1

            elif id == ((current_player_id + 1) % 4): 
                # es dreta
                cantar_rep[2] = 1

            elif id == ((current_player_id + 3) % 4): 
                # es esquerra
                cantar_rep[3] = 1

            else:
                raise Exception("what?")
        
        
        st_vicenc_rep = np.array([1] if game.round.doubling_cube == 8 else [0])
        recontrar_rep = np.array([1] if game.round.doubling_cube >= 4 else [0])
        contrar_rep = np.array([1] if game.round.doubling_cube >=2 else [0])

        trumfo_suit_rep = np.zeros(5, dtype=int)
        if game.round.is_bidding_over():
            trumfo_suit_rep[game.round.cantar_move.action.pal_id] = 1


        
        # state_names = ['hand',
        #                 'cartes_jugades_jo',
        #                 'cartes_jugades_company', 
        #                 'cartes_jugades_dreta', 
        #                 'cartes_jugades_esquerra',
        #                 'cartes_amagades',
        #                 'basa_actual',
        #                 'ordre_basa',
        #                 'estem_cantant'
        #                 'delegar_qui',
        #                 'cantar_qui',
        #                 'contrar',
        #                 'recontrar',
        #                 'stvicenc',
        #                 'trumfo',
        #                 'current_player'
        #                 ]


        rep = []
        rep.append(hand_rep)
        rep.append(cartes_jugades_jo)
        rep.append(cartes_jugades_company)
        rep.append(cartes_jugades_dreta)
        rep.append(cartes_jugades_esquerra)
        rep.append(cartes_amagades)
        rep.append(basa_actual)
        rep.append(basa_jugadors)
        rep.append(estem_cantant)
        rep.append(delegar_rep) 
        rep.append(cantar_rep)
        rep.append(contrar_rep)
        rep.append(recontrar_rep)
        rep.append(st_vicenc_rep)
        rep.append(trumfo_suit_rep)
        rep.append(current_player_rep)

        obs = np.concatenate(rep)
        extracted_state['obs'] = obs
        extracted_state['legal_actions'] = legal_actions
        extracted_state['raw_legal_actions'] = [str(a) for a in legal_actions] # TODO: needed for web server, as it complained of not being strings... Really have to check why othres don't have it
        extracted_state['raw_obs'] = obs
        return extracted_state



class DefaultHiddenButifarraStateExtractor(ButifarraStateExtractor):

    def __init__(self):
        super().__init__()

        state_names = ['hand',
                        'cartes_jugades_jo',
                        'cartes_jugades_esquerra',
                        'cartes_jugades_company', 
                        'cartes_jugades_dreta', 
                        'cartes_possibles_esquerra',
                        'cartes_possibles_company', 
                        'cartes_possibles_dreta', 
                        'cartes_amagades',
                        'basa_actual',
                        'basa_qui',
                        'estem_cantant'
                        'delegar_qui',
                        'cantar_qui',
                        'contrar',
                        'recontrar',
                        'stvicenc',
                        'trumfo'
                        ] # idees: nombre bases guanyades, nombre bases consecutives
        
        state_sizes = [48, # 'hand',  
                            48, # 'cartes_jugades_jo'
                            48, # 'cartes_jugades_company', 
                            48, # 'cartes_jugades_dreta', 
                            48, # 'cartes_jugades_esquerra',
                            48, # 'cartes_possibles_company', 
                            48, # 'cartes_possibles_dreta', 
                            48, # 'cartes_possibles_esquerra',
                            48, # 'cartes_amagades',
                            4, # 'basa_actual',
                            4, # 'basa_qui',
                            1, # 'estem_cantant'
                            4, # 'delegar_qui',
                            4, # 'cantar_qui',
                            1, # 'contrar',
                            1, # 'recontrar',
                            1, # 'stvicenc',
                            5 # 'trumfo',
                            
                            ]
        
        self.state_size = sum(state_sizes)
        self.state_idxs = {}
        last_idx = 0
        for i in range(len(state_names)):
            new_idx = last_idx + state_sizes[i]
            self.state_idxs[state_names[i]] = [last_idx, new_idx]
            last_idx = new_idx


    def get_state_shape_size(self) -> int:
        return self.state_size

    def extract_state(self, game: ButifarraGame):
        ''' Extract useful information from state for RL.

        Args:
            game (ButifarraGame): The game

        Returns:
            (numpy.array): The extracted state
        '''
        extracted_state = {}
        extracted_state['class'] = self.__class__.__name__
        legal_actions: OrderedDict = self.get_legal_actions(game=game)
        raw_legal_actions = list(legal_actions.keys())
        current_player = game.round.get_current_player()
        current_player_id = current_player.player_id

        # construct hands_rep of hands of players
        hand_rep = np.zeros(48, dtype=int)

        for card in game.round.players[current_player_id].hand:
            hand_rep[card.card_id] = 1

        # construct trick_pile_rep

        cartes_jugades_jo = np.zeros(48, dtype=int) 

        cartes_jugades_company = np.zeros(48, dtype=int) 
        cartes_jugades_dreta = np.zeros(48, dtype=int) 
        cartes_jugades_esquerra = np.zeros(48, dtype=int) 

        cartes_possibles_company = np.ones(48, dtype=int) 
        cartes_possibles_dreta = np.ones(48, dtype=int) 
        cartes_possibles_esquerra = np.ones(48, dtype=int) 

        cartes_amagades = np.zeros(48, dtype=int)

        basa_actual = np.ones(4, dtype=int) * -1
        basa_qui = np.ones(4, dtype=int) * -1

        player_company = ((current_player_id + 2) % 4)
        player_dreta = ((current_player_id + 3) % 4)
        player_esquerra = ((current_player_id + 1) % 4)

        basa_jugador = None

        if not game.round.is_bidding_over():
            for i in range(48):
                if hand_rep[i] == 1:
                    cartes_amagades[i] = 0 
                    cartes_possibles_company[i] = 0
                    cartes_possibles_dreta[i] = 0
                    cartes_possibles_esquerra[i] = 0
                elif hand_rep[i] == 0:
                    cartes_amagades[i] = 1
                else:
                    raise Exception("mes d'una mateixa carta apareix")


        else:
            first_play_card_idx = -1
            for i in range(len(game.round.move_sheet)):
                if isinstance(game.round.move_sheet[i], PlayCardMove):
                    first_play_card_idx = i
                    break

            if first_play_card_idx > 0:
            
                #trick_moves = game.round.get_bases_moves() # crec que esta malament, aixo retorna la basa actual, volem totes les cartes jugades
                for move in game.round.move_sheet[first_play_card_idx:]:
                    player = move.player
                    card = move.card
                    if player.player_id == current_player_id: 
                        # es jo
                        cartes_jugades_jo[card.card_id] = 1

                    elif player.player_id == player_company: 
                        # es company
                        cartes_jugades_company[card.card_id] = 1

                    elif player.player_id == player_dreta: 
                        # es dreta
                        cartes_jugades_dreta[card.card_id] = 1

                    elif player.player_id == player_esquerra: 
                        # es esquerra
                        cartes_jugades_esquerra[card.card_id] = 1

                    else:
                        raise Exception("Jugador inexistent")
                
            
            cartes_visibles = hand_rep + cartes_jugades_jo + cartes_jugades_company + cartes_jugades_dreta + cartes_jugades_esquerra
            for i in range(48):
                if cartes_visibles[i] == 1:
                    cartes_amagades[i] = 0 
                elif cartes_visibles[i] == 0:
                    cartes_amagades[i] = 1
                else:
                    raise Exception("mes d'una mateixa carta apareix")
                

            trumfo = game.round.get_trumfo()
            cartes_basa = game.round.get_bases_moves()

            basa_jugador = current_player_id

            if (len(cartes_basa) == 4):
                max_move = cartes_basa[0]
                for i in range(1,4):
                    if cartes_basa[i].card.mes_alta_que(max_move.card, cartes_basa[0].card.suit, trumfo):
                        max_move = cartes_basa[i]
                basa_jugador = max_move.player.player_id

            elif (len(cartes_basa) > 0):
                basa_jugador = cartes_basa[0].player.player_id

            #else: currentplayer

            if basa_jugador == current_player_id:
                basa_qui[0] = 1
            elif basa_jugador == player_esquerra:
                basa_qui[1] = 1
            elif basa_jugador == player_company:
                basa_qui[2] = 1
            elif basa_jugador == player_dreta:
                basa_qui[3] = 1

            else:
                raise Exception('la basa no es de ningu')


            # construct possible cards

            cartes_possibles_company = calculateHiddenInfo(game.round.move_sheet, hand_rep, trumfo, player_company)
            cartes_possibles_dreta = calculateHiddenInfo(game.round.move_sheet, hand_rep, trumfo, player_dreta)
            cartes_possibles_esquerra = calculateHiddenInfo(game.round.move_sheet, hand_rep, trumfo, player_esquerra)


        # construct is_bidding_rep
        estem_cantant = np.array([1] if game.round.is_bidding_over() else [0])

        delegar_rep = np.zeros(4, dtype=int)
        if game.round.delegar_move is not None:
            id = game.round.delegar_move.player.player_id

            if id == current_player_id: 
                    # es jo
                delegar_rep[0] = 1

            elif id == player_esquerra: 
                # es company
                delegar_rep[1] = 1

            elif id == player_company: 
                # es dreta
                delegar_rep[2] = 1

            elif id == player_dreta: 
                # es esquerra
                delegar_rep[3] = 1

            else:
                raise Exception("what?")
            

        cantar_rep = np.zeros(4, dtype=int)
        if game.round.cantar_move is not None:
            id = game.round.cantar_move.player.player_id

            if id == current_player_id: 
                cantar_rep[0] = 1

            elif id == player_esquerra: 
                cantar_rep[1] = 1

            elif id == player_company: 
                cantar_rep[2] = 1

            elif id == player_dreta: 
                cantar_rep[3] = 1

            else:
                raise Exception("what?")
        
        
        st_vicenc_rep = np.array([1] if game.round.doubling_cube == 8 else [0])
        recontrar_rep = np.array([1] if game.round.doubling_cube >= 4 else [0])
        contrar_rep = np.array([1] if game.round.doubling_cube >=2 else [0])

        trumfo_suit_rep = np.zeros(5, dtype=int)
        if game.round.is_bidding_over():
            trumfo_suit_rep[game.round.cantar_move.action.pal_id] = 1


        
        # state_names = ['hand',
        #                 'cartes_jugades_jo',
        #                 'cartes_jugades_company', 
        #                 'cartes_jugades_dreta', 
        #                 'cartes_jugades_esquerra',
        #                 'cartes_possibles_company', 
        #                 'cartes_possibles_dreta', 
        #                 'cartes_possibles_esquerra',
        #                 'cartes_amagades',
        #                 'basa_actual',
        #                 'ordre_basa',
        #                 'estem_cantant'
        #                 'delegar_qui',
        #                 'cantar_qui',
        #                 'contrar',
        #                 'recontrar',
        #                 'stvicenc',
        #                 'trumfo',
        #                 'current_player'
        #                 ]


        rep = []
        rep.append(hand_rep)
        rep.append(cartes_jugades_jo)
        rep.append(cartes_jugades_company)
        rep.append(cartes_jugades_dreta)
        rep.append(cartes_jugades_esquerra)
        rep.append(cartes_possibles_company)
        rep.append(cartes_possibles_dreta)
        rep.append(cartes_possibles_esquerra)
        rep.append(cartes_amagades)
        rep.append(basa_qui)
        rep.append(basa_actual)
        rep.append(estem_cantant)
        rep.append(delegar_rep) 
        rep.append(cantar_rep)
        rep.append(contrar_rep)
        rep.append(recontrar_rep)
        rep.append(st_vicenc_rep)
        rep.append(trumfo_suit_rep)

        obs = np.concatenate(rep)
        extracted_state['obs'] = obs
        extracted_state['legal_actions'] = legal_actions
        extracted_state['raw_legal_actions'] = [str(a) for a in legal_actions] # TODO: needed for web server, as it complained of not being strings... Really have to check why othres don't have it
        extracted_state['raw_obs'] = obs

        extracted_state['text'] = {}

        extracted_state['text']['hand'] = [ButifarraCard.card(i).__repr__() for i in range(48) if hand_rep[i] == 1]
        extracted_state['text']['cartes_jugades_jo'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_jugades_jo[i] == 1]
        extracted_state['text']['cartes_jugades_company'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_jugades_company[i] == 1]
        extracted_state['text']['cartes_jugades_dreta'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_jugades_dreta[i] == 1]
        extracted_state['text']['cartes_jugades_esquerra'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_jugades_esquerra[i] == 1]
        extracted_state['text']['cartes_possibles_company'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_possibles_company[i] == 1]
        extracted_state['text']['cartes_possibles_dreta'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_possibles_dreta[i] == 1]
        extracted_state['text']['cartes_possibles_esquerra'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_possibles_esquerra[i] == 1]
        extracted_state['text']['cartes_amagades'] = [ButifarraCard.card(i).__repr__() for i in range(48) if cartes_amagades[i] == 1]
        extracted_state['text']['basa_actual'] = [ButifarraCard.card(i).__repr__() for i in range(4) if basa_actual[i] != -1]
        extracted_state['text']['basa_jugador'] = 'None' if basa_jugador else basa_jugador
        #extracted_state['text']['estem_cantant'] = estem_cantant
        #extracted_state['text']['delegar_qui'] = [ButifarraCard.card(i) for i in range(4) if delegar_rep[i] == 1]
        #extracted_state['text']['cantar_qui'] = [ButifarraCard.card(i) for i in range(4) if cantar_rep[i] == 1]
        #extracted_state['text']['contrar'] = contrar_rep
        #extracted_state['text']['recontrar'] = recontrar_rep
        #extracted_state['text']['stvicenc'] = st_vicenc_rep
        #extracted_state['text']['trumfo'] = [CantarAction.accions[i] for i in range(5) if trumfo_suit_rep[i] == 1]
        #extracted_state['text']['current_player'] =  current_player.player_id #index of current player


        return extracted_state




### helpers

def oneHotPalInterval(pal):
    # pals = ['O', 'B', 'C', 'E']
    if pal == 'O':
        return [0,12]
    elif pal == 'B':
        return [12, 24]
    elif pal == 'C':
        return [24, 36]
    elif pal == 'E':
        return [36, 48]
    else:
        raise Exception("pal not valid")


# pals = ['O', 'B', 'C', 'E']
def calculateHiddenInfo(move_sheet, my_hand, trumfo, player_id) :

    # basa_actual: [4], may have empty slots
    # last_move: move, with action and player
    # trumfo: butifarraCard.pal
    # cartes_visibles: numpy [48] 1 if visible, 0 if hidden
    # one_hot_hidden_cards:  numpy [48] 1 if may be in hand, 0 if not

    # for each 1 in cartes_visibles, set one_hot_hidden_cards to 0

    one_hot_hidden_cards = np.ones(48, dtype=int)
    # for each card in my_hand, set one_hot_hidden_cards to 0
    for i in range(48):
        if my_hand[i] == 1:
            one_hot_hidden_cards[i] = 0


    #get idx of first play card
    first_play_card_idx = -1
    for i in range(len(move_sheet)):
        if isinstance(move_sheet[i], PlayCardMove):
            first_play_card_idx = i
            break

    # if no card has been played, then all hidden cards are possible
    if first_play_card_idx == -1:
        return one_hot_hidden_cards
    
    card_moves = len(move_sheet) - first_play_card_idx

    # for each move
    for i in range(first_play_card_idx, len(move_sheet)):
        move = move_sheet[i]
        # if card is visible, then set one_hot_hidden_cards to 0
        one_hot_hidden_cards[move.card.card_id] = 0
    
    basa_count = 0

    while True:

        cbidx = [first_play_card_idx + basa_count*4,  first_play_card_idx + (basa_count+1)*4]

        if cbidx[0] >= card_moves:
            break # return while
            
        if cbidx[1] > card_moves:
            cbidx[1] = card_moves

        cbhm = move_sheet[cbidx[0]]
        pal_basa = cbhm.card.suit
        cbpm = None
        for i in range(cbidx[0] + 1, cbidx[1]):
            cbcm = move_sheet[i]
            if cbcm.player.player_id == player_id:
                cbpm = cbcm
                break
            if cbcm.card.mes_alta_que(cbhm.card, pal_basa, trumfo):
                cbhm = cbcm

        if cbpm is None:
            # if no card of player has been played, we cannot make any assumption on this base. Also, it must be the last base
            break # return while

        # if player has played a card, then we can make some assumptions

        must_play_higher = (cbhm.player.player_id % 2) != (player_id % 2)
   
        # if lastmove is not of the same pal, then all hidden cards are possible
        if cbpm.card.suit != pal_basa:
            i = oneHotPalInterval(pal_basa)
            # fill with 0 from i[0] to i[1]
            for j in range(i[0], i[1]):
                one_hot_hidden_cards[j] = 0
        
            # if trumfo is not botifarra, lastmove is not trumfo (and not basa pal), and is forced to play higher, then he does not have trumfo
            if must_play_higher and trumfo is not None and cbpm.card.suit != trumfo:
                i = oneHotPalInterval(trumfo)
                # fill with 0 from i[0] to i[1]
                for j in range(i[0], i[1]):
                    one_hot_hidden_cards[j] = 0

        else : # lastmove is of the same pal
            # if must play higher but is not possible, then he does not have zny cards higher
            if must_play_higher and not cbpm.card.mes_alta_que(cbhm.card, pal_basa, None): 
                i = oneHotPalInterval(pal_basa)
                i[0] += ButifarraCard.numero.index(cbhm.card.rank)

                # fill with 0 from i[0] to i[1]
                for j in range(i[0], i[1]):
                    one_hot_hidden_cards[j] = 0
        
        basa_count += 1

    return one_hot_hidden_cards



def printHiddenInfo(one_hot_hidden_cards):
    str = "Player does not have: "
    for i in range(48):
        if one_hot_hidden_cards[i] == 0:
            str += ButifarraCard.card(i) + ", "
    print(str)


    
