EE 250 Final Project:
Plant Monitor

Team Members:
Joshua Williams

Github Repository:
https://github.com/jwills15/PlantMonitor

Video Demonstration Link:
https://drive.google.com/file/d/1NpRbgDctqdNc5Er7V7WB9srjZDacSF5W/view?usp=sharing

External Libraries:
influxdb (https://influxdb-python.readthedocs.io/en/latest/include-readme.html#id2)
grovepi (https://wiki.seeedstudio.com/Grove/)

Necessary Components:
Raspberry Pi 3 or 4
GrovePi+
Grove Temperature and Humidity Sensor
Grove Light Sensor
Grove Moisture Sensor

Instructions to Compile/Execute:
1. Setup a Raspberry Pi (steps 7 and 8 from EE 250 Lab 1: 
   https://docs.google.com/document/d/1Sl4HjEeK10h2NfUZMje7Aj0OvjpCaQ-ZqdPh4LEOkqc/edit)
2. Setup the GrovePi+ (step 2 from EE 250 Lab 2: 
   https://docs.google.com/document/d/1jxpLMv38NZ46V_gVaBvw_djnNSG7DVwQRD4_U_jR7bY/edit)
3. Create an AWS EC2 instance (step 4D from EE 250 Lab 3: 
   https://docs.google.com/document/d/1Noz8Pqig23o3zv6Xw697l2f5L-lZbjinNxRPcnj6dn8/edit).
   Make sure to allow inbound traffic for port 3000 (Grafana) and 8086 (InfluxDB).
4. SSH into the AWS EC2 instance and setup InfluxDB with HTTP and Grafana (steps
   3.1, 4.1-4.4, and 5 from EE 250 Lab 9: 
   https://docs.google.com/document/d/1oSitf82AZqWe7a0lVMXsFCsULKMTmgmPX2X7QaP95MY/edit)
5. Now logout from the EC2 and SSH into the Raspberry Pi. Clone the repository:
        "git clone git@github.com:jwills15/PlantMonitor.git" (or forked version)
6. Cd into the repository ("cd PlantMonitor")
7. Install the sensors at the GrovePi+ ports specified in "main_plant_monitor.py".
8. Change the InfluxDB settings on "main_plant_monitor.py" lines 58-62 according to
   the AWS EC2 values.
9. Modifiy the plant settings on "main_plant_monitor.py" lines 67-74 according to
   your plant.
10. Install the external influxdb library using the following commands (reference: 
    https://influxdb-python.readthedocs.io/en/latest/include-readme.html#id2):
        pip install influxdb
        pip install --upgrade influxdb
        sudo apt-get install python-influxdb
11. Install the crontab with the following command so that the program will always run on reboot:
        crontab run.crontab
12. Restart the pi with "sudo reboot" and the program should begin running.
13. Open Grafana on a web browser to view data (example: http://54.193.218.65:3000). 