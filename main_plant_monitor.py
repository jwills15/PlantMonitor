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

### Documentation for InfluxDB
### https://influxdb-python.readthedocs.io/en/latest/include-readme.html#id2
# Import for access to InfluxDB
from influxdb import InfluxDBClient

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
INFLUXDB_HOST = '54.193.218.65' # IP address of the AWS EC2 instance
INFLUXDB_PORT = 8086
INFLUXDB_USER = 'plant'
INFLUXDB_PASSWORD = 'finalproject'
INFLUXDB_DATABASE = 'plant_data'
influxdb_client = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASSWORD, INFLUXDB_DATABASE)

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

# gets the dht sensor readings and converts temp to Fahrenheit
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

# gets the light sensor readings and converts to percent
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

# gets the moisture sensor readings and converts to percent
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

# gets the current time in InfluxDB format
def get_influxdb_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# gets the current time in normal format
def get_errorlog_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# sends data with the specified value to the specified table in the database
def send_data_to_influx(table, value):
    data_json = [
        {
            "measurement": table,
            "tags": {
                "host": "server01",
                "region": "us-west"
            },
            "time": get_influxdb_time(),
            "fields": {
                "value": value
            }
        }
    ]
    influxdb_client.write_points(data_json)

### Main Function

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

            ### Real Time Data Processing: detection of the environment status of the plant in time domain
            # Equation of ellipse: ([x-i]^2)/(a^2) + ([y-j]^2)/(b^2) = 1
            # x = humidity
            # y = temperature
            # (i, j) is the point at center of the ellipse (midpoint of plant settings values)
            # a and b are the semi-axes (half of the difference between plant settings values)
            i = (HUMIDITY_MAX + HUMIDITY_MIN) / 2
            j = (TEMPERATURE_MAX + TEMPERATURE_MIN) / 2
            a = (HUMIDITY_MAX - HUMIDITY_MIN) / 2 
            b = (TEMPERATURE_MAX - TEMPERATURE_MIN) / 2
            # plot the current values on the ellipse
            x = (humidity - i) * (humidity - i) / (a * a)
            y = (temperature - j) * (temperature - j) / (b * b)
            plot = x + y
            # applies values to the ellipse to determine environment status (0 = bad, 1 = good)
            environment_status = 0
            if plot <= 1:
                environment_status = 1

            ### Real Time Data Processing: detection of water levels in the time domain
            # 0 = needs water, 1 = good, 2 = overwatered
            water_status = 1
            if moisture < MOISTURE_MIN:
                water_status = 0
            elif moisture > MOISTURE_MAX:
                water_status = 2

            ### sends data to InfluxDB on AWS EC2 server
            send_data_to_influx("temperature", temperature)
            send_data_to_influx("humidity", humidity)
            send_data_to_influx("light", light)
            send_data_to_influx("moisture", moisture)
            send_data_to_influx("environment_status", environment_status)
            send_data_to_influx("water_status", water_status)

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