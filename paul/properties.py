from dataclasses import dataclass

@dataclass
class RegularProperty:
    def __init__(self, name: str, color: str, buy_price: int, rent_price: dict, 
                 house_hotel_price: int, position: int, house_count: int = 0,
                 owner: str = None, mortgaged: bool = False):
        self.name = name
        self.color = color
        self.buy_price = buy_price
        self.rent_price = rent_price
        self.house_hotel_price = house_hotel_price
        self.house_count = house_count
        self.owner = owner
        self.mortgaged = mortgaged
        self.position = position
    
    
    
    def __str__(self):
        return f"{self.name} - {self.buy_price} - {self.rent_price} - {self.house_hotel_price} - {self.house_count} - {self.owner} - {self.mortgaged}"
    
@dataclass
class RailroadProperty:
    def __init__(self, name: str, buy_price: int, rent_price: dict, position: int, owner: str = None, mortgaged: bool = False):
        self.name = name
        self.buy_price = buy_price
        self.rent_price = rent_price
        self.owner = owner
        self.mortgaged = mortgaged
        self.position = position
        
    def __str__(self):
        return f"{self.name} - {self.buy_price} - {self.rent_price} - {self.owner} - {self.mortgaged}"
    
@dataclass
class UtilityProperty:
    def __init__(self, name: str, buy_price: int, rent_price: dict, position: int, owner: str = None, mortgaged: bool = False):
        self.name = name
        self.buy_price = buy_price
        self.rent_price = rent_price
        self.owner = owner
        self.mortgaged = mortgaged
        self.position = position
        
    def __str__(self):
        return f"{self.name} - {self.buy_price} - {self.rent_price} - {self.owner} - {self.mortgaged}"
