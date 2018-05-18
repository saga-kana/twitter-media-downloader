import config_
import sys, os, json, time
from io import BytesIO
import requests
from pymongo import MongoClient
from PIL import Image
from pprint import pprint

client = MongoClient(config_.mongodb_url)
db = client.twitter

session = requests.Session()

def wait_limit_reset(res):
    #if int(res.headers["x-rate-limit-remaining"]) == 0:
    #if float(res.headers["x-rate-limit-remaining"]) / float(res.headers["x-rate-limit-limit'"]) < 0.01:
    if float(res.headers["x-rate-limit-remaining"]) < 3:
        print("wait for {0} seconds until reset".format(
            int(res.headers["x-rate-limit-reset"])-time.time()))
        time.sleep(int(res.headers["x-rate-limit-reset"])-time.time()+ 10)
 
def check_res(res):
    res_json = json.loads(res.text)
    if isinstance(res_json,dict) and "errors" in res_json.keys():
        print(json.dumps(res_json,indent=2))
        wait_limit_reset(res)

def name2id(screen_name):
    url = "https://api.twitter.com/1.1/users/show.json"
    params = {"screen_name": screen_name}
    res = config_.twitter.get(url, params=params)
    # print(json.dumps(json.loads(res.text), indent=2))
    return json.loads(res.text)["id_str"]

def id2name(user_id):
    url = "https://api.twitter.com/1.1/users/show.json"
    params = {"user_id": user_id}
    res = config_.twitter.get(url, params=params)
    # print(json.dumps(json.loads(res.text), indent=2))
    return json.loads(res.text)["screen_name"]

def get_id(string):
    _id = ""
    screen_name = ""
    user_id = ""
    if "-" in string:
        user_id = string.split("-")[0]
        screen_name = id2name(user_id)
    elif string.isdigit():
        user_id = string
        screen_name = id2name(user_id)
    else:
        screen_name = string
        user_id = name2id(screen_name)

    _id = user_id + "-" + screen_name

    print('====================================================')
    print("ID={0}".format(_id))
    print('====================================================')

    return _id, user_id, screen_name

def print_error(msg, tweet_id, screen_name, media_url, path):
    with open("error.txt", "a") as f:
        f.write("#" + msg + "\n")
        f.write("# TWEET URL: https://twitter.com/{0}/status/{1}\n".format(screen_name, tweet_id))
        f.write("wget -O {0} {1}\n".format(path, media_url))
    return

def save_media(tweet):
    # print("save media")
    if db.tweets.find_one({"tweet_id": tweet["id"]}) == None:
        return
    if not "extended_entities" in tweet.keys():
        return

    user_id = tweet["user"]["id_str"]
    screen_name = tweet["user"]["screen_name"]
    directory = "{0}/{1}".format(config_.top, user_id)
    if not os.path.exists(directory):
        os.mkdir(directory)
    db.tweets.update(
        {"tweet_id": tweet["id"]},
        {"$set":{"user_id": tweet["user"]["id"]}}
    )

    for media in tweet["extended_entities"]["media"]:
        path = "{0}/{1}-{2}-{3}".format(directory, user_id, tweet["id"], media["media_url"].split("/")[-1])

        if db.tweets.find_one({"media.filename": path.split("/")[-1]}) != None:
            # print("skip")
            db.tweets.update(
                {"media.filename": path.split("/")[-1]},
                {"$set":{
                    "media.$.filetype": media["type"],
                    "media.$.url": media["media_url"]
                }}
            )
            continue

        if media["type"] == "photo":
            try:
                r = session.get(media["media_url"] + ":orig")
                i = Image.open(BytesIO(r.content))
                i.save(path)
            except:
                print_error("image download failed", tweet["id"], screen_name, media["media_url"], path)
                continue
        elif media["type"] == "video":
            bitrate = 0
            url = ""
            for variant in media["video_info"]["variants"]:
                if variant["content_type"] == "video/mp4" and variant["bitrate"] > bitrate:
                    bitrate = variant["bitrate"]
                    url = variant["url"]
            if url != "":
                r = os.system("wget -q -O {0} {1}".format(path, url))
                if r != 0:
                    print_error("video download failed", tweet["id"], screen_name, url, path)
        elif media["type"] == "animated_gif":
            for variant in media["video_info"]["variants"]:
                if variant["content_type"] == "video/mp4":
                    url = variant["url"]
                    r = os.system("wget -q -O {0} {1}".format(path, url))
                    if r != 0:
                        print_error("gif download failed", tweet["id"], screen_name, url, path)
        else:
            with open("error.txt", "a") as f:
                f.write("# undefined media type\n")
                f.write("https://twitter.com/{0}/status/{1}\n".format(tweet["user"]["screen_name"], tweet["id"]))
                f.write("{0}\n".format(media["type"]))
                f.write("{0}: {1}\n".format(tweet["user"]["name"], tweet["full_text"]))
                f.write("{0}\n".format(media["expanded_url"]))
        db.tweets.update(
            {"tweet_id": tweet["id"]},
            {"$push": {"media": {
                "filename": path.split("/")[-1],
                "filetype": media["type"],
                "url": media["media_url"]
            }}},
            True
        )
    # pprint(db.tweets.find_one({"tweet_id": tweet["id"]}))
    return

