

from properties import RegularProperty, RailroadProperty, UtilityProperty

property_data = {
    "Brown": [
        {
            "name": "Mediterranean Avenue",
            "price": 60,
            "rent": [2, 4, 10, 30, 90, 160, 250],
            "house_cost": 50,
        },
        {
            "name": "Baltic Avenue",
            "price": 60,
            "rent": [4, 8, 20, 60, 180, 320, 450],
            "house_cost": 50,
        },
    ],
    "Light Blue": [
        {
            "name": "Oriental Avenue",
            "price": 100,
            "rent": [6, 12, 30, 90, 270, 400, 550],
            "house_cost": 50,
        },
        {
            "name": "Vermont Avenue",
            "price": 100,
            "rent": [6, 12, 30, 90, 270, 400, 550],
            "house_cost": 50,
        },
        {
            "name": "Connecticut Avenue",
            "price": 120,
            "rent": [8, 16, 40, 100, 300, 450, 600],
            "house_cost": 50,
        },
    ],
    "Pink": [
        {
            "name": "St. Charles Place",
            "price": 140,
            "rent": [10, 20, 50, 150, 450, 625, 750],
            "house_cost": 100,
        },
        {
            "name": "States Avenue",
            "price": 140,
            "rent": [10, 20, 50, 150, 450, 625, 750],
            "house_cost": 100,
        },
        {
            "name": "Virginia Avenue",
            "price": 160,
            "rent": [12, 24, 60, 180, 500, 700, 900],
            "house_cost": 100,
        },
    ],
    "Orange": [
        {
            "name": "St. James Place",
            "price": 180,
            "rent": [14, 28, 70, 200, 550, 750, 950],
            "house_cost": 100,
        },
        {
            "name": "Tennessee Avenue",
            "price": 180,
            "rent": [14, 28, 70, 200, 550, 750, 950],
            "house_cost": 100,
        },
        {
            "name": "New York Avenue",
            "price": 200,
            "rent": [16, 32, 80, 220, 600, 800, 1000],
            "house_cost": 100,
        },
    ],
    "Red": [
        {
            "name": "Kentucky Avenue",
            "price": 220,
            "rent": [18, 36, 90, 250, 700, 875, 1050],
            "house_cost": 150,
        },
        {
            "name": "Indiana Avenue",
            "price": 220,
            "rent": [18, 36, 90, 250, 700, 875, 1050],
            "house_cost": 150,
        },
        {
            "name": "Illinois Avenue",
            "price": 240,
            "rent": [20, 40, 100, 300, 750, 925, 1100],
            "house_cost": 150,
        },
    ],
    "Yellow": [
        {
            "name": "Atlantic Avenue",
            "price": 260,
            "rent": [22, 44, 110, 330, 800, 975, 1150],
            "house_cost": 150,
        },
        {
            "name": "Ventnor Avenue",
            "price": 260,
            "rent": [22, 44, 110, 330, 800, 975, 1150],
            "house_cost": 150,
        },
        {
            "name": "Marvin Gardens",
            "price": 280,
            "rent": [24, 48, 120, 360, 850, 1025, 1200],
            "house_cost": 150,
        },
    ],
    "Green": [
        {
            "name": "Pacific Avenue",
            "price": 300,
            "rent": [26, 52, 130, 390, 900, 1100, 1275],
            "house_cost": 200,
        },
        {
            "name": "North Carolina Avenue",
            "price": 300,
            "rent": [26, 52, 130, 390, 900, 1100, 1275],
            "house_cost": 200,
        },
        {
            "name": "Pennsylvania Avenue",
            "price": 320,
            "rent": [28, 56, 150, 450, 1000, 1200, 1400],
            "house_cost": 200,
        },
    ],
    "Dark Blue": [
        {
            "name": "Park Place",
            "price": 350,
            "rent": [35, 70, 175, 500, 1100, 1300, 1500],
            "house_cost": 200,
        },
        {
            "name": "Boardwalk",
            "price": 400,
            "rent": [50, 100, 200, 600, 1400, 1700, 2000],
            "house_cost": 200,
        },
    ],
    "Railroads": [
        {
            "name": "Reading Railroad",
            "price": 200,
            "rent": [25, 50, 100, 200],
        },
        {
            "name": "Pennsylvania Railroad",
            "price": 200,
            "rent": [25, 50, 100, 200],
        },
        {
            "name": "B. & O. Railroad",
            "price": 200,
            "rent": [25, 50, 100, 200],
        },
        {
            "name": "Short Line",
            "price": 200,
            "rent": [25, 50, 100, 200],
        },
    ],
    "Utilities": [
        {
            "name": "Electric Company",
            "price": 150,
            "rent": ["4× dice roll", "10× dice roll"],
        },
        {
            "name": "Water Works",
            "price": 150,
            "rent": ["4× dice roll", "10× dice roll"],
        },
    ],
}


def create_new_game():
    properties = []
    for group, names in property_data.items():
        if group == "Railroads":
            for name in names:
                prop = RailroadProperty(
                    name=name,
                    buy_price=name["price"],
                    rent_price=[25, 50, 100, 200],
                    owner=None,
                )
                properties.append(prop)
        elif group == "Utilities":
            for name in names:
                prop = UtilityProperty(
                    name=name,
                    buy_price=name["price"],
                    rent_price=[4, 10],
                    owner=None,
                )
                properties.append(prop)
        else:
            for name in names:
                prop = RegularProperty(
                    name=name,
                    color=group,
                    buy_price=name["price"],
                    rent_price=name["rent"],
                    house_hotel_price=name["house_cost"],
                    owner=None,
                )
                properties.append(prop)
    return properties


def main():
    print("Hello from capstone-project!")
    all_properties = create_new_game()
    for property in all_properties:
        print(property)


if __name__ == "__main__":
    main()
