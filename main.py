"""
ToDo list

сделать shift button скролом
добавить кнопку анпина графиков в отдельном окне
добавить возможность мультиплота
"""

import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

import os
import scipy.io
import pandas as pd

from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QMainWindow, QApplication, QTableWidgetItem, QHeaderView, QHBoxLayout, QVBoxLayout,
                             QGridLayout, QCheckBox, QWidget, QFrame, QPushButton, QFileDialog)
from signalclass import * #class import


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('app2.ui', self)  # Загружаем UI-файл


        """DEFAULTS"""
        #Manager Init
        self.general = Data_General()

        self.def_dt = 0.01
        self.def_scale = 1
        self.def_units = 1

        #Table Defaults
        self.name_column = 0
        self.id_column = 1
        self.subid_column = 2
        self.subid2_column = 3
        self.record_column = 4
        self.visualization_column = 5
        self.scale_column = 6
        self.length_column = 7
        self.discretization_column = 8
        self.priority_column = 11
        self.units_column = 10
        self.value_column = 9

        #Timers
        self.emulator_time = 10
        self.plot_time = 100
        self.emulator_timer = QTimer(self)
        self.emulator_timer.timeout.connect(self.emulator)
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plot)


        """GUI SETTINGS"""
        # Button Binding
        self.Initialize.clicked.connect(self.sensor_init)
        self.ClearData.clicked.connect(self.clear_data)
        self.GetTest.clicked.connect(self.get_table_data)
        self.Start.clicked.connect(self.start_plot)
        self.Stop.clicked.connect(self.stop_plot)
        self.Continue.clicked.connect(self.continue_plot)
        self.Export.triggered.connect(self.save_file)

        # MainTable Settings
        self.resize(1280, 720)
        self.MainTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.MainTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.MainTable.verticalHeader().setStretchLastSection(False)
        self.MainTable.verticalHeader().setMinimumSectionSize(25)


    """METHODS"""
    def start_plot(self):
        """Запускает генерацию новых точек раз в 1 мс"""
        self.get_table_data()
        self.signal_record = {}
        for obj in self.general.array_sensors:
            self.general.create_signal(obj.sensor_id, obj.signal_dt, obj.signal_scale, obj.signal_units)
        print("Сигналы загружены!")

        #Start QTimer Update
        self.emulator_timer.start(self.emulator_time)  # обновление в мс
        self.plot_generation()


    def emulator(self):
        """Добавляет новую точку в каждый выбранный сигнал раз в 1 мс"""
        for row, obj in enumerate(self.general.array_sensors):
            sensor_id = obj.sensor_id
            if sensor_id in self.general.array_signals:
                signal = self.general.array_signals[sensor_id]
                signal.create_point()

                value_item = QTableWidgetItem(str(signal.y[-1]))
                value_item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.MainTable.setItem(row, self.value_column, value_item)

                widget_item = self.MainTable.cellWidget(row, self.record_column)
                if widget_item:
                    checkbox = widget_item.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        if sensor_id not in self.signal_record:
                            self.signal_record[sensor_id] = []
                        self.signal_record[sensor_id].append(signal.y[-1])


    def plot_generation(self):
        self.plot_data = []

        if hasattr(self, 'main_frame_layout'):
            while self.main_frame_layout.count():
                item = self.main_frame_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        else:
            self.main_frame_layout = self.main_frame.layout()

        selected_sensors = []
        for row, obj in enumerate(self.general.array_sensors):
            widget_item = self.MainTable.cellWidget(row, self.visualization_column)
            if widget_item:
                checkbox = widget_item.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_sensors.append((row, obj.sensor_id))

        # Проверяем, что для выбранных сигналов не выполнена настройка
        for row, sensor_id in selected_sensors:
            signal = self.general.array_signals.get(sensor_id)  # Получаем сигнал
            if signal is not None:  # Убедимся, что сигнал существует
                # Проверим, что настройки визуализации еще не применены (можно добавить флаг, если нужно)
                if not hasattr(signal, 'visualized') or not signal.visualized:
                    self.plots_canvas_settings(signal, sensor_id, row)
                    signal.visualized = True  # Отметим, что визуализация выполнена

        # Start QTimer Update
        self.plot_timer.start(self.plot_time)  # обновление в мс


    def save_file(self):
        if not hasattr(self, "signal_record") or self.signal_record is None or len(self.signal_record) == 0:
            print("Нет данных для сохранения!")
            return

        # Диалог выбора файла
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить как...",
            "",  # начальная директория
            "MAT-файл (*.mat);;CSV-файл (*.csv)"  # фильтры форматов
        )

        if not file_path:
            print("Сохранение отменено пользователем.")
            return

        # Определяем расширение файла
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        try:
            if ext == ".mat":
                scipy.io.savemat(file_path, {"signal_record": self.signal_record})
            elif ext == ".csv":
                df = pd.DataFrame(self.signal_record)
                df.to_csv(file_path, index=False)
            else:
                print(f"Ошибка: неизвестное расширение файла: {ext}")
                return
            print(f"Данные успешно сохранены в {file_path}")

        except Exception as e:
            print(f"Ошибка при сохранении: {e}")


    def update_plot(self):
        for line, ax, canvas, signal in self.plot_data:
            if len(signal.t) == 0:
                continue

            i = len(signal.t)  # Берём общее количество точек в сигнале
            window_size = int(1 / signal.signal_dt)  # Количество точек в 1 секунде
            start_index = max(0, i - window_size)  # Первая точка окна

            # Обновляем данные линии
            line.set_xdata(signal.t[start_index:i])  # Только последние N точек
            line.set_ydata(signal.y[start_index:i])

            # Корректно обновляем границы оси Y
            y_min = min(signal.y[start_index:i])
            y_max = max(signal.y[start_index:i])
            ax.set_ylim(y_min, y_max)

            # Корректно обновляем границы оси X (окно последних точек)
            if i > window_size:
                ax.set_xlim(signal.t[start_index], signal.t[i-1])  # От первой до последней точки окна

            canvas.flush_events()
            canvas.draw_idle()


    def plots_canvas_settings(self, signal, sensor_id, row):
        #out frame
        out_frame = QFrame(self.main_frame)
        out_frame_layout = QVBoxLayout(out_frame)

        #button frame
        button_frame = QFrame(out_frame)
        button_frame_layout = QHBoxLayout(button_frame)
        button_frame.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)

        # PINOUT BUTTON ADD
        pinout_button = QPushButton("⇱", button_frame)
        pinout_button.setFixedSize(25, 25)
        button_frame_layout.addWidget(pinout_button)

        # SCALE BUTTON ADD
        scale_button = QPushButton("📏", button_frame)
        scale_button.setFixedSize(25, 25)
        button_frame_layout.addWidget(scale_button)
        scale_button.clicked.connect(lambda: self.scale_up(sensor_id))

        out_frame_layout.addWidget(button_frame)

        #canvas frame
        canvas_frame = QFrame(out_frame)
        canvas_frame_layout = QVBoxLayout(canvas_frame)

        # Создание графика (канвас)
        figure, ax = plt.subplots(constrained_layout=True)
        canvas = FigureCanvas(figure)
        canvas.setObjectName(f"canvas_{sensor_id}")
        canvas_frame_layout.addWidget(canvas)

        # Настройки осей
        ax.set_xlim(0, 1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_xlabel("Time (t)")
        ax.set_ylabel("Amplitude (y)")
        ax.grid(True)
        # Добавление линии сигнала
        line, = ax.plot([], [])

        out_frame_layout.addWidget(canvas_frame)
        # Храним данные для обновления
        self.plot_data.append((line, ax, canvas, signal))

        # Добавляем фрейм в layout для вкладки
        row_pos = row // 3  # Примерное распределение по строкам
        col_pos = row % 3  # Примерное распределение по столбцам
        self.main_frame_layout.addWidget(out_frame, row_pos, col_pos)  # Добавляем кнопки
        self.main_frame.setLayout(self.main_frame_layout)


    def scale_up(self, sensor_id):
        """Увеличивает масштаб сигнала в 2 раза и обновляет график"""
        if sensor_id in self.general.array_signals:
            signal = self.general.array_signals[sensor_id]
            signal.signal_scale *= 2  # Увеличиваем масштаб в 2 раза
            # signal.create_point()  # Пересчитываем точки сигнала
            # self.update_plot()
            print(f"Масштаб сигнала {sensor_id} увеличен: {signal.signal_scale}")


    def sensor_init(self):
        self.row_number_test = 10
        for row in range(self.row_number_test):
            self.general.create_sensor(f"{chr(65 + row)}", row)

        #TableInit(Sensor)
        self.MainTable.setRowCount(self.row_number_test)
        for row, sensor in enumerate(self.general.array_sensors):
            name_item = QTableWidgetItem(sensor.sensor_name)
            name_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.MainTable.setItem(row, self.name_column, name_item)

            id_item = QTableWidgetItem(str(sensor.sensor_id))
            id_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.MainTable.setItem(row, self.id_column, id_item)
            self.table_widget_filling(row)

        print('Датчики инициализированы')
        self.ClearData.setEnabled(True)


    def get_table_data(self):
        """Обновляет данные сенсоров в `array_sensors`"""
        self.row_number = self.MainTable.rowCount()
        for row in range(self.row_number):
            try:
                sensor_name = self.MainTable.item(row, self.name_column).text() if self.MainTable.item(row, self.name_column) and self.MainTable.item(row, self.name_column).text() else None
                sensor_id = int(self.MainTable.item(row, self.id_column).text()) if self.MainTable.item(row, self.id_column) and self.MainTable.item(row, self.id_column).text() else None
                sensor_subid = int(self.MainTable.item(row, self.subid_column).text()) if self.MainTable.item(row, self.subid_column) and self.MainTable.item(row, self.subid_column).text() else None
                sensor_subid2 = int(self.MainTable.item(row, self.subid2_column).text()) if self.MainTable.item(row, self.subid2_column) and self.MainTable.item(row, self.subid2_column).text() else None
                signal_scale = float(self.MainTable.item(row, self.scale_column).text()) if self.MainTable.item(row, self.scale_column) and self.MainTable.item(row, self.scale_column).text() else None
                signal_length = float(self.MainTable.item(row, self.length_column).text()) if self.MainTable.item(row, self.length_column) and self.MainTable.item(row, self.length_column).text() else None
                signal_dt = float(self.MainTable.item(row, self.discretization_column).text()) if self.MainTable.item(row, self.discretization_column) and self.MainTable.item(row, self.discretization_column).text() else None
                signal_units = float(self.MainTable.item(row, self.units_column).text()) if self.MainTable.item(row, self.units_column) and self.MainTable.item(row, self.units_column).text() else None

                # Обновляем данные в `array_sensors`
                if row < len(self.general.array_sensors):
                    self.general.array_sensors[row].sensor_name = sensor_name
                    self.general.array_sensors[row].sensor_id = sensor_id
                    self.general.array_sensors[row].sensor_subid = sensor_subid
                    self.general.array_sensors[row].sensor_subid2 = sensor_subid2
                    self.general.array_sensors[row].signal_scale = signal_scale
                    self.general.array_sensors[row].signal_length = signal_length
                    self.general.array_sensors[row].signal_dt = signal_dt
                    self.general.array_sensors[row].signal_units = signal_units

            except ValueError as e:
                print(f"Ошибка при обработке данных на строке {row}: {e}")

        print("Данные из таблицы обновлены!")


    def stop_plot(self):
        """Останавливаем поток"""
        # Проверка, что plot_timer существует и активен
        if hasattr(self, "plot_timer") and self.plot_timer.isActive():
            self.plot_timer.stop()
            print("Графики остановлены")
        # Проверка, что emulator_timer существует и активен
        if hasattr(self, "emulator_timer") and self.emulator_timer.isActive():
            self.emulator_timer.stop()
            print("Эмуляция остановлена")


    def continue_plot(self):
        if hasattr(self, "plot_timer") and self.plot_timer.isActive():
            return
        if hasattr(self, "emulator_timer") and self.emulator_timer.isActive():
            return
        self.plot_timer.start(self.plot_time)
        self.emulator_timer.start(self.emulator_time)
        print("Продолжение")


    def clear_data(self):
        self.MainTable.clearContents()
        self.MainTable.setRowCount(0)
        self.general.array_sensors.clear()
        self.general.array_signals.clear()
        print("Данные очищены")


    def choose_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.DirectoryLine.setText(folder)


    def table_widget_filling(self, row):
        #ADD CHECKBOX INTO VISUALIZATION
        container_visual = QWidget()
        table_checkbox_visual = QCheckBox()

        layout_visual = QHBoxLayout(container_visual)
        layout_visual.addWidget(table_checkbox_visual)
        layout_visual.setAlignment(QtCore.Qt.AlignCenter)
        layout_visual.setContentsMargins(0, 0, 0, 0)

        container_visual.setLayout(layout_visual)

        self.MainTable.setCellWidget(row, self.visualization_column, container_visual)

        #ADD CHECKBOX INTO RECORD
        container_record = QWidget()
        layout_record = QHBoxLayout(container_record)
        table_checkbox_record = QCheckBox()
        layout_record.addWidget(table_checkbox_record)

        layout_record.setAlignment(QtCore.Qt.AlignCenter)
        layout_record.setContentsMargins(0, 0, 0, 0)
        container_record.setLayout(layout_record)

        self.MainTable.setCellWidget(row, self.record_column, container_record)

        # ROW FILLING WITH DEF VALUES
        scale_item = QTableWidgetItem(str(self.def_scale))
        scale_item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.MainTable.setItem(row, self.scale_column, scale_item)

        dt_item = QTableWidgetItem(str(self.def_dt))
        dt_item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.MainTable.setItem(row, self.discretization_column, dt_item)

        units_item = QTableWidgetItem(str(self.def_units))
        units_item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.MainTable.setItem(row, self.units_column, units_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
