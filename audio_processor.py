import numpy as np
import pyaudio
import threading
import time
import queue
from collections import deque
import sys

# Konfigurasi Audio
SAMPLE_RATE = 44100
FRAMES_PER_BUFFER = 1024
NUM_SECONDS = 0.1
AMPLITUDE_THRESHOLD = 0.005
SILENCE_TIMEOUT = 1.5  # detik

# Frekuensi nada (disesuaikan dengan kode C++ asli)
NOTE_FREQUENCIES = {
    "1": 2000.00,
    "2": 2050.00,
    "3": 2100.00,
    "4": 2150.01,
    "5": 2200.00,
    "6": 2250.00,
    "7": 2300.00
}
TOLERANCE = 15.0

class AudioProcessor:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        self.last_detected_note = ""
        self.last_signal_time = time.time()
        self.silence_detected = False
        
        # Buffer untuk analisis
        self.audio_buffer = deque(maxlen=int(SAMPLE_RATE * NUM_SECONDS))
        
    def start_listening(self, message_queue):
        """Mulai mendengarkan audio dan mengirim pesan ke queue"""
        self.is_running = True
        self.message_queue = message_queue
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=FRAMES_PER_BUFFER,
                stream_callback=self.audio_callback
            )
            
            self.stream.start_stream()
            
            # Main processing loop
            while self.is_running and self.stream.is_active():
                time.sleep(0.01)  # Small sleep to prevent CPU overuse
                
                # Check for silence timeout
                current_time = time.time()
                if (current_time - self.last_signal_time > SILENCE_TIMEOUT and 
                    not self.silence_detected and self.last_detected_note):
                    
                    self.silence_detected = True
                    message_queue.put(("end_of_transmission", None))
                    self.last_detected_note = ""
                    
        except Exception as e:
            message_queue.put(("error", f"Audio error: {str(e)}"))
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop listening to audio"""
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback untuk pemrosesan audio"""
        if status:
            print(f"Audio status: {status}")
        
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Add to buffer
        self.audio_buffer.extend(audio_data)
        
        if len(self.audio_buffer) >= FRAMES_PER_BUFFER:
            # Process the audio
            self.process_audio(np.array(self.audio_buffer)[-FRAMES_PER_BUFFER:])
        
        return (None, pyaudio.paContinue)
    
    def process_audio(self, audio_data):
        """Proses data audio untuk deteksi frekuensi"""
        # Calculate amplitude
        amplitude = np.max(np.abs(audio_data))
        
        # Update last signal time
        if amplitude > AMPLITUDE_THRESHOLD:
            self.last_signal_time = time.time()
            self.silence_detected = False
        
        # Perform FFT
        fft_data = np.fft.rfft(audio_data)
        frequencies = np.fft.rfftfreq(len(audio_data), 1.0/SAMPLE_RATE)
        magnitudes = np.abs(fft_data)
        
        # Find peak frequency
        if len(magnitudes) > 0:
            peak_index = np.argmax(magnitudes[1:]) + 1  # Skip DC component
            peak_frequency = frequencies[peak_index]
            peak_magnitude = magnitudes[peak_index]
            
            # Send frequency data to UI
            self.message_queue.put((
                "frequency_detected", 
                (float(peak_frequency), float(amplitude))
            ))
            
            # Check if above threshold
            if amplitude > AMPLITUDE_THRESHOLD:
                # Find matching note
                detected_note = None
                for note, freq in NOTE_FREQUENCIES.items():
                    if abs(peak_frequency - freq) <= TOLERANCE:
                        detected_note = note
                        break
                
                if detected_note and detected_note != self.last_detected_note:
                    self.last_detected_note = detected_note
                    self.message_queue.put(("note_detected", detected_note))
            else:
                self.last_detected_note = ""
        else:
            self.last_detected_note = ""
    
    def __del__(self):
        """Cleanup"""
        self.stop_listening()
        self.audio.terminate()