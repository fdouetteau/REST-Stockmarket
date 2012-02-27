

def content_cleanup(content):
    for m in [m for m in content if content[m] == 0]:
        del content[m]
    return content
     
def build_check_obj(content):
    check = {} 
    for m in content:
        check["content." + m] = { "$gte" : content[m]}
    return check     
    
# In order to use mongodb atomic document update, 
# a dictionary containing all the updated to perform to a given object is created
def build_update_obj(content, sign=1, neg = None):
    update = {}
    for m in content: 
        update["content." + m]  = sign * content[m]
    if not neg:
        return update
    for m in neg: 
        update["content." + m]  = -neg[m]
    return update
    
def portofolio_add(p1, p2, sign):
    "Add the portofolio content in p2 to p1 "
    for m in p2: 
        if m in p1: 
            p1[m] = p1[m] + sign * p2[m]
        else:
            p1[m] = sign * p2[m]
    
def init(mongodb, template_obj = {}):
    mongodb.portofolio.ensure_index("user")
    mongodb.portofolio.remove()
    o1 = template_obj.copy()
    o1.update({"user":"w.buffet", "content" : { "MS" : 1000, "VS" : 10 , "FOO" : 7 }})
    mongodb.portofolio.insert(o1, safe=True)
    k = mongodb.portofolio.find_one({"user":"w.buffet"})
    if not k: 
        raise Exception("Unable to insert item")
    o2 = template_obj.copy()
    o2.update({"user":"b.gates", "content" : { "MS" : 1000000, "TOTO" : 10 , "BAR" : 6}})
    mongodb.portofolio.insert(o2, safe=True)
