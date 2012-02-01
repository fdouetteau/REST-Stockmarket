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
    
@app.route("/stockexchange/trade", method="POST")
def stock_trade(mongodb):
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    update_1 = build_update_obj(add_2, add_1)
    update_2 = build_update_obj(add_1, add_2)
    mongodb.portofolio.update({ "user":add_1["user"] }, { "$inc" : update_1 }, safe=True )
    mongodb.portofolio.update({ "user":add_2["user"] }, { "$inc" : update_2 }, safe=True )
    
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

        
if __name__ == "__main__": 
    init()
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)