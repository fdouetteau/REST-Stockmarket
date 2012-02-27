
import pymongo
import utils

class MongoBaseStockmarket(object): 
    def get_portofolio(self, user):
        portofolio = self.mongodb.portofolio.find_one({ "user" : user})  
        return utils.content_cleanup(portofolio['content'])
    
    def setMongo(self, host, db):
        self.connection = pymongo.Connection(host=host)
        self.mongodb = self.connection[db]