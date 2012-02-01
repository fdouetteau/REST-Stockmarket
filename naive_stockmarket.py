
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
    
def portofolio_add(p1, p2, sign):
    "Add the portofolio content in p2 to p1 "
    for m in p2: 
        for k in p2[m]: 
            if not m in p1: 
                p1[m] = {}
            if not k in p1[m]: 
                p1[m][k] = 0 
            p1[m][k] = p1[m][k] + sign * p2[m][k]
    
## Naive, transaction broken trade     

@app.route("/stockexchange/trade", method="POST")
def stock_trade(mongodb):
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    p2  = mongodb.portofolio.find_one({ "user" : add_2['user']})
    p1  = mongodb.portofolio.find_one({ "user" : add_1['user']})

    portofolio_add(p2['content'], add_1['content'], sign = 1 )
    portofolio_add(p1['content'], add_1['content'], sign = -1 )
    portofolio_add(p1['content'], add_2['content'], sign=1)
    portofolio_add(p2['content'], add_2['content'], sign=-1)
    mongodb.portofolio.update({"_id" : p1['_id']}, p1)
    mongodb.portofolio.update({"_id" : p2['_id']}, p2)
    pass
    
## Naive distribute
@app.route("/stockexchange/distribute", method="POST")
def stock_distribute(mongodb):
    portofolio_order = request.json
    p1  = mongodb.portofolio.find_one({ "user" : portofolio_order['user']})
    portofolio_add(p1['content'], portofolio_order['content'])
    mongodb.portofolio.update({"_id" : p1._id}, p1)
    
    
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

        
if __name__ == "__main__": 
    init()
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)


