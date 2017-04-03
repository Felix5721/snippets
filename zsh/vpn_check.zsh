#!/bin/zsh
vpn_stat="off"
vpn_config=$1
wait_time=1
while [[ $vpn_stat = "off" ]]; do
	#the program has_internet needs to be in path to be found (is in this repo) 
	inet_stat=$(has_internet)
	if [[ $inet_stat = "Online" ]]; then
		pip=$(curl -sH "Host: ip4.nnev.de" 79.140.42.102)
		if [[ $pip = "37.120.184.171" ]]; then
		else
			systemctl restart openvpn-client@$vpn_config.service
		fi
		vpn_stat="on"
	elif [[ $(systemctl is-active openvpn-client@$vpn_config.service) = "active" ]]; then
		systemctl stop openvpn-client@$vpn_config.service
	else
		sleep $wait_time
		if [[ $wait_time -lt 15 ]]; then
			wait_time=$((wait_time+1))
		else
			vpn_stat="no_internet"
		fi
	fi
done
echo "VPN Status: "$vpn_stat
