# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in ShadowSentinel, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, email: security@shadowsentinel.dev (or the maintainer's private email).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You should receive a response within 72 hours. We will work with you to understand and address the issue before any public disclosure.

## Security Considerations

- ShadowSentinel requires **root/admin privileges** for packet capture. Run in isolated environments only.
- Model files loaded via `pickle` are inherently unsafe — only load models you trained yourself or from trusted sources.
- The API server binds to `0.0.0.0` by default. Restrict access in production via firewall or reverse proxy.
- Never expose the detection API to untrusted networks without authentication.
- PCAP files and training data may contain sensitive network traffic — handle accordingly.

## Dependency Security

Run `pip audit` regularly to check for known vulnerabilities in dependencies.
