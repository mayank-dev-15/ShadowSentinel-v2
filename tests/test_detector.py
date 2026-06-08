import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from core.detector import FlowDetector


def test_detector_initialization():
    d = FlowDetector(threshold=0.5)
    assert d.threshold == 0.5


def test_detector_empty():
    d = FlowDetector()
    result = d.detect(np.array([[0.1, 0.2, 0.3]]))
    assert result is not None


def test_detector_threshold():
    d = FlowDetector(threshold=0.0)
    scores = d.detect(np.random.randn(10, 28))
    assert len(scores) == 10


if __name__ == '__main__':
    test_detector_initialization()
    test_detector_empty()
    test_detector_threshold()
    print("All detector tests passed.")
