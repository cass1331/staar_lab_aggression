import sys
import types
import importlib
import importlib.util
import os

# Create a fake pulse_pal module with a PulsePalObject factory we can inspect
pulse_pal = types.SimpleNamespace()
_created = []

class FakePulsePal:
    def __init__(self, port):
        self.port = port
        self.params = []
        self.triggers = []
        _created.append(self)

    def programOutputChannelParam(self, name, channel, value):
        self.params.append((name, channel, value))

    def triggerOutputChannels(self, **kwargs):
        self.triggers.append(kwargs)

class PulsePalError(Exception):
    pass

# factory that records created instances
def PulsePalFactory(port):
    return FakePulsePal(port)

pulse_pal.PulsePalObject = PulsePalFactory
pulse_pal.PulsePalError = PulsePalError
sys.modules['pulse_pal'] = pulse_pal

# Create a fake PySpin module with two fake cameras
class FakeDeviceName:
    def __init__(self, name):
        self._name = name
    def GetValue(self):
        return self._name

class FakeCamera:
    def __init__(self, name):
        self.DeviceModelName = FakeDeviceName(name)
    def Init(self):
        pass
    def DeInit(self):
        pass

class FakeCamList(list):
    def GetSize(self):
        return len(self)
    def Clear(self):
        pass

class FakeSystem:
    @staticmethod
    def GetInstance():
        return FakeSystem()
    def GetCameras(self):
        return FakeCamList([FakeCamera('Blackfly S'), FakeCamera('Oryx')])

pyspin = types.SimpleNamespace(System=FakeSystem)
sys.modules['PySpin'] = pyspin

# Now import the module under test after faking dependencies
# Load the target module by file path so the test works regardless of CWD
module_path = os.path.join(os.path.dirname(__file__), 'run_red_blue_pulse_timed.py')
module_path = os.path.abspath(module_path)
spec = importlib.util.spec_from_file_location('run_red_blue_pulse_timed', module_path)
mod = importlib.util.module_from_spec(spec)
sys.modules['run_red_blue_pulse_timed'] = mod
spec.loader.exec_module(mod)

# Patch out the sleep to avoid waiting
mod.time.sleep = lambda s: None

# Initialize per-camera time_log (as main() would)
mod.time_log = [[] for _ in range(2)]

# Dummy simple variable object that mimics tkinter.StringVar.get()
class DummyVar:
    def __init__(self, value):
        self._value = value
    def get(self):
        return self._value


def test_run_trial_blue_triggers_and_logs():
    # run a blue trial on camera 0
    # force a stimulation to be delivered (make random.choice True)
    mod.random.random = lambda: 0.9
    mod.run_trial(0, DummyVar('BLUE'))

    # ensure a FakePulsePal instance was created
    assert len(_created) >= 1
    inst = _created[-1]
    # ensure trigger was called
    assert len(inst.triggers) >= 1

    # ensure the per-camera log has one entry
    assert len(mod.time_log[0]) == 1
    start, end = mod.time_log[0][0]
    assert isinstance(start, float)
    assert isinstance(end, float)


def test_run_trial_red_triggers_and_logs():
    # run a red trial on camera 1
    mod.random.random = lambda: 0.9
    mod.run_trial(1, DummyVar('RED'))

    inst = _created[-1]
    assert len(inst.triggers) >= 1
    assert len(mod.time_log[1]) == 1