def save_tweet(tweet):
    # print("save tweet")
    db.tweets.update({"tweet_id": tweet["id"]},
                 {"$set": {
                     "user_id": tweet["user"]["id"],
                     "user_id_str": tweet["user"]["id_str"],
                     "screen_name": tweet["user"]["screen_name"],
                     "full_text": tweet["full_text"],
                     "tweet_id_str": tweet["id_str"]
                 }},True)
    #print(db.tweets.find_one({"tweet_id": tweet["id"]}))

def update_user_detail(user):
    # print("update user detail")
    db.users.update({"_id": user["id"]},
                 {"$set": {
                     "screen_name": user["screen_name"],
                     "name": user["name"],
                     "_id_str": user["id_str"],
                     "profile_image_url": user["profile_image_url_https"]
                 }},True)
    # print(db.users.find_one({"_id": tweet["user"]["id"]}))

def get_user_detail(user_id):
    url = "https://api.twitter.com/1.1/users/show.json"
    params = {"user_id":user_id}
    res = config_.twitter.get(url, params=params)
    j = json.loads(res.text)
    if not "errors" in j.keys():
        update_user_detail(j)
    else:
        print(json.dumps(j, indent=4))

def get_status(status_id):
    url = "https://api.twitter.com/1.1/statuses/show.json"
    params = {"id": status_id, "include_entities":True,"tweet_mode": "extended","trim_user":False}
    res = config_.twitter.get(url, params=params)
    wait_limit_reset(res)
    # print(json.dumps(json.loads(res.text), indent=2))
    return json.loads(res.text)

def process_tweet(tweet):
    print("# {0} https://twitter.com/{2}/status/{1}"
          .format(tweet["created_at"], tweet["id"], tweet["user"]["screen_name"]))
    if "retweeted_status" in tweet.keys():
        update_user_detail(tweet["user"])
        tweet = tweet["retweeted_status"]
    if "quoted_status" in tweet.keys():
        update_user_detail(tweet["user"])
        tweet = tweet["quoted_status"]
    update_user_detail(tweet["user"])
    #if db.tweets.find_one({"tweet_id": tweet["id"]}) == None:
    #    return
    save_tweet(tweet)
    save_media(tweet)

def list_members(screen_name, slug):
    url = "https://api.twitter.com/1.1/lists/members.json"
    params = {"slug": slug, "owner_screen_name": screen_name, "include_entities": "false", "count": "5000"}
    if screen_name == "saga_kana":
        r = config_.sessions["saga_kana"]["apps"].get(url, params=params)
    else:
        r = config_.sessions["gc_yamm"]["apps"].get(url, params=params)
    users = json.loads(r.text)
    if not "users" in users.keys():
        print(r.headers)
        print(json.dumps(users,indent=2))
    user_list = {}
    #print(json.dumps(users,indent=4))
    for user in users["users"]:
        #print("{0},{1}".format(user["id"],user["screen_name"]))
        user_list[user["screen_name"]] = user["id"]
    return user_list

