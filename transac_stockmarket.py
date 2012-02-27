from mongo_market import MongoBaseStockmarket 
import utils

class TransacStockmarket(MongoBaseStockmarket):
    def trade(self, user1, content1, user2, content2): 
        trade_order = {}
        trade_order['user_1'] = user1
        trade_order['content_1'] = content1
        trade_order['user_2'] = user2
        trade_order['content_2'] = content2   
        credit_for_1 = utils.build_update_obj(content2)
        debit_for_1 = utils.build_update_obj(content1, sign=-1)
        credit_for_2 = utils.build_update_obj(content1, sign=1)
        debit_for_2 = utils.build_update_obj(content2, sign=-1)    
        check_1 = utils.build_check_obj(content1)
        check_2 = utils.build_check_obj(content2)
    
        # Insert the transaction in base
        trade_order['state'] = "running"
        t_id =  self.mongodb.transaction.insert(trade_order, safe=True)
    
        check_1.update({ "user":user1,  "debited" : { "$ne" : t_id}})
        check_2.update({ "user":user2,  "debited" : { "$ne" : t_id}})
    
        ## Try to apply all the debits 
        ret = self.mongodb.portofolio.update(check_1, { "$inc" : debit_for_1, "$push" : { "debited" : t_id} }, safe=True )
        if not ret['updatedExisting']:
            self.mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "failed" }})
            raise Exception()
        ret = self.mongodb.portofolio.update(check_2, { "$inc" : debit_for_2, "$push" : { "debited" : t_id } }, safe=True )
        if not ret['updatedExisting']:
            ## Rollback debit on 1 
            self.mongodb.portofolio.update({"user":user1 } , { "$inc":credit_for_2, "$pull" : { "debited" : t_id }}, safe=True)
            ## Notify failed transaction
            self.mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "failed" }}, safe=True)
            raise Exception() 

        # Notify Sucessfull debits. 
        self.mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "debited" }}, safe=True)
        if not ret['updatedExisting']:
             # Rollback
             ret = self.mongodb.portofolio.update({"user":user1 } , { "$inc":credit_for_2, "$pull" : { "debited" : t_id }}, safe=True)
             ret = self.mongodb.portofolio.update({"user":user2 } , { "$inc":credit_for_1, "$pull" : { "debited" : t_id }}, safe=True)
             self.mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "failed" }}, safe=True)
             raise Exception()

        # Apply all the credits    
        ret = self.mongodb.portofolio.update({"user": user1}, { "$inc" : credit_for_1,"$pull" : { "debited" : t_id }}, safe=True)
        if not ret['updatedExisting']:
            raise Exception()
        ret = self.mongodb.portofolio.update({"user": user2}, { "$inc" : credit_for_2,"$pull" : { "debited" : t_id }}, safe=True)
        if not ret['updatedExisting']:
            raise Exception()
        
        # Notify Sucessfull transaction. 
        self.mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "done" }}, safe=True)
        if not ret['updatedExisting']:
             raise Exception()        
    
    def distribute(self, user, content):
        update_obj = utils.build_update_obj(content)
        ret = self.mongodb.portofolio.update({ "user" : user}, { "$inc" : update_obj }, safe=True)
        if not ret['updatedExisting']:
            self.mongodb.portofolio.insert({"user": user, "content": content, 'debited' : []})

