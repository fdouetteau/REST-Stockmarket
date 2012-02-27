
from mongo_market import MongoBaseStockmarket 
import utils

class NaiveStockmarket(MongoBaseStockmarket):    
    def trade(self, user1, content1, user2, content2):
        p2  = self.mongodb.portofolio.find_one({ "user" : user2 })
        p1  = self.mongodb.portofolio.find_one({ "user" : user1 })
        utils.portofolio_add(p2['content'], content1, sign = 1 )
        utils.portofolio_add(p1['content'], content1, sign = -1 )
        utils.portofolio_add(p1['content'], content2, sign=1)
        utils.portofolio_add(p2['content'], content2, sign=-1)
        self.mongodb.portofolio.update({"_id" : p1['_id']}, p1)
        self.mongodb.portofolio.update({"_id" : p2['_id']}, p2)
    def distribute(self, user, content):
        p1  = self.mongodb.portofolio.find_one({ "user" : user}) 
        if not p1: 
            self.mongodb.portofolio.insert({ 'user' : user, 'content' : content })
        else:
            utils.portofolio_add(p1['content'], content, 1)
            self.mongodb.portofolio.update({"_id" : p1['_id']}, p1)


