'''
player.py

Defines the Player class for a Monopoly game using a dataclass, including core attributes and behaviors.
'''

from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class Player:

    name: str
    token: str
    money: int = 1500
    position: int = 0
    properties: List[Any] = field(default_factory=list)
    get_out_of_jail_free: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    bankrupt: bool = False

    def move(self, steps: int, board_size: int = 40) -> int:
        """
        Move the player forward by 'steps'.
        Pass GO (position 0) to collect $200.

        Returns:
            int: New position on the board.
        """
        if self.bankrupt:
            return self.position

        old_pos = self.position
        self.position = (self.position + steps) % board_size
        # Passed or landed on GO
        if self.position < old_pos:
            self.receive(200)
        return self.position

    def move_to(self, new_position: int, collect_go: bool = False) -> None:
        """
        Move directly to 'new_position'.
        Optionally collect $200 if passing GO.
        """
        if self.bankrupt:
            return

        old_pos = self.position
        self.position = new_position
        if collect_go and self.position < old_pos:
            self.receive(200)

    def pay(self, amount: int) -> bool:
        """
        Attempt to pay 'amount'.

        Returns:
            bool: True if payment succeeded, False if bankrupt.
        """
        if amount <= 0:
            return True

        self.money -= amount
        if self.money < 0:
            self.declare_bankruptcy()
            return False
        return True

    def receive(self, amount: int) -> None:
        """
        Receive 'amount' of money.
        """
        if amount > 0:
            self.money += amount

    def net_worth(self) -> int:
        """
        Compute net worth as cash plus property values.
        Assumes each property has a 'value' attribute.
        """
        return self.money + sum(getattr(prop, 'value', 0) for prop in self.properties)

    def buy_property(self, prop: Any) -> bool:
        """
        Buy a property if affordable.

        Returns:
            bool: True if purchase succeeded.
        """
        price = getattr(prop, 'price', None)
        if price is None or price < 0:
            return False
        if self.pay(price):
            self.properties.append(prop)
            return True
        return False

    def go_to_jail(self) -> None:
        """
        Sends the player to jail (position 10).
        """
        self.in_jail = True
        self.jail_turns = 0
        self.position = 10

    def use_get_out_of_jail_free_card(self) -> bool:
        """
        Use a "Get Out of Jail Free" card if available.

        Returns:
            bool: True if card used successfully.
        """
        if self.get_out_of_jail_free > 0 and self.in_jail:
            self.get_out_of_jail_free -= 1
            self.in_jail = False
            self.jail_turns = 0
            return True
        return False

    def declare_bankruptcy(self) -> None:
        """
        Mark the player as bankrupt and clear assets.
        """
        self.bankrupt = True
        self.properties.clear()
        self.money = 0

    def __str__(self) -> str:
        return (
            f"Player({self.name}, Token={self.token}, Money=${self.money}, "
            f"Position={self.position}, Properties={len(self.properties)}, "
            f"JailFree={self.get_out_of_jail_free}, InJail={self.in_jail}, "
            f"Bankrupt={self.bankrupt})"
        )
