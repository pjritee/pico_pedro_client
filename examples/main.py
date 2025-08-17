import pedroclient
import connect_wlan
import prolog_parser

import time
import am2320
from machine import I2C, Pin

i2c = I2C(scl=Pin(9), sda=Pin(8))
sensor = am2320.AM2320(i2c)

status_pin = Pin("LED", machine.Pin.OUT)

clientID = "kitchen_thermometer"

sample_rate = 5 

parser = prolog_parser.PrologParser()

def callback(msg):
    print('callback', msg)
    term = parser.parse(msg)
    if term is None:
        print('Error parsing term:', msg)
        return
    print('Parsed term:', str(term))
    global sample_rate
    sample_rate = term.args[1].val
    print('Sample rate set to:', sample_rate)

try:
    status_pin.off()
    time.sleep(1)
    ip = connect_wlan.connect_wlan()
    print('connected')
    status_pin.on()
    time.sleep(1)
    status_pin.off()
    time.sleep(1)

    client = pedroclient.PedroClient(ip, callback, '192.168.0.80', reader_period=1000)
    print('Pedro connected')
    status_pin.on()
    time.sleep(1)
    status_pin.off()
    time.sleep(1)

    ack = client.subscribe('set_sample_rate('+clientID+', X)', 'X > 0')
    print('subscribed ack:', ack)
    if ack:
        status_pin.on()
        
        while True:
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
    status_pin.off()
    



