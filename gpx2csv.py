import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from numpy import size
import pandas as pd
import os
import argparse
import xml.etree.ElementTree as ET
from matplotlib import pyplot as plt
import datetime

class PathInputDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set window size and position (x, y, width, height)
        self.setGeometry(300, 300, 400, 250)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)  # Add padding
        layout.setSpacing(10)  # Space between widgets

        # Title with styling
        title = QLabel('GPX File Converter', self)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Rest of the widgets with some styling
        style = """
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QPushButton {
                padding: 8px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        
        self.input_label = QLabel('Input Path:', self)
        self.input_path = QLineEdit(self)
        self.input_button = QPushButton('Browse', self)
        self.input_button.clicked.connect(self.browse_input)

        self.output_label = QLabel('Output Name:', self)
        self.output_name = QLineEdit(self)

        self.submit_button = QPushButton('Submit', self)
        self.submit_button.clicked.connect(self.submit_paths)

        # Add widgets to layout
        layout.addWidget(self.input_label)
        layout.addWidget(self.input_path)
        layout.addWidget(self.input_button)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_name)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)
        self.setWindowTitle('GPX File Converter')
        self.setStyleSheet(style)

    def browse_input(self):
        input_path = QFileDialog.getOpenFileName(self, 'Select Input File')[0]
        if input_path:
            self.input_path.setText(input_path)

    def submit_paths(self):
        self.result = (self.input_path.text(), self.output_name.text())
        self.close()

class Activity:
    def __init__(self):
        self.input_path: str = ""
        self.output_name: str = ""
        self.output_path: str = ""
        self.output_path_plot: str = ""
        self.dataframe: pd.DataFrame = pd.DataFrame()

    def input_and_output(self, input_path, output_name):
        self.input_path = input_path
        self.output_name = output_name
        self._compute_output_path()
    
    def _compute_output_path(self):
        # Get the directory of the input path
        input_dir = os.path.dirname(self.input_path)
        self.output_path = os.path.join(input_dir, self.output_name) + '.csv'
        self.output_path_plot = os.path.join(input_dir, self.output_name) + '.png'

    def gpx2df(self):
        root = ET.parse(self.input_path)
        # Parse the XML
        namespace = {'default': 'http://www.topografix.com/GPX/1/1'}  # Namespace used in the XML

        # Extract time and speed
        times_and_speeds = []
        for trkpt in root.findall('.//default:trkpt', namespace):
            time = trkpt.find('default:time', namespace).text
            speed = trkpt.find('default:extensions/default:speed', namespace).text
            times_and_speeds.append((time, float(speed)))
        
        self.dataframe = pd.DataFrame(times_and_speeds, columns=['time', 'speed'])
        self._speed2pace()
        self._speed2kmh()


    def _speed2pace(self):
        # converting meter per second to min per km
        self.dataframe['pace'] = 1 / (self.dataframe['speed'] * 60 / 1000)
    
    def _speed2kmh(self):
        # converting meter per second to km per hour
        self.dataframe['speed'] = self.dataframe['speed'] * 3.6

    def groupby_min(self):
        # Group by minute
        self.dataframe['time'] = pd.to_datetime(self.dataframe['time'])
        self.dataframe = self.dataframe.set_index('time').resample('1min').mean().dropna()
        self.dataframe.index = pd.to_datetime(self.dataframe.index).strftime("%Y-%m-%d %H:%M")

    def plot(self):
        date = pd.to_datetime(self.dataframe.index[0]).strftime("%Y-%m-%d")
        plt.figure(figsize=(12,4))

        self.dataframe["speed"].plot(title=f"{date} activity", ylabel="Speed in km/h", xlabel="Time")
        plt.tight_layout()
        plt.savefig(self.output_path_plot, dpi=300)
        plt.show()

    def df2csv(self):
        self.dataframe.to_csv(self.output_path)


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-i', '--input', type=str, help='Input Path')
    arg_parser.add_argument('-o', '--output', type=str, help='Output Name')
    args = arg_parser.parse_args()

    activity = Activity()

    if args.input and args.output:
        # CLI input provided
        activity.input_and_output(args.input, args.output)
    else:
        # No CLI input provided, open dialog
        app = QApplication(sys.argv)
        dialog = PathInputDialog()
        dialog.show()
        app.exec_()
        
        if hasattr(dialog, 'result'):
            activity.input_and_output(*dialog.result)
        else:
            print("No input path provided, exiting")
            sys.exit()
    
    assert os.path.isfile(activity.input_path), "Invalid Input Path"
    assert os.path.splitext(activity.input_path)[1] == '.gpx', "Invalid Input File Type"

    print(f'Stored Input Path: {activity.input_path}')
    print(f'Stored Output Path: {activity.output_path}')

    activity.gpx2df()
    activity.groupby_min()
    activity.plot()
    activity.df2csv()

    assert os.path.isfile(activity.output_path), "Conversion Failed"
    print(f"Conversion Successful: {activity.output_path}")
