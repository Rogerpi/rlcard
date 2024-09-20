''' Game-related base classes
'''
from __future__ import annotations

from rlcard.games.base import Card


class ButifarraCard(Card):
    '''
    Card stores the suit and rank of a single card

    '''
    pals = ['O', 'B', 'C', 'E'] # Orus, Bastos, Copes, Espases
    numero = ['2', '3', '4', '5', '6', '7', '8', 'A', 'B', 'C', 'D', 'E'] # ABCDE per 10, 11, 12 1 i 9
    valor = [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5]
    # map of names
    pals_noms = {'O': 'Orus', 'B': 'Bastos', 'C': 'Copes', 'E': 'Espases'}
    numero_noms = {'2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', 'A': '10', 'B': '11', 'C': '12', 'D' : '1', 'E' : '9'}


    @staticmethod
    def card(card_id: int):
        return _deck[card_id]

    @staticmethod
    def get_deck() -> [Card]:
        return _deck.copy()

    def __init__(self, pal: str, valor: str):
        super().__init__(suit=pal, rank=valor)

        pal_index = ButifarraCard.pals.index(self.suit)
        valor_index = ButifarraCard.numero.index(self.rank)

        self.card_id = 12 * pal_index + valor_index
    
    def __repr__(self):
        return f'{self.rank}{self.suit}'

    def __str__(self):
        return self.numero_noms[self.rank] + ' ' + self.pals_noms[self.suit] 
    
    def mes_alta_que(self, carta: ButifarraCard, pal_basa : str, pal_trumfo : str or None):

        # Si es botifarra, pal_trumfo és None
        # No passa res, ja que una carta no pot tenir pal none, per tant els 3 primers ifs no fan res
        if self.suit == pal_trumfo and carta.suit == pal_trumfo:
            return self.rank > carta.rank 
        elif self.suit != pal_trumfo and carta.suit == pal_trumfo:
            return False
        elif self.suit == pal_trumfo and carta.suit != pal_trumfo:
            return True
        else: # Cap carta es trumfo
            if self.suit == pal_basa and carta.suit == pal_basa:
                return self.rank > carta.rank
            elif self.suit != pal_basa and carta.suit == pal_basa:
                return False
            elif self.suit == pal_basa and carta.suit != pal_basa:
                return True
            else: # Aixo no hauria de passar mai
                print("Warning")
                return self.rank > carta.rank
            
    def get_valor(self):
        return self.valor[ButifarraCard.numero.index(self.rank)]
        

        

# deck is always in order from 2C, ... KC, AC, 2D, ... KD, AD, 2H, ... KH, AH, 2S, ... KS, AS
_deck = [ButifarraCard(pal=pal, valor=valor) for pal in ButifarraCard.pals for valor in ButifarraCard.numero]  # want this to be read-only


