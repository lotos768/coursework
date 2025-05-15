import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFileDialog, QMessageBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class SpeedGraphWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("График скорости")
        self.setGeometry(200, 200, 600, 400)
        self.figure = plt.figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax = self.figure.add_subplot(111)

    def updateGraph(self, time, velocity):
        self.ax.clear()
        self.ax.plot(time, velocity, 'r', label="Скорость v(t)")
        self.ax.set_xlabel("Время (с)", fontsize=12)
        self.ax.set_ylabel("Скорость (м/с)", fontsize=12)
        self.ax.set_title("График зависимости скорости от времени", fontsize=14)
        self.ax.legend(fontsize=10)
        self.ax.grid(True, linestyle='--')
        self.canvas.draw()

    def clearGraph(self):
        self.ax.clear()
        self.ax.set_xlabel("Время (с)", fontsize=12)
        self.ax.set_ylabel("Скорость (м/с)", fontsize=12)
        self.ax.set_title("График зависимости скорости от времени", fontsize=14)
        self.ax.grid(True, linestyle='--')
        self.canvas.draw()

    def save_graph(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить график скорости",
            "speed_graph",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
            options=options,
        )
        if file_path:
            try:
                if not file_path.lower().endswith((".png", ".jpg", ".jpeg")):
                    file_path += ".png"
                self.figure.savefig(file_path, dpi=300)
                QMessageBox.information(self, "Сохранение графика", f"График успешно сохранен в\n{file_path}")
            except Exception as e:
                 QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось сохранить график:\n{e}")