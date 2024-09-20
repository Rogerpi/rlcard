'''
    File name: bridge/judger.py
    Author: William Hale
    Date created: 11/25/2021
'''

from typing import List

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game import ButifarraGame

from .utils.action_event import PlayCardAction
from .utils.action_event import ActionEvent, CantarAction, DelegarAction, ContrarAction, RecontrarAction, SantVicencAction, PassarAction
from .utils.move import MakeCantarMove, MakeDelegarMove, MakeContrarMove, MakeRecontrarMove, MakeSantVicencMove
from .utils.butifarra_card import ButifarraCard


class ButifarraJudger:

    '''
        Judger decides legal actions for current player
    '''

    def __init__(self, game: 'ButifarraGame'):
        ''' Initialize the class BridgeJudger
        :param game: ButifarraGame
        '''
        self.game: ButifarraGame = game

    def get_legal_actions(self) -> List[ActionEvent]:
        """
        :return: List[ActionEvent] of legal actions
        """
        legal_actions: List[ActionEvent] = []
        if not self.game.is_over():
            current_player = self.game.round.get_current_player()
            if not self.game.round.is_bidding_over():
                last_delegar_move: MakeContrarMove or None = None
                last_cantar_move: MakeCantarMove or None = None
                last_contrar_move: MakeContrarMove or None = None
                last_recontrar_move: MakeRecontrarMove or None = None
                last_santvicenc_move: MakeSantVicencMove or None = None
                num_pass_move: int = 0

                for move in reversed(self.game.round.move_sheet):
                    if isinstance(move, MakeCantarMove):
                        last_cantar_move = move
                    elif isinstance(move, MakeDelegarMove):
                        last_delegar_move = move
                    elif isinstance(move, MakeSantVicencMove):
                        last_santvicenc_move = move
                    elif isinstance(move, MakeRecontrarMove):
                        last_recontrar_move = move
                    elif isinstance(move, MakeContrarMove):
                        last_contrar_move = move

                if (not last_cantar_move):
                    legal_actions.append(ActionEvent.from_action_id(action_id=ActionEvent.bastos_action_id))
                    legal_actions.append(ActionEvent.from_action_id(action_id=ActionEvent.espases_action_id))
                    legal_actions.append(ActionEvent.from_action_id(action_id=ActionEvent.orus_action_id))
                    legal_actions.append(ActionEvent.from_action_id(action_id=ActionEvent.copes_action_id))
                    legal_actions.append(ActionEvent.from_action_id(action_id=ActionEvent.butifarra_action_id))

                    if not last_delegar_move:
                        legal_actions.append(DelegarAction())
                

                if last_cantar_move:
                    legal_actions.append(PassarAction())
                    if current_player.player_id % 2 != last_cantar_move.player.player_id % 2:
                        if not last_contrar_move:
                            legal_actions.append(ContrarAction())
                        if last_recontrar_move:
                            legal_actions.append(SantVicencAction())

                    else:
                        if last_contrar_move:
                            legal_actions.append(RecontrarAction())

            else:
                trick_moves = self.game.round.get_bases_moves()
                hand = self.game.round.players[current_player.player_id].hand
                legal_cards = hand # En cas de ser la primera tirada, qualsevol carta es valida
                if trick_moves and len(trick_moves) < 4: # si ja s'ha tirat, aqui venen les normes
                    carta_basa: ButifarraCard = trick_moves[0].card
                    carta_mes_alta = carta_basa
                    jugador_guanyador = trick_moves[0].player

                    pal_basa = carta_basa.suit
                    pal_trumfo = self.game.round.get_trumfo()
                    for move in trick_moves[1:]:
                        if move.card.mes_alta_que(carta_mes_alta, pal_basa, pal_trumfo):
                            carta_mes_alta = move.card
                            jugador_guanyador = move.player

                    is_basa_company = (jugador_guanyador.player_id % 2) == (current_player.player_id % 2)
                    
                    cartes_de_la_basa = [card for card in hand if card.suit == carta_basa.suit]
                    
                    if (is_basa_company):
                        if cartes_de_la_basa: # Si hi ha alguna carta del pal de la basa, obligat a tirar basa
                            legal_cards = cartes_de_la_basa
                        else:
                            legal_cards = hand 
                    else: # de l'altre equip
                        if cartes_de_la_basa: # Ha de jugar el pal i si pot matar
                            cartes_basa_mes_altes = [card for card in cartes_de_la_basa if card.mes_alta_que(carta_mes_alta, pal_basa, pal_trumfo)]
                            if cartes_basa_mes_altes: # Alguna carta de la basa pot matar la mes alta (no trumfo)
                                legal_cards = cartes_basa_mes_altes
                            else: # No podem matar pero tenim basa
                                legal_cards = cartes_de_la_basa
                        else: # No tenim cartes de la basa. Mirem si hi ha trumfo
                            cartes_que_guanyen = [card for card in hand if card.mes_alta_que(carta_mes_alta, pal_basa, pal_trumfo)]
                            if cartes_que_guanyen:
                                legal_cards = cartes_que_guanyen
                            else: # No tenim res que guany
                                legal_cards = hand

                for card in legal_cards:
                    action = PlayCardAction(card=card)
                    legal_actions.append(action)

        return legal_actions
