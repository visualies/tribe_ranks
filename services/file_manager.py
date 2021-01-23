import json


def load_config():
    file = open("./services/config/config.json")
    config = json.load(file)  
    return config