def copy_list(from_name, from_slug, to_name, to_slug):
    try:
        from_list = list_members(from_name, from_slug)
        to_list = list_members(to_name, to_slug)
    except Exception as e:
        print("Exception at copy_list")
        print(e)
        return
    lists = []
    for name in from_list.keys():
        if not name in to_list:
            lists.append(name)

    url = "https://api.twitter.com/1.1/lists/members/create_all.json"
    params = {"slug": to_slug, "owner_screen_name": to_name}
    chunks = zip(*[iter(lists)]*100)
    for _tuple in chunks:
        params["user_id"] = ",".join(_tuple)
        #r = config.twitter.post(url, params=params)
        r = config_.sessions[to_name]["apps"].post(url, params=params)
        print("add users to the list")
        # status_check(r)
        time.sleep(1)
    return lists

def get_searched_tweets(max_id=config_.status_max, since_id=0, q=""):
    url = "https://api.twitter.com/1.1/search/tweets.json"

    params = {
        "q": q + " include:retweets filter:media max_id:{0} since_id:{1}".format(max_id - 1, since_id + 1),
        "tweet_mode": "extended",
        "include_entities": "true",
        "count": 100,
        "f": "tweets",
        "result_type": "mixed"
    }

    #res = config_.twitter.get(url, params=params)
    res = config_.sessions["gc_yamm"]["apps"].get(url, params=params)
    tweets = json.loads(res.text)["statuses"]
    print(len(tweets))

    latest_id = 0
    oldest_id = config_.status_max
    for tweet in tweets:
        tweet_id = tweet["id"]
        if latest_id == 0:
            latest_id = tweet_id
        oldest_id = tweet_id
        process_tweet(tweet)
    print('----------------------------------------------------')
    return latest_id,oldest_id,res

def get_universal_searched_tweets(max_id=config_.status_max, since_id=0, q=""):
    url = "https://api.twitter.com/1.1/search/universal.json"
    params = {
        "q": q + " max_id:{0} since_id:{1}".format(max_id-1,since_id+1),
        "tweet_mode": "extended",
        "include_entities": "true",
        "count": 100
    }
    res = config_.twitter.get(url, params=params)
    tweets = json.loads(res.text)["modules"]
    print(len(tweets))

    latest_id = 0
    oldest_id = config_.status_max
    for tweet in tweets:
        if not "status" in tweet.keys():
            continue
        tweet = tweet["status"]["data"]
        tweet_id = tweet["id"]
        if latest_id < tweet_id:
            latest_id = tweet_id
        oldest_id = tweet_id
        process_tweet(tweet)
    print('----------------------------------------------------')

    return latest_id,oldest_id,res

def search_tweet(query):
    r = db.query.find_one({"query": query})
    universal_max = 0
    search_max = 0
    if r != None:
        if "universal_max" in r.keys():
            universal_max = r["universal_max"]
        if "search_max" in r.keys():
            search_max = r["search_max"]

    # universeal search
    print("# search/universal")
    latest_id = 0
    max = config_.status_max
    since = universal_max
    while True:
        tmp, max, res = get_universal_searched_tweets(max_id=max, since_id=since, q = query + " include:retweets filter:media")
        if tmp == 0:
            break
        wait_limit_reset(res)
        if latest_id == 0:
            latest_id = tmp

    if latest_id != 0:
        db.query.update({"query": query},
                        {"$set": {"universal_max": latest_id}},True)
        print(db.query.find_one({"query": query}))

    # public api search
    print("# search/tweets")
    latest_id = 0
    max = config_.status_max
    since = search_max
    while True:
        tmp, max, res = get_searched_tweets(max_id=max, since_id=since, q = query + " include:retweets filter:media")
        if tmp == 0:
            break
        wait_limit_reset(res)
        if latest_id == 0:
            latest_id = tmp

    if latest_id != 0:
        db.query.update({"query": query},
                        {"$set": {"search_max": latest_id}},True)
        print(db.query.find_one({"query": query}))

