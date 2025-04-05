import numpy as np  # Импортируем библиотеку для работы с массивами и математическими функциями


class Data_General:
    """Класс для управления множеством датчиков и сигналов"""

    def __init__(self):
        """Создаёт пустые списки для датчиков и сигналов"""
        self.array_sensors = []  # Список датчиков
        self.array_signals = {}  # Словарь сигналов {id: Signal_one}

    def create_sensor(self, name, id):
        """
        Добавляет новый датчик в систему

        :param name: Название датчика
        :param id: Уникальный идентификатор датчика
        """
        new_sensor = Sensor_one(name, id)
        self.array_sensors.append(new_sensor)
        print(f"✅ Датчик добавлен: {new_sensor}")

    def create_signal(self, id, dt, scale, units):
        """
        Создаёт сигнал для конкретного датчика (по `id`)

        :param id: ID датчика, к которому привязан сигнал
        :param dt: Временной шаг (разрешение)
        :param scale: Масштаб сигнала
        :param units: Единицы измерения
        """
        if id not in [sensor.id for sensor in self.array_sensors]:
            print(f"⚠ Ошибка: Датчик с ID {id} не найден!")
            return

        new_signal = Signal_one(dt, scale, units)
        self.array_signals[id] = new_signal  # Привязываем сигнал к датчику
        print(f"✅ Сигнал для датчика {id} создан: {new_signal}")


class Sensor_one:
    """Класс, представляющий один датчик"""

    def __init__(self, name, id):
        self.name = name  # Название датчика
        self.id = id  # Уникальный ID датчика

    def __str__(self):
        """Возвращает строковое представление датчика"""
        return f"{self.name}_{self.id}"


class Signal_one:
    """Класс, представляющий сигнал, привязанный к датчику"""

    def __init__(self, dt, scale, units):
        """
        Инициализирует параметры сигнала

        :param dt: Временной шаг
        :param scale: Масштаб сигнала
        :param units: Единицы измерения
        """
        self.dt = dt
        self.scale = scale
        self.units = units
        self.t = [0]  # Временные точки
        self.y = [self.scale * self.units * np.cos(2 * np.pi * 5 * 0)]
        self.time = 0


    # def generate_test_signal(self):

    def add_dot(self):
        self.time += self.dt
        new_amplitude = self.scale * self.units * np.cos(2 * np.pi * 5 * self.time)  # Новая амплитуда
        self.t.append(self.time)
        self.y.append(new_amplitude)

    def __str__(self):
        """Возвращает строковое представление сигнала"""
        return f"Signal(dt={self.dt}, scale={self.scale}, units={self.units})"
