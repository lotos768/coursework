import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog,
    QLineEdit, QFormLayout, QGroupBox, QMessageBox, QHBoxLayout, QComboBox
)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

from simulation import Simulation
from visualization import SpeedGraphWindow


class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ввод данных")
        self.setGeometry(300, 300, 400, 350)

        self.angle_input = QLineEdit("30")
        self.length_input = QLineEdit("10")
        self.horizontal_length_input = QLineEdit("10")
        self.v0_input = QLineEdit("0")
        self.friction_incline_input = QLineEdit("0.1")
        self.friction_horizontal_input = QLineEdit("0.1")

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.angle_input.setToolTip("Угол наклона плоскости в градусах (0-90)")
        self.length_input.setToolTip("Длина наклонной плоскости в метрах")
        self.horizontal_length_input.setToolTip("Длина горизонтальной плоскости в метрах")
        self.v0_input.setToolTip("Начальная скорость тела в м/с")
        self.friction_incline_input.setToolTip("Коэффициент трения на наклонной плоскости (0-1)")
        self.friction_horizontal_input.setToolTip("Коэффициент трения на горизонтальной плоскости (0-1)")

        form_layout.addRow("Угол наклона (градусы):", self.angle_input)
        form_layout.addRow("Длина наклонной плоскости (м):", self.length_input)
        form_layout.addRow("Длина гориз. плоскости (м):", self.horizontal_length_input)
        form_layout.addRow("Начальная скорость (м/с):", self.v0_input)
        form_layout.addRow("Коэф. трения (наклон):", self.friction_incline_input)
        form_layout.addRow("Коэф. трения (горизонт):", self.friction_horizontal_input)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        form_layout.addRow(button_layout)

        self.setLayout(form_layout)

    def getValues(self):
        try:
            angle = float(self.angle_input.text())
            length = float(self.length_input.text())
            horizontal_length = float(self.horizontal_length_input.text())
            v0 = float(self.v0_input.text())
            friction_incline = float(self.friction_incline_input.text())
            friction_horizontal = float(self.friction_horizontal_input.text())

            if not 0 <= angle <= 90:
                raise ValueError("Угол должен быть от 0 до 90 градусов")
            if not 0 <= friction_incline <= 1:
                raise ValueError("Коэф. трения (наклон) должен быть между 0 и 1")
            if not 0 <= friction_horizontal <= 1:
                raise ValueError("Коэф. трения (горизонт) должен быть между 0 и 1")
            if horizontal_length <= 0:
                raise ValueError("Длина гориз. плоскости должна быть > 0")
            if v0 < 0:
                raise ValueError("Начальная скорость не может быть отрицательной")
            if v0 > 299792458:
                raise ValueError("Начальная скорость не может быть больше скорости света")

            return angle, length, horizontal_length, v0, friction_incline, friction_horizontal
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return None, None, None, None, None, None


class SimulationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.c = 299792458
        self.angle = 30
        self.length = 10
        self.horizontal_length = 10
        self.v0 = 0
        self.friction_incline = 0.1
        self.friction_horizontal = 0.1
        self.animation_speed = 20
        self.object_color = "red"
        self.simulation = Simulation(self.angle, self.length, self.horizontal_length, self.v0,
                                     self.friction_incline, self.friction_horizontal)
        self.speed_window = SpeedGraphWindow(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Моделирование движения тела")
        self.setGeometry(100, 100, 900, 750)
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.label = QLabel("Анимация движения тела по наклонной плоскости", self)
        self.label.setAlignment(Qt.AlignCenter)
        font = self.label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)
        self.layout.addWidget(self.label)
        self.canvas = FigureCanvas(plt.figure(figsize=(5, 3)))
        self.layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.add_subplot(111)
        button_layout = QHBoxLayout()

        self.input_button = QPushButton("Ввести данные", self)
        self.input_button.clicked.connect(self.showInputDialog)
        button_layout.addWidget(self.input_button)

        self.start_button = QPushButton("Начать анимацию", self)
        self.start_button.clicked.connect(self.startAnimation)
        button_layout.addWidget(self.start_button)

        self.save_button = QPushButton("Сохранить график скорости", self)
        self.save_button.clicked.connect(self.speed_window.save_graph)
        button_layout.addWidget(self.save_button)

        self.layout.addLayout(button_layout)

        color_layout = QHBoxLayout()
        color_label = QLabel("Цвет объекта:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Red", "Blue", "Green", "Yellow", "Purple"])
        self.color_combo.setCurrentIndex(0)
        self.color_combo.currentIndexChanged.connect(self.updateObjectColor)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_combo)
        self.layout.addLayout(color_layout)

        self.input_group = QGroupBox("Входные данные")
        input_layout = QFormLayout()
        self.input_group.setLayout(input_layout)

        self.angle_label = QLabel()
        self.length_label = QLabel()
        self.horizontal_length_label = QLabel()
        self.v0_label = QLabel()
        self.friction_incline_label = QLabel()
        self.friction_horizontal_label = QLabel()

        input_layout.addRow("Угол:", self.angle_label)
        input_layout.addRow("Длина наклонной:", self.length_label)
        input_layout.addRow("Длина гориз.:", self.horizontal_length_label)
        input_layout.addRow("Нач. скорость:", self.v0_label)
        input_layout.addRow("Коэф. трения (наклон):", self.friction_incline_label)
        input_layout.addRow("Коэф. трения (горизонт):", self.friction_horizontal_label)
        self.layout.addWidget(self.input_group)

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateAnimation)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 12px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 12px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
            QGroupBox {
                border: 1px solid gray;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        self.input_group.hide()
        self.updateLabels()
        self.drawGraph()

    def updateLabels(self):
        self.angle_label.setText(f"{np.degrees(self.simulation.angle):.2f}°")
        self.length_label.setText(f"{self.simulation.L:.2f} м")
        self.horizontal_length_label.setText(f"{self.simulation.horizontal_length:.2f} м")
        self.v0_label.setText(f"{self.simulation.v0:.2f} м/с")
        self.friction_incline_label.setText(f"{self.simulation.friction_incline:.2f}")
        self.friction_horizontal_label.setText(f"{self.simulation.friction_horizontal:.2f}")

    def showInputDialog(self):
        dialog = InputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            angle, length, horizontal_length, v0, friction_incline, friction_horizontal = dialog.getValues()
            if angle is not None:
                self.simulation.update_parameters(angle, length, horizontal_length, v0, friction_incline, friction_horizontal)
                self.input_group.show()
                self.updateLabels()
                self.drawGraph()
                self.speed_window.clearGraph()


    def startAnimation(self):
        self.simulation.reset()
        self.timer.start(self.animation_speed)
        self.speed_window.show()
        self.speed_window.clearGraph()
        self.updateLabels()
        self.drawGraph()


    def updateAnimation(self):
        if not self.simulation.is_finished():
            time, velocity, x_body, y_body = self.simulation.step(self.simulation.dt)
            self.speed_window.updateGraph(self.simulation.time_points, self.simulation.velocity_points)
            self.drawGraph(x_body, y_body)
        else:
            self.timer.stop()
            self.drawGraph(self.simulation.x_body, self.simulation.y_body)
            self.speed_window.updateGraph(self.simulation.time_points, self.simulation.velocity_points)


    def drawGraph(self, x_body=None, y_body=None):
        self.ax.clear()
        x_plane, y_plane = self.simulation.get_plane_coordinates()
        x_horizontal, y_horizontal = self.simulation.get_horizontal_coordinates()
        self.ax.plot(x_plane, y_plane, 'b', label="Наклонная плоскость", linewidth=2)
        self.ax.plot(x_horizontal, y_horizontal, 'g', label="Горизонтальная поверхность", linewidth=2)

        if x_body is not None and y_body is not None:
            self.ax.scatter(x_body, y_body, color=self.object_color, label="Тело", zorder=5, s=100)
        else:
             self.ax.scatter(self.simulation.x_body, self.simulation.y_body, color=self.object_color, label="Тело", zorder=5, s=100)
        self.ax.set_xlabel("x (м)", fontsize=12)
        self.ax.set_ylabel("y (м)", fontsize=12)
        self.ax.legend(fontsize=10)
        self.ax.grid(True, linestyle='--')
        self.ax.set_aspect('equal')
        self.canvas.draw()

    def updateObjectColor(self):
        self.object_color = self.color_combo.currentText().lower()
        self.drawGraph()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulationApp()
    window.show()
    sys.exit(app.exec_())