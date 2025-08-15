import network
import socket
import time
import machine
import ntptime

import secrets


def connect_wlan():
  #Connect to WLAN
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.connect(secrets.ssid, secrets.password)
  while wlan.isconnected() == False:
    print('Waiting for connection...')
    time.sleep(1)     
  ip = wlan.ifconfig()[0]
  print(f'Connected on {ip}')
  rtc = machine.RTC()
  rtc.datetime((2000, 1, 1, 0, 0, 0, 0, 0))
  ntptime.settime()
  print("Current time:", time.localtime(time.time() + 36000))
  return ip

