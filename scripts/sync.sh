#!/bin/bash

pi_ip=192.168.178.53 # the ip of your rpi

files=(.git __pycache__ .idea audio-reactive-led-strip/images Resources )
excludes=()
for f in "${files[@]}"; do
  excludes+=(--exclude "$f")
done

rsync --progress -av "${excludes[@]}" -r $1 pi@$pi_ip:$2
