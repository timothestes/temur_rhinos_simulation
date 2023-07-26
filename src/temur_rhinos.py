import csv
import os
import random
from collections import deque
from typing import Optional, Tuple

# if you are feeling crazy...
# N_CYCLERS_TO_TRY = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
# N_LANDS_TO_TRY = [26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10]

# normal parameters
N_CYCLERS_TO_TRY = [0, 1, 2, 3, 4]
N_LANDS_TO_TRY = [26, 25, 24, 23, 22, 21, 20, 19, 18]
N_GAMES = 10000
N_TURNS = 3
ON_THE_PLAY = True


class Card:
    def __init__(self, card_type: str):
        self.card_type = card_type

    def __str__(self):
        return f"{self.card_type} card"


class Deck:
    def __init__(self, cards: deque):
        self.cards = cards

    def shuffle(self):
        """Randomize the list of cards."""
        random.shuffle(self.cards)

    def draw(self) -> Card:
        """Return the first card of the deck."""
        if not self.cards:
            raise ValueError("Deck is empty. Cannot draw a card.")
        return self.cards.popleft()

    def draw_n(self, number_of_cards_to_draw: int) -> list[Card]:
        """Return the first n cards of the deck."""
        if number_of_cards_to_draw <= 0:
            raise ValueError("Number of cards to draw should be greater than zero.")

        if number_of_cards_to_draw > len(self.cards):
            raise ValueError("Not enough cards in the deck to draw the specified number.")

        drawn_cards = [self.cards.popleft() for _ in range(number_of_cards_to_draw)]
        return drawn_cards

    def search_for(self, card_type: str) -> Optional[Card]:
        """Return a card of the given type and remove it from the deck if found."""
        for _ in range(len(self.cards)):
            card = self.cards[0]
            if card.card_type == card_type:
                self.cards.popleft()
                return card
            self.cards.rotate(-1)
        return None

    def cards_in_deck(self):
        return len(self.cards)

    def shuffle_in(self, cards: list[Card]) -> None:
        """Take a list of cards and shuffle them into the deck."""
        self.cards.extend(cards)
        self.shuffle()

    def bottom_cards(self, cards: list[Card], random_order=False) -> None:
        """Return some cards to the bottom of the deck."""
        if random_order:
            random.shuffle(cards)
        self.cards.extend(cards)


class Zone:
    def __init__(self, cards: Optional[list[Card]] = None):
        self._zone = cards or []
        self._card_types = {card_type: 0 for card_type in ["Land", "Non-Land", "Cycler"]}
        for card in self._zone:
            self._card_types[card.card_type] += 1

    def add(self, cards):
        if isinstance(cards, list):
            for card in cards:
                self.append(card)
        else:
            self.append(cards)

    def append(self, card: Card):
        self._zone.append(card)
        self._card_types[card.card_type] += 1

    def count(self, card_type: str):
        return self._card_types.get(card_type, 0)

    def remove(self, card_type: str):
        for card in self._zone:
            if card.card_type == card_type:
                self._zone.remove(card)
                self._card_types[card_type] -= 1
                return card
        return None

    def __str__(self):
        return ", ".join(str(card) for card in self._zone)

    @property
    def cards(self) -> list[Card]:
        return self._zone


class Hand(Zone):
    def __init__(self, cards: Optional[list[Card]] = None):
        super().__init__(cards if cards else [])


class Play(Zone):
    def __init__(self, cards: Optional[list[Card]] = None):
        super().__init__(cards if cards else [])


class Discard(Zone):
    def __init__(self, cards: Optional[list[Card]] = None):
        super().__init__(cards if cards else [])


