
class DevNullModel(object):
    "Dummy model that does nothing"
    def get_portofolio(self, user):
        return { 'BAR' : 1 };    
    def trade(self, user_1, content_1, user_2, content_2):
        pass
    def distribute(self, user, content):
        pass
    def setMongo(self, host, db):
        pass