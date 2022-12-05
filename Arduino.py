from PyQt5 import QtWidgets, uic
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice

app = QtWidgets.QApplication([])
ui = uic.loadUi("design.ui")

serial = QSerialPort()
serial.setBaudRate(9600)
ports = QSerialPortInfo().availablePorts()
portList = []

data = []
magniteState = 0


def openSerial():
	global magniteState
	serial.setPortName(ui.comL.currentText())
	serial.open(QIODevice.ReadWrite)
	serial.write('0'.encode())
	magniteState = '0'
	colorBut()


def closeSerial():
	serial.close()
	magniteState = ','
	colorBut()

def updateSerial():
	global portList, ports
	for port in ports:
		portList.append(port.portName())
	ui.comL.addItems(portList)

def sRead():
	global data, magniteState
	rx = str(serial.readLine(), 'utf-8').strip()
	data = rx.split(',')

	if data[0] == '1':
		magniteState = data[1]

	colorBut()
	print(magniteState)


def turnMagnit():
	global magniteState
	serial.write('1'.encode())
	

def colorBut():
	global magniteState
	if not(serial.isOpen()) or magniteState == ',':
		ui.buttonStart.setStyleSheet("background-color: rgb(255,215,0)")
	elif magniteState == '1':
		ui.buttonStart.setStyleSheet("background-color: rgb(127,255,0)")
	elif magniteState:
		ui.buttonStart.setStyleSheet("background-color: rgb(211,211,211)")
	

updateSerial()
#ui.comL.activated.connect(updateSerial)
ui.sOpen.clicked.connect(openSerial)
ui.sClose.clicked.connect(closeSerial)
serial.readyRead.connect(sRead)

ui.buttonStart.clicked.connect(turnMagnit)

ui.show()
app.exec()