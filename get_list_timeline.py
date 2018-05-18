import twitter
import sys

if __name__ == '__main__':
    twitter.copy_list("saga_kana", "p", sys.argv[1], sys.argv[2])
    twitter.get_list_timeline(sys.argv[1],sys.argv[2])
