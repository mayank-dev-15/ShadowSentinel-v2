"""
Packet capture using scapy with BPF filtering and async processing.
"""
import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional
from scapy.all import sniff, Ether, IP, TCP, UDP, ICMP, Raw
import logging

logger = logging.getLogger(__name__)


@dataclass
class PacketInfo:
    """Normalized packet information for feature extraction."""
    timestamp: float
    src_mac: str
    dst_mac: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    length: int
    flags: int
    payload_len: int
    payload_entropy: float


class PacketCapture:
    """Async packet capture with configurable filtering and callbacks."""

    def __init__(
        self,
        interface: str,
        bpf_filter: str = "ip",
        buffer_size: int = 10000,
        callback: Optional[Callable[[PacketInfo], None]] = None,
    ):
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.buffer = deque(maxlen=buffer_size)
        self.callback = callback
        self._running = False
        self._sniffer = None

    def _packet_handler(self, pkt):
        """Process raw scapy packet into PacketInfo."""
        if not pkt.haslayer(IP):
            return

        ip = pkt[IP]
        eth = pkt[Ether] if pkt.haslayer(Ether) else None

        src_port = 0
        dst_port = 0
        flags = 0
        payload_len = 0
        payload_entropy = 0.0

        if pkt.haslayer(TCP):
            tcp = pkt[TCP]
            src_port = tcp.sport
            dst_port = tcp.dport
            flags = int(tcp.flags)
        elif pkt.haslayer(UDP):
            udp = pkt[UDP]
            src_port = udp.sport
            dst_port = udp.dport

        if pkt.haslayer(Raw):
            payload = bytes(pkt[Raw].load)
            payload_len = len(payload)
            if payload_len > 0:
                payload_entropy = self._entropy(payload)

        info = PacketInfo(
            timestamp=pkt.time,
            src_mac=eth.src if eth else "00:00:00:00:00:00",
            dst_mac=eth.dst if eth else "00:00:00:00:00:00",
            src_ip=ip.src,
            dst_ip=ip.dst,
            src_port=src_port,
            dst_port=dst_port,
            protocol=ip.proto,
            length=len(pkt),
            flags=flags,
            payload_len=payload_len,
            payload_entropy=payload_entropy,
        )

        self.buffer.append(info)
        if self.callback:
            try:
                self.callback(info)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    @staticmethod
    def _entropy(data: bytes) -> float:
        """Calculate Shannon entropy of payload."""
        if not data:
            return 0.0
        from collections import Counter
        import math
        counts = Counter(data)
        length = len(data)
        return -sum((c / length) * math.log2(c / length) for c in counts.values())

    def start(self):
        """Start packet capture in background thread."""
        self._running = True
        logger.info(f"Starting capture on {self.interface} with filter: {self.bpf_filter}")
        self._sniffer = sniff(
            iface=self.interface,
            filter=self.bpf_filter,
            prn=self._packet_handler,
            store=False,
            stop_filter=lambda _: not self._running,
        )

    def stop(self):
        """Stop packet capture."""
        self._running = False
        logger.info("Capture stopped")

    def get_buffer(self) -> list[PacketInfo]:
        """Get copy of current buffer."""
        return list(self.buffer)

    def clear_buffer(self):
        """Clear packet buffer."""
        self.buffer.clear()