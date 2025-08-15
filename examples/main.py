import pedroclient
import connect_wlan
import _thread
import uasyncio

def cb(msg):
    print(msg)
    
def test():
    ip = connect_wlan.connect_wlan()
    print('connected')
    c = pedroclient.PedroClient(ip, cb, '192.168.0.80')
    print('Pedro connected')

    c.subscribe('temp(X)', 'true')
    print('subscribed')
    return c


c = test()


