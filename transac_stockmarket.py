from bottle import run, debug, request, Bottle
import os
import bottle_mongo

app = Bottle(autojson=False)
plugin = bottle_mongo.MongoPlugin(uri="mongodb://localhost/naive_stock", db="naive_stock", json_mongo=True)
app.install(plugin)


@app.route("/portofolio/:user", method="GET")
def get_portofolio(user, mongodb):
    portofolio = mongodb.portofolio.find_one({ "user" : user})    
    return portofolio
    
def build_update_obj(p, factor):
    update = {}
    for m in p["content"]: 
        for s in p["content"][m]: 
            update["content." + m + "." + s]  = factor * p["content"][m][s]
    return update
    
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
    
    credit_for_1 = build_update_obj(add_2, 1)
    debit_for_1 = build_update_obj(add_1, -1)
    credit_for_2 = build_update_obj(add_1, 1)
    debit_for_2 = build_update_obj(add_2, -1)    
    check_1 = build_check_obj(add_1)
    check_2 = build_check_obj(add_2)
    
    # Insert the transaction in base
    trade_order['state'] = "running"
    t_id =  mongodb.transaction.insert(trade_order, safe=True)
    
    print t_id
    check_1.update({ "user":add_1["user"],  "pending" : { "$ne" : t_id}})
    check_2.update({ "user":add_2["user"],  "pending" : { "$ne" : t_id}})
    
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
    portofolio_order = request.json
    update_obj = build_update_obj(portofolio_order)
    mongodb.portofolio.update({ "user" : portofolio_order['user']}, { "$inc" : update_obj })


def init():
    mongodb = plugin.get_mongo()
    mongodb.portofolio.remove()
    mongodb.transaction.remove()
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
                        
                },
            "debited": []
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
                    
            }, 
        "debited" : []
    });

"""
{ "portofolio_1" : { "user" :  "w.buffet" , "content": { "FR"  : { "FOO" : 1 } }  } , "portofolio_2" : { "user" : "b.gates", "content" : { "US" : { "MS" :  1 } } } } 
"""

        
if __name__ == "__main__": 
    init()
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)
