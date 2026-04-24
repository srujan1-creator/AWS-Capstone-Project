import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import time
import requests
import speech_recognition as sr

# API Endpoint for the FastAPI backend
API_URL = "http://127.0.0.1:8000/process_command"

class MinnuUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minnu Assistant")
        
        # Configure dark theme and fullscreen
        self.bg_color = "#0a0a0f"  # Deep dark color
        self.fg_color = "#00ffcc"  # Cyan/Teal futuristic text
        self.root.configure(bg=self.bg_color)
        
        # Make the window fullscreen
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        
        # Main layout frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        # Header / Status indicator
        self.header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="MINNU SYSTEM ONLINE", 
            font=("Courier New", 24, "bold"), 
            bg=self.bg_color, 
            fg=self.fg_color
        )
        self.title_label.pack(side="left")
        
        self.status_label = tk.Label(
            self.header_frame, 
            text="● INITIALIZING", 
            font=("Courier New", 20, "bold"), 
            bg=self.bg_color, 
            fg="#aaaaaa" # Grey default
        )
        self.status_label.pack(side="right")
        
        # Central Terminal Display
        self.terminal = scrolledtext.ScrolledText(
            self.main_frame, 
            font=("Courier New", 14), 
            bg="#050508", 
            fg=self.fg_color, 
            insertbackground=self.fg_color,
            borderwidth=2,
            relief="sunken",
            state="disabled"
        )
        self.terminal.pack(expand=True, fill="both")
        
        # System control queue
        self.msg_queue = queue.Queue()
        
        # Initialize Speech Recognizer
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
            self.audio_available = True
        except AttributeError:
            self.log_to_terminal("PyAudio not found. Audio input disabled.", prefix="SYS")
            self.audio_available = False
        except Exception as e:
            self.log_to_terminal(f"Failed to initialize microphone: {e}", prefix="SYS")
            self.audio_available = False
        
        # Thread controls
        self.is_running = True
        
        # Start processes
        self.log_to_terminal("System initialization complete. Booting audio module...")
        self.set_status("LISTENING", "#00ff00") # Green for listening
        
        # Start GUI update loop
        self.process_queue()
        
        # Start audio listening in a non-blocking thread
        if self.audio_available:
            self.audio_thread = threading.Thread(target=self.audio_listener_loop, daemon=True)
            self.audio_thread.start()
        else:
            self.log_to_terminal("Running in text-only mode (No PyAudio)", prefix="SYS")
        
        # Visual pulsing effect state
        self.pulse_state = True
        self.pulse_status_indicator()

    def set_status(self, text, color):
        """Updates the top right status indicator."""
        self.current_status_text = text
        self.current_status_color = color
        self.status_label.config(text=f"● {text}", fg=color)

    def pulse_status_indicator(self):
        """Creates a pulsing effect on the status indicator."""
        if self.current_status_text == "LISTENING":
            color = self.current_status_color if self.pulse_state else "#005500"
            self.status_label.config(fg=color)
            self.pulse_state = not self.pulse_state
        elif self.current_status_text == "PROCESSING":
            color = self.current_status_color if self.pulse_state else "#555500"
            self.status_label.config(fg=color)
            self.pulse_state = not self.pulse_state
            
        # Re-run every 500ms
        self.root.after(500, self.pulse_status_indicator)

    def log_to_terminal(self, message, prefix="SYS"):
        """Safely sends messages to the Tkinter text area from any thread."""
        self.msg_queue.put(f"[{prefix}] {message}")

    def process_queue(self):
        """Processes messages from the queue and updates the terminal safely."""
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            self.terminal.config(state="normal")
            self.terminal.insert(tk.END, msg + "\n")
            self.terminal.see(tk.END) # Scroll to bottom
            self.terminal.config(state="disabled")
        
        # Check queue again in 100ms
        self.root.after(100, self.process_queue)

    def send_to_backend(self, text):
        """Sends transcribed text to the FastAPI backend."""
        self.set_status("PROCESSING", "#ffff00") # Yellow for processing
        self.log_to_terminal(f"Transcribed: {text}", prefix="USR")
        self.log_to_terminal("Sending to Cloud/Backend...", prefix="NET")
        
        try:
            response = requests.post(API_URL, json={"text": text}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_to_terminal(f"Action: {data.get('action')} (Confidence: {data.get('confidence')})", prefix="AI")
                self.log_to_terminal(f"Response: {data.get('response_text')}", prefix="AI")
            else:
                self.log_to_terminal(f"Backend returned error: {response.status_code}", prefix="ERR")
        except requests.exceptions.RequestException as e:
            self.log_to_terminal(f"Failed to connect to backend: {e}", prefix="ERR")
            
        self.set_status("LISTENING", "#00ff00") # Back to listening

    def audio_listener_loop(self):
        """Background thread function to listen for audio continuously."""
        # Calibrate microphone once
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            self.log_to_terminal("Microphone calibrated. Ready for input.")
            
        while self.is_running:
            if self.current_status_text != "LISTENING":
                time.sleep(0.5)
                continue
                
            try:
                with self.microphone as source:
                    # Listen for audio chunk
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                self.set_status("PROCESSING", "#ffff00")
                self.log_to_terminal("Audio captured. Transcribing...", prefix="SYS")
                
                # Transcribe using Google's free API (replace with local Whisper or similar for production)
                text = self.recognizer.recognize_google(audio)
                
                # Process the text in a new thread so we can resume listening quickly if needed
                # (or block if we want to wait for backend response)
                threading.Thread(target=self.send_to_backend, args=(text,), daemon=True).start()
                
            except sr.WaitTimeoutError:
                # Normal timeout when no one speaks, just loop again
                pass
            except sr.UnknownValueError:
                self.log_to_terminal("Could not understand audio.", prefix="SYS")
                self.set_status("LISTENING", "#00ff00")
            except sr.RequestError as e:
                self.log_to_terminal(f"Speech Recognition service error: {e}", prefix="ERR")
                self.set_status("LISTENING", "#00ff00")
            except Exception as e:
                self.log_to_terminal(f"Audio Error: {e}", prefix="ERR")
                self.set_status("LISTENING", "#00ff00")
                time.sleep(1) # Prevent tight loop on permanent hardware error

    def on_closing(self):
        self.is_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app_ui = MinnuUI(root)
    root.protocol("WM_DELETE_WINDOW", app_ui.on_closing)
    root.mainloop()
