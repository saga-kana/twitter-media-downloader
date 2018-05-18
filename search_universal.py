import config_, twitter
import sys, os, json
from io import BytesIO
import requests
from pymongo import MongoClient
from PIL import Image
from pprint import pprint

if __name__ == '__main__':
    if sys.argv[1].isdigit():
        twitter.get_tweets_from_user(user_id=int(sys.argv[1]))
    else:
        twitter.get_tweets_from_user(screen_name=sys.argv[1])




