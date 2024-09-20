'''
    File name: bridge/utils/action_event.py
    Author: William Hale
    Date created: 11/25/2021
'''

from .butifarra_card import ButifarraCard

# ====================================
# Action_ids:
#       0 -> Delegar
#       1 to 4 -> O, B, C, E
#       5 -> Butifarra
#       6 -> Passar
#       7 -> contrar
#       8 -> recontrar
#       9 -> Sant Vicenç
#        to 58 -> play_card_action_id
# ====================================


class ActionEvent(object):  # Interface

    delegar_action_id = 0
    orus_action_id = 1
    bastos_action_id = 2
    copes_action_id = 3
    espases_action_id = 4
    butifarra_action_id = 5
    passar_action_id = 6
    contrar_action_id = 7
    recontrar_action_id = 8
    sant_vicenc_action_id = 9
    first_play_card_action_id = 10

    def __init__(self, action_id: int):
        self.action_id = action_id

    def __eq__(self, other):
        result = False
        if isinstance(other, ActionEvent):
            result = self.action_id == other.action_id
        return result

    @staticmethod
    def from_action_id(action_id: int):
        if action_id == ActionEvent.delegar_action_id:
            return DelegarAction()
        elif ActionEvent.orus_action_id <= action_id <= ActionEvent.butifarra_action_id:
            pal = None if action_id == ActionEvent.butifarra_action_id else ButifarraCard.pals[action_id - ActionEvent.orus_action_id]
            return CantarAction(pal=pal)
        elif action_id == ActionEvent.passar_action_id:
            return PassarAction()
        elif action_id == ActionEvent.contrar_action_id:
            return ContrarAction()
        elif action_id == ActionEvent.recontrar_action_id:
            return RecontrarAction()
        elif action_id == ActionEvent.sant_vicenc_action_id:
            return SantVicencAction()
        elif ActionEvent.first_play_card_action_id <= action_id < ActionEvent.first_play_card_action_id + 48:
            card_id = action_id - ActionEvent.first_play_card_action_id
            card = ButifarraCard.card(card_id=card_id)
            return PlayCardAction(card=card)
        else:
            raise Exception(f'ActionEvent from_action_id: invalid action_id={action_id}')

    @staticmethod
    def get_num_actions():
        ''' Return the number of possible actions in the game
        '''
        return  58 #  1 passar 1 delegar 5 cantar 3 contrar 48 cartes 
        
class CallActionEvent(ActionEvent):  # Interface
    pass

class PassarAction(CallActionEvent):

    def __init__(self):
        super().__init__(action_id=ActionEvent.passar_action_id)

    def __str__(self):
        return "Passo"

    def __repr__(self):
        return "Passo"
    
class DelegarAction(CallActionEvent):

    def __init__(self):
        super().__init__(action_id=ActionEvent.delegar_action_id)

    def __str__(self):
        return "Delego"

    def __repr__(self):
        return "Delego"


class CantarAction(CallActionEvent):

    accions = ['Orus', 'Bastos', 'Copes', 'Espases', 'Butifarra']

    def __init__(self, pal: str or None): #None for Butifarra
        pals = ButifarraCard.pals
        if pal and pal not in pals:
            raise Exception(f'Cantar has invalid pal: {pal}')
        if pal in pals:
            self.pal_id = pals.index(pal) 
        else:
            self.pal_id = 4
        self.pal = pal
        super().__init__(action_id=self.pal_id + 1)

    def __str__(self):
        return f"{CantarAction.accions[self.pal_id]}"

    def __repr__(self):
        return self.__str__()


class ContrarAction(CallActionEvent):

    def __init__(self):
        super().__init__(action_id=ActionEvent.contrar_action_id)

    def __str__(self):
        return "Contro"

    def __repr__(self):
        return "Contro"
    
class RecontrarAction(CallActionEvent):
    
        def __init__(self):
            super().__init__(action_id=ActionEvent.recontrar_action_id)
    
        def __str__(self):
            return "Recontro"
    
        def __repr__(self):
            return "Recontro"

class SantVicencAction(CallActionEvent):
    
        def __init__(self):
            super().__init__(action_id=ActionEvent.sant_vicenc_action_id)
    
        def __str__(self):
            return "Sant Vicenç"
    
        def __repr__(self):
            return "Sant Vicenç"


class PlayCardAction(ActionEvent):

    def __init__(self, card: ButifarraCard):
        play_card_action_id = ActionEvent.first_play_card_action_id + card.card_id
        super().__init__(action_id=play_card_action_id)
        self.card: ButifarraCard = card

    def __str__(self):
        return f"{self.card}"

    def __repr__(self):
        return f"{self.card}"
