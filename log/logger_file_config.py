import logging
import os

def setup_logging():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(current_dir, 'game_logging.log')
    
    logging.basicConfig(
        filename=log_path,
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True
    )