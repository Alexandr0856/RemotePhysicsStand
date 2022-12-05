import cv2
import numpy as np

from design import *
from datetime import datetime

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QIODevice, QTimer
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo


class Arduino(Ui_MainWindow):
    def __init__(self):
        self.serial = QSerialPort()
        self.serial.setBaudRate(9600)

        self.ports = QSerialPortInfo().availablePorts()
        self.portList = []

        self.data = [0, 0, 0]  # 1-connect; 2-work; 3-magnit
        self.magnitState = 0

        self.serial.readyRead.connect(self.serial_read)

    def serial_read(self):
        rx = str(self.serial.readLine(), 'utf-8').strip()
        self.data = rx.split(',')
        print(self.data)

        if self.data[0] == '1':
            self.magnitState = self.data[2]

    def serial_print(self, value):
        self.serial.write(f'1,{value};'.encode())


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    print("VideoThread - create")

    def __init__(self):
        super().__init__()
        self.run_flag = True
        self.record_flag = False
        self.record_time = 30

        # capture from web cam
        self.cap = cv2.VideoCapture(0)
        self.path_to_video = "video.mp4"
        self.path_to_img = "IMG/image"
        self.type_of_img = ".png"
        self.fps = 20
        self.my_res = [640, 480]  # width and height - 480p
        self.video_type_cv2 = cv2.VideoWriter_fourcc(*'XVID')
        self.out = None

        print("VideoThread - init")

    def d_time(func):
        """'delta time' - print execution time of the function """

        def wrapper(*args):
            start = datetime.now()
            func(args[0])
            print(f'Execution time of the function: {datetime.now() - start}')

        return wrapper

    def run(self):
        self.cap.set(3, self.my_res[0])  # set frame width
        self.cap.set(4, self.my_res[1])  # set frame hight

        while self.run_flag:
            ret, cv_img = self.cap.read()
            if self.record_flag:
                self.out.write(cv_img)
                self.arr_img.append(cv_img)
            if ret:
                self.change_pixmap_signal.emit(cv_img)

        # shut down capture system    
        self.cap.release()
        if self.out:
            self.out.release()

    def start_record(self):
        self.arr_img = []
        self.out = cv2.VideoWriter(self.path_to_video, self.video_type_cv2, self.fps, self.my_res)
        self.record_flag = True
        print("Start Record")

    def stop_video(self):
        """Sets run flag to False and waits for thread to finish"""
        self.run_flag = False
        self.wait()

    @d_time
    def stop_record(self):
        self.record_flag = False
        self.out.release()
        print("Stop Record")
        for index, img in enumerate(self.arr_img):
            cv2.imwrite(f"{self.path_to_img}{index}{self.type_of_img}", img)


class ExampleApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

        self.arduino = Arduino()
        self.update_serial()
        self.arduino.serial.readyRead.connect(self.start_record)
        self.arduino.serial.readyRead.connect(self.color_but)

        self.color_but()

        self.sOpen.clicked.connect(self.open_serial)
        self.sClose.clicked.connect(self.close_serial)
        self.slider.valueChanged.connect(self.value_change)
        self.buttonStart.clicked.connect(self.print_serial)

        self.old_input = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.stop_record)

    def start_record(self):
        if self.arduino.data == ['1', '0', '0'] and self.old_input == ['1', '0', '1']:
            self.thread.start_record()
            self.timer.start(self.thread.record_time * 1000)
            self.old_input = ['1', '0', '0']
        
        self.old_input = self.arduino.data

    def stop_record(self):
        self.thread.stop_record()
        self.timer.stop()
        self.color_but()

    def closeEvent(self, event):
        self.thread.stop_video()
        event.accept()

    def value_change(self):
        self.label_slide.setText(str(self.slider.value()) + "%")

    def open_serial(self):
        self.arduino.serial.setPortName(self.comL.currentText())
        self.arduino.serial.open(QIODevice.ReadWrite)
        self.arduino.serial.write('0'.encode())
        self.arduino.magnitState = '0'
        self.color_but()

    def close_serial(self):
        self.arduino.serial.close()
        self.arduino.magnitState = ','
        self.color_but()

    def update_serial(self):
        print(1002)
        for port in self.arduino.ports:
            self.arduino.portList.append(port.portName())
        self.comL.addItems(self.arduino.portList)

    def print_serial(self):
        self.arduino.serial_print(self.slider.value())
        print("Button 'Start' was clecked")

    def color_but(self):
        if not (self.arduino.serial.isOpen()) or self.arduino.magnitState == ',':
            self.buttonStart.setStyleSheet("background-color: rgb(211,211,211)")
        elif self.arduino.data[1] == '1' or self.arduino.data[2] == '1' or self.thread.record_flag:
            self.buttonStart.setStyleSheet("background-color: rgb(255,215,0)")
        elif self.arduino.serial.isOpen():
            self.buttonStart.setStyleSheet("background-color: rgb(127,255,0)")

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the label_image with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.label_image.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # b и запускаем приложение
