#!/usr/bin/env bash
cd /home/ogawara/git/twitter_media_downloader/twitter-media-downloader/
if [ -e search_universal.ps ]
then
    echo already running
    exit
fi

touch search_universal.ps

cat people.txt user_id.txt | sort | uniq | grep -v ^$ > user_id.tmp
echo > people.txt
mv user_id.tmp user_id.txt
sort -R user_id.txt | while read i
do
    if [ -e search_universal.flag ]
    then
        echo flag exists
        break
    fi
    /home/ogawara/.pyenv/shims/python -u search_universal.py $i >> search_universal.stdout.log 2>> search_universal.stderr.log
done

rm search_universal.ps
