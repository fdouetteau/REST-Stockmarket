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

@app.route("/stockexchange/trade", method="POST")
def stock_trade(mongodb):
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    update_1 = utils.build_update_obj(add_2, neg=add_1)
    update_2 = utils.build_update_obj(add_1, neg=add_2)
    mongodb.portofolio.update({ "user":add_1["user"] }, { "$inc" : update_1 }, safe=True )
    mongodb.portofolio.update({ "user":add_2["user"] }, { "$inc" : update_2 }, safe=True )
    
@app.route("/stockexchange/distribute", method="POST")
def stock_distribute(mongodb):
    portofolio_order = request.json
    update_obj = utils.build_update_obj(portofolio_order)
    mongodb.portofolio.update({ "user" : portofolio_order['user']}, { "$inc" : update_obj })
    
if __name__ == "__main__": 
    utils.init(plugin.get_mongo())
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True)