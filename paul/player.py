from dataclasses import dataclass
from property import Property

@dataclass
class Player:
    ''' 
    Player class for the game Monopoly. 
    '''
    def __init__(self, name):
        self.name = name
        self.position = 0
        self.money = 1500
        self.properties = []
        self.in_jail = False
        self.jail_turns = 0
        self.get_out_of_jail_free_cards = 0
        self.bankrupt = False
        
    def move(self, spaces) -> int:
        ''' 
        Moves the player a certain number of spaces on the board.
        '''
        self.position = (self.position + spaces) % 40
        return self.position
    
    def go_to(self, position) -> int:
        ''' 
        Moves the player to a specific position on the board.
        '''
        self.position = position
        return self.position
    
    def add_money(self, amount) -> int:
        ''' 
        Adds a certain amount of money to the player's balance.
        '''
        self.money += amount
        return self.money
    
    def remove_money(self, amount) -> int:
        ''' 
        Removes a certain amount of money from the player's balance.
        '''
        self.money -= amount
        return self.money
    
    def buy_property(self, property) -> bool:
        ''' 
        Allows the player to buy a property if they have enough money and sets the owner of the property to the player.
        '''
        if self.money >= property.buy_price:
            self.remove_money(property.buy_price)
            self.properties.append(property)
            property.owner = self.name
            return True
        return False

    def go_to_jail(self) -> None:
        ''' 
        Moves the player to jail.
        '''
        self.in_jail = True
        self.position = 10

    def leave_jail(self) -> None:
        ''' 
        Moves the player out of jail.
        '''
        self.in_jail = False
        self.jail_turns = 0
        
    def is_bankrupt(self) -> bool:
        ''' 
        Checks if the player is bankrupt.
        '''
        return self.bankrupt()
    
    def __str__(self) -> str:
        ''' 
        Returns a string representation of the player.
        '''
        return f"{self.name} - {self.money} - {self.position} - {self.properties} - {self.in_jail} - {self.jail_turns} - {self.get_out_of_jail_free_cards} - {self.bankrupt}"
    
    def __repr__(self) -> str:
        ''' 
        Returns a string representation of the player.
        '''
        return self.__str__()
        
    def __eq__(self, other) -> bool:
        ''' 
        Checks if two players are equal.
        '''
        return self.name == other.name
    
    def __hash__(self) -> int:
        ''' 
        Returns a hash of the player's name.
        '''
        return hash(self.name)
    
    
if __name__ == "__main__":
    player = Player("Player 1")
    print(player)
    property = Property("Property 1", "Red", 100, {1: 10, 2: 20, 3: 30, 4: 40, 5: 50}, 50, 100)
    print(property)
    try:
        player.buy_property(property)
    except ValueError as e:
        print(e)
    print(player)
    player.add_money(100)
    print(player)
    player.go_to_jail()
    print(player)
    player.leave_jail()
    print(player)

    
