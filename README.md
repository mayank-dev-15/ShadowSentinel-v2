# ShadowSentinel v2

Enhanced ML-powered Network Intrusion Detection System (NIDS) with real-time anomaly detection, behavioral analysis, and automated threat correlation.

## Features

- **Real-time Traffic Analysis**: Process packets at line rate using optimized feature extraction
- **ML Anomaly Detection**: Isolation Forest, Autoencoder, and LSTM-based detectors
- **Behavioral Profiling**: Learn baseline behavior per host/subnet, detect deviations
- **Threat Correlation**: Multi-stage attack detection via temporal correlation engine
- **Rule Engine**: YARA-like rules for known signatures + ML scoring
- **REST API**: Integration with SIEM/SOAR platforms
- **Web Dashboard**: Live traffic view, alert timeline, model performance metrics
- **Offline Training**: Retrain models on captured PCAPs without production impact

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Packet     │────▶│  Feature     │────▶│  ML Models  │
│  Capture    │     │  Extraction  │     │  Ensemble   │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌──────────────┐     ┌──────▼──────┐
                    │  Correlation │◀────│  Scoring &  │
                    │  Engine      │     │  Alerting   │
                    └──────────────┘     └─────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Train models on sample data
python -m models.train --data data/sample.pcap --output models/

# Run live detection (requires root/admin for packet capture)
sudo python -m core.detector --interface eth0 --models models/

# Start API server
python -m api.server --host 0.0.0.0 --port 8080

# Start web dashboard
cd web && npm install && npm run dev
```

## Requirements

- Python 3.10+
- scikit-learn, pandas, numpy, scapy
- PyTorch (for LSTM autoencoder)
- FastAPI, uvicorn (API)
- Node.js 18+ (web dashboard)

## License

Apache-2.0

---

## ⚠️ Attribution & Credit Notice

This project is created and maintained by **Mayank Basena** ([@mayank-dev-15](https://github.com/mayank-dev-15)).

If you fork, use, modify, or derive work from this repository, **you must give proper credit** to the original author. This includes:

- Keeping this attribution section intact in any fork or derivative work
- Crediting **Mayank Basena** in your project's README or documentation
- Linking back to the original repository

**Failure to provide proper credit is a violation of the spirit of open source and may result in a DMCA takedown request.**

> *"No AI. No Shortcuts."* — Mayank Basena
