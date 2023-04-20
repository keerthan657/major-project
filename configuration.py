import yaml

with open('configuration.yaml', 'r') as file:
    data = yaml.load(file, Loader=yaml.FillLoader)

def get_atlas_uri():
    uri = data['MONGO_ATLAS_URI']
    password = data['MONGO_PASSWORD']
    return uri.replace('<password>', password)