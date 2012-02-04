from bottle import run, debug, request, Bottle
import os
import bottle_mongo
import time
import utils

app = Bottle(autojson=False)
plugin = bottle_mongo.MongoPlugin(uri="mongodb://localhost/naive_stock", db="naive_stock", json_mongo=True)
app.install(plugin)


@app.route("/portofolio/:user", method="GET")
def get_portofolio(user, mongodb):
    portofolio = mongodb.portofolio.find_one({ "user" : user})    
    return utils.portofolio_cleanup(portofolio)
        
# Build a query object that checks that a portofolio at least the stocks to trade  
def build_check_obj(p):
    check = {} 
    for m in p["content"]:
        for s in p["content"][m]:
            check["content." + m + "." + s] = { "$gte" : p["content"][m][s]}
    return check
    
@app.route("/stockexchange/trade", method="POST")
def stock_trade(mongodb):
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    update_1 = utils.build_update_obj(add_2, neg=add_1)
    update_2 = utils.build_update_obj(add_1, neg=add_2)
    
    check_1 = build_check_obj(add_1)
    check_2 = build_check_obj(add_2)
    check_1.update({ "user":add_1["user"], "_locked": 1 })
    check_2.update({ "user":add_2["user"], "_locked": 1 })
    ## Acquire a lock on object. 
    while True:     
        t = time.time()
        elasped = t - 30  
        # To lock an object, we set a _locked attributed and a _lock_time
        # The lock is considered to be  valid for only 30 seconds. 
        # A expiring lock is necessary to protect from crash of this thread in mid-air. 
        lock_check_expr =  { '$or' : [{ "_locked" : { "$ne" : 1 } } , { "$le" : { "_lock_time" : elasped } }  ]  }
        ret = mongodb.portofolio.update({ "$and" : [ {"user":add_1["user"]}, lock_check_expr] }, { "$set" : { "_locked" : 1, "_lock_time" : t  } }  , safe=True)
        if not ret['updatedExisting']: 
            # Unable to lock the object : retry
            # (A better implementation would check that the object actually exists in the database, and have some retry limit)
            time.sleep(0.5)
            continue 
        ret = mongodb.portofolio.update({ "$and": [ {"user":add_2["user"]}, lock_check_expr] } , { "$set" : { "_locked" : 1, "_lock_time" : t } } , safe=True)
        if not ret['updatedExisting']: 
            # Release lock on 1 
            mongodb.portofolio.update({ "user":add_1["user"], "_locked" : 1 } , { "$unset" : { "_locked" : 1 } } , safe=True)
            time.sleep(0.5)
            continue
        break 
        
    ## We perform atomically a check on availability and update on each objects, under the common lock
      
    ret = mongodb.portofolio.update(check_1, { "$inc" : update_1 }, safe=True )
    if not ret['updatedExisting']:
        raise Exception()
    ret = mongodb.portofolio.update(check_2, { "$inc" : update_2 }, safe=True )
    if not ret['updatedExisting']: 
        raise Exception()
        
    ## Release the lock on objects
    mongodb.portofolio.update({ "user":add_1["user"], "_locked" : 1 } , { "$unset" : { "_locked" : 1 } } , safe=True)
    mongodb.portofolio.update({ "user":add_2["user"], "_locked" : 1 } , { "$unset" : { "_locked" : 1 } } , safe=True)
    
    
@app.route("/stockexchange/distribute", method="POST")
def stock_distribute(mongodb):
    portofolio_order = request.json
    update_obj = utils.build_update_obj(portofolio_order)
    ret = mongodb.portofolio.update({ "user" : portofolio_order['user']}, { "$inc" : update_obj }, safe=True)
    if not ret['updatedExisting']:
        mongodb.portofolio.insert(portofolio_order)


"""
{ "portofolio_1" : { "user" :  "w.buffet" , "content": { "FR"  : { "FOO" : 1 } }  } , "portofolio_2" : { "user" : "b.gates", "content" : { "US" : { "MS" :  1 } } } } 
"""

        
if __name__ == "__main__": 
    utils.init(plugin.get_mongo())
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)