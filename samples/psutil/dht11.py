# *****************************************************************************
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html 
#
# *****************************************************************************

# Adapted from https://github.com/ibm-messaging/iot-python/tree/master/samples/psutil
# Adapted from https://github.com/adafruit/Adafruit_Python_DHT/blob/master/examples/AdafruitDHT.py

import getopt
import time
import sys
import platform
import json
import signal
from uuid import getnode as get_mac
import Adafruit_DHT


try:
	import ibmiotf.device
except ImportError:
	# This part is only required to run the sample from within the samples
	# directory when the module itself is not installed.
	#
	# If you have the module installed, just use "import ibmiotf"
	import os
	import inspect
	cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../../src")))
	if cmd_subfolder not in sys.path:
		sys.path.insert(0, cmd_subfolder)
	import ibmiotf.device



def interruptHandler(signal, frame):
	client.disconnect()
	sys.exit(0)

def usage():
	print(
		"DHT11: Publish DHT11 Temperature and Humidity to the IBM Internet of Things Foundation." + "\n" +
		"\n" +
		"Datapoints sent:" + "\n" +
		"  name          The name of this device.  Defaults to hostname ('%s')" % platform.node() + "\n" +
		"  temperature   " + "\n" +
		"  humidity      " + "\n" +
		"\n" + 
		"Options: " + "\n" +
		"  -h, --help       Display help information" + "\n" + 
		"  -n, --name       Override the default device name" + "\n" + 
		"  -v, --verbose    Be more verbose"
	)

def commandProcessor(cmd):
	global interval
	print("Command received: %s" % cmd.data)
	if cmd.command == "setInterval":
		if 'interval' not in cmd.data:
			print("Error - command is missing required information: 'interval'")
		else:
			interval = cmd.data['interval']
	elif cmd.command == "print":
		if 'message' not in cmd.data:
			print("Error - command is missing required information: 'message'")
		else:
			print(cmd.data['message'])
	
if __name__ == "__main__":
	signal.signal(signal.SIGINT, interruptHandler)

	try:
		opts, args = getopt.getopt(sys.argv[1:], "hn:vo:t:i:T:c:", ["help", "name=", "verbose", "type=", "id=", "token=", "config="])
	except getopt.GetoptError as err:
		print(str(err))
		usage()
		sys.exit(2)

	verbose = False
	organization = "quickstart"
	deviceType = "sample-iotpsutil"
	deviceId = str(hex(int(get_mac())))[2:]
	deviceName = platform.node()
	authMethod = None
	authToken = None
	configFilePath = None
	
	# Seconds to sleep between readings
	interval = 60
	
	for o, a in opts:
		if o in ("-v", "--verbose"):
			verbose = True
		elif o in ("-n", "--name"):
			deviceName = a
		elif o in ("-o", "--organization"):
			organization = a
		elif o in ("-t", "--type"):
			deviceType = a
		elif o in ("-i", "--id"):
			deviceId = a
		elif o in ("-T", "--token"):
			authMethod = "token"
			authToken = a
		elif o in ("-c", "--cfg"):
			configFilePath = a
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		else:
			assert False, "unhandled option" + o

	client = None
	try:
		if configFilePath is not None:
			options = ibmiotf.device.ParseConfigFile(configFilePath)
		else:
			options = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
		client = ibmiotf.device.Client(options)
		client.commandCallback = commandProcessor
		client.connect()
	except ibmiotf.ConfigurationException as e:
		print(str(e))
		sys.exit()
	except ibmiotf.UnsupportedAuthenticationMethod as e:
		print(str(e))
		sys.exit()
	except ibmiotf.ConnectionException as e:
		print(str(e))
		sys.exit()
	

	print("(Press Ctrl+C to disconnect)")

	while True:
		time.sleep(interval)

	# Try to grab a sensor reading.  Use the read_retry method which will retry up
	# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
		humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 23)

	# Un-comment the line below to convert the temperature to Fahrenheit.
		temperature = temperature * 9/5.0 + 32

	# Note that sometimes you won't get a reading and
	# the results will be null (because Linux can't
	# guarantee the timing of calls to read the sensor).
	# If this happens try again!
		if humidity is not None and temperature is not None:
        		print 'Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity)
		else:
        		print 'Failed to get reading. Try again!'
        		sys.exit(1)

                data = {
                       'd': {
				'name' : deviceName,
                       		'temperature' : temperature,
                       		'humidity' : humidity
			}
                }
                if verbose:
                        print("Datapoint = " + json.dumps(data))

                client.publishEvent("dht11", "json", data)
