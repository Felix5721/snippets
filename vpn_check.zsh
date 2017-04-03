#!/bin/zsh
pip=$(curl -sH "Host: ip4.nnev.de" 79.140.42.102)
if [[ $pip = "37.120.184.171" ]]; then
else
	systemctl restart openvpn-client@dijkstra.service
fi
