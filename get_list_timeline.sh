 cd /home/ogawara/git/twitter_media_downloader/twitter-media-downloader/
 if [ -e get_list_timeline.ps ]
 then
    echo ps exists
    exit
 fi
 touch get_list_timeline.ps
 /home/ogawara/.pyenv/shims/python get_list_timeline.py $1 $2
 rm get_list_timeline.ps
