'''
    File name: Butifarra/utils/move.py
    Author: William Hale
    Date created: 11/25/2021
'''

#
#   These classes are used to keep a move_sheet history of the moves in a round.
#

from .action_event import ActionEvent, DelegarAction, CantarAction, PassarAction, ContrarAction, RecontrarAction, SantVicencAction, PlayCardAction
from .butifarra_card import ButifarraCard

from ..player import ButifarraPlayer


class ButifarraMove(object):  # Interface
    pass


class PlayerMove(ButifarraMove):  # Interface

    def __init__(self, player: ButifarraPlayer, action: ActionEvent):
        super().__init__()
        self.player = player
        self.action = action


class CallMove(PlayerMove):  # Interface

    def __init__(self, player: ButifarraPlayer, action: ActionEvent):
        super().__init__(player=player, action=action)


class DealHandMove(ButifarraMove):

    def __init__(self, dealer: ButifarraPlayer, shuffled_deck: [ButifarraCard]):
        super().__init__()
        self.dealer = dealer
        self.shuffled_deck = shuffled_deck

    def __str__(self):
        shuffled_deck_text = " ".join([str(card) for card in self.shuffled_deck])
        return f'{self.dealer} deal shuffled_deck=[{shuffled_deck_text}]'


class MakeDelegarMove(CallMove):

    def __init__(self, player: ButifarraPlayer):
        super().__init__(player=player, action=DelegarAction())

    def __str__(self):
        return f'{self.player}: {self.action}'


class MakeContrarMove(CallMove):

    def __init__(self, player: ButifarraPlayer):
        super().__init__(player=player, action=ContrarAction())

    def __str__(self):
        return f'{self.player}: {self.action}'
    
class MakeRecontrarMove(CallMove):

    def __init__(self, player: ButifarraPlayer):
        super().__init__(player=player, action=RecontrarAction())

    def __str__(self):
        return f'{self.player}: {self.action}'

class MakeSantVicencMove(CallMove):

    def __init__(self, player: ButifarraPlayer):
        super().__init__(player=player, action=SantVicencAction())

    def __str__(self):
        return f'{self.player}: {self.action}'
    
class MakePassarMove(CallMove):

    def __init__(self, player: ButifarraPlayer):
        super().__init__(player=player, action=PassarAction())

    def __str__(self):
        return f'{self.player}: {self.action}'
    



class MakeCantarMove(CallMove):

    def __init__(self, player: ButifarraPlayer, cantar_action: CantarAction):
        super().__init__(player=player, action=cantar_action)
        self.action = cantar_action  # Note: keep type as BidAction rather than ActionEvent

    def __str__(self):
        return f'{self.player}: canto {self.action}'


class PlayCardMove(PlayerMove):

    def __init__(self, player: ButifarraPlayer, action: PlayCardAction):
        super().__init__(player=player, action=action)
        self.action = action  # Note: keep type as PlayCardAction rather than ActionEvent

    @property
    def card(self):
        return self.action.card

    def __str__(self):
        return f'{self.player} plays {self.action}'
