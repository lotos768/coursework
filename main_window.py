import sys
import numpy as np
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog,
    QLineEdit, QFormLayout, QGroupBox, QMessageBox, QHBoxLayout, QComboBox,
    QDialogButtonBox, QTextBrowser
)

from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from simulation import Simulation
from rollup_simulation import RollupSimulation
from visualization import SpeedGraphWindow


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("О программе")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout(self)

        title_label = QLabel("Моделирование Движения Тела")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)

        info_text = QTextBrowser()
        info_text.setReadOnly(True)
        info_text.setOpenExternalLinks(True)
        info_text.setHtml(
            """<p><b>Версия:</b> 1.0</p><p>
            <p>Эта программа моделирует движение тела по наклонной и горизонтальной плоскостям.</p>
            <p><b>Сценарии:</b></p><ul>
            <li><b>Скат:</b> Тело скатывается с наклонной плоскости.</li>
            <li><b>Вкат:</b> Тело движется к наклонной плоскости и пытается на нее вкатиться.</li>"""
        )

        layout.addWidget(info_text)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)

        layout.addWidget(button_box)

        self.setLayout(layout)


class InputDialog(QDialog):
    def __init__(self, parent=None, current_scenario_type='roll_down'):
        super().__init__(parent)

        self.setWindowTitle("Ввод данных")
        self.setGeometry(300, 300, 450, 400)

        self.current_scenario_type = current_scenario_type

        self.angle_input = QLineEdit("30")
        self.length_input = QLineEdit("10")

        self.horizontal_length_label_widget = QLabel("Длина гориз. плоскости (м):")
        self.horizontal_length_input = QLineEdit("10")

        self.v0_input = QLineEdit("5")
        self.friction_incline_input = QLineEdit("0.1")
        self.friction_horizontal_input = QLineEdit("0.1")

        self.init_dist_label = QLabel("Нач. гориз. расст. справа от наклона (м):")
        self.initial_distance_input = QLineEdit("5")

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.angle_input.setToolTip("Угол наклона плоскости в градусах (0-90)")
        self.length_input.setToolTip("Длина наклонной плоскости в метрах")
        self.horizontal_length_input.setToolTip(
            "Длина гориз. плоскости (м) (для 'Ската' - после наклона)"
        )
        self.v0_input.setToolTip("Начальная скорость тела в м/с (модуль)")
        self.friction_incline_input.setToolTip("Коэффициент трения на наклонной плоскости (0-1)")
        self.friction_horizontal_input.setToolTip("Коэффициент трения на гориз. плоскости (0-1)")
        self.initial_distance_input.setToolTip(
            "Расстояние по горизонтали от основания наклонной плоскости вправо, где стартует тело"
        )

        form_layout.addRow("Угол наклона (градусы):", self.angle_input)
        form_layout.addRow("Длина наклонной плоскости (м):", self.length_input)
        form_layout.addRow(self.horizontal_length_label_widget, self.horizontal_length_input)
        form_layout.addRow("Начальная скорость (м/с):", self.v0_input)
        form_layout.addRow("Коэф. трения (наклон):", self.friction_incline_input)
        form_layout.addRow("Коэф. трения (горизонт):", self.friction_horizontal_input)
        form_layout.addRow(self.init_dist_label, self.initial_distance_input)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        form_layout.addRow(button_layout)

        self.setLayout(form_layout)
        self.toggleInitialDistField()

    def toggleInitialDistField(self):
        is_roll_up = (self.current_scenario_type == 'roll_up')

        self.init_dist_label.setVisible(is_roll_up)
        self.initial_distance_input.setVisible(is_roll_up)

        self.horizontal_length_label_widget.setVisible(not is_roll_up)
        self.horizontal_length_input.setVisible(not is_roll_up)

    def getValues(self):
        try:
            angle = float(self.angle_input.text())
            length = float(self.length_input.text())

            horizontal_length = 0.0
            if self.current_scenario_type == 'roll_down':
                h_len_text = self.horizontal_length_input.text()
                if not h_len_text.strip():
                    raise ValueError("Длина гориз. плоскости не может быть пустой")
                horizontal_length = float(h_len_text)
                if horizontal_length <= 0:
                    raise ValueError("Длина гориз. плоскости должна быть > 0")

            v0 = abs(float(self.v0_input.text()))
            friction_incline = float(self.friction_incline_input.text())
            friction_horizontal = float(self.friction_horizontal_input.text())

            read_initial_distance = 0.0
            if self.current_scenario_type == 'roll_up':
                text_val = self.initial_distance_input.text()
                if not text_val.strip():
                    raise ValueError("Начальное гориз. расстояние не может быть пустым.")
                read_initial_distance = float(text_val)
                if read_initial_distance < 0:
                    raise ValueError("Начальное гориз. расстояние не может быть отрицательным")

            if not (0 <= angle <= 90):
                raise ValueError("Угол должен быть от 0 до 90 градусов")
            if length <= 0:
                raise ValueError("Длина наклонной плоскости должна быть > 0")
            if not (0 <= friction_incline <= 1):
                raise ValueError("Коэф. трения (наклон) должен быть между 0 и 1")
            if not (0 <= friction_horizontal <= 1):
                raise ValueError("Коэф. трения (горизонт) должен быть между 0 и 1")
            if v0 > 299792458:
                raise ValueError("Начальная скорость не может быть больше скорости света")

            if self.current_scenario_type == 'roll_up' and v0 == 0 and read_initial_distance > 0:
                raise ValueError("Для вката с расстояния начальная скорость должна быть > 0.")

            return angle, length, horizontal_length, v0, friction_incline, friction_horizontal, read_initial_distance

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
            return None, None, None, None, None, None, None


class SimulationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.angle = 30.0
        self.length = 10.0
        self.horizontal_length = 10.0
        self.v0 = 5.0
        self.friction_incline = 0.1
        self.friction_horizontal = 0.1
        self.initial_distance_param = 5.0

        self.animation_speed = 20
        self.object_color = "red"
        self.scenario_type = 'roll_down'
        self.simulation = None

        self.speed_window = SpeedGraphWindow(self)

        self.initUI()
        self.changeScenario(self.scenario_combo.currentIndex())

    def initUI(self):
        self.setWindowTitle("Моделирование движения тела")
        self.setGeometry(100, 100, 900, 800)

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)

        self.label = QLabel("Анимация движения тела", self)
        self.label.setAlignment(Qt.AlignCenter)
        font = self.label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)

        self.layout.addWidget(self.label)

        self.canvas = FigureCanvas(plt.figure(figsize=(5, 3)))
        self.layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.add_subplot(111)

        main_control_layout = QHBoxLayout()

        self.input_button = QPushButton("Ввести данные", self)
        self.input_button.clicked.connect(self.showInputDialog)
        main_control_layout.addWidget(self.input_button)

        self.start_button = QPushButton("Начать анимацию", self)
        self.start_button.clicked.connect(self.startAnimation)
        main_control_layout.addWidget(self.start_button)

        self.resume_button = QPushButton("Продолжить", self)
        self.resume_button.clicked.connect(self.resumeAnimation)
        self.resume_button.setEnabled(False)
        main_control_layout.addWidget(self.resume_button)

        self.stop_button = QPushButton("Стоп", self)
        self.stop_button.clicked.connect(self.stopAnimation)
        self.stop_button.setEnabled(False)
        main_control_layout.addWidget(self.stop_button)

        self.save_button = QPushButton("Сохранить график скорости", self)
        self.save_button.clicked.connect(self.speed_window.save_graph)
        main_control_layout.addWidget(self.save_button)

        self.layout.addLayout(main_control_layout)

        options_layout = QHBoxLayout()

        scenario_label = QLabel("Сценарий:")
        options_layout.addWidget(scenario_label)

        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(["Скат с наклонной", "Вкат на наклонную"])
        self.scenario_combo.setCurrentIndex(0)
        options_layout.addWidget(self.scenario_combo)

        options_layout.addSpacing(20)

        color_label = QLabel("Цвет объекта:")
        options_layout.addWidget(color_label)

        self.color_combo = QComboBox()
        self.color_combo.addItems(["Красный", "Синий", "Зеленый", "Желтый", "Фиолетовый"])
        self.color_combo.setCurrentIndex(0)
        options_layout.addWidget(self.color_combo)

        options_layout.addStretch(1)

        self.about_button = QPushButton("О программе", self)
        self.about_button.clicked.connect(self.showAboutDialog)
        options_layout.addWidget(self.about_button)

        self.layout.addLayout(options_layout)

        self.input_group = QGroupBox("Входные данные")
        self.input_layout_form = QFormLayout()
        self.input_group.setLayout(self.input_layout_form)

        self.angle_label = QLabel()
        self.length_label = QLabel()
        self.horizontal_length_display_label_widget = QLabel("Длина гориз.:")
        self.horizontal_length_label = QLabel()

        self.v0_label = QLabel()
        self.friction_incline_label = QLabel()
        self.friction_horizontal_label = QLabel()
        self.init_dist_text = QLabel("Нач. гориз. расст. (справа от наклона):")
        self.init_dist_val = QLabel()

        self.input_layout_form.addRow("Угол:", self.angle_label)
        self.input_layout_form.addRow("Длина наклонной:", self.length_label)
        self.input_layout_form.addRow(self.horizontal_length_display_label_widget, self.horizontal_length_label)
        self.input_layout_form.addRow("Нач. скорость (модуль):", self.v0_label)
        self.input_layout_form.addRow("Коэф. трения (наклон):", self.friction_incline_label)
        self.input_layout_form.addRow("Коэф. трения (горизонт):", self.friction_horizontal_label)
        self.input_layout_form.addRow(self.init_dist_text, self.init_dist_val)

        self.layout.addWidget(self.input_group)

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateAnimation)

        self.color_combo.currentIndexChanged.connect(self.updateObjectColor)
        self.scenario_combo.currentIndexChanged.connect(self.changeScenario)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF3E0;
            }
            QLabel {
                font-size: 12px;
                color: #4E342E;
            }
            QLabel#title_lbl {
                font-size: 17px;
                font-weight: bold;
                color: #D84315;
                padding-bottom: 10px;
                margin-top: 5px;
            }
            QPushButton {
                background-color: #FF7043;
                color: white;
                border: none;
                padding: 9px 18px;
                font-size: 12px;
                font-weight: 500;
                border-radius: 4px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #FF8A65;
            }
            QPushButton:pressed {
                background-color: #F4511E;
            }
            QPushButton:disabled {
                background-color: #FFCCBC;
                color: #BCAAA4;
            }
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #FFCCBC;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 18px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px 0 5px;
                left: 10px;
                color: #D84315;
            }
            QLineEdit {
                background-color: #FFF9C4;
                color: #4E342E;
                border: 1px solid #FFCC80;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #FF7043;
                background-color: #FFFFFF;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #4E342E;
                border: 1px solid #FFCC80;
                border-radius: 4px;
                padding: 6px;
                min-width: 6em;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #FFCC80;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #FFE0B2;
            }
            QComboBox:hover {
                border: 1px solid #FFB74D;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #FFCC80;
                background-color: #FFFDE7;
                color: #4E342E;
                selection-background-color: #FFB74D;
                selection-color: #4E342E;
            }
            QTextBrowser {
                background-color: #FFF9C4;
                color: #4E342E;
                border: 1px solid #FFCCBC;
                border-radius: 4px;
            }
            QDialog {
                 background-color: #FFF3E0;
            }
        """)
        self.input_group.hide()
        self.setInitialDistRowVisible(False)
        self.setHorizontalLengthDisplayVisible(False)

    def showAboutDialog(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    def setHorizontalLengthDisplayVisible(self, visible):
        self.horizontal_length_display_label_widget.setVisible(visible)
        self.horizontal_length_label.setVisible(visible)

    def setInitialDistRowVisible(self, visible):
        self.init_dist_text.setVisible(visible)
        self.init_dist_val.setVisible(visible)

    def updateLabels(self):
        if not self.simulation:
            self.setHorizontalLengthDisplayVisible(False)
            self.setInitialDistRowVisible(False)
            return

        self.angle_label.setText(f"{np.degrees(self.simulation.angle):.2f}°")
        self.length_label.setText(f"{self.simulation.L:.2f} м")

        h_len_attr_name = 'h_len_display' if self.scenario_type == 'roll_up' else 'horizontal_length'
        h_len_attr = getattr(self.simulation, h_len_attr_name, 0.0)
        self.horizontal_length_label.setText(f"{h_len_attr:.2f} м")

        self.setHorizontalLengthDisplayVisible(True)

        v0_val = getattr(self.simulation, 'v0_input',
                         getattr(self.simulation, 'v0', 0.0))
        self.v0_label.setText(f"{abs(v0_val):.2f} м/с")

        self.friction_incline_label.setText(f"{self.simulation.friction_incline:.2f}")
        self.friction_horizontal_label.setText(f"{self.simulation.friction_horizontal:.2f}")

        if self.scenario_type == 'roll_up':
            dist_attr = getattr(self.simulation, 'init_h_dist', 0.0)
            if isinstance(dist_attr, (int, float)):
                self.init_dist_val.setText(f"{dist_attr:.2f} м")
            else:
                self.init_dist_val.setText("Ошибка")
            self.setInitialDistRowVisible(True)
        else:
            self.init_dist_val.setText("")
            self.setInitialDistRowVisible(False)

    def showInputDialog(self):
        dialog = InputDialog(self, current_scenario_type=self.scenario_type)

        dialog.angle_input.setText(str(self.angle))
        dialog.length_input.setText(str(self.length))
        if self.scenario_type == 'roll_down':
            dialog.horizontal_length_input.setText(str(self.horizontal_length))

        dialog.v0_input.setText(str(self.v0))
        dialog.friction_incline_input.setText(str(self.friction_incline))
        dialog.friction_horizontal_input.setText(str(self.friction_horizontal))

        if self.scenario_type == 'roll_up':
            dialog.initial_distance_input.setText(str(self.initial_distance_param))

        dialog_accepted = dialog.exec_()

        if dialog_accepted == QDialog.Accepted:
            values = dialog.getValues()
            if values and values[0] is not None:
                self.angle = values[0]
                self.length = values[1]
                if self.scenario_type == 'roll_down':
                    self.horizontal_length = values[2]

                self.v0 = values[3]
                self.friction_incline = values[4]
                self.friction_horizontal = values[5]
                if self.scenario_type == 'roll_up':
                    self.initial_distance_param = values[6]

                self.input_group.show()
                self.changeScenario(self.scenario_combo.currentIndex())

                self.speed_window.clearGraph()
                self.speed_window.hide()

    def changeScenario(self, index):
        self.timer.stop()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(False)

        selected_text = self.scenario_combo.itemText(index)
        self.scenario_type = 'roll_down' if selected_text == "Скат с наклонной" else 'roll_up'

        if self.scenario_type == 'roll_down':
            self.simulation = Simulation(
                self.angle, self.length, self.horizontal_length, self.v0,
                self.friction_incline, self.friction_horizontal
            )
            self.label.setText("Анимация ската тела с наклонной плоскости")
        elif self.scenario_type == 'roll_up':
            self.simulation = RollupSimulation(
                self.angle, self.length, self.v0,
                self.friction_incline, self.friction_horizontal,
                self.initial_distance_param
            )
            self.label.setText("Анимация вката тела на наклонную плоскость")

        self.updateLabels()

        if self.simulation:
            self.simulation.reset()
            self.drawGraph()

        self.speed_window.clearGraph()
        self.speed_window.hide()

    def drawGraph(self, x_body=None, y_body=None):
        if not self.simulation:
            return

        self.ax.clear()

        x_plane, y_plane, x_horizontal, y_horizontal = None, None, None, None

        if hasattr(self.simulation, 'get_plane_coordinates') and \
                callable(getattr(self.simulation, 'get_plane_coordinates')):
            plane_coords = self.simulation.get_plane_coordinates()
            if len(plane_coords) == 2:
                x_plane, y_plane = plane_coords

        if x_horizontal is None and \
                hasattr(self.simulation, 'get_horizontal_coordinates') and \
                callable(getattr(self.simulation, 'get_horizontal_coordinates')):
            horizontal_coords = self.simulation.get_horizontal_coordinates()
            if len(horizontal_coords) == 2:
                x_horizontal, y_horizontal = horizontal_coords

        if x_plane is not None and x_plane.size > 0:
            self.ax.plot(x_plane, y_plane, 'b', label="Наклонная плоскость", linewidth=2)
        if x_horizontal is not None and x_horizontal.size > 0:
            self.ax.plot(x_horizontal, y_horizontal, 'g', label="Горизонтальная поверхность", linewidth=2)

        current_x = x_body if x_body is not None else self.simulation.x_body
        current_y = y_body if y_body is not None else self.simulation.y_body
        self.ax.scatter(current_x, current_y, color=self.object_color, label="Тело", zorder=5, s=100)

        self.ax.set_xlabel("x (м)", fontsize=12)
        self.ax.set_ylabel("y (м)", fontsize=12)

        if self.ax.has_data():
            self.ax.legend(fontsize=10)

        self.ax.grid(True, linestyle='--')

        all_xcoords = []
        all_ycoords = []
        try:
            if x_plane is not None and x_plane.size > 0:
                all_xcoords.extend([np.nanmin(x_plane), np.nanmax(x_plane)])
            if x_horizontal is not None and x_horizontal.size > 0:
                all_xcoords.extend([np.nanmin(x_horizontal), np.nanmax(x_horizontal)])
            if y_plane is not None and y_plane.size > 0:
                all_ycoords.extend([np.nanmin(y_plane), np.nanmax(y_plane)])
            if y_horizontal is not None and y_horizontal.size > 0:
                all_ycoords.extend([np.nanmin(y_horizontal), np.nanmax(y_horizontal)])

            if hasattr(self.simulation, 'x_body') and np.isfinite(self.simulation.x_body):
                all_xcoords.append(self.simulation.x_body)
            if hasattr(self.simulation, 'y_body') and np.isfinite(self.simulation.y_body):
                all_ycoords.append(self.simulation.y_body)

            if all_xcoords and all_ycoords:
                valid_x = [x for x in all_xcoords if np.isfinite(x)]
                valid_y = [y for y in all_ycoords if np.isfinite(y)]

                if valid_x and valid_y:
                    min_x, max_x = min(valid_x), max(valid_x)
                    min_y, max_y = min(valid_y), max(valid_y)

                    padding_x = max(1.0, (max_x - min_x) * 0.15)
                    padding_y = max(1.0, (max_y - min_y) * 0.15)

                    if np.isfinite(min_x - padding_x) and np.isfinite(max_x + padding_x):
                        self.ax.set_xlim(min_x - padding_x, max_x + padding_x)
                    if np.isfinite(min_y - padding_y) and np.isfinite(max_y + padding_y):
                        self.ax.set_ylim(min_y - padding_y, max_y + padding_y)
        except Exception:
            pass

        self.ax.set_aspect('equal', adjustable='box')
        self.canvas.draw()

    def startAnimation(self):
        self.simulation.reset()
        self.timer.start(self.animation_speed)

        self.speed_window.show()
        self.speed_window.clearGraph()

        if self.input_group.isVisible():
            self.updateLabels()

        self.drawGraph()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)

    def stopAnimation(self):
        if self.timer.isActive():
            self.timer.stop()

            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.resume_button.setEnabled(True)

            if self.simulation:
                self.drawGraph(self.simulation.x_body, self.simulation.y_body)
                self.speed_window.updateGraph(self.simulation.time_points, self.simulation.velocity_points)

    def resumeAnimation(self):
        if not self.timer.isActive() and self.simulation and not self.simulation.is_finished():
            self.timer.start(self.animation_speed)

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.resume_button.setEnabled(False)

    def updateAnimation(self):
        if not self.simulation:
            return

        if self.simulation.is_finished():
            if self.timer.isActive():
                self.timer.stop()

                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.resume_button.setEnabled(False)

                self.drawGraph(self.simulation.x_body, self.simulation.y_body)
                self.speed_window.updateGraph(self.simulation.time_points, self.simulation.velocity_points)
            return

        time, velocity, x_body, y_body = self.simulation.step(self.simulation.dt)

        self.speed_window.updateGraph(self.simulation.time_points, self.simulation.velocity_points)
        self.drawGraph(x_body, y_body)

        if self.simulation.is_finished():
            if self.timer.isActive():
                self.timer.stop()

                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.resume_button.setEnabled(False)

                self.drawGraph(self.simulation.x_body, self.simulation.y_body)
                self.speed_window.updateGraph(self.simulation.time_points, self.simulation.velocity_points)

    def updateObjectColor(self):
        color_map = {
            "Красный": "red",
            "Синий": "blue",
            "Зеленый": "green",
            "Желтый": "yellow",
            "Фиолетовый": "purple"
        }
        self.object_color = color_map.get(self.color_combo.currentText(), "red")
        if self.simulation:
            self.drawGraph()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulationApp()
    window.show()
    sys.exit(app.exec_())