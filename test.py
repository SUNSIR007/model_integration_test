import psutil


temperature = psutil.sensors_temperatures()
print(temperature['thermal_fan_est'][0].current)
