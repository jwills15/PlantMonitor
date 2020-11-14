""" EE 250L Final Project: Plant Monitor

List team members here.
Joshua Williams

Insert Github repository link here.
https://github.com/jwills15/PlantMonitor
"""

import sys
import time
import datetime
import threading

lock = threading.Lock()

# Appending the folder of all the GrovePi libraries to 'import grovepi`
sys.path.append('GrovePi-EE250/Software/Python/')
import grovepi

### Documentation for Temperature and Humidity Sensor 
### https://wiki.seeedstudio.com/Grove-TemperatureAndHumidity_Sensor/

### Settings for Temperature and Humidity Sensor
# Connect the Grove Temperature and Humidity Sensor to digital port 4 (D4)
DHT_PORT = 4

### Documentation for Light Sensor
### https://wiki.seeedstudio.com/Grove-Light_Sensor/

### Settings for Light Sensor
# Connect the Grove Light Sensor to analog port 0 (A0)
LIGHT_PORT = 0
grovepi.pinMode(LIGHT_PORT, "INPUT")
# maximum value of sensor reading (different for each light sensor, found through testing)
LIGHT_SENSOR_MAX = 800
# takes 10 values for the average
LIGHT_AVERAGE_AMOUNT = 5

### Documentation for Moisture Sensor
### https://wiki.seeedstudio.com/Grove-Moisture_Sensor/

### Settings for Moisture Sensor
# Connect the Grove Moisture Sensor to analog port 1 (A1)
MOISTURE_PORT = 1
grovepi.pinMode(MOISTURE_PORT, "INPUT")
# maximum value of sensor reading (different for each moisture sensor, found through testing)
MOISTURE_SENSOR_MAX = 700
# takes 10 values for the average
MOISTURE_AVERAGE_AMOUNT = 5

### Setup for InfluxDB
#INFLUXDB_HOST = TODO
#INFLUXDB_PORT = TODO

### Settings for Plant Environment
# temperature max and minimum (in Fahrenheit)
TEMPERATURE_MIN = 50.0
TEMPERATURE_MAX = 85.0
# humidity max and minimum (in percent)
HUMIDITY_MIN = 20
HUMIDITY_MAX = 60
# moisture maximum and minimum (in percent)
MOISTURE_MIN = 1
MOISTURE_MAX = 90

### Helper Function Definitions

# returns the average of a list
def get_list_average(passed_list):
    return (sum(passed_list) / len(passed_list))

# Real Time Filtering in Time Domain: Low Pass Filter
def low_pass_filter(passed_list):
    list_len = len(passed_list)
    # iterates through each element in the list and looks at the two adjacent items for a pure moving average filter
    for i in range(list_len):
        pure_average_filter = []
        pure_average_filter.append(passed_list[i])
        if (i + 1) == list_len and list_len > 2:
            pure_average_filter.append(passed_list[i-1])
            pure_average_filter.append(passed_list[i-2])
        elif i == 0 and list_len > 2:
            pure_average_filter.append(passed_list[i+1])
            pure_average_filter.append(passed_list[i+2])
        elif list_len > 2:
            pure_average_filter.append(passed_list[i-1])
            pure_average_filter.append(passed_list[i+1])
        # gets the average from the current and adjacent and modifies value in list
        pure_average_filter = get_list_average(pure_average_filter)
        passed_list[i] = pure_average_filter
    # returns the filtered list
    return passed_list

def get_dht_in_f():
    temperature, humidity = grovepi.dht(DHT_PORT, 0)
    if temperature is None or humidity is None:
        # bad readings of sensor will return None
        return (temperature, humidity)
    # converts the temperature from Celcius to Fahrenheit
    temperature = (temperature * 9 / 5) + 32
    # rounds the values
    temperature = round(temperature, 1)
    humidity = round(humidity, 1)
    # return the temperature in Fahrenheit and humidity percentage
    return (temperature, humidity)

def get_light_average_in_percent():
    light_list = []
    for i in range(LIGHT_AVERAGE_AMOUNT):
        current = grovepi.analogRead(LIGHT_PORT)
        if current < LIGHT_SENSOR_MAX:
            # reading was good, add to list of values
            light_list.append(current)
        # waits 1 second between sensor readings
        time.sleep(1)
    # puts the values through a low pass filter
    light_list = low_pass_filter(light_list)
    # takes the average of the low pass filter values
    light = get_list_average(light_list)
    # converts the average to a percent
    light = 100 * (light / LIGHT_SENSOR_MAX)
    light = round(light, 1)
    return light

def get_moisture_average_in_percent():
    moisture_list = []
    for i in range(MOISTURE_AVERAGE_AMOUNT):
        current = grovepi.analogRead(MOISTURE_PORT)
        if current < MOISTURE_SENSOR_MAX:
            # reading was good, add to list of values
            moisture_list.append(current)
        # waits 1 second between sensor readings
        time.sleep(1)
    # puts the values through a low pass filter
    moisture_list = low_pass_filter(moisture_list)
    # takes the average of the low pass filter values
    moisture = get_list_average(moisture_list)
    # converts the average to a percent
    moisture = 100 * (moisture / MOISTURE_SENSOR_MAX)
    moisture = round(moisture, 1)
    return moisture

def get_influxdb_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def get_errorlog_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    while True:
        try:
            ### only reads and sends data every 30 seconds (subtracts time for sensor readings)
            time.sleep(30 - LIGHT_AVERAGE_AMOUNT - MOISTURE_AVERAGE_AMOUNT)

            ### reads sensors
            # read the values from the temperature and humidity sensor
            with lock:
                temperature, humidity = get_dht_in_f()
            # read the values from the light sensor (average of LIGHT_AVERAGE_AMOUNT values)
            with lock:
                light = get_light_average_in_percent()
            # read the values from the moisture sensor (average of MOISTURE_AVERAGE_AMOUNT values)
            with lock:
                moisture = get_moisture_average_in_percent()

            ### ensure that all sensor readings were good
            if temperature is None or humidity is None:
                # dht sensor did not provide good values, write to log
                error_log = open("error_log.txt", "a")
                current_time = get_errorlog_time()
                message = current_time + ": Error while reading temperature and humidity sensor.\n"
                error_log.write(message)
                error_log.close()
                # starts the loop over again
                continue

            ### Real Time Data Processing: status of plant detection in time domain
            

            ### sends data to InfluxDB on AWS EC2 server
            print(temperature)
            print(humidity)
            print(light)
            print(moisture)
            print()

        except KeyboardInterrupt:
            # stops the script with "ctrl + c"
            break
        except ZeroDivisionError:
            # caused when light and/or moisture sensors do not provide good values
            error_log = open("error_log.txt", "a")
            current_time = get_errorlog_time()
            message = current_time + ": Error while reading light and/or moisture sensor.\n"
            error_log.write(message)
            error_log.close()
        except:
            # generic catch for exceptions not handled so that loop does not crash
            error_log = open("error_log.txt", "a")
            current_time = get_errorlog_time()
            message = current_time + ": Error caught in loop.\n"
            error_log.write(message)
            error_log.close()