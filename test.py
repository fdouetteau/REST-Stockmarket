
import urllib3 
import json
import random
import time
from multiprocessing import Pool
import logging
import optparse


markets = None
stocks = None
users = None

N_STOCKS = 500 # 10   # Number of stocks
N_USERS = 10000 # 100000 # Number of distinct users
N_RUNNERS = 10 # Number of Sessions runners objects created
N_POOL = 4 # Max in Parallel   
N_SESSIONS = 1000
N_DISTRIBUTE = 3 # 10 # Number of distributions factors
N_DISTRIBUTE_SIZE = 10 # 10 # Number of items in distribution
N_GIVE = 3 # 5 # Number of gives.

have_timer = True

def get_time(): 
    if have_timer: 
        return time.time()
    return 0 

class TimeCounter(object):
    """A Simple Counter for number of calls / time spent """
    def __init__(self, name):
        self.name = name
        self.count = 0 
        self.time = 0 
    
    def do_count(self, time_begin, time_end):
        self.count = self.count + 1
        self.time = self.time + (time_end - time_begin)

    def get_info(self):
        return '%s: %u times, %0.3f s overall, %0.3f ms mean time' % (self.name, self.count, self.time*1000000, (self.time/self.count)*1000)
        
    def __add__(self, other):
        s = TimeCounter(self.name)
        s.count = self.count + other.count
        s.time = self.time + other.time
        return s
        
class TimeCounters(dict):
    def __add__(self, other):
        s = TimeCounters()
        for k in self: 
            s[k] = self[k] + other[k]
        return s

class Runner(object):
    def get_portofolio(self, user):
        t1 = get_time()
        r = self.http.request('GET', '/portofolio/' + user)
        t2 = get_time()
        self.counter['get'].do_count(t1, t2)
        if r.status != 200: 
            raise Exception()
        return json.loads(r.data) 

    def distribute(self, user, content):
        obj = { 'user' : user, 'content': content}
        t1 = get_time()
        r = self.http.urlopen('POST', '/stockexchange/distribute', body=json.dumps(obj), headers={'Content-Type':'application/json'})
        t2 = get_time()
        self.counter['distribute'].do_count(t1, t2)
        if r.status != 200: 
            raise Exception()

    def trade(self, u1, c1, u2, c2):
        obj = { 'portofolio_1' : { 'user': u1,'content': c1}, 'portofolio_2' : { 'user' : u2, 'content' : c2 } }
        t1 = get_time()
        r = self.http.urlopen('POST', '/stockexchange/trade', body=json.dumps(obj), headers={'Content-Type':'application/json'})
        t2 = get_time()
        self.counter['trade'].do_count(t1, t2)
        if r.status != 200:
            raise Exception()
    
    def __init__(self, users, timer):
        super(Runner, self).__init__()
        global have_timer
        have_timer = timer  
        self.counter = TimeCounters()
        self.counter['get'] = TimeCounter("Get Portofolio")
        self.counter['distribute'] = TimeCounter("Distribute")
        self.counter['trade'] = TimeCounter("Trade")
        self.users = users
        
    def playSession(self):
        for i in xrange(0, N_DISTRIBUTE): 
            u = {}
            si = random.randint(0, len(stocks)-1)
            for k in xrange(0, N_DISTRIBUTE_SIZE):
                u[stocks[(k+si)%len(stocks)]] = 1  
            self.distribute(self.user, u)
            
        portofolio = self.get_portofolio(self.user)
        
        for i in xrange(0, N_GIVE):
            s = random.choice([m for m in portofolio['content']])
            other_user = None
            while True:
                other_user = random.choice(users)
                if other_user != self.user: 
                    break 
            self.trade(self.user,  { s : 1 }, other_user, { })
            portofolio = self.get_portofolio(self.user)
        

def init_user(runner):
    runner.http = urllib3.HTTPConnectionPool('localhost:8080', maxsize=2)
    for u in runner.users:
        runner.distribute(u, {})
        
def play_sessions(runner):
    runner.http = urllib3.HTTPConnectionPool('localhost:8080', maxsize=2)
    for i in xrange(0, runner.nsessions):
            # Select a user
          runner.user = random.choice(runner.users)
          # Play a session
          runner.playSession()
    return runner.counter

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('--no_timing', action="store_true", default=False)
    parser.add_option('--connection_log', action="store_true", default=False)
    options, remainder = parser.parse_args()
    
    if options.connection_log: 
        logging.basicConfig()
        logging.getLogger("urllib3.connectionpool").setLevel("INFO")
        
    if options.no_timing: 
        print "Disabling timer"
        have_timer = False
    else: 
        have_timer = True 
        
    
    stocks =  ["stock_%u" % i for i in xrange(0,N_STOCKS) ]
    users = ["user_%u" % i for i in xrange(0,N_USERS) ]
    
    runners = [Runner(users[i*(N_USERS/N_RUNNERS):(i+1)*(N_USERS/N_RUNNERS)], have_timer) for i in xrange(0, N_RUNNERS)] 
    for r in runners: 
        r.nsessions = N_SESSIONS / N_RUNNERS
        
    runners[-1].nsessions = N_SESSIONS - ((N_SESSIONS / N_RUNNERS) * (N_RUNNERS - 1))

    pool = Pool(4)

    init_start = get_time()   
    pool.map(init_user, runners)
    init_stop = get_time()
    print "Completed user initialization in %0.3f s " % (init_stop - init_start)

    session_start = get_time()
    results = pool.map(play_sessions, runners)
    session_stop = get_time()
    print 'Played %u sessions in %0.3f s' % (N_SESSIONS, (session_stop - session_start))
    
    
    s = reduce(lambda r1, r2 : r1+r2, results)

    for k in s: 
        print s[k].get_info()
    
    