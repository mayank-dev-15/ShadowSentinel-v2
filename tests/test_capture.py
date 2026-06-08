import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.capture import PacketCapture, FlowAnalyzer


def test_capture_initialization():
    cap = PacketCapture(interface='any')
    assert cap is not None
    assert cap.interface == 'any'


def test_flow_analyzer():
    analyzer = FlowAnalyzer()
    assert analyzer is not None
    assert len(analyzer.flows) == 0


def test_capture_context():
    cap = PacketCapture(interface='any')
    with cap as c:
        assert c.running is False


if __name__ == '__main__':
    test_capture_initialization()
    test_flow_analyzer()
    test_capture_context()
    print("All capture tests passed.")
