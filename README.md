# pico_pedro_client
A micropython client for the Pedro publish-subscribe system.

Pedro is a subscription/notification communications system that also provides support for peer-to-peer communication. It can provide high-level communications support for agents. Pedro is based on Prolog technology - notifications are Prolog terms and subscriptions consists of a Prolog term (head) and a Prolog goal (body). A notification matches a subscription if the notification term unifies with the subscription head and the subscription body succeeds. (See https://staff.eecs.uq.edu.au/pjr/HomePages/PedroHome.html).

A possible use of this micropython client is to set up the Pico as a "smart sensor"  within a smart home where the sensor notifications from the Pico are used as percepts of a TeleoR program - TeleoR is a major extension of Nilsson's Teleo Reactive Procedures (see https://staff.eecs.uq.edu.au/pjr/HomePages/QulogHome.html).  