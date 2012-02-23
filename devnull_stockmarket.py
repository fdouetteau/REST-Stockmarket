from bottle import run, debug, request, Bottle
import os
import bottle_mongo
import utils

app = Bottle(autojson=True)


@app.route("/portofolio/:user", method="GET")
def get_portofolio(user):
    return { "user" : user, "content" : { 'FOO' : { 'BAR' : 1 }}};     

@app.route("/stockexchange/trade", method="POST")
def stock_trade():
    return 
    
@app.route("/stockexchange/distribute", method="POST")
def stock_distribute():
    return 
    
if __name__ == "__main__": 
    debug(True)
    run(app=app, host="0.0.0.0", port=os.environ.get("PORT", 8080), reloader=True, server="tornado")