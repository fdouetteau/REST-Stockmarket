import utils
from mongo_market import MongoBaseStockmarket

class LessNaiveStockmarket(MongoBaseStockmarket):        
    def trade(self, user_1, content_1, user_2, content_2):
        update_1 = utils.build_update_obj(content_2, neg=content_1)
        update_2 = utils.build_update_obj(content_1, neg=content_2)
        self.mongodb.portofolio.update({ "user":user_1 }, { "$inc" : update_1 }, safe=True )
        self.mongodb.portofolio.update({ "user":user_2 }, { "$inc" : update_2 }, safe=True )
        
    def distribute(self, user, content):
        update_obj = utils.build_update_obj(content)
        ret = self.mongodb.portofolio.update({ "user" : user}, { "$inc" : update_obj }, safe=True)
        if not ret['updatedExisting']:
            self.mongodb.portofolio.insert({ "user" : user, "content" : content }, safe=True)
