import random

from dataclasses import dataclass

from player import Player
from villager import Villager
from pirate import Pirate
from merchant import Merchant
from merchant import Shop
from .enums import ActionChoice, MerchantActionChoice, PirateActionChoice, VillagerActionChoice


@dataclass
class Simulation:
    players: list[Player]
    day: int = 0
    DAY_MAX : int = 10000
    item_list = list[Shop]

    @property
    def pirate_list(self) -> list[Pirate]:
        return [p for p in self.players if isinstance(p, Pirate)]
    
    @property
    def villager_list(self) -> list[Villager]:
        return [v for v in self.players if isinstance(v, Villager)]
    
    @property
    def merchant_list(self) -> list[Merchant]:
        return [m for m in self.players if isinstance(m, Merchant)]
    
    @property
    def list_of_all_items(self) -> list[Shop]:
        all_items = []
        for merchant in self.merchant_list:
            all_items.extend(merchant.store)
        return all_items
    
    def random_integer(self, minimum: int, maximum: int) -> int:
        return random.randint(minimum, maximum)
    

    def step(self,player : Player) -> None :
        player.step()

        if isinstance(player, Villager):
            match player.action_choice:
                case ActionChoice.Buy:
                    items = self.list_of_all_items
                    if items:
                        player.target = random.choice(items)
                case ActionChoice.Barter:
                    pirates = self.pirate_list
                    if pirates:
                        player.target = random.choice(pirates)

        elif isinstance(player, Pirate):
            match player.action_choice:
                case ActionChoice.Theft:
                    villagers = self.villager_list
                    if villagers:
                        player.target = random.choice(villagers)
                case ActionChoice.Rest:
                    items = self.list_of_all_items
                    if items:
                        player.target = random.choice(items)

        elif isinstance(player, Merchant):
            if player.store:
                player.target = self.random_integer(1, len(player.store))

        
    def run(self):
        while self.day < self.DAY_MAX:
            for player in self.players:
                if not player.can_play:
                    continue
                self.step(player)
            self.day += 1
                

if __name__ == "__main__":
    simulation = Simulation()
    print(type(simulation.item_list))
    #simulation.run()