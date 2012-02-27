from mongo_market import MongoBaseStockmarket 
import utils
import time

# Build a query object that checks that a portofolio at least the stocks to trade  
def build_check_obj(p):
    check = {} 
    for m in p:
        check["content." + m] = { "$gte" : p[m]}
    return check

class LockStockmarket(MongoBaseStockmarket):
    def trade(self, user_1, content_1, user_2, content_2):
        update_1 = utils.build_update_obj(content_2, neg=content_1)
        update_2 = utils.build_update_obj(content_1, neg=content_2)    
        check_1 = build_check_obj(content_1)
        check_2 = build_check_obj(content_2)
        check_1.update({ "user":user_1, "_locked": 1 })
        check_2.update({ "user":user_2, "_locked": 1 })
        ## Acquire a lock on object. 
        while True:     
            t = time.time()
            elasped = t - 30  
            # To lock an object, we set a _locked attributed and a _lock_time
            # The lock is considered to be  valid for only 30 seconds. 
            # A expiring lock is necessary to protect from crash of this thread in mid-air. 
            lock_check_expr =  { '$or' : [{ "_locked" : { "$ne" : 1 } } , { "$le" : { "_lock_time" : elasped } }  ]  }
            ret = self.mongodb.portofolio.update({ "$and" : [ {"user":user_1}, lock_check_expr] }, { "$set" : { "_locked" : 1, "_lock_time" : t  } }  , safe=True)
            if not ret['updatedExisting']: 
                # Unable to lock the object : retry
                # (A better implementation would check that the object actually exists in the database, and have some retry limit)
                time.sleep(0.5)
                continue 
            ret = self.mongodb.portofolio.update({ "$and": [ {"user":user_2}, lock_check_expr] } , { "$set" : { "_locked" : 1, "_lock_time" : t } } , safe=True)
            if not ret['updatedExisting']: 
                # Release lock on 1 
                self.mongodb.portofolio.update({ "user":user_1, "_locked" : 1 } , { "$unset" : { "_locked" : 1 } } , safe=True)
                time.sleep(0.5)
                continue
            break 
        
        ## We perform atomically a check on availability and update on each objects, under the common lock      
        ret = self.mongodb.portofolio.update(check_1, { "$inc" : update_1 }, safe=True )
        if not ret['updatedExisting']:
            raise Exception()
        ret = self.mongodb.portofolio.update(check_2, { "$inc" : update_2 }, safe=True )
        if not ret['updatedExisting']: 
            raise Exception()        
        ## Release the lock on objects
        self.mongodb.portofolio.update({ "user":user_1, "_locked" : 1 } , { "$unset" : { "_locked" : 1 } } , safe=True)
        self.mongodb.portofolio.update({ "user":user_2, "_locked" : 1 } , { "$unset" : { "_locked" : 1 } } , safe=True)

    def distribute(self, user, content):
        update_obj = utils.build_update_obj(content)
        ret = self.mongodb.portofolio.update({ "user" : user}, { "$inc" : update_obj }, safe=True)
        if not ret['updatedExisting']:
            self.mongodb.portofolio.insert({ "user" : user, "content" : content }, safe=True)
