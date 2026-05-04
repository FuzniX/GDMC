import random

from dataclasses import dataclass

from player import Player
from villager import Villager
from pirate import Pirate
from merchant import Merchant
from merchant import Item
from .enums import ActionChoice, MerchantActionChoice, PirateActionChoice, VillagerActionChoice


@dataclass
class Simulation:
    players: list[Player]
    day: int = 0
    DAY_MAX : int = 10000
    item_list = []

    def pirate_list(self) -> list[Pirate]:
        pirate_list : list[Pirate] = []
        for i in range(len(self.players)):
            if isinstance(self.players[i], Pirate):
                pirate_list.append(self.players[i])
        return pirate_list
    
    def villager_list(self) -> list[Villager]:
        villager_list : list[Villager] = []
        for i in range(len(self.players)):
            if isinstance(self.players[i], Villager):
                villager_list.append(self.players[i])
        return villager_list
    
    def merchant_list(self) -> list[Merchant]:
        merchant_list : list[Merchant] = []
        for i in range(len(self.players)):
            if isinstance(self.players[i], Merchant):
                merchant_list.append(self.players[i])
        return merchant_list
    
    def list_of_all_items(self,merchant_list : list[Merchant]) -> None:
        for merchant in merchant_list:
            self.item_list += merchant.inventory 
    
    def random_integer(minimum: int, maximum: int) -> int :
        return random.randint()
    
    def merchant_associated_to_player(player: Player, merchant_list: list[Merchant]) -> Merchant:
        for merchant in merchant_list:
            if merchant is player: 
                return merchant
        return None

    def run(self):
        while self.day < self.DAY_MAX :
            for i in range(len(self.players)):
                if self.players[i].can_play:
                    if isinstance(self.players[i], Villager):
                        match self.players[i].action_choice:
                            case ActionChoice.Buy:
                                self.list_of_all_item(self.merchant_list())
                                random_target = self.random_integer(0, len(self.item_list))
                                self.players[i].target = self.item_list[random_target]
                            case ActionChoice.Barter:
                                pirate_list = self.pirate_list()
                                random_target = self.random_integer(0, len(pirate_list))
                                self.players[i].target = pirate_list[random_target]
                    elif isinstance(self.players[i], Pirate):
                        match self.players[i].action_choice:
                            case ActionChoice.Theft:
                                villager_list = self.villager_list()
                                random_target = self.random_integer(0, len(villager_list))
                                self.players[i].target = villager_list[random_target]
                            case ActionChoice.Rest:
                                self.list_of_all_item(self.merchant_list())
                                random_target = self.random_integer(0, len(self.item_list))
                                self.players[i].target = self.item_list[random_target]
                    else:
                        match self.players[i].action_choice:
                            case ActionChoice.IncreasePrice:
                                merchant = self.merchant_associated_to_player(self.players[i], self.merchant_list)
                                if merchant:
                                    random_target = self.random_integer(0, len(merchant.inventory))
                                    self.players[i].target = merchant.inventory[random_target]
                            case ActionChoice.DecreasePrice:
                                merchant = self.merchant_associated_to_player(self.players[i], self.merchant_list)
                                if merchant:
                                    random_target = self.random_integer(0, len(merchant.inventory))
                                    self.players[i].target = merchant.inventory[random_target]
                self.player[i].step()
                

if __name__ == "__main__":
    simulation = Simulation()
    print(type(simulation.item_list))
    #simulation.run()
    

            