import twitter
import config_
import time,sys,json

if __name__ == '__main__':
    with open(sys.argv[1], "r") as f:
        txt = f.read().strip("\n")
        lines = txt.split("\n")
        for line in lines:
            line = line.split("/")[-1]
            print(line)
            r = twitter.db.tweets.find_one({"tweet_id_str":line})
            if r != None:
                continue
            try:
                res = twitter.get_status(line)
                twitter.process_tweet(res)
            except Exception as e:
                print("ERROR:{0}".format(e))
                print("STATUS_ID:{0}".format(line))
                print(json.dumps(res, indent=4))
            time.sleep(1)
