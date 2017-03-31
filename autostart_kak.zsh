sessionname=$(basename $(pwd))
if [[ $(kak -l | grep $sessionname) == $sessionname ]]; then
	echo "kak session running: "$sessionname
else
	kak -d -s $sessionname
fi
