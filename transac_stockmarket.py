from bottle import run, debug, request, Bottle, response
import os
import bottle_mongo
import utils

app = Bottle(autojson=False)
plugin = bottle_mongo.MongoPlugin(uri="mongodb://localhost/naive_stock", db="naive_stock", json_mongo=True)
app.install(plugin)

def prepare_response():
    pass
    #response.add_header("Connection", "Keep-Alive")
    

@app.route("/portofolio/:user", method="GET")
def get_portofolio(user, mongodb):
    prepare_response()
    portofolio = mongodb.portofolio.find_one({ "user" : user})    
    return utils.portofolio_cleanup(portofolio) 
    

@app.route("/stockexchange/trade", method="POST")
def stock_trade(mongodb):
    prepare_response()
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    
    credit_for_1 = utils.build_update_obj(add_2)
    debit_for_1 = utils.build_update_obj(add_1, sign=-1)
    credit_for_2 = utils.build_update_obj(add_1, sign=1)
    debit_for_2 = utils.build_update_obj(add_2, sign=-1)    
    check_1 = utils.build_check_obj(add_1)
    check_2 = utils.build_check_obj(add_2)
    
    # Insert the transaction in base
    trade_order['state'] = "running"
    t_id =  mongodb.transaction.insert(trade_order, safe=True)
    
    check_1.update({ "user":add_1["user"],  "debited" : { "$ne" : t_id}})
    check_2.update({ "user":add_2["user"],  "debited" : { "$ne" : t_id}})
    
    ## Try to apply all the debits 

    ret = mongodb.portofolio.update(check_1, { "$inc" : debit_for_1, "$push" : { "debited" : t_id} }, safe=True )
    if not ret['updatedExisting']:
        mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "failed" }})
        raise Exception()
    ret = mongodb.portofolio.update(check_2, { "$inc" : debit_for_2, "$push" : { "debited" : t_id } }, safe=True )
    if not ret['updatedExisting']:
        ## Rollback debit on 1 
        mongodb.portofolio.update({"user":add_1["user"] } , { "$inc":credit_for_2, "$pull" : { "debited" : t_id }}, safe=True)
        ## Notify failed transaction
        mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "failed" }}, safe=True)
        raise Exception() 

    # Notify Sucessfull debits. 
    mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "debited" }}, safe=True)
    if not ret['updatedExisting']:
         # Rollback
         ret = mongodb.portofolio.update({"user":add_1["user"] } , { "$inc":credit_for_2, "$pull" : { "debited" : t_id }}, safe=True)
         ret = mongodb.portofolio.update({"user":add_2["user"] } , { "$inc":credit_for_1, "$pull" : { "debited" : t_id }}, safe=True)
         mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "failed" }}, safe=True)
         raise Exception()

    # Apply all the credits
    
    ret = mongodb.portofolio.update({"user": add_1['user']}, { "$inc" : credit_for_1,"$pull" : { "debited" : t_id }}, safe=True)
    if not ret['updatedExisting']:
        raise Exception()
    ret = mongodb.portofolio.update({"user": add_2['user']}, { "$inc" : credit_for_2,"$pull" : { "debited" : t_id }}, safe=True)
    if not ret['updatedExisting']:
        raise Exception()
        
    # Notify Sucessfull transaction. 
    mongodb.transaction.update({"_id" : t_id}, {"$set" : {"state" : "done" }}, safe=True)
    if not ret['updatedExisting']:
         raise Exception()        
    
@app.route("/stockexchange/distribute", method="POST")
def stock_distribute(mongodb):
    prepare_response()
    portofolio_order = request.json
    update_obj = utils.build_update_obj(portofolio_order)
    ret = mongodb.portofolio.update({ "user" : portofolio_order['user']}, { "$inc" : update_obj }, safe=True)
    if not ret['updatedExisting']:
        portofolio_order['debited'] = []
        mongodb.portofolio.insert(portofolio_order)


"""
{ "portofolio_1" : { "user" :  "w.buffet" , "content": { "FR"  : { "FOO" : 1 } }  } , "portofolio_2" : { "user" : "b.gates", "content" : { "US" : { "MS" :  1 } } } } 
"""
        
if __name__ == "__main__": 
    utils.init(plugin.get_mongo(), {"debited":[]})
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), server='tornado', reloader=True)
