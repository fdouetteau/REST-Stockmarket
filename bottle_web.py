from bottle import run, debug, request, Bottle
import os
import utils
import optparse 

app = Bottle(autojson=True)

global model

@app.route("/portofolio/:user", method="GET")
def get_portofolio(user):
    return { 'user' : user, 'content' : model.get_portofolio(user) }; 

@app.route("/stockexchange/trade", method="POST")
def stock_trade():
    trade_order = request.json
    add_1 = trade_order['portofolio_1']
    add_2 = trade_order['portofolio_2']
    model.trade(add_1['user'], add_1['content'], add_2['user'], add_2['content'])
    
@app.route("/stockexchange/distribute", method="POST")
def stock_distribute():
    portofolio_order = request.json
    model.distribute(portofolio_order['user'], portofolio_order['content'])
    
if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('--mongo_db', default='naive_stock')
    parser.add_option('--mongo_host', default='localhost')    
    parser.add_option('--model', default='transac_stockmarket.TransacStockmarket')
    parser.add_option('--server', default='tornado')
    parser.add_option('--debug', action='store_true', default=False)
    parser.add_option('--reset', action='store_true', default=False)
    options, remainder = parser.parse_args()
    global model 
    [module, cls] = options.model.split('.', 1)
    m = __import__(module)
    c = getattr(m, cls)
    model = c()
    model.setMongo(options.mongo_host, options.mongo_db) 
    if options.reset: 
        utils.init(model)
    if options.debug: 
        debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True, server=options.server)