def get_tweets_from_user(user_id=0, screen_name=""):
    if user_id != 0:
        r = db.users.find_one({"_id":user_id})
        if r == None:
            get_user_detail(user_id)
        r = db.users.find_one({"_id":user_id})
        screen_name = r["screen_name"]
    elif len(screen_name) != 0:
        user_id = name2id(screen_name)
        get_user_detail(user_id)
        r = db.users.find_one({"_id":user_id})
        screen_name = r["screen_name"]
    else:
        print("set argument, user_id or screen_name")
        return

    # universeal search
    print("# search/universal")
    latest_id = 0
    max = config_.status_max
    if "universal_max" in r.keys():
        since = r["universal_max"]
    else:
        since = 0
    while True:
        tmp,max,res = get_universal_searched_tweets(max_id = max, since_id = since, q = "from:" + screen_name +  " include:retweets filter:media")
        if tmp == 0:
            break
        wait_limit_reset(res)
        if latest_id == 0:
            latest_id = tmp

    if latest_id != 0:
        db.users.update({"_id": user_id},
                        {"$set":{"universal_max":latest_id}})
        print(db.users.find_one({"_id": user_id}))

    # public api search
    print("# search/tweets")
    latest_id = 0
    max = config_.status_max
    if "search_max" in r.keys():
        since = r["search_max"]
    else:
        since = 0
    while True:
        tmp,max,res = get_searched_tweets(max_id = max, since_id = since, q = "from:" + screen_name +  " include:retweets filter:media")
        if tmp == 0:
            break
        wait_limit_reset(res)
        if latest_id == 0:
            latest_id = tmp

    if latest_id != 0:
        res = db.users.update({"_id": user_id},
                        {"$set":{"search_max":latest_id}})
        print(db.users.find_one({"_id": user_id}))

def get_list_timeline(screen_name, slug):
    url = "https://api.twitter.com/1.1/lists/statuses.json"
    max_id = config_.status_max
    latest_id = 0

    with open("{0}.{1}.txt".format(screen_name,slug),"r") as f:
        since_id = int(f.readline())
    while True:
    # if True:
        params = {
            "owner_screen_name": screen_name, 
            "slug": slug, 
            "since_id": since_id + 1, 
            "max_id": max_id - 1,
            "count": 200, "tweet_mode": "extended", 
            "include_rts": "true"
        }
        try:
            res = config_.twitter.get(url, params=params)
        except Exception as e:
            print(e)
            time.sleep(10)
            continue

        # for key in res.headers.keys():
        #     print(key + " " + res.headers[key])
        # print(time.time())
        # return
        tweets = json.loads(res.text)
        if isinstance(tweets,dict) and "errors" in  tweets.keys():
            print(tweets)
            print(res.headers)
            wait_limit_reset(res)
            continue
        print(len(tweets))
        if len(tweets) < 1:
            break
            print()
        else:
            print(max_id)
        for tweet in tweets:
            max_id = tweet["id"]
            if latest_id == 0:
                latest_id = max_id
            if "retweeted_status" in tweet.keys():
                tweet = tweet["retweeted_status"]
            if "quoted_status" in tweet.keys():
                tweet = tweet["quoted_status"]
            process_tweet(tweet)
        wait_limit_reset(res)
        print('----------------------------------------------------')
    if max_id != config_.status_max:
        with open("{0}.{1}.txt".format(screen_name,slug),"w") as f:
            f.write("{0}\n".format(latest_id))
    return

def get_likes(screen_name):
    max_id = config_.status_max
    url = "https://api.twitter.com/1.1/favorites/list.json"
    params = {"screen_name": screen_name, "count": 200, "tweet_mode": "extended"}
    # ids = []
    while True:
        print('----------------------------------------------------')
        params["max_id"] = max_id - 1
        # r = config_.twitter.get(url, params=params)
        print(url)
        print(params)
        try:
            r = config_.sessions["gc_yamm"]["apps"].get(url, params=params)
        except:
            return
        j = json.loads(r.text)
        if len(j) < 1:
            break
        for tweet in j:
            max_id = tweet["id"]
            process_tweet(tweet)
        print(r.headers)
        wait_limit_reset(r)
        time.sleep(1)

if __name__ == '__main__':
    print("twitter")
