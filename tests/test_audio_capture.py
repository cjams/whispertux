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
    def test_normalize_device_reference_handles_default_string_ids_and_stable_refs(self):
        self.assertIsNone(AudioCapture.normalize_device_reference(None))
        self.assertIsNone(AudioCapture.normalize_device_reference(''))
        self.assertIsNone(AudioCapture.normalize_device_reference(' default '))
        self.assertEqual(AudioCapture.normalize_device_reference('7'), 7)
        self.assertEqual(AudioCapture.normalize_device_reference(3), 3)
        self.assertEqual(
            AudioCapture.normalize_device_reference({
                'name': 'PipeWire ALSA [android-mic]',
                'host_api': 'PipeWire',
                'id': '7',
            }),
            {
                'name': 'PipeWire ALSA [android-mic]',
                'host_api': 'PipeWire',
                'id': 7,
            }
        )
        self.assertEqual(
            AudioCapture.normalize_device_reference('PipeWire ALSA [android-mic]'),
            'PipeWire ALSA [android-mic]'
        )

    def test_resolve_input_device_reference_uses_stable_name_and_host_api(self):
        with patch.object(AudioCapture, 'get_available_input_devices', return_value=[
            {
                'id': 2,
                'name': 'PipeWire ALSA [android-mic]',
                'host_api': 'PipeWire',
                'reference': {'name': 'PipeWire ALSA [android-mic]', 'host_api': 'PipeWire'},
                'display_name': 'PipeWire ALSA [android-mic] (PipeWire)',
            },
            {
                'id': 8,
                'name': 'PipeWire ALSA [android-mic]',
                'host_api': 'PulseAudio',
                'reference': {'name': 'PipeWire ALSA [android-mic]', 'host_api': 'PulseAudio'},
                'display_name': 'PipeWire ALSA [android-mic] (PulseAudio)',
            },
        ]):
            resolved = AudioCapture._resolve_input_device_reference({
                'name': 'PipeWire ALSA [android-mic]',
                'host_api': 'PipeWire',
            })

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved['id'], 2)

    @patch.object(AudioCapture, '_initialize_sounddevice', autospec=True, return_value=None)
    def test_set_device_none_switches_back_to_system_default(self, _mock_initialize):
        capture = AudioCapture(device_reference=5)

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
    def test_set_device_accepts_stable_device_reference(self, _mock_samplerate, _mock_initialize):
        capture = AudioCapture()

        with patch('src.audio_capture.sd') as mock_sd:
            mock_sd.default.device = [None, None]
            mock_sd.query_devices.return_value = {
                'name': 'PipeWire ALSA [android-mic]',
                'hostapi': 0,
                'max_input_channels': 1,
                'default_samplerate': 48000,
            }
            with patch.object(AudioCapture, 'get_available_input_devices', return_value=[
                {
                    'id': 7,
                    'name': 'PipeWire ALSA [android-mic]',
                    'host_api': 'PipeWire',
                    'reference': {'name': 'PipeWire ALSA [android-mic]', 'host_api': 'PipeWire'},
                    'display_name': 'PipeWire ALSA [android-mic] (PipeWire)',
                }
            ]):
                result = capture.set_device({
                    'name': 'PipeWire ALSA [android-mic]',
                    'host_api': 'PipeWire',
                })

        self.assertTrue(result)
        self.assertEqual(capture.preferred_device, {
            'name': 'PipeWire ALSA [android-mic]',
            'host_api': 'PipeWire',
        })
        self.assertEqual(capture.preferred_device_id, 7)
        self.assertEqual(capture.device_id, 7)
        self.assertEqual(capture.device_info['name'], 'PipeWire ALSA [android-mic]')
        self.assertEqual(mock_sd.default.device[0], 7)


if __name__ == '__main__':
    unittest.main()
