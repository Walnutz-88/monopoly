from dataclasses import dataclass

@dataclass
class RegularProperty:
    name: str
    color: str
    buy_price: int
    rent_price: dict
    house_hotel_price: int
    position: int
    house_count: int = 0
    owner: str = None
    mortgaged: bool = False
    
    def __str__(self):
        return f"{self.name} - {self.buy_price} - {self.rent_price} - {self.house_hotel_price} - {self.house_count} - {self.owner} - {self.mortgaged}"
    
@dataclass
class RailroadProperty:
    name: str
    buy_price: int
    rent_price: dict
    position: int
    owner: str = None
    mortgaged: bool = False
    
    def __str__(self):
        return f"{self.name} - {self.buy_price} - {self.rent_price} - {self.owner} - {self.mortgaged}"
    
@dataclass
class UtilityProperty:
    name: str
    buy_price: int
    rent_price: dict
    position: int
    owner: str = None
    mortgaged: bool = False
    
    def __str__(self):
        return f"{self.name} - {self.buy_price} - {self.rent_price} - {self.owner} - {self.mortgaged}"
