'''
    File name: Butifarra/round.py
    Author: William Hale
    Date created: 11/25/2021
'''

from typing import List

from .dealer import ButifarraDealer
from .player import ButifarraPlayer

from .utils.action_event import CallActionEvent, ActionEvent, DelegarAction, CantarAction, ContrarAction, RecontrarAction, SantVicencAction, PassarAction, PlayCardAction
from .utils.move import ButifarraMove, MakeDelegarMove, MakeCantarMove, MakePassarMove, MakeContrarMove, MakeRecontrarMove, MakeSantVicencMove, DealHandMove, CallMove, PlayCardMove
from .utils.tray import Tray
from .utils.butifarra_card import ButifarraCard

class ButifarraRound:

    @property
    def dealer_id(self) -> int:
        return self.tray.dealer_id

    @property
    def board_id(self) -> int:
        return self.tray.board_id

    @property
    def round_phase(self):
        if self.is_over():
            result = 'game over'
        elif self.is_bidding_over():
            result = 'play card'
        else:
            result = 'cantar'
        return result

    def __init__(self, num_players: int, board_id: int, np_random):
        ''' Initialize the round class

            The round class maintains the following instances:
                1) dealer: the dealer of the round; dealer has bases_pile
                2) players: the players in the round; each player has his own hand_pile
                3) current_player_id: the id of the current player who has the move
                4) doubling_cube: 2 if contract is doubled; 4 if contract is redoubled; else 1
                5) play_card_count: count of PlayCardMoves
                5) move_sheet: history of the moves of the players (including the deal_hand_move)

            The round class maintains a list of moves made by the players in self.move_sheet.
            move_sheet is similar to a chess score sheet.
            I didn't want to call it a score_sheet since it is not keeping score.
            I could have called move_sheet just moves, but that might conflict with the name moves used elsewhere.
            I settled on the longer name "move_sheet" to indicate that it is the official list of moves being made.

        Args:
            num_players: int
            board_id: int
            np_random
        '''
        tray = Tray(board_id=board_id)
        dealer_id = tray.dealer_id
        self.tray = tray
        self.np_random = np_random
        self.dealer: ButifarraDealer = ButifarraDealer(self.np_random)
        self.players: List[ButifarraPlayer] = []
        for player_id in range(num_players):
            self.players.append(ButifarraPlayer(player_id=player_id, np_random=self.np_random))
        self.current_player_id: int = dealer_id
        self.doubling_cube: int = 1
        self.is_butifarra: bool = False
        self.play_card_count: int = 0
        self.cantar_move: MakeCantarMove or None = None
        self.delegar_move: MakeDelegarMove or None = None
        self.won_bases_counts = [0, 0]  # count of won basess by side
        self.won_cards : List[List[ButifarraCard]] = [[],[]]
        
        self.move_sheet: List[ButifarraMove] = []
        self.move_sheet.append(DealHandMove(dealer=self.players[dealer_id], shuffled_deck=self.dealer.shuffled_deck))

    def is_bidding_over(self) -> bool:
        ''' Return whether the current bidding is over
        '''

        # Idea. Per que s'acabi la ronda inicial, cal que els dos membres d'una parella hagin passat despres que l'altra parella hagi cantat o apostat.
        if isinstance(self.move_sheet[-1], PlayCardMove) or \
           isinstance(self.move_sheet[-1], MakeSantVicencMove):
            return True
        pass_count = 0
        for move in reversed(self.move_sheet):
            if isinstance(move, MakePassarMove):
                pass_count +=1
            if isinstance(move, MakeCantarMove) or \
               isinstance(move, MakeDelegarMove) or \
               isinstance(move, MakeRecontrarMove) or \
               isinstance(move, MakeContrarMove):
                return pass_count == 2
        
        return False


    def is_over(self) -> bool:
        ''' Return whether the current game is over
        '''
        is_over = True
        if not self.is_bidding_over():
            is_over = False
        elif self.cantar_move:
            for player in self.players:
                if player.hand:
                    is_over = False
                    break

        if (is_over):
            return is_over

    def get_current_player(self) -> ButifarraPlayer or None:
        current_player_id = self.current_player_id
        return None if current_player_id is None else self.players[current_player_id]

    # No entenc
    def get_bases_moves(self) -> List[PlayCardMove]:
        bases_moves: List[PlayCardMove] = []
        if self.is_bidding_over():
            if self.play_card_count > 0:
                bases_pile_count = self.play_card_count % 4
                if bases_pile_count == 0:
                    bases_pile_count = 4  # wch: note this
                for move in self.move_sheet[-bases_pile_count:]:
                    if isinstance(move, PlayCardMove):
                        bases_moves.append(move)
                if len(bases_moves) != bases_pile_count:
                    raise Exception(f'get_bases_moves: count of bases_moves={[str(move.card) for move in bases_moves]} does not equal {bases_pile_count}')
        return bases_moves

    def get_trumfo(self) -> str or None:
        if self.cantar_move.action.pal_id == self.cantar_move.action.butifarra_action_id:
            return None
        else:
            return self.cantar_move.action.pal

    def make_call(self, action: CallActionEvent):
        # when current_player takes CallActionEvent step, the move is recorded and executed
        current_player = self.players[self.current_player_id]
        if isinstance(action, DelegarAction):
            make_delegar_move = MakeDelegarMove(current_player)
            self.move_sheet.append(make_delegar_move)
            self.delegar_move = make_delegar_move
            self.current_player_id = self.get_company().player_id
        elif isinstance(action, CantarAction):
            self.doubling_cube = 1
            self.is_butifarra = (action.action_id == CantarAction.butifarra_action_id)   
            make_cantar_move = MakeCantarMove(current_player, action)
            self.cantar_move = make_cantar_move
            self.move_sheet.append(make_cantar_move)
            self.current_player_id = (self.current_player_id + 1) % 4
        elif isinstance(action, ContrarAction):
            self.doubling_cube = 2
            make_contrar_move = MakeContrarMove(current_player)
            self.move_sheet.append(make_contrar_move)
            self.current_player_id = (self.current_player_id + 1) % 4
        elif isinstance(action, RecontrarAction):
            self.doubling_cube = 4
            make_recontrar_move = MakeRecontrarMove(current_player)
            self.move_sheet.append(make_recontrar_move)
            self.current_player_id = (self.current_player_id + 1) % 4
        elif isinstance(action, SantVicencAction):
            self.doubling_cube = 8
            make_stvicenc_move = MakeSantVicencMove(current_player)
            self.move_sheet.append(make_stvicenc_move)
            # Acaba la ronda, no cal decidir seguent jugador
        elif isinstance(action, PassarAction):
            self.move_sheet.append(MakePassarMove(current_player))
            self.current_player_id = self.get_company().player_id

        if self.is_bidding_over():
            if not self.is_over():
                self.current_player_id = self.get_left_defender().player_id

    def play_card(self, action: PlayCardAction):
        # when current_player takes PlayCardAction step, the move is recorded and executed
        current_player = self.players[self.current_player_id]
        self.move_sheet.append(PlayCardMove(current_player, action))
        card = action.card
        current_player.remove_card_from_hand(card=card)
        self.play_card_count += 1
        # update current_player_id
        bases_moves = self.get_bases_moves()
        if len(bases_moves) == 4:
            trump_suit = self.get_trumfo()
            winning_card = bases_moves[0].card
            bases_winner = bases_moves[0].player
            for move in bases_moves[1:]:
                bases_card = move.card
                bases_player = move.player
                if bases_card.suit == winning_card.suit:
                    if bases_card.card_id > winning_card.card_id:
                        winning_card = bases_card
                        bases_winner = bases_player
                elif bases_card.suit == trump_suit:
                    winning_card = bases_card
                    bases_winner = bases_player
            self.current_player_id = bases_winner.player_id
            self.won_bases_counts[bases_winner.player_id % 2] += 1
            for move in bases_moves:
                self.won_cards[bases_winner.player_id % 2].append(move.card)
        else:
            self.current_player_id = (self.current_player_id + 1) % 4

    def get_declarer(self) -> ButifarraPlayer or None:
        declarer = None
        if self.cantar_move:
            trump_suit = self.cantar_move.action.pal
            side = self.cantar_move.player.player_id % 2
            for move in self.move_sheet:
                if isinstance(move, MakeCantarMove) and move.action.pal == trump_suit and move.player.player_id % 2 == side:
                    declarer = move.player
                    break
        return declarer

    def get_dummy(self) -> ButifarraPlayer or None:
        dummy = None
        declarer = self.get_declarer()
        if declarer:
            dummy = self.players[(declarer.player_id + 2) % 4]
        return dummy

    def get_left_defender(self) -> ButifarraPlayer or None:
        left_defender = None
        declarer = self.get_declarer()
        if declarer:
            left_defender = self.players[(declarer.player_id + 1) % 4]
        return left_defender

    def get_right_defender(self) -> ButifarraPlayer or None:
        right_defender = None
        declarer = self.get_declarer()
        if declarer:
            right_defender = self.players[(declarer.player_id + 3) % 4]
        return right_defender
    
    def get_company(self) -> ButifarraPlayer or None:
        if self.current_player_id is not None:
            return self.players[(self.current_player_id + 2) % 4]
        return None

    def get_perfect_information(self):
        print("get perfect info")
        state = {}
        last_call_move = None
        if not self.is_bidding_over() or self.play_card_count == 0:
            last_move = self.move_sheet[-1]
            if isinstance(last_move, CallMove):
                last_call_move = last_move
        bases_moves = [None, None, None, None]
        if self.is_bidding_over():
            for bases_move in self.get_bases_moves():
                bases_moves[bases_move.player.player_id] = bases_move.card
        state['move_count'] = len(self.move_sheet)
        state['tray'] = self.tray
        state['current_player_id'] = self.current_player_id
        state['round_phase'] = self.round_phase
        state['last_call_move'] = last_call_move
        state['doubling_cube'] = self.doubling_cube
        state['contact'] = self.cantar_move if self.is_bidding_over() and self.cantar_move else None
        state['hands'] = [player.hand for player in self.players]
        state['bases_moves'] = bases_moves
        return state

    def print_scene(self):
        print(f'===== Board: {self.tray.board_id} move: {len(self.move_sheet)} player: {self.players[self.current_player_id]} phase: {self.round_phase} =====')
        print(f'dealer={self.players[self.tray.dealer_id]}')
        if not self.is_bidding_over() or self.play_card_count == 0:
            last_move = self.move_sheet[-1]
            last_call_text = f'{last_move}' if isinstance(last_move, CallMove) else 'None'
            print(f'last call: {last_call_text}')
        if self.is_bidding_over() and self.cantar_move:
            pal = self.cantar_move.action.pal
            doubling_cube = self.doubling_cube
            if not pal:
                pal = 'Butifarra'
            doubling_cube_text = "" if doubling_cube == 1 else "contrar" if doubling_cube == 2 else "recontrar" if doubling_cube == 4 else "st vicenc" if doubling_cube == 8 else ""
            print(f'Trumfo: {self.cantar_move.player} {self.cantar_move.action.pal} {doubling_cube_text}')
        for player in self.players:
            print(f'{player}: {[str(card) for card in player.hand]}')
        if self.is_bidding_over():
            bases_pile = ['None', 'None', 'None', 'None']
            for bases_move in self.get_bases_moves():
                bases_pile[bases_move.player.player_id] = bases_move.card
            print(f'bases_pile: {[str(card) for card in bases_pile]}')
