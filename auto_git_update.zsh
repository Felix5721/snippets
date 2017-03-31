if [[ $(git status | grep "nothing to commit") == "nothing to commit, working tree clean" ]]; then
	git pull
else
	echo "Local changes in repo, not auto updateing!"
fi
