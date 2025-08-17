import network
import socket
import time
import machine
import ntptime

import wifi_secrets


def connect_wlan():
  #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi_secrets.ssid, wifi_secrets.password)
    max_wait = 10
    while max_wait > 0:
        if wlan.status() >= 3:  # Connected
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(1)
    if wlan.status() != 3:
        raise RuntimeError('Failed to establish a network connection')
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    time.sleep(2)
    rtc = machine.RTC()
    rtc.datetime((2000, 1, 1, 0, 0, 0, 0, 0))
    ntptime.settime()
    print("Current time:", time.localtime(time.time() + 36000))
    return ip

