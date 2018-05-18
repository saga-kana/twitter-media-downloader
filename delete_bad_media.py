import twitter, config_
import sys, os

if __name__ == '__main__':
    tweets = twitter.db.tweets.find({"media.evaluation":"bad"})
    print(config_.top)
    for tweet in tweets:
        for f in tweet["media"]:
            path = config_.top + "/" + tweet["user_id_str"] + "/" +  f["filename"]
            if "evaluation" in f.keys() and f["evaluation"] == "bad" and os.path.exists(path):
                print(tweet["screen_name"] + " : " + tweet["full_text"])
                os.remove(path)
