# PyQuotex

PyQuotex is a Python library aimed to automate trading on the Quotex platform.  
It leverages Playwright for browser automation, handles WebSocket communication, and interacts with the Quotex API to execute trades, monitor market data, and manage accounts.  
This library aims to provide a robust and flexible framework for automated trading strategies on Quotex.

## Features

* **Automated Login and Session Management:** Handles Quotex login, including potential two-factor authentication (2FA) via email, and saves session data for efficient reuse.  Session data is stored securely in a JSON file.
* **WebSocket Integration:** Real-time data streaming from Quotex using WebSocket connections.
* **API Interaction:** Provides methods for interacting with the Quotex API, including placing orders, retrieving market data, and managing account balances. (to be completed)
* **Email Integration (for 2FA):** Handles the retrieval of 2FA codes from email using IMAP.

## Installation

1. **Prerequisites:**
   - Python 3.12 or higher
   - OpenSSL (required for some Python libraries)
     - **Windows:** Download and install OpenSSL from [https://slproweb.com/products/Win32OpenSSL.html](https://slproweb.com/products/Win32OpenSSL.html)
     - **Linux/macOS:** Install OpenSSL using your system's package manager (e.g., `sudo apt install openssl` on Debian/Ubuntu).
   - Playwright: Install Playwright using pip:
     ```bash
     pip install playwright
     ```
   - Other dependencies: Install all required packages using pip:
     ```bash
     pip install -r requirements.txt
     ```

2. **Cloning the Repository:**
   ```bash
   git clone https://github.com/jechaviz/pyquotex.git
   cd pyquotex
   ```

3. **Configuration:**
   - See on `src/resources/env_*.yml` the settings.  
   - Replace placeholders on `src/resources/env_secrets.yml` with your actual values.
   
## Usage

`python ./src/api/websocket/qx_ws_client.py`

## Dependencies and Their Use

The `requirements.txt` file lists the dependencies used by PyQuotex.  Here's a breakdown of their roles:

* **`beautifulsoup4`:** Used for parsing HTML content, specifically for extracting data from web pages, such as login forms and email content.
* **`certifi`:** Provides root certificates for verifying SSL connections.
* **`chevron`:**  (Likely) Used for data serialization/deserialization, potentially for handling complex data structures.
* **`pandas`:**  (Likely) Used for data manipulation and analysis, potentially for handling financial data.
* **`paprika`:** Used for the `@singleton` decorator, ensuring that certain classes are instantiated only once.
* **`playwright`:**  Crucial for browser automation, enabling the library to interact with the Quotex website.
* **`pyfiglet`:** (Likely) Used for generating ASCII art, potentially for display purposes.
* **`pyperclip`:** Used for copying and pasting text, likely for handling 2FA codes.
* **`pytz`:** Used for handling time zones, crucial for accurate time-based operations.
* **`PyYAML`:** Used for loading configuration data from the YAML file (`config.yml`).
* **`requests`:** Used for making HTTP requests, potentially for interacting with the Quotex API or other web services.
* **`setuptools`:** Used for packaging the library.
* **`snoop`:** Used for debugging purposes, providing detailed information about the execution flow.
* **`urllib3`:** Used for making HTTP requests, potentially for interacting with the Quotex API or other web services.
* **`websocket-client`:** Used for establishing and maintaining WebSocket connections with the Quotex platform.


## Contributing

We welcome contributions to PyQuotex!  To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear, descriptive messages using clean architecture, SOLID, DRY, KISS principles.
4. Push your changes to your fork.
5. Create a pull request to the main repository.

## License

MIT License

## Contact 

jesus.cgalaviz@gmail.com

## Example config.yml.example

```yaml
# ... (other configuration) ...
```

**Important:** Replace placeholders with your actual values.  Ensure the `src/resources/` directory exists and that the `config.yml` file is in the correct location.


```
```
```bash
# Example command to run the application
python main.py
```
```
```