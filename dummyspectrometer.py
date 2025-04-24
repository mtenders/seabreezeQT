import numpy as np

def _gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

class DummySpectrometer:
    '''Dummy spectrometer object, which outputs a random spectrum and mirrors
    the methods of the Spectrometer object from seabreeze.spectrometers.'''
    def hello(self):
        print("Hello")
    def integration_time_micros(self, int_time):
        pass
    def wavelengths(self):
        wavelengths = np.genfromtxt("./dummy_wavelengths.txt")
        return wavelengths
    def intensities(self):
        intensities = np.random.rand(2068) \
            * 5e4 * _gaussian(np.linspace(0, 2067, 2068), 1000, 50) \
            + np.random.rand(2068) * 1e4
        return intensities
    def spectrum(self):
        return np.array([self.wavelengths(), self.intensities()])
