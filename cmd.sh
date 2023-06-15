#!/bin/bash

# [Still need to be tested]

# Get the command-line argument
arg=$1

# Check if an argument was provided
if [ -z "$arg" ]; then
  echo "No argument provided."
  exit 1
fi

# Construct a switch case based on the argument
case $arg in
  "1")
    # for h1 - video streaming server
    ffmpeg -re -stream_loop -1 -i ./assets/video3.mp4 -vcodec copy -f mpegts - | nc -l -p 9999
    ;;
  "2")
    # for h2 - video stream receiver client
    nc -v 10.0.0.1 9999 > /dev/null
    ;;
  "3")
    # for h3 - file hosting server
    python3 -m http.server 9998
    ;;
  "4")
    # for h4 - file downloading client
    while true; do wget http://10.0.0.3:9998/assets/random_data -O ./assets/temp/random; sleep 5; done
    ;;
  "5")
    # for h5 - web hosting server
    python3 -m http.server 9997
    ;;
  "6")
    # for h6 - web accessing client
    while true; do curl 10.0.0.5:9997; sleep 2; done
    ;;
  "7")
    # for h7 - DoS attack generating machine
    hping3 -c 1000 -d 10 -S -w 8 -p 80 -i u7000 --rand_source 10.0.0.8
    ;;
  *)
    echo "Invalid option."
    exit 1
    ;;
esac
