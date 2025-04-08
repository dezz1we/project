import numpy as np
import random



class Data_General:
    def __init__(self):
        self.array_sensors = []  # Список датчиков
        self.array_signals = {}  # Словарь сигналов


    def create_sensor(self, sensor_name, sensor_id):
        new_sensor = Sensor_class(sensor_name, sensor_id)
        self.array_sensors.append(new_sensor)
        # print('Датчик создан')


    def create_signal(self, sensor_id, signal_dt, signal_scale, signal_units):
        new_signal = Signal_class(signal_dt, signal_scale, signal_units)
        self.array_signals[sensor_id] = new_signal  # Привязываем сигнал к датчику
        print(f"Сигнал для датчика {sensor_id} создан")



class Sensor_class:
    def __init__(self, sensor_name, sensor_id):
        self.sensor_name = sensor_name
        self.sensor_id = sensor_id

    def __str__(self):
        return f"{self.sensor_name}_{self.sensor_id}"



class Signal_class:
    def __init__(self, signal_dt, signal_scale, signal_units):

        self.signal_dt = signal_dt
        self.signal_scale = signal_scale
        self.signal_units = signal_units

        """ZEROS"""
        self.t =  [0] # TimeLine
        self.time = 0 # Time
        self.y = [self.signal_scale * self.signal_units * np.cos(2 * np.pi * 5 * 0)] #Zero_Y


    def create_point(self):
        self.time += self.signal_dt
        self.y.append(self.signal_scale * self.signal_units * random.randint(0, 200))
        # self.y.append(self.signal_scale * self.signal_units * np.cos(2 * np.pi * 5 * self.time))
        self.t.append(self.time)


    def __str__(self):
        return f"{self.signal_dt}_{self.signal_scale}_{self.signal_units}"