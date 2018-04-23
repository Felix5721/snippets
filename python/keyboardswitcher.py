#!/bin/python3
#
#Program to switch keyboard layout between de and us

import subprocess
import re

def getLayout():
	cmd = ["setxkbmap", "-query"]
	out = subprocess.check_output(cmd)
	out = str(out)[2:-1]
	reg = re.compile(".*layout: *(.*)")
	m = re.findall(reg, out)[0]
	return m[:-2]

def main():
	cmd = ["setxkbmap"]
	if getLayout() == "de":
		cmd.append("us")
	elif getLayout():
		cmd.append("de")
	subprocess.call(cmd)

if __name__ == "__main__":
	main()
