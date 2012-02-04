
from bottle import run, debug, request, Bottle
import os
import bottle_mongo
import utils

app = Bottle(autojson=False)
plugin = bottle_mongo.MongoPlugin(uri="mongodb://localhost/naive_stock", db="naive_stock", json_mongo=True)
app.install(plugin)

@app.route("/portofolio/:user", method="GET")
def get_portofolio(user, mongodb):
    portofolio = mongodb.portofolio.find_one({ "user" : user})    
    return utils.portofolio_cleanup(portofolio)
    
## Naive, transaction broken trade     
@app.route("/stockexchange/trade", method="POST")
def stock_trade(mongodb):
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    p2  = mongodb.portofolio.find_one({ "user" : add_2['user']})
    p1  = mongodb.portofolio.find_one({ "user" : add_1['user']})

    utils.portofolio_add(p2['content'], add_1['content'], sign = 1 )
    utils.portofolio_add(p1['content'], add_1['content'], sign = -1 )
    utils.portofolio_add(p1['content'], add_2['content'], sign=1)
    utils.portofolio_add(p2['content'], add_2['content'], sign=-1)
    mongodb.portofolio.update({"_id" : p1['_id']}, p1)
    mongodb.portofolio.update({"_id" : p2['_id']}, p2)
    pass
    
## Naive distribute
@app.route("/stockexchange/distribute", method="POST")
def stock_distribute(mongodb):
    portofolio_order = request.json
    p1  = mongodb.portofolio.find_one({ "user" : portofolio_order['user']})
    if not p1: 
        mongodb.portofolio.insert(portofolio_order)
    else:
        utils.portofolio_add(p1['content'], portofolio_order['content'], 1)
        mongodb.portofolio.update({"_id" : p1['_id']}, p1)
        
if __name__ == "__main__": 
    utils.init(plugin.get_mongo())
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), server="tornado", reloader=True)


