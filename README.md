# Brutus | ZIP Password Recovery Tool

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)

Brutus is a lightweight, high-performance ZIP password recovery tool written in Python. It features a modern graphical interface built with Pygame and supports both brute-force and dictionary-based attacks.

## Features

- **Brute-Force Attack**: Systematically tries every combination of characters.
- **Dictionary Attack**: Tests passwords from a provided wordlist (txt file).
- **Secure Extraction**: Implements safety checks to prevent "Zip Slip" vulnerabilities.
- **Real-time Statistics**: View attempts, cracking speed (passwords per second), and elapsed time.
- **Modern UI**: Clean, dark-themed interface for better user experience.
- **Multi-threaded**: Cracking runs in the background, keeping the UI responsive.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/brutus.git
   cd brutus
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python brutus.py
```

1. **Enter the path** to your ZIP file.
2. (Optional) **Enter the path** to a wordlist file for dictionary attacks.
3. Press **Enter** to load the ZIP file.
4. Click **Start Brute Force** or **Start Dictionary** to begin.

## Security Warning

This tool is for educational purposes and authorized security testing only. Using this tool on files you do not own or have permission to test is illegal and unethical.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
