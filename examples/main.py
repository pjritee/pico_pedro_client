""" 
Kitchen Thermometer Example.
This simple example demonstrates how to use the PedroClient to read temperature data from an AM2320 sensor
and send it to a Pedro server as a notification. 
It also allows setting the sample rate via a Pedro notification from another client.
Plenty of prints are included to help understand the flow of the program.
"""

import pedroclient
import connect_wlan
import prolog_parser

import time
import am2320
from machine import I2C, Pin

# The IP address of the Pedro server to connect to.
# This should be the IP address of the machine running the Pedro server.
# In this example, we assume the Pedro server is running on a machine with this IP address
PEDRO_SERVER_IP = '192.168.0.80'

# Initialize the AM2320 sensor
i2c = I2C(scl=Pin(9), sda=Pin(8))
sensor = am2320.AM2320(i2c)

# Initialize the onboard LED to be used as a status indicator
status_pin = Pin("LED", machine.Pin.OUT)

# Set the client ID for this thermometer
# This ID is used to identify the thermometer in the Pedro server
# It should be unique for each sensor instance.
clientID = "kitchen_thermometer"

# Initialize the sample rate for reading the sensor
# This can be set dynamically via a Pedro notification
sample_rate = 5 # seconds

# Althogh if received notification is easy enough to parser within Python, we use a Prolog parser
# to demonstrate how to handle Prolog terms in a more structured way.
parser = prolog_parser.PrologParser()

# Callback function to handle incoming notifications from the Pedro server
# This function is called when a notification is received that matches the subscription (the
# only notification we subscribe to is 'set_sample_rate(clientID, X)' where X is the new sample rate).
# It parses the notification message and updates the sample rate accordingly.
def callback(msg):
    print('callback', msg)
    term = parser.parse(msg)
    if term is None:
        print('Error parsing term:', msg)
        return
    print('Parsed term:', str(term))
    # update the sample rate.
    global sample_rate
    sample_rate = term.args[1].val
    print('Sample rate set to:', sample_rate)

# The status pin is turned off initially to indicate that the device is not connected
# It is flashed during the connection process to indicate activity and finally stays turned on
# when the device is connected and active. If an exeption occurs, the status pin is turned off
# to signify that the device is not functioning properly.
try:
    status_pin.off()
    time.sleep(1)
    # Connect to the WLAN and get the IP address
    ip = connect_wlan.connect_wlan()
    print('connected')
    status_pin.on()
    time.sleep(1)
    status_pin.off()
    time.sleep(1)

    # Create a PedroClient instance with the IP address and callback function
    # Becase we are expecting notifications we need to create a Reader object 
    # that will handle incoming messages from the Pedro server. We do this by supplying
    # the reader_period parameter to the PedroClient constructor. This causes the Reader object
    # to be created and it polls the data socket for incoming messages at the specified interval.
    
    client = pedroclient.PedroClient(ip, callback, PEDRO_SERVER_IP, reader_period=1000)
    print('Pedro connected')
    status_pin.on()
    time.sleep(1)
    status_pin.off()
    time.sleep(1)

    # Subscribe to the 'set_sample_rate(clientID, X)' notification. The Pedro server will only pass on
    # notifications that match the subscription pattern where the sample rate is (a number) greater than 0.
    ack = client.subscribe('set_sample_rate('+clientID+', X)', 'X > 0')
    print('subscribed ack:', ack)
    if ack:
        status_pin.on()
        
        while True:
            # Read the sensor data at the specified sample rate and send it to the Pedro server 
            # as a termperature(clientID, temperature) notification.
            time.sleep(sample_rate)
            try:
                sensor.measure()
            except Exception as e:
                print('Error reading sensor:', e)
                continue    
            
            temperature = sensor.temperature()
            print('Temperature:', temperature)
            msg = 'temperature('+clientID+', '+str(temperature)+')'
            ack = client.notify(msg)
            print('ack', ack, 'msg', msg)
except Exception as e:
    print('Exception', e)
    # If an exception occurs, turn off the status pin to indicate that the device is not functioning properly
    status_pin.off()
    



