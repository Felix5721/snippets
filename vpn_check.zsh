#!/bin/zsh
vpn_stat="off"
while [[ $vpn_stat = "off" ]]; do
	inet_stat=$(/home/judge/Projects/zsh_scripts/has_internet.zsh)
	if [[ $inet_stat = "Online" ]]; then
		pip=$(curl -sH "Host: ip4.nnev.de" 79.140.42.102)
		if [[ $pip = "37.120.184.171" ]]; then
		else
			systemctl restart openvpn-client@dijkstra.service
		fi
		vpn_stat="on"
	elif [[ $(systemctl is-active openvpn-client@dijkstra.service) ]]; then
		systemctl stop openvpn-client@dijkstra.service
	fi
done
