import httplib
import requests, requests.auth
import twitter
import time
import re
import json
import threading


'''
I could use the lock and queue libraries associated with Python's threading
library, but it just seemed like too much for this project. Better off just
making this small class that -- more or less -- achieves the same goal.

Basic operation for threads that make use of this class:
check if lock == true, if true, wait till false, then lock, do your thing,
then unlock.

The idea here is that the reddit API is going to return a lot more data
than the Twitter side of this app can deal with at any given time. But more
importantly, it allows both sides of the app to work indepenently from each
other.
'''


class LinkQueue:
    def __init__(self):
        self.queue = [];
        self.lock = False
	self.history = []

    def enqueue(self, val):
        self.queue.append(val)

    def dequeue(self):
        ret = self.queue[0]
    	self.history.append(ret)
        del self.queue[0]
        return ret

    def isEmpty(self):
        if len(self.queue) == 0:
            return True
        else:
            return False

    def isLocked(self):
        return self.lock

    def lockQueue(self):
        self.lock = True

    def unlockQueue(self):
        self.lock = False


class Twitter:
    def __init__(self):
        self.api = twitter.Api(
        consumer_key=u"",
        consumer_secret=u"",
        access_token_key=u"",
        access_token_secret=u"")

    def tweet(self, image="", status=""):
        self.api.PostUpdate(status, media=image)

class Reddit:
    def __init__(self, user, password, clientID, key):
        self.user = user
        self.clientID = clientID
        self.password = password
        self.key = key
        self.auth = requests.auth.HTTPBasicAuth(clientID, key)
        self.token = self.requestToken()["access_token"]
        self.reqestHeader = {"Authorization":"bearer " + self.token}

    def requestToken(self):
        pd = {"grant_type":"password", "username": self.user, "password":self.password}
        headers = {"User-Agent":"Tweddit by Twedditbot"}
        return requests.post("https://www.reddit.com/api/v1/access_token", auth=self.auth, data=pd, headers=headers).json()

    def getPage(self):
        links = requests.get("https://oauth.reddit.com/r/aww+catsstandingup+birdswitharms+cattaps+otters/rising", headers=self.reqestHeader)
        try:
            return links.json()
        except ValueError:
            print "JSON Error: Reddit is Being Reddit"
            return None

class Bot:
    def __init__(self):
        self.redditApp = Reddit('', '', '', '')
        self.twitterApp = Twitter()
        self.queue = LinkQueue()
        self.t1 = threading.Thread(target=self.grabImages)
        self.t2 = threading.Thread(target=self.tweet)
        self.t3 = threading.Thread(target=self.checkTime)
        self.clock = time.time() #used to cull the queue's history every hour


    def run(self):
        self.t1.start()
        self.t2.start()
        self.t3.start()
        while True:
            pass #hack to use ctrl-c without daemonizing the threads

    def checkTime(self):
        if time.time() - self.clock >= 3600:
            self.clock = time.time()
            self.queue.history = []

    def grabImages(self, subreddits=[]):
        while True:
            results = self.redditApp.getPage()
            if(results != None):
                try:
                    results = results["data"]["children"]
                except KeyError:   #this just makes sure that if the server sends some other JSON,
                    time.sleep(10) #like an error message for example, that the entire script won't
                    continue       #collapse on itself
                if self.queue.isLocked():
                    while self.queue.isLocked():
                        time.sleep(1)
                self.queue.lockQueue()
                for i in range(0, len(results)):
                    if re.match(r'https?.*\..*\/.*\.(jpg|jpeg|png)', results[i]["data"]["url"]) or re.match(r'.*i\.reddituploads\.com\/.*\.(jpg|jpeg|png)',results[i]["data"]["url"]):
                        tmp = results[i]["data"]["url"].replace("&amp;", "&")
                        if not tmp in self.queue.queue and not tmp in self.queue.history:
                            self.queue.enqueue(tmp)
                print "Thread completed at %s, currently the queue looks like this:\n%s" % (time.localtime(), self.queue.queue)
                self.queue.unlockQueue()
            else:
                print "JSON Error"
            time.sleep(30)
        #print self.imageDataTmp

    def tweet(self):
        while True:
            while self.queue.isEmpty():
                time.sleep(1)
            while self.queue.isLocked():
                time.sleep(1)
            self.queue.lockQueue()

            try:
                self.twitterApp.tweet(self.queue.dequeue(), status="")
            except Exception as e:
                print e
            print "Tweeted t %s" % time.localtime()

            self.queue.unlockQueue()

            time.sleep(30)

#see
Bot().run()
