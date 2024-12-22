import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
import gpxpy
import folium
import numpy as np
import os
from tqdm import tqdm
import argparse
import subprocess
import platform

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
        try:
            home_dir = os.path.expanduser('~/Documents')
            input_path = QFileDialog.getExistingDirectory(
                self,
                'Select Directory',
                home_dir,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            
            if input_path:
                self.input_path.setText(input_path)
        except Exception as e:
            print(f"Error selecting directory: {e}")

    def submit_paths(self):
        self.result = (self.input_path.text(), self.output_name.text())
        self.close()

class Activities:
    def __init__(self):
        self.input_path = ""
        self.output_name = ""
        self.output_path = ""
        self.paths: list[str] = []
        self.longitudes: list = []
        self.latitudes: list = []

    def input_and_output(self, input_path, output_name):
        self.input_path = input_path
        self.output_name = output_name
        self._compute_output_path()
    
    def _compute_output_path(self):
        # Get the directory of the input path
        input_dir = os.path.dirname(self.input_path)
        self.output_path = os.path.join(input_dir, self.output_name) + '.html'

    def get_all_gpx_paths(self):
        # os walk through the input path to get all gpx files
        for root, _, files in os.walk(self.input_path):
            for file in files:
                if file.endswith('.gpx'):
                    self.paths.append(os.path.join(root, file))
        
        print(f"{len(self.paths)} GPX Files Found")

    def convert_gpx_to_html(self):
        for file in tqdm(self.paths, desc="Converting GPX to HTML", total=len(self.paths)):
            # parse the GPX file
            parsed_gpx = gpxpy.parse(open(file, "r"))
            
            # ensure parsed_gpx has data
            if not parsed_gpx.tracks or not parsed_gpx.tracks[0].segments or not parsed_gpx.tracks[0].segments[0].points:
                print(f"No data available in {file}")
                continue

            # extract latitude and longitude points
            self.latitudes.append([point.latitude for point in parsed_gpx.tracks[0].segments[0].points])
            self.longitudes.append([point.longitude for point in parsed_gpx.tracks[0].segments[0].points])
        
        # calculate the center of the map
        center_lat = np.mean([lat for lat_list in self.latitudes for lat in lat_list])
        center_lon = np.mean([lon for lon_list in self.longitudes for lon in lon_list])

        # create a map centered around the track
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        # add the track to the map
        for lat, lon in zip(self.latitudes, self.longitudes):
            folium.PolyLine(list(zip(lat, lon)), color="blue", weight=2.5, opacity=1).add_to(m)

        # display the map
        m.save(self.output_path)

def open_file(filepath):
    try:
        system = platform.system().lower()
        
        if system == 'darwin':  # macOS
            subprocess.run(['open', filepath])
        elif system == 'linux':
            subprocess.run(['xdg-open', filepath])
        elif system == 'windows':
            subprocess.run(['start', filepath], shell=True)
        else:
            print(f"Unsupported operating system (to launch output html file): {system}")
            
    except Exception as e:
        print(f"Error opening file: {e}")


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-i', '--input', type=str, help='Input Path')
    arg_parser.add_argument('-o', '--output', type=str, help='Output Name')
    args = arg_parser.parse_args()

    activites = Activities()

    if args.input and args.output:
        # CLI input provided
        activites.input_and_output(args.input, args.output)
    else:
        # No CLI input provided, open dialog
        app = QApplication(sys.argv)
        dialog = PathInputDialog()
        dialog.show()
        app.exec_()
        
        if hasattr(dialog, 'result'):
            activites.input_and_output(*dialog.result)
        else:
            print("No input path provided, exiting")
            sys.exit()
    
    assert os.path.isdir(activites.input_path), "Invalid Input Path"

    print(f'Stored Input Path: {activites.input_path}')
    print(f'Stored Output Path: {activites.output_path}')

    activites.get_all_gpx_paths()

    assert activites.paths, "No GPX Files Found"

    activites.convert_gpx_to_html()

    assert os.path.isfile(activites.output_path), "Conversion Failed"
    print(f"Conversion Successful: {activites.output_path}")
    open_file(activites.output_path)