
import urllib3 
import json
from threading import Thread
import random
import time

http = urllib3.HTTPConnectionPool('localhost:8080', maxsize=10)

markets = None
stocks = None
users = None

N_MARKETS = 50 # 50   # Number of markets. 
N_STOCKS = 10 # 10   # Number of stocks
N_USERS = 100000 # 100000 # Number of distinct users
N_THREADS = 10 # 20 # Number of concurrent threads. 
N_SESSIONS_PER_THREAD = 100 # 100 # Number of sessions played by a thread 
N_DISTRIBUTE = 3 # 10 # Number of distributions factors
N_DISTRIBUTE_SIZE = 10 # 10 # Number of items in distribution
N_GIVE = 3 # 5 # Number of gives.

class Runner(Thread):

    count_get = 0 
    time_get = 0 

    def get_portofolio(self, user):
        t1 = time.clock()
        r = http.request('GET', '/portofolio/' + user)
        t2 = time.clock()
        self.count_get = self.count_get + 1
        self.time_get = self.time_get + (t2-t1)
        if r.status != 200: 
            raise Exception()
        return json.loads(r.data) 

    count_distribute = 0 
    time_distribute = 0 

    def distribute(self, user, content):
        obj = { 'user' : user, 'content': content}
        t1 = time.clock()
        r = http.urlopen('POST', '/stockexchange/distribute', body=json.dumps(obj), headers={'Content-Type':'application/json'})
        t2 = time.clock()
        self.count_distribute = self.count_distribute + 1 
        self.time_distribute = self.time_distribute + (t2 - t1)
        if r.status != 200: 
            raise Exception()

    count_trade = 0 
    time_trade  = 0 

    def trade(self, u1, c1, u2, c2):
        obj = { 'portofolio_1' : { 'user': u1,'content': c1}, 'portofolio_2' : { 'user' : u2, 'content' : c2 } }
        t1 = time.clock()
        r = http.urlopen('POST', '/stockexchange/trade', body=json.dumps(obj), headers={'Content-Type':'application/json'})
        t2 = time.clock()
        self.count_trade = self.count_trade + 1 
        self.time_trade = self.time_trade + (t2 - t1)
        if r.status != 200:
            raise Exception()
    
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
            mi = random.randint(0, len(markets)-1)
            si = random.randint(0, len(stocks)-1)
            for k in xrange(0, N_DISTRIBUTE_SIZE):
                u[markets[(k+mi)%len(markets)]] = { stocks[(k+si)%len(stocks)] : 1 } 
#            for k in xrange(0, N_DISTRIBUTE_SIZE):
#                m = random.choice(markets) 
#                s = random.choice(stocks)
#                if not m in u: 
#                    u[m] = {}
#                u[m][s] = 1 
            self.distribute(self.user, u)
            
        portofolio = self.get_portofolio(self.user)
        
        for i in xrange(0, N_GIVE):
            m = random.choice([m for m in portofolio['content']])
            s = random.choice([s for s in portofolio['content'][m]])
            other_user = None
            while True:
                other_user = random.choice(users)
                if other_user != self.user: 
                    break 
            self.trade(self.user, { m : { s : 1 } }, other_user, { })
            portofolio = self.get_portofolio(self.user)
        

if __name__ == "__main__": 
    markets = ["market_%u" % i for i in xrange(0,N_MARKETS) ]
    stocks =  ["stock_%u" % i for i in xrange(0,N_STOCKS) ]
    users = ["user_%u" % i for i in xrange(0,N_USERS) ]
    
    threads = [Runner(users[i*(N_USERS/N_THREADS):(i+1)*(N_USERS/N_THREADS)]) for i in xrange(0, N_THREADS)] 
    
    init_start = time.clock()
    init_runner = Runner(users)
    for u in users: 
        init_runner.distribute(u, {})
    init_stop = time.clock()
    print "Completed user initialization in %0.3f s " % (init_stop - init_start)
     
    start_time = time.clock()
    for r in threads: 
        r.start()
        
    sum_runner = Runner(users)
    for r in threads: 
        r.join()
        sum_runner.count_get += r.count_get
        sum_runner.time_get += r.time_get
        sum_runner.count_distribute += r.count_distribute 
        sum_runner.time_distribute += r.time_distribute 
        sum_runner.count_trade += r.count_trade
        sum_runner.time_trade += r.time_trade
    end_time = time.clock()
    
    print 'Played %u sessions in %0.3f s' % (N_THREADS * N_SESSIONS_PER_THREAD, (end_time - start_time))
    print 'Get Portofolio: %u times, %0.3f s overall, %0.3f ms mean time' % (sum_runner.count_get, sum_runner.time_get*1000000, (sum_runner.time_get/sum_runner.count_get)*1000)
    print 'Distribute: %u times, %0.3f s overall, %0.3f ms mean time' % (sum_runner.count_distribute, sum_runner.time_distribute*1000000, (sum_runner.time_distribute /sum_runner.count_distribute )*1000)
    print 'Trade: %u times, %0.3f s overall, %0.3f ms mean time' % (sum_runner.count_trade, sum_runner.time_trade*1000000, (sum_runner.time_trade/sum_runner.count_trade)*1000)
    
    