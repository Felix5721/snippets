#!/bin/python3
import subprocess
import re
import socket
from pydbus import SystemBus
from gi.repository import GLib

WIRELESS_SERVICE = "network-wireless@wlp4s0.service"
WIRED = "/org/freedesktop/network1/link/_3"
VPN = "openvpn-client@dijkstra.service"
SYSTEMD = "org.freedesktop.systemd1"
NETWORKD = "org.freedesktop.network1"

class NetworkattachListener:
	def __init__(self):
		self.system_bus = SystemBus()
		self.systemd= self.system_bus.get(SYSTEMD)
		self.sysmanager = self.systemd[".Manager"]
		self.wired_iface = self.system_bus.get(NETWORKD, WIRED+str(self.getWiredNum('enp0s25')));
		self.wireless_iface = self.system_bus.get(NETWORKD, WIRED+str(self.getWiredNum('wlp4s0')));
		self.wireless_srv = self.system_bus.get(SYSTEMD, self.sysmanager.GetUnit(WIRELESS_SERVICE))
		self.wireless_status = False
		self.eth_status = False

		self.wired_iface.PropertiesChanged.connect(self.worker_wlan)
		self.wireless_iface.PropertiesChanged.connect(self.worker_vpn)
		if self.isRoutable(self.wired_iface.Get(NETWORKD + ".Link", "OperationalState")):
			self.eth_status = True
			self.WirelessOff()
		else:
			self.WirelessOn()
		self.updateIcon()

	def getWiredNum(self, iface_name):
		#I know this isn't a nice way to do it, but I didn't find any other documentation on how to get his down
		#If you do now how to get this information properly, please let me know
		linkn = subprocess.run(['networkctl', 'list', iface_name], stdout=subprocess.PIPE).stdout.decode("utf-8")
		linkn = re.search("(?<=\n).*(?= "+iface_name+")", linkn).group(0)
		return int(linkn)


	def isRoutable(self, op_state):
		if(op_state == 'no-carrier'):
			return False
		elif(op_state == 'routable'):
			return True

	def worker_vpn(self, interface, changed, inv):
		if "OperationalState" in changed.keys():
			if self.isRoutable(changed["OperationalState"]):
				self.wireless_status = True
				self.sysmanager.StopUnit(VPN, "fail")
				self.sysmanager.StartUnit(VPN, "replace")
			else:
				self.wireless_status = False
			self.updateIcon()

	def worker_wlan(self, interface, changed, inv):
		if "OperationalState" in changed.keys():
			if self.isRoutable(changed["OperationalState"]):
				self.eth_status = True
				self.WirelessOff()
			else:
				self.eth_status = False
				self.WirelessOn()
			self.updateIcon()

	def updateIcon(self):
		if self.eth_status or self.wireless_status:
			if self.eth_status:
				self.setIcon("ethernet")
			else:
				self.setIcon("wireless")
		else:
			self.setIcon("offline")

	def setIcon(self, state):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(("localhost", 4224))
		sock.send(state.encode())
		sock.close()

	def getWirelessState(self):
		return self.wireless_srv.Get(SYSTEMD + ".Unit", "ActiveState")

	def setWireless(self, status):
		state = "active" if status == True else "inactive"
		if self.getWirelessState() != state:
			if status:
				self.sysmanager.StartUnit(WIRELESS_SERVICE, "replace")
			else:
				self.sysmanager.StopUnit(WIRELESS_SERVICE, "fail")
				self.sysmanager.StopUnit(VPN, "fail")
				self.sysmanager.StartUnit(VPN, "replace")

	def WirelessOn(self):
		print("Turn Wifi on")
		self.setWireless(True)
	def WirelessOff(self):
		print("Turn Wifi off")
		self.setWireless(False)

def main():
	loop = GLib.MainLoop()
	devlistener = NetworkattachListener()
	loop.run()

if __name__ == "__main__":
	main()
