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

def get_mongodb_dbname():
    dbname = data['MONGODB_DB_NAME']
    return dbname

def get_mongodb_collectionname():
    cname = data['MONGODB_COLLECTION_NAME']
    return cname

def get_ml_windowsize():
    ws = data['WINDOW_SIZE']
    return int(ws)

def get_dl_model():
    dlm = data['DL_MODEL']
    return dlm