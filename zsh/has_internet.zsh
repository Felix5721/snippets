#!/bin/zsh
echo -e "GET http://google.com HTTP/1.0\n\n" | nc --wait=1 172.217.22.110 80 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Online"
else
    echo "Offline"
fi
