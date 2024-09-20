'''
    File name: bridge/dealer.py
    Author: William Hale
    Date created: 11/25/2021
'''

from typing import List

from .player import ButifarraPlayer
from .utils.butifarra_card import ButifarraCard


class ButifarraDealer:
    ''' Initialize a BridgeDealer dealer class
    '''
    def __init__(self, np_random):
        ''' set shuffled_deck, set stock_pile
        '''
        self.np_random = np_random
        self.shuffled_deck: List[ButifarraCard] = ButifarraCard.get_deck()  # keep a copy of the shuffled cards at start of new hand
        self.np_random.shuffle(self.shuffled_deck)
        self.stock_pile: List[ButifarraCard] = self.shuffled_deck.copy()

    def deal_cards(self, player: ButifarraPlayer, num: int):
        ''' Deal some cards from stock_pile to one player

        Args:
            player (ButifarraPlayer): The ButifarraPlayer object
            num (int): The number of cards to be dealt
        '''
        for _ in range(num):
            player.hand.append(self.stock_pile.pop())
