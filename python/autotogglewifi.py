#!/bin/python3
from pydbus import SystemBus
from gi.repository import GLib

WIRELESS_SERVICE = "network-wireless@wlp4s0.service"
WIRED = "/org/freedesktop/network1/link/_32"
VPN = "vpn_checker.service"
SYSTEMD = "org.freedesktop.systemd1"
NETWORKD = "org.freedesktop.network1"

class NetworkattachListener:
	def __init__(self):
		self.system_bus = SystemBus()
		self.systemd= self.system_bus.get(SYSTEMD)
		self.sysmanager = self.systemd[".Manager"]
		self.wired = self.system_bus.get(NETWORKD, WIRED);
		self.wireless = self.system_bus.get(SYSTEMD, self.sysmanager.GetUnit(WIRELESS_SERVICE))

		self.wired.PropertiesChanged.connect(self.worker)
		if self.isRoutable(self.wired.Get(NETWORKD + ".Link", "OperationalState")):
			self.WirelessOff()
		else:
			self.WirelessOn()

	def isRoutable(self, op_state):
			if(op_state == 'no-carrier'):
				return False
			elif(op_state == 'routable'):
				return True

	def worker(self, interface, changed, inv):
		if "OperationalState" in changed.keys():
			if self.isRoutable(changed["OperationalState"]):
				self.WirelessOff()
			else:
				self.WirelessOn()

	def getWirelessState(self):
		return self.wireless.Get(SYSTEMD + ".Unit", "ActiveState")

	def setWireless(self, status):
		state = "active" if status == True else "inactive"
		if self.getWirelessState() != state:
			if status:
				self.sysmanager.StartUnit(WIRELESS_SERVICE, "replace")
				self.sysmanager.StartUnit(VPN, "replace")
			else:
				self.sysmanager.StopUnit(WIRELESS_SERVICE, "fail")
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