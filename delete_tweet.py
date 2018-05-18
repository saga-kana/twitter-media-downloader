import twitter
import config_
import time,sys,json

def del_tweet(status_id):
    s = config_.sessions["saga_kana"]["apps"]
    print(s.post("https://api.twitter.com/1.1/statuses/destroy.json",params={"id":status_id}).status_code)

def del_retweet(status_id):
    s = config_.sessions["saga_kana"]["apps"]
    _id = json.loads(s.get("https://api.twitter.com/1.1/statuses/show.json",params={"id":status_id,"include_my_retweet":1}).text)
    if "current_user_retweet" in _id.keys():
        _id = _id["current_user_retweet"]
        del_tweet(_id["id"])
        return
    print("DEL RT")
    #ids = json.loads(s.get("https://api.twitter.com/1.1/statuses/retweets.json",params={"id":status_id,"trim_user":False,"count":100}).text)
    r = s.get("https://api.twitter.com/1.1/statuses/retweets.json",params={"id":status_id,"trim_user":False,"count":100})
    print("WAIT LIMIT RESET")
    twitter.wait_limit_reset(r)
    ids = json.loads(r.text)
    #print(ids)
    if "errors" in ids:
        print("error")
        print(ids)
        sys.exit()
    for i in ids:
        print(i["user"]["screen_name"])
        if i["user"]["id"] == 485621951: # saga_kana
            del_tweet(i["id"])
            return
    print("NOT RT")

if __name__ == '__main__':
    r = config_.sessions["saga_kana"]["apps"]
    with open(sys.argv[1], "r") as f:
        txt = f.read().strip("\n")
        lines = txt.split("\n")
        for line in lines:
            status_id = line.split("/")[-1]
            print(line)
            r = twitter.db.tweets.find_one({"tweet_id_str":status_id})
            #if r != None and "full_text" in r.keys():
            if False and r != None and "full_text" in r.keys():
                print(r["full_text"])
            else:
                try:
                    r = twitter.get_status(status_id)
                    #twitter.process_tweet(res)
                    if "errors" in r.keys():
                        print(r)
                    print(r["full_text"])
                    #if "7mb_yut" in r["full_text"]:
                    #    del_tweet(status_id)
                    #continue
                    if not "@" in r["full_text"] or "popopooch" in r["full_text"]:
                        continue
                except Exception as e:
                    print("ERROR:{0}".format(e))
                    continue
            screen_name = line.split("/")[-3]
            print(screen_name)
            input_test_word = input("delete? y/[n]")
            if input_test_word == "y":
                if screen_name == "saga_kana":
                    del_tweet(status_id)
                else:
                    del_retweet(status_id)
