# Contributing to ESP8266 PixelMatrix 200

Thank you for your interest in contributing to **ESP8266 PixelMatrix 200**! We welcome bug reports, hardware testing results, documentation improvements, and new animation effects.

---

## Code of Conduct

Please be respectful, collaborative, and constructive when opening issues or participating in pull request discussions.

---

## How to Contribute

### 1. Reporting Bugs
- Search existing [GitHub Issues](https://github.com/chetanngavali/PixelMatrix/issues) to ensure the bug has not already been reported.
- Provide clear details:
  - ESP8266 board model (NodeMCU V2, V3, D1 Mini, etc.).
  - LED strip model and pixel count.
  - Power supply voltage and amperage rating.
  - Serial monitor boot log output at 115200 baud.
  - Steps to reproduce the issue.

### 2. Suggesting New Lighting Effects & Features
- Suggestions and improvements can be submitted via Pull Requests or Issues maintained by **[Chetan Gavali](https://github.com/chetanngavali)**.
- Frame timing must be driven by `millis()` or fractional step calculations so the ESP8266 network stack and watchdog timer are not starved.
- Animations should perform smoothly at 45 FPS on 200 pixels.

---

## Development Workflow

1. **Fork the repository** on GitHub: [https://github.com/chetanngavali/PixelMatrix](https://github.com/chetanngavali/PixelMatrix)
2. **Clone your fork**:
   ```bash
   git clone https://github.com/chetanngavali/PixelMatrix.git
   cd PixelMatrix
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-cool-effect
   ```
4. **Compile and test locally**:
   ```bash
   pio run -e nodemcuv2
   ```
5. **Commit your changes**:
   ```bash
   git commit -m "feat(effects): add aurora borealis wave pattern"
   ```
6. **Push to your fork and submit a Pull Request**.

---

## Coding Standards

- **C++ (Firmware)**: Follow standard modern Arduino C++ conventions. Use `const` correctness, avoid dynamic heap reallocations in tight loops, and prefer `F()` macro for flash strings.
- **Hardware Safety**: Changes that impact power limits or pin assignments must preserve safety headroom and document hardware prerequisites clearly.

---

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
