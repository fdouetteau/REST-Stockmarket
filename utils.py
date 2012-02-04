

def portofolio_cleanup(portofolio):
    for m in portofolio['content']:
        k = [s for s in portofolio['content'][m] if portofolio['content'][m][s] == 0]
        for s in k:
            del portofolio['content'][m][s]
    for m in [m for m in portofolio['content'] if len(portofolio['content'][m]) == 0]:
        del portofolio['content'][m]
    return portofolio
 
    
def build_check_obj(p):
    check = {} 
    for m in p["content"]:
        for s in p["content"][m]:
            check["content." + m + "." + s] = { "$gte" : p["content"][m][s]}
    return check     
    
# In order to use mongodb atomic document update, 
# a dictionary containing all the updated to perform to a given object is created
def build_update_obj(p, sign=1, neg = None):
    update = {}
    for m in p["content"]: 
        for s in p["content"][m]: 
            update["content." + m + "." + s]  = sign * p["content"][m][s]
    if not neg:
        return update
    for m in neg["content"]: 
        for s in neg["content"][m]: 
            update["content." + m + "." + s]  = -neg["content"][m][s]
    return update
    
def portofolio_add(p1, p2, sign):
    "Add the portofolio content in p2 to p1 "
    for m in p2: 
        for k in p2[m]: 
            if not m in p1: 
                p1[m] = {}
            if not k in p1[m]: 
                p1[m][k] = 0 
            p1[m][k] = p1[m][k] + sign * p2[m][k] 
    
def init(mongodb, template_obj = {}):
    mongodb.portofolio.ensure_index("user")
    mongodb.portofolio.remove()
    o1 = template_obj.copy()
    o1.update({"user":"w.buffet", "content" : { "US" : { "MS" : 1000, "VS" : 10 }, "FR" : { "FOO" : 7 } }})
    mongodb.portofolio.insert(o1, safe=True)
    k = mongodb.portofolio.find_one({"user":"w.buffet"})
    if not k: 
        raise Exception("Unable to insert item")
    o2 = template_obj.copy()
    o2.update({"user":"b.gates", "content" : { "US" : { "MS" : 1000000, "TOTO" : 10 }, "FR" : {"BAR" : 6} }})
    mongodb.portofolio.insert(o2, safe=True)
