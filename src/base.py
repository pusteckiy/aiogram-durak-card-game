import random
from typing import List


class Card:

    def __init__(self, score: str, suit: str):
        self._translate_dict = {'J': 11, 'Q': 12, 'K': 13, 'T': 14}

        self.score: str = score
        self.suit: str = suit
        self.level: int = int(score) if score.isdigit() else self._translate_dict[score]
       
    def __repr__(self):
        return self.score + self.suit

    def __lt__(self, other):
        return self.level < other.level and self.suit == other.suit
    
    def __gt__(self, other):
        return self.level > other.level and self.suit == other.suit
    
    def __eq__(self, other):
        return self.level == other.level and self.suit == other.suit



class Deck:

    def __init__(self) -> None:
        self.stack: List[Card] = []

    def __repr__(self) -> str:
        return str(self.stack)
    
    def __len__(self) -> int:
        return len(self.stack)
    
    def __list__(self) -> list:
        return self.stack

    def generate(self) -> None:
        """ Генерує 36 карт в колоду.
        """
        for score in ('6', '7', '8', '9', '10', 'J', 'Q', 'K', 'T',):
            for suit in ('♥', '♦', '♣', '♠',):
                self.stack.append(Card(score, suit))

    def shuffle(self) -> list:
        """ Перемішує карти в колоді.
        """
        return random.shuffle(self.stack)



class Player:

    def __init__(self, id: int, name: str) -> None:
        self.id: int = id
        self.name: str = name
        self.cards: List[Card] = []
    
    def __repr__(self) -> str:
        return f'Player {self.id} ' + str(self.cards)
