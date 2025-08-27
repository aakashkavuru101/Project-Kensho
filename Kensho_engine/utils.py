# kensho_engine/utils.py
import configparser
import logging

def load_config(path: str = 'config.ini'):
    """
    Loads the configuration file.
    """
    config = configparser.ConfigParser()
    try:
        if not config.read(path):
            logging.error(f"Configuration file not found or is empty: {path}")
            return None
        return config
    except configparser.Error as e:
        logging.error(f"Error parsing configuration file: {e}")
        return None
