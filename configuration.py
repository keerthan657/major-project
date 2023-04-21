import yaml

with open('configuration.yaml', 'r') as file:
    data = yaml.load(file, Loader=yaml.FullLoader)

def get_atlas_uri():
    uri = data['MONGO_ATLAS_URI']
    password = data['MONGO_PASSWORD']
    return uri.replace('<password>', password)

def get_controller_timeperiod():
    timep = data['CONTROLLER_TIMEPERIOD']
    return int(timep)