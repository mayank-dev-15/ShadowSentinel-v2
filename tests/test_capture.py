import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.capture import PacketCapture, PacketInfo
from core.features import FeatureExtractor, FlowKey


def test_capture_initialization():
    cap = PacketCapture(interface='lo')
    assert cap.interface == 'lo'
    assert cap.bpf_filter == 'ip'
    assert cap._running is False
    assert len(cap.buffer) == 0


def test_capture_buffer():
    cap = PacketCapture(interface='lo', buffer_size=5)
    info = PacketInfo(
        timestamp=1.0, src_mac="aa:bb:cc:dd:ee:ff", dst_mac="11:22:33:44:55:66",
        src_ip="10.0.0.1", dst_ip="10.0.0.2", src_port=12345, dst_port=80,
        protocol=6, length=64, flags=0x02, payload_len=0, payload_entropy=0.0,
    )
    cap.buffer.append(info)
    assert len(cap.get_buffer()) == 1
    cap.clear_buffer()
    assert len(cap.buffer) == 0


def test_feature_extractor():
    extractor = FeatureExtractor(flow_timeout=30.0)
    assert len(extractor.flows) == 0
    assert extractor.flow_timeout == 30.0


if __name__ == '__main__':
    test_capture_initialization()
    test_capture_buffer()
    test_feature_extractor()
    print("All capture tests passed.")
