from termcolor import colored

from rlcard.games.butifarra.utils.butifarra_card import ButifarraCard


def print_cards(cards):

    if isinstance(cards, str):
        cards = [cards]
    for i, card in enumerate(cards):

        print(card ,end='')

        if i < len(cards) - 1:
            print(', ', end='')
