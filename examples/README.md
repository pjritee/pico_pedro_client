# Kitchen Thermometer Example.

This example illustrates how to set up a temperature sensor, possibly as part of a smart house, where each notification from the sensor might be treated as a percept for a TeleoR agent. Perhaps such an agent, in response to an unexpected increase in the temperature of the kitchen might ask the sensor to increase the sample rate.

## Testing the code.

The first thing to do is to start a Pedro server on some machine on the network and to set PEDRO_SERVER_IP to the IP address of that machine.

The next step is to edit wifi_secrets.py with the required information for your network.

For setup (and testing purposes) start Thonny and copy the required files to the Pico W. Assuming you have
set up the temperature sensor connected to the Pico appropriately (or modified main.py with a different sensor or pins).

If you now start main.py from within Thonny you should see output as the program runs.

In order to play with it there are two simple ways to see the notifications and to interact with the program.

## Using pedro_gui.py
The python_api for Pedro includes ```pedro_gui.py```. If you run that and add the subscription ```temperature(CID, Temp)``` then the temperature notifications from the Pico will be displayed. A notification such as ```set_sample_rate(kitchen_thermometer, 0.2)``` can be added in the ```Notification box```.

## Using QuProlog
QuProlog can be downloaded from https://staff.eecs.uq.edu.au/pjr/HomePages/PedroHome.html. Once downloaded
start two terminals. In the first terminal enter the command ```qp -Afirst```. In the second enter the command ```qp -Asecond```. Using the ```-A``` switch makes this instance of QuProlog a Pedro client (```first`` and ```second`` name the process and is not relevant other that starting up the Pedro interface).

In the first terminal (now in the QuProlog interpreter) enter the query ```pedro_subscribe(temperature(A, B), true,ID)```. The interpreter should respond with something like
<code>
A = A
B = B
ID = 1
<code>
The following query will then create an 'infinite loop' of getting a notification and printing it out.
<code>
repeat, Message \<\<- Address, write(Message), nl, fail.
<code>

In the second terminal, at any time, enter a query like
<code>
set_sample_rate(kitchen_thermometer, 0.2) -\>\> pedro.
<code>

The Pico sensor should then start sending notifications every 0.2 seconds.

