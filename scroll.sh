#!/usr/bin/env bash
sort scroll.txt | uniq | grep -v ^$ > scroll.tmp
mv scroll.tmp scroll.txt
sort -R scroll.txt | while read i
do
    #python -u twitter.py $i
    if [ -e scroll.flag ]
    then
        echo flag
        break
    fi
    /home/ogawara/.pyenv/shims/python -u scroll.py $i >> scroll.stdout.log 2>> scroll.stderr.log
done
