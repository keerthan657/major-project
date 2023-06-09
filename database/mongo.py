from pymongo.mongo_client import MongoClient
from configuration import get_atlas_uri

class MongoDB:

    def __init__(self, db_name, collection_name):
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = MongoClient(get_atlas_uri())
        self.connection = self.get_collection()
        self.debugMode = True
    
    def printDebug(self, msg):
        if(self.debugMode):
            print(msg)

    def get_collection(self):
        db = self.client[self.db_name]
        return db[self.collection_name]
    
    def issue_ping(self):
        try:
            self.client.admin.command('ping')
            print("issue_ping: Successfully connected to MongoDB")
        except Exception as e:
            print("issue_ping - error: ", e)
    
    def send_single_data(self, data):
        try:
            result = self.connection.insert_one(data)
            # self.printDebug("send_single_data succeeded - record id: " + str(result.inserted_id))
            self.printDebug("send_single_data succeeded")
        except Exception as e:
            print("send_single_data failed - error: ", e)
        
    def send_many_data(self, data):
        try:
            result = self.connection.insert_many(data)
        except Exception as e:
            print("send_many_data failed - error: ", e)