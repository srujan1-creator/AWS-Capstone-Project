# Minnu Assistant: Cinematic Full-Stack AI Platform

Minnu is a high-end, cinematic personal AI assistant designed with a futuristic "sci-fi terminal" aesthetic. This project integrates cloud-based intent classification (AWS SageMaker), local hardware sensor support, and a secure full-stack web dashboard.

## 🚀 Features

- **Cinematic Web Interface:** A single-page application (SPA) built with vanilla HTML/CSS/JS, featuring glowing glassmorphism, dynamic animations, and a real-time system terminal.
- **Voice & Gesture Control:** 
  - **Voice:** Uses the browser's native Web Speech API for high-performance voice-to-text without local driver dependencies.
  - **Gestures:** Includes a standalone Python script for reading gyro/accelerometer data via Serial (USB/COM).
- **Secure Full-Stack Backend:** 
  - **FastAPI:** High-performance Python backend serving both the API and the static frontend.
  - **Authentication:** Secure Sign-up/Login flow with hashed passwords (bcrypt) and JWT session management.
  - **Database:** Local SQLite database for persistent user management.
- **Cloud Integration:** Ready-to-use boilerplate for AWS SageMaker Runtime to process natural language intents.

## 🛠️ Tech Stack

- **Backend:** Python 3.x, FastAPI, Uvicorn, Boto3 (AWS SDK).
- **Database:** SQLite.
- **Security:** PyJWT, Bcrypt.
- **Frontend:** Vanilla HTML5, CSS3 (Glow/Glassmorphism), JavaScript.
- **Hardware:** PySerial (for Gyro sensors).

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/srujan1-creator/AWS-Capstone-Project.git
   cd AWS-Capstone-Project
   ```

2. **Set up the environment:**
   We recommend using `uv` for lightning-fast environment management:
   ```bash
   uv venv
   .venv\Scripts\activate
   uv pip install fastapi uvicorn boto3 pydantic pyserial requests pyjwt bcrypt
   ```

## 🏃 Running the Application

### 1. Launch the Web Platform
Start the FastAPI server:
```bash
python app.py
```
Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)**.

### 2. Hardware Integration (Optional)
If you have a gyro sensor connected via USB:
```bash
python hardware.py
```
*(Note: Ensure you update the `SERIAL_PORT` in `hardware.py` to match your device).*

### 3. Desktop UI (Legacy)
The original Tkinter desktop interface is still available:
```bash
python ui.py
```

## 🔐 Authentication
The system is locked behind a secure authentication wall. 
1. Launch the web interface.
2. Click **"Initialize New Subject"** to create an account.
3. Once logged in, you will be granted access to the terminal grid and voice command stream.

## ⚠️ Notes
- **AWS SageMaker:** The backend currently runs in a "Mock/Offline" mode if AWS credentials are not detected. To use live SageMaker inference, ensure your environment is configured with `aws configure`.
- **Microphone:** Ensure you grant microphone permissions in your browser to enable voice commands.

---
Built for the AWS Capstone Project.
