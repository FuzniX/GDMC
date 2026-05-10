import logging
from log.logger_file_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

from src.simulation.simulation import Simulation, DAY_MAX
from src.simulation.simulation import Simulation, DAY_MAX
from src.simulation.pirate import Pirate, PirateCrew
from src.simulation.merchant import Merchant, Shop
from src.simulation.villager import Villager


def start_simulation():
    logger.info("--- BEGINING OF THE SIMULATION ---")

    crew = PirateCrew(money=500)
    m1 = Merchant(_money=2000)
    for _ in range(3):
        m1.store.append(Shop.from_item(owner=m1))
    m1.store[0].is_food = True
    m1.store[0].owned_quantity = 100

    players = [
        Pirate(crew=crew, food=10),
        m1,
        Villager(_money=100, happiness=50)
    ]

    sim = Simulation(players=players)
    
    try:
        for day in range(DAY_MAX):
            sim.step()
    finally:
        logger.info("--- END OF THE SIMULATION ---")
        logging.shutdown() 

if __name__ == "__main__":
    start_simulation()