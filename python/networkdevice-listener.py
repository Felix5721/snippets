from pydbus import SystemBus
from gi.repository import GLib

def main():
	system_bus = SystemBus()
	loop = GLib.MainLoop()

	net = system_bus.get('org.freedesktop.network1', '/org/freedesktop/network1/network/_350_2dwired');
	net.PropertiesChanged.connect(print)
	loop.run()

if __name__ == "__main__":
	main()
