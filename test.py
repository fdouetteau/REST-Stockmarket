
import urllib3 
import json
from threading import Thread, Lock
import random
import time

http = urllib3.HTTPConnectionPool('localhost:8080', maxsize=10)

lock = Lock()

count_get = 0 
time_get = 0 

def get_portofolio(user):
    t1 = time.time()
    r = http.request('GET', '/portofolio/' + user)
    t2 = time.time()
    lock.acquire()
    global count_get, time_get
    count_get = count_get + 1
    time_get = time_get + (t2-t1)
    lock.release()
    if r.status != 200: 
        raise Exception()
    return json.loads(r.data) 

count_distribute = 0 
time_distribute = 0 

def distribute(user, content):
    obj = { 'user' : user, 'content': content}
    t1 = time.time()
    r = http.urlopen('POST', '/stockexchange/distribute', body=json.dumps(obj), headers={'Content-Type':'application/json'})
    t2 = time.time()
    lock.acquire()
    global count_distribute, time_distribute 
    count_distribute = count_distribute + 1 
    time_distribute = time_distribute + (t2 - t1)
    lock.release()
    if r.status != 200: 
        raise Exception()

count_trade = 0 
time_trade  = 0 

def trade(u1, c1, u2, c2):
    obj = { 'portofolio_1' : { 'user': u1,'content': c1}, 'portofolio_2' : { 'user' : u2, 'content' : c2 } }
    t1 = time.time()
    r = http.urlopen('POST', '/stockexchange/trade', body=json.dumps(obj), headers={'Content-Type':'application/json'})
    t2 = time.time()
    lock.acquire()
    global count_trade, time_trade 
    count_trade = count_trade + 1 
    time_trade = time_trade + (t2 - t1)
    lock.release()
    if r.status != 200:
        raise Exception()

markets = None
stocks = None
users = None

N_MARKETS = 50 # 50   # Number of markets. 
N_STOCKS = 10 # 10   # Number of stocks
N_USERS = 1000 # 100000 # Number of distinct users
N_THREADS = 10 # 20 # Number of concurrent threads. 
N_SESSIONS_PER_THREAD = 15 # 100 # Number of sessions played by a thread 
N_DISTRIBUTE = 3 # 10 # Number of distributions factors
N_DISTRIBUTE_SIZE = 10 # 10 # Number of items in distribution
N_GIVE = 5 # 5 # Number of gives. 

class Runner(Thread):
    
    def run(self):
        for i in xrange(0, N_SESSIONS_PER_THREAD):
            # Select a user
            self.user = random.choice(self.users)
            # Play a session
            self.playSession()
    
    def __init__(self, users):
        super(Runner, self).__init__()
        self.users = users
        
    def playSession(self):
        for i in xrange(0, N_DISTRIBUTE): 
            u = {}
            for k in xrange(0, N_DISTRIBUTE_SIZE):
                m = random.choice(markets) 
                s = random.choice(stocks)
                if not m in u: 
                    u[m] = {}
                u[m][s] = 1 
            distribute(self.user, u)
            
        portofolio = get_portofolio(self.user)
        
        for i in xrange(0, N_GIVE):
            m = random.choice([m for m in portofolio['content']])
            s = random.choice([s for s in portofolio['content'][m]])
            other_user = None
            while True:
                other_user = random.choice(users)
                if other_user != self.user: 
                    break 
            trade(self.user, { m : { s : 1 } }, other_user, { })
            portofolio = get_portofolio(self.user)
        

if __name__ == "__main__": 
    markets = ["market_%u" % i for i in xrange(0,N_MARKETS) ]
    stocks =  ["stock_%u" % i for i in xrange(0,N_STOCKS) ]
    users = ["user_%u" % i for i in xrange(0,N_USERS) ]
    
    threads = [Runner(users[i*(N_USERS/N_THREADS):(i+1)*(N_USERS/N_THREADS)]) for i in xrange(0, N_THREADS)] 
    
    for u in users: 
        distribute(u, {})
    
    for r in threads: 
        r.start()
        
    for r in threads: 
        r.join()
    
    print 'Get Portofolio: %u times, %0.3f s overall, %0.3f ms mean time' % (count_get, time_get*1000000, (time_get/count_get)*1000)
    print 'Distribute: %u times, %0.3f s overall, %0.3f ms mean time' % (count_distribute, time_distribute*1000000, (time_distribute /count_distribute )*1000)
    print 'Trade: %u times, %0.3f s overall, %0.3f ms mean time' % (count_trade, time_trade*1000000, (time_trade/count_trade)*1000)
    
    