class Simulation:
    def __init__(
        self,
        n_lands: int,
        n_cyclers: int,
        n_games: int,
        n_turns: int,
        on_the_play: bool,
    ):
        self.n_lands = n_lands
        self.n_cyclers = n_cyclers
        self.n_games = n_games
        self.n_turns = n_turns
        self.on_the_play = on_the_play

    def _determine_mulligans(self) -> Tuple[Hand, Deck]:
        """Adjust the hand and the deck to take mulligans."""
        # determine if to take a mulligan
        num_mulligans = 0
        # if you don't have any land cards in hand its a mulligan
        # if you also have only one land card in hand an NO cyclers, its also a mulligan
        while self.hand.count("Land") < 1 or (
            self.hand.count("Land") == 1 and self.hand.count("Cycler") == 0
        ):
            # if mulligan, shuffle the hand back in, draw 7 cards,
            self.deck.bottom_cards(self.hand.cards)
            self.deck.shuffle()
            self.hand = Hand(self.deck.draw_n(7))
            num_mulligans += 1
            # bubble any games with more than 5 mulligans
            if num_mulligans > 5:
                raise AssertionError("greater than 5 mulligans reached")

        # mulligan logic
        if num_mulligans > 1:
            for _ in range(num_mulligans):
                if (self.hand.count("Cycler") + self.hand.count("Land")) > 3:
                    if self.hand.count("Cycler") > 0:
                        # if we have "enough" lands, we don't need extra cyclers
                        self.deck.bottom_cards([self.hand.remove("Cycler")])
                    else:
                        # if we have "enough" lands, we don't need extra lands
                        self.deck.bottom_cards([self.hand.remove("Land")])
                else:
                    # we don't have enough lands or cyclers and need to bottom a non-land
                    self.deck.bottom_cards([self.hand.remove("Non-Land")])

    def generate_deck(self, n_lands, n_cyclers) -> list[Card]:
        """Generate a deck based upon certain parameters."""
        deck_of_cards = deque()

        # Add lands to the deck
        for _ in range(n_lands):
            deck_of_cards.append(Card("Land"))

        # Add cyclers to the deck
        for _ in range(n_cyclers):
            deck_of_cards.append(Card("Cycler"))

        # Add non-lands to the deck
        n_nonlands = 60 - (n_lands + n_cyclers)
        for _ in range(n_nonlands):
            deck_of_cards.append(Card("Non-Land"))

        return deck_of_cards

    def _take_a_turn(
        self,
        turn_number: int,
        sim_number: int,
    ) -> dict:
        """Take a turn of mtg."""
        land_for_turn = False
        cycled_this_turn = False
        # draw a card for turn (except if on the play)
        if not (self.on_the_play and turn_number == 1):
            drawn_card = self.deck.draw()
            self.hand.add(drawn_card)

        # then placing one land card from hand into play (if you have one)
        if self.hand.count("Land") > 0:
            self.play.add(self.hand.remove("Land"))
            land_for_turn = True

        # check to see if you have at least ONE land in play and ONE cycler in hand
        if self.play.count("Land") >= 1 and self.hand.count("Cycler") >= 1:
            # only need to cycle if its not turn 3 and we already have 3 lands in play
            if not (turn_number == 3 and self.play.count("Land") == 3):
                # "tap" the land and discard the cycler to search your deck for a land and put it into hand
                self.discard.add(self.hand.remove("Cycler"))
                land_card = self.deck.search_for("Land")
                cycled_this_turn = True
                if land_card is not None:
                    self.hand.add(land_card)

                # if you haven't played a land this turn, play the land you just searched for with the cycler
                if not land_for_turn and self.hand.count("Land") > 0:
                    self.play.add(self.hand.remove("Land"))
                    land_for_turn = True

        # at the end of the turn, if we are over 7 cards in hand, discard a non-land card:
        if len(self.hand.cards) > 7:
            if self.hand.count("Non-Land") > 0:
                self.discard.add(self.hand.remove("Non-Land"))
            else:
                # if for some reason we have 8 cards in hand and no non-lands, discard a land.
                self.discard.add(self.hand.remove("Land"))

        # return the turn log
        return {
            "simulation": sim_number,
            "turn": turn_number,
            "n_cards_in_deck": len(self.deck.cards),
            "n_cards_in_hand": len(self.hand.cards),
            "n_lands_in_play": self.play.count("Land"),
            "n_cyclers_in_discard": self.discard.count("Cycler"),
            "n_cyclers_in_hand": self.hand.count("Cycler"),
            "n_lands_in_hand": self.hand.count("Land"),
            "n_lands_in_starting_deck": self.n_lands,
            "n_cyclers_in_starting_deck": self.n_cyclers,
            # can only play cascade this turn if we have 3 lands in play and we didn't cycle this turn.
            "can_play_cascade": self.play.count("Land") >= 3 and not cycled_this_turn,
        }

    @staticmethod
    def create_empty_log_file():
        """Create empty log file."""
        headers = [
            "simulation",
            "turn",
            "n_cards_in_deck",
            "n_cards_in_hand",
            "n_lands_in_play",
            "n_cyclers_in_discard",
            "n_cyclers_in_hand",
            "n_lands_in_hand",
            "n_lands_in_starting_deck",
            "n_cyclers_in_starting_deck",
            "can_play_cascade",
        ]
        with open("game_log.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

    @staticmethod
    def print_file_size(filename: str) -> None:
        """Print the size of a file in bytes"""
        size = os.path.getsize(filename)
        size_kb = size / 1024  # size in kilobytes
        print(f"The size of '{filename}' is {size_kb} kilobytes")

    @staticmethod
    def append_log_to_file(dict_to_add: list[dict], csv_file: str) -> None:
        """Add a row of log data to the csv file"""
        with open(csv_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=dict_to_add[0].keys())
            writer.writerows([row for row in dict_to_add])

    def simulate_game(self) -> None:
        """Simulate a game of Temur Rhinos to try and find probabilities!"""
        # Create the deck of cards
        deck_of_cards = self.generate_deck(self.n_lands, self.n_cyclers)

        # for x in n_games
        for sim_number in range(self.n_games):
            # Create a deck object based on the list of cards we created
            self.deck = Deck(deque(deck_of_cards.copy()))
            self.deck.shuffle()

            # create empty zones
            self.play = Play(cards=[])
            self.discard = Discard(cards=[])
            self.hand = Hand(cards=[])

            # draw 7 cards from deck
            self.hand.add(self.deck.draw_n(7))

            try:
                self._determine_mulligans()
            except AssertionError:
                # Ignore games with more than 5 mulligans in them
                continue

            # Log file for the current game simulation
            log_file = []
            for turn_number in range(1, self.n_turns + 1):
                # take a turn
                turn_log = self._take_a_turn(turn_number, sim_number)
                # save the turn log to the current log file
                log_file.append(turn_log)

            # After all simulations are done, append to the file
            self.append_log_to_file(log_file, "game_log.csv")


if __name__ == "__main__":
    Simulation.create_empty_log_file()
    for n_lands in N_LANDS_TO_TRY:
        for n_cyclers in N_CYCLERS_TO_TRY:
            simulation = Simulation(
                n_lands=n_lands,
                n_cyclers=n_cyclers,
                n_games=N_GAMES,
                n_turns=N_TURNS,
                on_the_play=ON_THE_PLAY,
            )
            simulation.simulate_game()
            print(
                f"Finished a simulation for n_lands: {n_lands}, n_cyclers: {n_cyclers}, n_games: {N_GAMES}"
            )
