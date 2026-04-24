import subprocess
import time
import sys
import os

def start_process(command, name):
    print(f"[{name}] Starting...")
    # Use python executable from the virtual environment if available, otherwise fallback to sys.executable
    venv_python = os.path.join(".venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    
    process = subprocess.Popen(
        [python_exe] + command,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    return process

def main():
    print("=== MINNU ASSISTANT LAUNCHER ===")
    
    # 1. Start the FastAPI Backend
    backend = start_process(["app.py"], "BACKEND")
    
    # Give backend a moment to initialize
    time.sleep(2)
    
    # 2. Start the Hardware Listener
    hardware = start_process(["hardware.py"], "HARDWARE")
    
    # Give hardware a moment
    time.sleep(1)
    
    # 3. Start the UI Frontend
    ui = start_process(["ui.py"], "UI")
    
    try:
        # Keep the launcher running until the UI is closed
        ui.wait()
    except KeyboardInterrupt:
        print("\nShutting down Minnu Assistant...")
    finally:
        # Terminate all processes when UI closes or Ctrl+C is pressed
        print("Terminating Background Processes...")
        ui.terminate()
        hardware.terminate()
        backend.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
