import os
import json

MENU_FILE = os.path.join("data", "menu.json")

DEFAULT_MENU = [
    {
        "section": "Daily Specials",
        "items": [
            {"name": "Taco Tuesday", "description": "Tacos — $3 | Burrito — $12 | Burrito Bowl — $14\nChicken, Steak, Fish, Pork, Pastor, Veggie\nFor Shrimp or Tongue add $1"},
            {"name": "WTF Wednesday", "description": "WHO THE F#$% Knows? Ask your server."},
            {"name": "Thirsty Thursday", "description": "Texas Burger & 16oz Draft Beer — $19.99\n12oz Cider — $3"},
            {"name": "Fried Chicken Friday", "description": "(Includes sides) 4pc — $19 | 8pc — $29"},
            {"name": "Smoked Saturday", "description": "Ribs, Salmon, Pork, or Brisket Plate with 1 side — $19\nSandwich with fries — $16"},
        ]
    },
    {
        "section": "Drinks",
        "items": [
            {"name": "Beer", "description": "We have several rotating taps of micro, macro, nano, regional breweries and everything in between. Plus numerous varieties of 12–19oz canned beer, agua fresca, hard kombucha, cider and cocktails."},
            {"name": "Wine", "description": "Wine available by glass or bottle. Beer and wine also offered to go."},
        ]
    }
]


def load_menu():
    if not os.path.exists(MENU_FILE):
        return DEFAULT_MENU
    with open(MENU_FILE, "r") as f:
        return json.load(f)


def save_menu(menu):
    directory = os.path.dirname(MENU_FILE)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(MENU_FILE, "w") as f:
        json.dump(menu, f, indent=2)
