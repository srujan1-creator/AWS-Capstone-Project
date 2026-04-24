import serial
import time
import json
import requests

# Configuration
# Replace with your actual COM port (Windows) or /dev/ttyUSB0 (Linux/Mac)
SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600

# Backend API configuration to route hardware triggers if needed
API_URL = "http://127.0.0.1:8000/process_command"

def map_gyro_to_command(gyro_x, gyro_y, gyro_z):
    """
    Translates raw gyro/accelerometer data into discrete actions.
    Adjust thresholds based on your specific hardware sensor limits.
    """
    threshold = 50.0  # Example threshold value
    
    if gyro_x > threshold:
        return "right tilt"
    elif gyro_x < -threshold:
        return "left tilt"
    elif gyro_y > threshold:
        return "forward tilt"
    elif gyro_y < -threshold:
        return "backward tilt"
        
    return None

def execute_local_command(gesture):
    """
    Executes a local system command based on the detected gesture.
    This acts as the secondary input method alongside voice.
    """
    print(f"\n[HARDWARE] Gesture Detected: {gesture}")
    
    if gesture == "left tilt":
        print("[ACTION] Decreasing system volume...")
        # Add your OS-specific volume decrease code here
    elif gesture == "right tilt":
        print("[ACTION] Increasing system volume...")
        # Add your OS-specific volume increase code here
    elif gesture == "forward tilt":
        print("[ACTION] Triggering mute...")
    else:
        print(f"[ACTION] Unmapped gesture: {gesture}")

def main():
    print(f"Initializing connection on {SERIAL_PORT} at {BAUD_RATE} baud...")
    
    try:
        # Open serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        # Give the sensor a moment to initialize (common with Arduinos)
        time.sleep(2) 
        print("Successfully connected to hardware sensor.")
        
    except serial.SerialException as e:
        print(f"CRITICAL ERROR: Could not open serial port {SERIAL_PORT}.")
        print(f"Details: {e}")
        print("Please check your USB connection and ensure the correct COM port is specified.")
        return

    print("Listening for continuous gyro data... (Press Ctrl+C to stop)")
    
    try:
        while True:
            # Read a line of data from the serial port
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    
                    # Assuming the sensor sends data in a comma-separated format: "X,Y,Z"
                    # E.g., "12.5,-60.2,3.1"
                    if line:
                        parts = line.split(',')
                        if len(parts) >= 3:
                            x, y, z = map(float, parts[:3])
                            
                            # Determine if a gesture happened
                            gesture = map_gyro_to_command(x, y, z)
                            
                            if gesture:
                                execute_local_command(gesture)
                                # Add a small debounce delay so we don't trigger 100 times for one tilt
                                time.sleep(1)
                                
                except ValueError:
                    # Ignore corrupted serial lines
                    pass
                except UnicodeDecodeError:
                    pass
            
            # Small sleep to prevent 100% CPU usage
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nShutting down hardware listener...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    main()
