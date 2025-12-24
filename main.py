import customtkinter as ctk
import threading
import queue
import json
from datetime import datetime
import os
from tkinter import filedialog, messagebox
import numpy as np
from audio_processor import AudioProcessor
from penerjemah import Penerjemah

class MachineLanguageTranslator:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Machine Language Translator - Audio to Text")
        self.root.geometry("1200x800")
        
        # State variables
        self.is_listening = False
        self.word_count = 0
        self.note_count = 0
        self.current_frequency = 0.0
        self.current_amplitude = 0.0
        self.rangkaian_nada = ""
        
        # Initialize components
        self.mesin_penerjemah = Penerjemah("kamus.txt")
        self.audio_processor = AudioProcessor()
        self.message_queue = queue.Queue()
        
        # Setup UI
        self.setup_ui()
        
        # Start polling queue for messages from audio thread
        self.poll_message_queue()
        
    def setup_ui(self):
        # Configure grid layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # === TOP SECTION: Control Panel ===
        control_frame = ctk.CTkFrame(self.root)
        control_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.start_stop_button = ctk.CTkButton(
            control_frame,
            text="🎤 Start Listening",
            command=self.on_start_stop_clicked,
            height=50,
            font=("Arial", 16, "bold")
        )
        self.start_stop_button.pack(side="left", padx=5, pady=5)
        
        clear_button = ctk.CTkButton(
            control_frame,
            text="🗑️ Clear",
            command=self.on_clear_clicked,
            height=50
        )
        clear_button.pack(side="left", padx=5, pady=5)
        
        save_button = ctk.CTkButton(
            control_frame,
            text="💾 Save to File",
            command=self.on_save_clicked,
            height=50
        )
        save_button.pack(side="left", padx=5, pady=5)
        
        reset_dict_button = ctk.CTkButton(
            control_frame,
            text="🔄 Reset Dictionary",
            command=self.on_reset_dictionary_clicked,
            height=50
        )
        reset_dict_button.pack(side="left", padx=5, pady=5)
        
        # === LEFT PANEL: Note Sequence ===
        left_frame = ctk.CTkFrame(self.root)
        left_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        note_label = ctk.CTkLabel(left_frame, text="Note Sequence", font=("Arial", 16, "bold"))
        note_label.pack(pady=5)
        
        self.note_sequence_list = ctk.CTkScrollableFrame(left_frame, width=250)
        self.note_sequence_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === CENTER PANEL: Status & Text Areas ===
        center_frame = ctk.CTkFrame(self.root)
        center_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        center_frame.grid_columnconfigure(0, weight=1)
        
        # Status Group
        status_group = ctk.CTkFrame(center_frame)
        status_group.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            status_group,
            text="Status: Siap",
            font=("Arial", 14, "bold"),
            text_color="#2196F3"
        )
        self.status_label.pack(anchor="w", padx=10, pady=5)
        
        self.current_note_label = ctk.CTkLabel(
            status_group,
            text="Current Note: -",
            font=("Arial", 18, "bold"),
            text_color="#FF5722"
        )
        self.current_note_label.pack(anchor="w", padx=10, pady=5)
        
        self.frequency_label = ctk.CTkLabel(
            status_group,
            text="Frequency: 0.00 Hz",
            font=("Arial", 14),
            text_color="#555"
        )
        self.frequency_label.pack(anchor="w", padx=10, pady=5)
        
        # Audio Level Bar
        self.audio_level_bar = ctk.CTkProgressBar(status_group)
        self.audio_level_bar.pack(fill="x", padx=10, pady=5)
        self.audio_level_bar.set(0)
        
        # Stats Label
        self.stats_label = ctk.CTkLabel(
            status_group,
            text="Words: 0 | Notes: 0",
            font=("Arial", 12),
            text_color="#666"
        )
        self.stats_label.pack(anchor="w", padx=10, pady=5)
        
        # Preview Text
        preview_label = ctk.CTkLabel(
            center_frame,
            text="Real-time Preview:",
            font=("Arial", 14, "bold")
        )
        preview_label.grid(row=1, column=0, padx=5, pady=(10, 0), sticky="w")
        
        self.preview_text = ctk.CTkTextbox(
            center_frame,
            height=100,
            font=("Arial", 16),
            fg_color="#FFF3E0",
            text_color="black"
        )
        self.preview_text.grid(row=2, column=0, padx=5, pady=(0, 10), sticky="ew")
        self.preview_text.configure(state="disabled")
        
        # Result Text
        result_label = ctk.CTkLabel(
            center_frame,
            text="Translation Result:",
            font=("Arial", 14, "bold")
        )
        result_label.grid(row=3, column=0, padx=5, pady=(10, 0), sticky="w")
        
        self.result_text = ctk.CTkTextbox(
            center_frame,
            height=200,
            font=("Arial", 18, "bold"),
            fg_color="#E8F5E9",
            text_color="black"
        )
        self.result_text.grid(row=4, column=0, padx=5, pady=(0, 10), sticky="nsew")
        center_frame.grid_rowconfigure(4, weight=1)
        self.result_text.configure(state="disabled")
        
        # === RIGHT PANEL: History ===
        right_frame = ctk.CTkFrame(self.root)
        right_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        
        history_label = ctk.CTkLabel(right_frame, text="Translation History", font=("Arial", 16, "bold"))
        history_label.pack(pady=5)
        
        self.history_list = ctk.CTkScrollableFrame(right_frame, width=250)
        self.history_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === BOTTOM: Info Bar ===
        info_label = ctk.CTkLabel(
            self.root,
            text="💡 Tips: Speak clearly near the microphone. Wait for silence to complete a word.",
            font=("Arial", 12),
            fg_color="#E3F2FD",
            text_color="black",
            corner_radius=3
        )
        info_label.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
    def on_start_stop_clicked(self):
        if not self.is_listening:
            # Start listening
            self.is_listening = True
            self.start_stop_button.configure(
                text="⏹️ Stop Listening",
                fg_color="#f44336",
                hover_color="#da190b"
            )
            self.status_label.configure(
                text="Status: Listening... 🎤",
                text_color="#4CAF50"
            )
            
            # Start audio processing in a separate thread
            self.audio_thread = threading.Thread(
                target=self.audio_processor.start_listening,
                args=(self.message_queue,),
                daemon=True
            )
            self.audio_thread.start()
            
        else:
            # Stop listening
            self.is_listening = False
            self.start_stop_button.configure(
                text="🎤 Start Listening",
                fg_color="#4CAF50",
                hover_color="#45a049"
            )
            self.status_label.configure(
                text="Status: Stopped ⏸️",
                text_color="#FF9800"
            )
            self.current_note_label.configure(text="Current Note: -")
            self.audio_level_bar.set(0)
            self.audio_processor.stop_listening()
    
    def on_clear_clicked(self):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.configure(state="disabled")
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.configure(state="disabled")
        
        # Clear note sequence list
        for widget in self.note_sequence_list.winfo_children():
            widget.destroy()
        
        self.mesin_penerjemah.reset()
        self.word_count = 0
        self.note_count = 0
        self.update_stats()
        self.rangkaian_nada = ""
    
    def on_save_clicked(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_translation.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write("=== Machine Language Translation ===\n")
                    file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    file.write("Result:\n")
                    file.write(self.result_text.get("1.0", "end-1c") + "\n\n")
                    file.write("Note Sequence:\n")
                    
                    # Get note sequence from list
                    notes = []
                    for widget in self.note_sequence_list.winfo_children():
                        if hasattr(widget, 'cget'):
                            notes.append(widget.cget("text"))
                    
                    for note in notes:
                        file.write(note + "\n")
                
                messagebox.showinfo("Success", "Translation saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def on_reset_dictionary_clicked(self):
        self.mesin_penerjemah = Penerjemah("kamus.txt")
        messagebox.showinfo("Dictionary Reset", "Dictionary has been reloaded from kamus.txt")
    
    def handle_note_detected(self, note):
        self.note_count += 1
        self.current_note_label.configure(text=f"Current Note: {note}")
        
        # Add to note sequence display
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        note_label = ctk.CTkLabel(
            self.note_sequence_list,
            text=f"{timestamp} - Note: {note}",
            font=("Courier New", 12)
        )
        note_label.pack(anchor="w", padx=5, pady=2)
        
        # Update audio level bar
        self.audio_level_bar.set(min(self.current_amplitude * 100, 1.0))
        
        # Process through translator
        self.mesin_penerjemah.proses_input(note)
        hasil_pratinjau = self.mesin_penerjemah.get_kalimat_sementara()
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", hasil_pratinjau)
        self.preview_text.configure(state="disabled")
        
        self.update_stats()
    
    def handle_end_of_transmission(self):
        hasil_final = self.mesin_penerjemah.get_kalimat()
        
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", hasil_final)
        self.result_text.configure(state="disabled")
        
        if hasil_final:
            self.add_to_history(hasil_final)
        
        self.mesin_penerjemah.reset()
        
        # Add end marker to note sequence
        end_label = ctk.CTkLabel(
            self.note_sequence_list,
            text="--- End of Transmission ---",
            font=("Courier New", 12, "italic"),
            text_color="gray"
        )
        end_label.pack(anchor="w", padx=5, pady=2)
        
        self.current_note_label.configure(text="Current Note: -")
        self.audio_level_bar.set(0)
    
    def handle_frequency_detected(self, frequency, amplitude):
        self.current_frequency = frequency
        self.current_amplitude = amplitude
        self.frequency_label.configure(text=f"Frequency: {frequency:.2f} Hz")
        
        if self.is_listening:
            # Update audio level based on amplitude
            level = min(amplitude * 200, 100)
            self.audio_level_bar.set(level / 100)
    
    def update_stats(self):
        # Count words in result
        text = self.result_text.get("1.0", "end-1c")
        self.word_count = len(text.split())
        
        self.stats_label.configure(text=f"Words: {self.word_count} | Notes: {self.note_count}")
    
    def add_to_history(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        history_item = ctk.CTkLabel(
            self.history_list,
            text=f"{timestamp} - {text}",
            font=("Arial", 11),
            wraplength=230
        )
        history_item.pack(anchor="w", padx=5, pady=2)
        
        # Limit history to 50 items
        children = self.history_list.winfo_children()
        if len(children) > 50:
            children[0].destroy()
    
    def poll_message_queue(self):
        """Check for messages from audio thread"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                msg_type, data = message
                
                if msg_type == "note_detected":
                    self.handle_note_detected(data)
                elif msg_type == "end_of_transmission":
                    self.handle_end_of_transmission()
                elif msg_type == "frequency_detected":
                    self.handle_frequency_detected(data[0], data[1])
                elif msg_type == "error":
                    messagebox.showerror("Audio Error", data)
                    self.status_label.configure(
                        text="Status: Error ❌",
                        text_color="#f44336"
                    )
                    
        except queue.Empty:
            pass
        
        # Schedule next poll
        self.root.after(100, self.poll_message_queue)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MachineLanguageTranslator()
    app.run()