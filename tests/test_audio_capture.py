import sys
import types
import unittest
from unittest.mock import patch

if 'sounddevice' not in sys.modules:
    mock_sounddevice = types.ModuleType('sounddevice')
    mock_sounddevice.default = types.SimpleNamespace(
        device=[None, None],
        samplerate=None,
        channels=None,
        dtype=None,
    )
    mock_sounddevice.query_devices = lambda *args, **kwargs: []
    mock_sounddevice.query_hostapis = lambda *args, **kwargs: {'name': 'mock'}
    mock_sounddevice.check_input_settings = lambda *args, **kwargs: None
    mock_sounddevice.InputStream = object
    mock_sounddevice.PortAudioError = Exception
    sys.modules['sounddevice'] = mock_sounddevice

from src.audio_capture import AudioCapture


class AudioCaptureDeviceSelectionTests(unittest.TestCase):
    def test_normalize_device_reference_handles_default_and_string_ids(self):
        self.assertIsNone(AudioCapture.normalize_device_reference(None))
        self.assertIsNone(AudioCapture.normalize_device_reference(''))
        self.assertIsNone(AudioCapture.normalize_device_reference(' default '))
        self.assertEqual(AudioCapture.normalize_device_reference('7'), 7)
        self.assertEqual(AudioCapture.normalize_device_reference(3), 3)
        self.assertEqual(
            AudioCapture.normalize_device_reference('PipeWire ALSA [android-mic]'),
            'PipeWire ALSA [android-mic]'
        )

    @patch.object(AudioCapture, '_initialize_sounddevice', autospec=True, return_value=None)
    def test_set_device_none_switches_back_to_system_default(self, _mock_initialize):
        capture = AudioCapture(device_id=5)

        with patch('src.audio_capture.sd') as mock_sd:
            mock_sd.default.device = [5, None]
            mock_sd.default.samplerate = 48000

            result = capture.set_device('default')

        self.assertTrue(result)
        self.assertIsNone(capture.preferred_device_id)
        self.assertIsNone(capture.device_info)
        self.assertIsNone(capture.device_id)
        self.assertEqual(capture.sample_rate, capture.target_sample_rate)
        self.assertIsNone(mock_sd.default.device[0])
        self.assertEqual(mock_sd.default.samplerate, capture.target_sample_rate)

    @patch.object(AudioCapture, '_initialize_sounddevice', autospec=True, return_value=None)
    @patch.object(AudioCapture, '_ensure_supported_samplerate', autospec=True, return_value=None)
    def test_set_device_accepts_stringified_device_ids(self, _mock_samplerate, _mock_initialize):
        capture = AudioCapture()

        with patch('src.audio_capture.sd') as mock_sd:
            mock_sd.default.device = [None, None]
            mock_sd.query_devices.return_value = {
                'name': 'PipeWire ALSA [android-mic]',
                'max_input_channels': 1,
                'default_samplerate': 48000,
            }

            result = capture.set_device('7')

        self.assertTrue(result)
        self.assertEqual(capture.preferred_device_id, 7)
        self.assertEqual(capture.device_id, 7)
        self.assertEqual(capture.device_info['name'], 'PipeWire ALSA [android-mic]')
        self.assertEqual(mock_sd.default.device[0], 7)


if __name__ == '__main__':
    unittest.main()
