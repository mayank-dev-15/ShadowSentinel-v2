"""
Feature extraction from packet streams for ML models.
"""
import numpy as np
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional
import time


@dataclass
class FlowKey:
    """Bidirectional flow identifier."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int

    def __hash__(self):
        return hash((self.src_ip, self.dst_ip, self.src_port, self.dst_port, self.protocol))

    def reverse(self):
        return FlowKey(self.dst_ip, self.src_ip, self.dst_port, self.src_port, self.protocol)

    def canonical(self):
        forward = (self.src_ip, self.src_port)
        reverse = (self.dst_ip, self.dst_port)
        if forward <= reverse:
            return self
        return self.reverse()


@dataclass
class FlowFeatures:
    """Aggregated flow features for ML detection."""
    flow_key: FlowKey
    start_time: float
    last_time: float
    duration: float
    fwd_packets: int
    bwd_packets: int
    fwd_bytes: int
    bwd_bytes: int
    fwd_payload_bytes: int
    bwd_payload_bytes: int
    fwd_packet_lengths: List[int]
    bwd_packet_lengths: List[int]
    fwd_iat: List[float]
    bwd_iat: List[float]
    flags: Dict[str, int]
    payload_entropy: List[float]

    def to_vector(self):
        """Convert to fixed-size feature vector for ML models."""
        feats = []
        feats.append(self.duration)
        feats.append(self.fwd_packets)
        feats.append(self.bwd_packets)
        feats.append(self.fwd_bytes)
        feats.append(self.bwd_bytes)
        feats.append(self.fwd_payload_bytes)
        feats.append(self.bwd_payload_bytes)
        for arr in [self.fwd_packet_lengths, self.bwd_packet_lengths]:
            if arr:
                feats.extend([np.mean(arr), np.std(arr), np.min(arr), np.max(arr)])
            else:
                feats.extend([0.0, 0.0, 0.0, 0.0])
        for arr in [self.fwd_iat, self.bwd_iat]:
            if arr:
                feats.extend([np.mean(arr), np.std(arr), np.min(arr), np.max(arr)])
            else:
                feats.extend([0.0, 0.0, 0.0, 0.0])
        for flag in ['SYN', 'ACK', 'FIN', 'RST', 'PSH', 'URG']:
            feats.append(self.flags.get(flag, 0))
        if self.payload_entropy:
            feats.extend([np.mean(self.payload_entropy), np.std(self.payload_entropy)])
        else:
            feats.extend([0.0, 0.0])
        return np.array(feats, dtype=np.float32)


class FeatureExtractor:
    """Extract flow-based features from packet stream in real-time."""

    def __init__(self, flow_timeout=60.0, max_flows=100000):
        self.flow_timeout = flow_timeout
        self.max_flows = max_flows
        self.flows = {}
        self.last_cleanup = time.time()

    def process_packet(self, pkt):
        key = FlowKey(pkt.src_ip, pkt.dst_ip, pkt.src_port, pkt.dst_port, pkt.protocol)
        canon = key.canonical()
        is_forward = (key == canon)
        now = pkt.timestamp
        self._maybe_cleanup(now)

        if canon not in self.flows:
            if len(self.flows) >= self.max_flows:
                self._evict_oldest()
            self.flows[canon] = FlowFeatures(
                flow_key=canon, start_time=now, last_time=now, duration=0.0,
                fwd_packets=0, bwd_packets=0, fwd_bytes=0, bwd_bytes=0,
                fwd_payload_bytes=0, bwd_payload_bytes=0,
                fwd_packet_lengths=[], bwd_packet_lengths=[],
                fwd_iat=[], bwd_iat=[], flags=defaultdict(int),
                payload_entropy=[],
            )

        flow = self.flows[canon]
        iat = now - flow.last_time
        flow.last_time = now
        flow.duration = now - flow.start_time

        if is_forward:
            flow.fwd_packets += 1
            flow.fwd_bytes += pkt.length
            flow.fwd_payload_bytes += pkt.payload_len
            flow.fwd_packet_lengths.append(pkt.length)
            if len(flow.fwd_packet_lengths) > 1:
                flow.fwd_iat.append(iat)
        else:
            flow.bwd_packets += 1
            flow.bwd_bytes += pkt.length
            flow.bwd_payload_bytes += pkt.payload_len
            flow.bwd_packet_lengths.append(pkt.length)
            if len(flow.bwd_packet_lengths) > 1:
                flow.bwd_iat.append(iat)

        if pkt.protocol == 6:
            f = pkt.flags
            if f & 0x02: flow.flags['SYN'] += 1
            if f & 0x10: flow.flags['ACK'] += 1
            if f & 0x01: flow.flags['FIN'] += 1
            if f & 0x04: flow.flags['RST'] += 1
            if f & 0x08: flow.flags['PSH'] += 1
            if f & 0x20: flow.flags['URG'] += 1

        if pkt.payload_entropy > 0:
            flow.payload_entropy.append(pkt.payload_entropy)

        if (flow.flags.get('FIN', 0) > 0 or flow.flags.get('RST', 0) > 0) and flow.duration > 1.0:
            return self.flows.pop(canon)
        return None

    def _maybe_cleanup(self, now):
        if now - self.last_cleanup > 30.0:
            self._cleanup_expired(now)
            self.last_cleanup = now

    def _cleanup_expired(self, now):
        expired = [k for k, v in self.flows.items() if now - v.last_time > self.flow_timeout]
        for k in expired:
            self.flows.pop(k, None)

    def _evict_oldest(self):
        if self.flows:
            oldest = min(self.flows.items(), key=lambda x: x[1].last_time)
            self.flows.pop(oldest[0], None)

    def get_active_flows(self):
        return list(self.flows.values())
