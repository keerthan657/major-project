from pymongo.mongo_client import MongoClient
from configuration import get_atlas_uri

class MongoDB:

    def __init__(self, db_name, collection_name):
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = MongoClient(get_atlas_uri())
        self.connection = self.get_collection()

    def get_collection(self):
        db = self.client.db_name
        return db[self.connection]
    
    def issue_ping(self):
        try:
            self.client.admin.command('ping')
            print("issue_ping: Successfully connected to MongoDB")
        except e:
            print("issue_ping - error: ", e)
    
    def send_single_data(self, data):
        try:
            result = self.collection.insert_single(data)
        except e:
            print("send_single_data failed - error: ", e)
        
    def send_many_data(self, data):
        try:
            result = self.collection.insert_many(data)
        except e:
            print("send_many_data failed - error: ", e)