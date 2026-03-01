from dataclasses import dataclass

from events import load_events, save_events
from menu_data import load_menu, save_menu


@dataclass
class JsonContentStore:
    """JSON-backed content store that can be swapped for SQLite later."""

    def get_events(self):
        return load_events()

    def save_events(self, events):
        save_events(events)

    def get_menu(self):
        return load_menu()

    def save_menu(self, menu):
        save_menu(menu)


def create_store():
    return JsonContentStore()
