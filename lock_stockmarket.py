from bottle import run, debug, request, Bottle
import os
import bottle_mongo
import time

app = Bottle(autojson=False)
plugin = bottle_mongo.MongoPlugin(uri="mongodb://localhost/naive_stock", db="naive_stock", json_mongo=True)
app.install(plugin)


@app.route("/portofolio/:user", method="GET")
def get_portofolio(user, mongodb):
    portofolio = mongodb.portofolio.find_one({ "user" : user})    
    return portofolio
    
def build_update_obj(p, q = None):
    update = {}
    for m in p["content"]: 
        for s in p["content"][m]: 
            update["content." + m + "." + s]  = p["content"][m][s]
    if not q:
        return update
    for m in q["content"]: 
        for s in q["content"][m]: 
            update["content." + m + "." + s]  = -q["content"][m][s]
    return update
    
def build_check_obj(p):
    check = {} 
    for m in p["content"]:
        for s in p["content"][m]:
            check["content." + m + "." + s] = { "$gt" : p["content"][m][s]}
    return check
    
@app.route("/stockexchange/trade", method="POST")
def stock_trade(mongodb):
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    update_1 = build_update_obj(add_2, add_1)
    update_2 = build_update_obj(add_1, add_2)
    
    check_1 = build_check_obj(add_1)
    check_2 = build_check_obj(add_2)
    check_1.update({ "user":add_1["user"], "_locked": 1 })
    check_2.update({ "user":add_2["user"], "_locked": 1 })
    ## Acquire a lock on object. 
    while True:     
        t = time.time()
        elasped = t - 30  
        # To lock an object, we set a _locked attributed and a _lock_time
        # The lock is only valid for 30 seconds. 
        lock_check_expr =  { '$or' : [{ "_locked" : { "$ne" : 1 } } , { "$le" : { "_lock_time" : elasped } }  ]  }
        ret = mongodb.portofolio.update({ "$and" : [ {"user":add_1["user"]}, lock_check_expr] }, { "$set" : { "_locked" : 1, "_lock_time" : t  } }  , safe=True)
        if not ret['updatedExisting']: 
            time.sleep(0.5)
            continue 
        ret = mongodb.portofolio.update({ "$and": [ {"user":add_2["user"]}, lock_check_expr] } , { "$set" : { "_locked" : 1, "_lock_time" : t } } , safe=True)
        if not ret['updatedExisting']: 
            # Release lock on 1 
            mongodb.portofolio.update({ "user":add_1["user"], "_locked" : 1 } , { "$unset" : { "_locked" : 1 } } , safe=True)
            time.sleep(0.5)
            continue
        break 
        
    ## Perform the update 
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
    update_obj = build_update_obj(portofolio_order)
    mongodb.portofolio.update({ "user" : portofolio_order['user']}, { "$inc" : update_obj })


def init():
    mongodb = plugin.get_mongo()
    mongodb.portofolio.remove()
    mongodb.portofolio.insert(
        {
            "user":"w.buffet", 
            "content" : 
                { 
                    "US" : 
                        { 
                            "MS" : 1000, 
                            "VS" : 10 
                            }, 
                    "FR" : 
                        {
                            "FOO" : 7
                        } 
                        
                }
        });
    k = mongodb.portofolio.find_one({"user":"w.buffet"})
    if not k: 
        raise Exception("Unable to insert item")
    mongodb.portofolio.insert(
    {
        "user":"b.gates", 
        "content" : 
            { 
                "US" : 
                    { 
                        "MS" : 1000000, 
                        "TOTO" : 10 
                        }, 
                "FR" : 
                    {
                        "BAR" : 6
                    } 
                    
            }
    });

"""
{ "portofolio_1" : { "user" :  "w.buffet" , "content": { "FR"  : { "FOO" : 1 } }  } , "portofolio_2" : { "user" : "b.gates", "content" : { "US" : { "MS" :  1 } } } } 
"""

        
if __name__ == "__main__": 
    init()
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)