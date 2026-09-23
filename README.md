![License](https://img.shields.io/badge/License-MIT-blue.svg) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey) ![Python](https://img.shields.io/badge/Python-3.9+-green.svg) ![aiogram](https://img.shields.io/badge/aiogram-3.x-blue)

---

### What is this?

BarberBot wraps the entire barbershop booking routine into a native Telegram interface — no web apps, no browser redirects, no way for clients to get lost. Drop in your bot token, run the script, and distribute a polished booking system directly to your customers.

Perfect for:

* Small shops that need a digital presence without paying monthly SaaS fees
* Solo barbers managing their own schedules
* Keeping users locked to a single, familiar interface
* Giving your business an automated booking flow without rewriting it from scratch

---

### Features

* **Zero config headache** - change your token in the `config.py` or `.env` file, done.
* **Local persistence** - SQLite database survives app restarts and server reboots, storing all client data locally.
* **State machine logic** - FSM heavily restricts user navigation to the configured booking flow, preventing broken inputs.
* **Offline error handling** - custom text responses shown when the database is locked or unavailable.
* **Interactive UI** - pure inline keyboards. It just feels native to Telegram. 

---

### Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/ScarlettTheBrave/BarberBot.git
cd BarberBot

# 2. Setup your virtual environment
python -m venv .venv

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run in development mode
python main.py
```

---

### Configuration

Edit `.env` at the project root - no code changes needed:

```text
BOT_TOKEN="123456789:ABCdefGHIjklmNOPqrstUVWxyz"
ADMIN_ID="987654321"
```

| Key | Default | Description |
| :--- | :--- | :--- |
| `BOT_TOKEN` | none | The token you get from BotFather |
| `ADMIN_ID` | none | Your personal Telegram ID for notifications |

---

### Deploying on Windows (Step-by-Step from Scratch)

Follow these steps on a fresh Windows machine that has nothing installed.

**Step 1: Install Python**

1. Open a browser and go to: https://python.org
2. Download the stable version (the big yellow button on the main page). This will download an `.exe` file.
3. Double-click the downloaded file to run the installer.
4. Look at the bottom of the installer window. Check the box "Add python.exe to PATH" — this installs the background tools that your terminal actually needs.
5. Click Install Now, then Finish.
6. **Restart your computer** (recommended to ensure PATH is updated).

**Step 2: Verify Installation**

1. Press `Win + R`, type `cmd`, press Enter to open Command Prompt.
2. Run these commands to verify:

```bash
python --version
pip --version
```

You should see version numbers (e.g., `3.10.x` and `23.x.x`). If you get "not recognized", restart your PC and try again.

**Step 3: Copy the Project**

Copy the entire `BarberBot` folder to your Windows machine. You can use a USB drive, file share, or zip and transfer it. Place it somewhere convenient, for example:

```text
C:\Users\YourName\Desktop\BarberBot
```

**Important:** Do NOT copy the `.venv` folder or the `barbershop.db` file from your local testing — they will cause conflicts on a fresh system. Let the script regenerate them.
