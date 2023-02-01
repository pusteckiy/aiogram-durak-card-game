from typing import List

from aiogram import Dispatcher, types
from aiogram.dispatcher import filters, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.base import Card, Deck, Player


CHAT_TEXT = "👉 **{}**\n\nКозир: [{}]\nКолода: {}🃏\n\nСтіл: {}"


class MoveState(StatesGroup):
    attack = State()
    defend = State()


class Durak:

    def __init__(self, id: int, dp: Dispatcher) -> None:

        self.id = id
        self.is_started = False
        self.dp: Dispatcher = dp
        self.players: List[Player] = list()
        self.discarded = list()
        self.playholder = list()

        self.defender: Player
        self.attacker: Player

        self.deck = Deck()
        self._move_index = 1
   

    def join(self, player_id: int, player_name: str) -> None:
        """ Підключає гравця по вказаному player_id до гри.
        """
        self.players.append(Player(player_id, player_name))
    

    def leave(self, player_id: int) -> None:
        """ Відключає гравця по вказаному player_id з гри.
        """
        for i, player in enumerate(self.players):
            if player.id == player_id:
                return self.players.pop(i)
    

    async def start(self) -> None:
        """ Робить підготовку і запускає гру.
        """
        if len(self.players) < 2:
            return await self.dp.bot.send_message(chat_id=self.id, text="Недостатньо гравців для запуску, мінімум 2.")

        self.deck.generate()
        self.deck.shuffle()
        
        for player in self.players:
            player.cards.extend([self.deck.stack.pop() for _ in range(6)])

        self.trump: Card = self.deck.stack[0]

        await self._set_players()

        self.is_started = True
        await self.dp.bot.send_message(chat_id=self.id, text="🃏 Запускаю..")
        await self._move()
        

    def can_beat(self, attack_card: Card, defend_card: Card) -> bool:
        """ Перевіряє чи можна відбити `attack_card`
            за допомогою defend_card`.
        """
        if attack_card.suit == defend_card.suit:
            return attack_card < defend_card
        return attack_card.suit != self.trump.suit and defend_card.suit == self.trump.suit


    def can_throw_up(self, player: Player) -> bool:
        """ Перевіряє чи може `attacker` підкинути карти.
            Визначає по рівню карт, які вже є на полі.
        """
        playholder_levels = [card.level for card in self.playholder]
        player_levels = [card.level for card in player.cards]
        return bool(set(playholder_levels) & set(player_levels))


    def _create_keyboard(self, options: List[str]):
        """ Створює клавіатуру для телеграм з потрібними
            кнопками з списка `options`.
        """
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(*options)
        return keyboard
    

    async def _make_move(self, player: Player, move_type: str):
        """ 1. Встановлює `state` для `player`.
            2. Відправляє в бесіду `CHAT_TEXT`.
            3. Відправляє в приватні повідомлення `player` текст `CHAT_TEXT` та створює клавіатуру з картами.
            4. Реєструє хендлер який приймає тільки карти які є в гравця, щоб він зміг атакувати.
        """
        action = {
            'attack': (self._attack_handler, 'Бито'),
            'defend': (self._defend_handler, 'Взяти')
            }
        
        await self.dp.storage.set_state(user=player.id, chat=player.id, state=MoveState.attack.state)
        await self.dp.bot.send_message(
            chat_id=self.id, 
            text=CHAT_TEXT.format(player.name, self.trump, len(self.deck.stack), self.playholder),
            parse_mode=types.ParseMode.MARKDOWN)
        await self.dp.bot.send_message(
            chat_id=player.id, 
            text=CHAT_TEXT.format(player.name, self.trump, len(self.deck.stack), self.playholder),
            reply_markup=self._create_keyboard([*[str(card) for card in player.cards], action.get(move_type)[1]]),
            parse_mode=types.ParseMode.MARKDOWN)
        self.dp.register_message_handler(
            action.get(move_type)[0],
            filters.Text(equals=[*self.attacker.cards, action.get(move_type)[1]]),
            state=MoveState.attack, 
        )


    async def _attack_handler(self, message: types.Message, state: FSMContext):
        self.dp.message_handlers.unregister(self._attack_handler)
        if message.text == 'Бито':
            if len(self.playholder) > 1:
                return await self._make_move(self.attacker, 'attack')
            self.playholder = list()
            return await self._move()

        score, suit = message.text[:-1], message.text[-1:]
        self.attack_card = Card(score, suit)
        await message.answer(f'[НАПАД] Вибрано карту: {self.attack_card}', reply_markup=types.ReplyKeyboardRemove())
        self.playholder.append(self.attack_card)
        self.attacker.cards.remove(self.attack_card)
        await self._make_move(self.defender, 'defend')


    async def _defend_handler(self, message: types.Message, state: FSMContext):
        self.dp.message_handlers.unregister(self._defend_handler)
        if message.text == 'Взяти':
            self.defender.cards.extend(self.playholder)
            self.playholder = list()
            self._move_index += 1
            await message.answer('😱 Ти взяв/ла карти..', reply_markup=types.ReplyKeyboardRemove())
            await self.dp.bot.send_message(self.id, f'😱 {self.defender.name} взяв/ла карти.')
            return await self._move()


        score, suit = message.text[:-1], message.text[-1:]
        self.defend_card = Card(score, suit)
        await message.answer(f'[ЗАХИСТ] Вибрано карту: {self.defend_card}', reply_markup=types.ReplyKeyboardRemove())

        if self.can_beat(self.attack_card, self.defend_card):
            self.playholder.append(self.defend_card)
            self.defender.cards.remove(self.defend_card)

            if self.can_throw_up(self.attacker):
                return await self._make_move(self.attacker, 'attack')
            
            await self.dp.bot.send_message(
                chat_id=self.id,
                text=f"{self.defender.name} відбився за допомогою {self.defend_card}. {self.attacker.name} не має що підкинути."
            )
            self.playholder = list()
            await self._move()

        else:
            await message.answer('Ти не можеш битись цією картою 🥸')
            await self._make_move(self.defender, 'defend')


    async def _remove_blank_players(self):
        """ Прибирає гравців без карт з гри.
        """
        if not len(self.attacker.cards):
            self.players.remove(self.attacker)
        if not len(self.defender.cards):
            self.players.remove(self.defender)


    async def _fill_players_from_deck(self):
        """ Заповнює гравцім картами якщо їх менше ніж 6.
        """
        for player in self.players:
            if len(player.cards) < 6:
                need_cards = 6 - len(player.cards)
                deck_lenght = len(self.deck.stack)
                
                if deck_lenght < need_cards:
                    need_cards = deck_lenght

                player.cards.extend(self.deck.stack[-need_cards:])
                self.deck.stack = self.deck.stack[:-need_cards]


    async def _set_players(self):
        self._move_index %= len(self.players)
        self.attacker = self.players[self._move_index - 1]
        self.defender = self.players[self._move_index]


    async def _move(self):
        await self._fill_players_from_deck()
        await self._remove_blank_players()

        if len(self.players) <= 1:
            self.is_started = False
            loser = self.players.pop()
            return await self.dp.bot.send_message(self.id, text=f"🤡 Дурак: {loser.name}\n🃏 Залишились карти {loser.cards}")

        await self._set_players()
        await self._make_move(self.attacker, 'attack')

        self._move_index += 1
        self.playholder = list()
