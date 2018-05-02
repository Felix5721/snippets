#!/bin/python3

import subprocess
import os
import re
import sys
from jinja2 import Environment, FileSystemLoader

## This program is used to setup a network namespace with a wiregurad peer running inside, for trafic redirection

def do_make_nns(nns):
	mk = ["ip", "netns", "add",  nns]
	setup = nns_wrap(nns, link_up("lo"))
	subprocess.call(mk)
	subprocess.call(setup)
	directory = "/etc/netns/" + nns
	if not os.path.exists(directory):
		os.makedirs(directory)
	dnsf = open(directory + "/resolv.conf", "w")
	dnsf.write("nameserver 10.129.53.1")
	dnsf.close()

def delete_nns(nns):
	subprocess.call(["ip", "netns", "delete", nns])

def do_add_peers(nns, rt_table, num):
	#variables
	veth = nns + "-veth"
	peer = nns + "-peer"
	adr_veth = "10.129.%d.0" % num
	adr_peer = "10.129.%d.1" % num
	adr_veth6 = "2a03:4000:f:af:1111::%x:0" % num
	adr_peer6 = "2a03:4000:f:af:1111::%x:1" % num
	#setup links
	subprocess.call(["ip", "link", "add", veth, "type", "veth", "peer", "name", peer])
	subprocess.call(move_link(peer, nns))
	#setup ipv4 routing
	subprocess.call(link_addr(veth, adr_veth + "/31"))
	subprocess.call(nns_wrap(nns, link_addr(peer, adr_peer + "/31")))
	subprocess.call(link_up(veth))
	subprocess.call(nns_wrap(nns, link_up(peer)))
	subprocess.call(nns_wrap(nns, route_add(peer, adr_veth, "main", 31, True)))
	subprocess.call(route_add(veth, adr_veth, "direct", 31))
	#setup ipv6 routing
	subprocess.call(link_addr(veth, adr_veth6 + "/127", True))
	subprocess.call(nns_wrap(nns, link_addr(peer, adr_peer6 + "/127", True)))
	subprocess.call(route_add(veth, adr_veth6, "direct", 127, False, True))
	subprocess.call(nns_wrap(nns, route_add(peer, adr_veth6, "main", 127, True, True)))
	subprocess.call(["ip", "-6", "neigh", "add", "proxy", adr_peer6, "dev", veth])
	#add default routes to dedicated table
	subprocess.call(route_add(veth, adr_peer, rt_table, 31, True))
	subprocess.call(route_add(veth, adr_peer6, rt_table, 127, True, True))
	

def nns_wrap(nns ,cmd):
	c = ["ip", "netns", "exec", nns]
	return c + cmd

def link_up(link):
	c = ["ip", "link", "set", link, "up"]
	return c

def link_addr(link, addr, ipv6=False):
	if not ipv6:
		c = ["ip", "addr", "add", addr, "dev", link]
	else:
		c = ["ip", "-6", "addr", "add", addr, "dev", link]
	return c

def move_link(link, nns):
	c = ["ip", "link", "set", link, "netns", nns]
	return c

def route_add(link, addr, table, net, default=False, ipv6=False):
	c = [ "ip" ]
	if ipv6:
		c.append("-6")
	if default:
		c += [ "route", "add", "default", "via", addr, "dev", link, "table", table]
	else:
		c += [ "route", "add", addr + "/%d"%net , "dev", link, "table", table]
	return c

def load_nft_nat(oifname):
	#create nft_rules files
	j2_env = Environment(loader=FileSystemLoader("/root"),trim_blocks=True)
	nft_rules = j2_env.get_template("nftables.tmpl").render(ifname=oifname)
	nftfile = open("/tmp/nftables-tmp.conf", "w")
	nftfile.write(nft_rules)
	nftfile.write("\n")
	return ["nft", "-f", "/tmp/nftables-tmp.conf"]


def setup_wg_tunnel(wgname, nns=None):
	if nns is None:
		def do(cmd):
			subprocess.call(cmd)
	else:
		def do(cmd):
			subprocess.call(nns_wrap(nns, cmd))
	do(["wg-quick", "up", wgname])
	if not nns is None:
		#setup rules so that traffic to other subnets does not get routed though vpn
		do(["ip", "rule", "add", "to", "10.128.0.0/9", "lookup", "main"])
		do(["ip", "-6", "rule", "add", "to", "2a03:4000:f:af::/64", "lookup", "main"])
		#load nft rules to and enable ip forwarding
		do(["sysctl","net/ipv6/conf/all/forwarding=1"])
		do(["sysctl","net/ipv6/conf/all/proxy_ndp=1"])
		do(load_nft_nat(wgname))

def get_subnetnum(rt_table):
	rtfile = open("/etc/iproute2/rt_tables")
	rc = re.compile("^([\d]*) " + rt_table)
	for line in rtfile:
		match = rc.findall(line)
		if len(match) != 0:
			return int(match[0])
	return None
	

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: %s [start|stop] wgname" % sys.argv[0])
	else:
		wgname = sys.argv[2]
		action = sys.argv[1]
		rc = re.compile("mullvad-(.*)")
		mulid = rc.findall(wgname)[0]
		nns = "mul" + mulid
		rt_table = "mul_" + mulid
		if action == "start":
			subnet = get_subnetnum(rt_table)
			if not subnet is None:
				do_make_nns(nns)
				do_add_peers(nns, rt_table, subnet)
				setup_wg_tunnel(wgname, nns)
				print("Created Network Namespace with wireguard peer running.")
				subprocess.call(nns_wrap(nns, ["ip", "a"]))
			else:
				print("Unknown wireguard peer, not creating routing network namespace.")
		else:
			delete_nns(nns)
			print("Deleted network namespace.")

