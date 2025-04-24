import sys

from datetime import datetime
from textwrap import dedent, fill

import os
import itertools

import numpy as np
from seabreeze.spectrometers import Spectrometer, list_devices

from PyQt5 import QtWidgets, QtGui, QtCore, uic
import pyqtgraph as pg

from dummyspectrometer import DummySpectrometer

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Load UI
        pg.setConfigOption('leftButtonPan', False)
        uic.loadUi('MainWindow.ui', self)
        self.graphWidget.setBackground(None)
        self.graphWidget.showGrid(x=True, y=True)

        # List all available devices
        devices = list_devices()
        
        # Check if spectrometer is connected
        if devices == []:
            self.spec_name = "Dummy Spectrometer"
            self.spec = DummySpectrometer()
            self.spectrometerLabel.setText(self.spec_name)
        else:
            # Get name of first spectrometer in list
            spec_name = str(devices[0])[1:-1]
            spec_name, _ = spec_name.split(":")
            self.spec_name = spec_name.replace(' ', '\n')
            # Set label to name of the spectrometer
            self.spectrometerLabel.setText(self.spec_name[16:])
            # Load first spectrometer in list
            self.spec = Spectrometer(devices[0])

        # Integration time double spin box
        self.int_time = self.integrationTimeSpinBox.value()  # ms
        # Averaging
        self.avg = self.averagingSpinBox.value()
        # Autorange button
        self.autoRangeButton.clicked.connect(self.toggle_autoRange)
        # Background button
        self.backgroundButton.clicked.connect(self.update_background)
        # Keep the current spectrum in the background
        self.keepButton.clicked.connect(self.keep_spectrum)
        # Clear screen from opend spectra
        self.clearButton.clicked.connect(self.clear_spectrum)
        # Open spectrum and plot it in the background
        self.openButton.clicked.connect(self.open_spectrum)
        # Save spectrum button
        self.saveButton.clicked.connect(self.save_spectrum)

        # Set integration time
        self.spec.integration_time_micros(self.int_time*1000)
        # Read spectrum
        self.x = self.spec.wavelengths()
        self.y = self.spec.intensities()

        # Plot
        self.x, self.y = self.spec.spectrum()
        # Initialize background to zero
        self.bg = np.zeros(len(self.x))
        # Number of open background spectra
        self.bg_sp = 0

        # Format plot
        styles = {
            'font-size': '18px',
            # 'color': 'k'
        }
        self.graphWidget.setLabel('left', 'Intensity (counts)', **styles)
        self.graphWidget.setLabel('bottom', 'Wavelength (nm)', **styles)
        pen = pg.mkPen(color=(255, 0, 0))

        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)
        self.vb = self.data_line.getViewBox()

        # Move live spectrum to the foreground. Default z value is 0.
        self.data_line.setZValue(1)

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def toggle_autoRange(self):
        if any(self.vb.autoRangeEnabled()) is True:
            self.vb.disableAutoRange()
        else:
            self.vb.enableAutoRange()

    def update_background(self):
        # Read current spectrum as background
        _, int_bg = self.spec.spectrum()
        self.bg = int_bg

    def keep_spectrum(self):
        bg_x, bg_y = self.spec.spectrum()
        bg_y = bg_y - self.bg
        pen = pg.mkPen(color=pg.intColor(self.bg_sp, maxValue=200))
        tmp_line = self.graphWidget.plot(bg_x, bg_y, pen=pen)
        # Move plot to the background
        tmp_line.setZValue(0)
        self.bg_sp += 1

    def clear_spectrum(self):
        # Clear everything
        self.graphWidget.clear()
        self.bg_sp = 0
        # Replot the live spectrum
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)
        # Move live spectrum to the foreground
        self.data_line.setZValue(1)

    def open_spectrum(self):
        filename = QtGui.QFileDialog.getOpenFileName(
            self, 'Open Spectrum', '', "Text Files (*.txt);;All Files (*)"
        )
        if filename[0] != '':
            bg_spectrum = np.genfromtxt(filename[0])
            pen = pg.mkPen(color=pg.intColor(self.bg_sp, maxValue=200))
            tmp_line = self.graphWidget.plot(
                bg_spectrum[:, 0], bg_spectrum[:, 1], pen=pen
            )
            # Move plot to the background
            tmp_line.setZValue(0)
            self.bg_sp += 1

    def save_spectrum(self):
        # Save spectrum when save button is pressed
        x_tmp = self.x
        y_tmp = self.y
        # Open save dialog and get entered filename
        filename = QtGui.QFileDialog.getSaveFileName(
            self, 'Save Spectrum', '', "Text Files (*.txt);;All Files (*)"
        )
        # Only proceed if filename is entered
        if filename[0] != '':
            # Automatically append .txt
            if filename[1] == 'Text Files (*.txt)' \
               and filename[0][-4:] != '.txt':
                fname = filename[0] + '.txt'
            else:
                fname = filename[0]
            # Generate header
            # Header data
            spc = ' '
            newl = '\n'+12*spc+'#'+19*spc
            cstring_raw = self.commentPlainTextEdit.toPlainText()
            cstring_wrapped = fill(cstring_raw,width=29)
            cstring = cstring_wrapped.replace('\n', newl)
            content = {
                'fn': os.path.basename(fname),
                'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'int_time': self.int_time,
                'avg': self.avg,
                'spectrometer': self.spec_name[16:],  # kill "SeabreezeDevice"
                'rows': len(x_tmp),
                'comment': cstring
            }
            # Header string
            header = dedent("""\
            # ------------------- HEADER ------------------- #
            # Filename:         {fn}
            # Spectrometer:     {spectrometer}
            # Date:             {date}
            # Integration time: {int_time} ms
            # Averaging:        {avg}
            # Number of rows:   {rows}
            # Comment:          {comment}
            # ----------------- END HEADER ----------------- #

            """.format(**content))
            # Save header to file
            with open(fname, "w") as f:
                f.write(header)
            # Append spectrum to file
            with open(fname, "ab") as f:
                np.savetxt(f, np.transpose([x_tmp, y_tmp]))

    def update_plot_data(self):
        # Check for integration time
        new_int_time = self.integrationTimeSpinBox.value()
        if self.int_time != new_int_time:
            # Update integration time
            self.int_time = new_int_time
            self.spec.integration_time_micros(self.int_time*1000)

        # Update text on autoRangeButton
        if any(self.vb.autoRangeEnabled()) is True:
            self.autoRangeButton.setText('Auto range: on')
        else:
            self.autoRangeButton.setText('Auto range: off')

        # Averaging
        self.avg = self.averagingSpinBox.value()
        # List comprehension to collect self.avg spectra and average them.
        new_inten = np.mean([self.spec.intensities()
                             for _ in itertools.repeat(None, self.avg)],
                            axis=0)

        # Background substraction
        self.y = new_inten - self.bg
        # Update the data.
        self.data_line.setData(self.x, self.y)


def main():
    app = QtWidgets.QApplication(sys.argv)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
