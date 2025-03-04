import os
import tkinter as tk
from tkinter import filedialog, ttk
from google.cloud import speech
import pyaudio
import queue
import threading


#Insert the path of the Google Speech API key and the name of your key( .json file)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\user\Downloads\key.json"


RATE = 16000
CHUNK = int(RATE / 10)   

LANGUAGES = {
    "Română": "ro-RO",
    "Engleză": "en-US",
    "Greacă": "el-GR"
}


is_listening = False
audio_queue = queue.Queue()
selected_language = "ro-RO"  

def audio_callback(in_data, frame_count, time_info, status):
    """Callback pentru capturarea audio."""
    if is_listening:
        audio_queue.put(in_data)
    return (in_data, pyaudio.paContinue)

def recognize_speech():
    """Proces de recunoaștere vocală."""
    global is_listening
    client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=selected_language,
        enable_automatic_punctuation=True
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config)

    def audio_generator():
        while is_listening:
            chunk = audio_queue.get()
            if chunk is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    try:
        responses = client.streaming_recognize(streaming_config, audio_generator())
        for response in responses:
            if not is_listening:
                break
            if response.results and response.results[0].alternatives:
                text = response.results[0].alternatives[0].transcript.strip()
                update_text_display(text)
    except Exception as e:
        update_text_display(f"Eroare: {e}")

def start_recognition():
    """Începe recunoașterea vocală."""
    global is_listening
    if is_listening:
        return
    is_listening = True
    threading.Thread(target=recognize_speech, daemon=True).start()

def stop_recognition():
    """Oprește recunoașterea vocală."""
    global is_listening
    is_listening = False
    audio_queue.put(None)

def update_text_display(text):
    """Actualizează textul afișat."""
    text_display.insert(tk.END, text + "\n")
    text_display.see(tk.END)

def clear_text():
    """Șterge textul afișat."""
    text_display.delete("1.0", tk.END)

def save_text():
    """Salvează textul recunoscut într-un fișier."""
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text_display.get("1.0", tk.END))

def change_language(event):
    """Schimbă limba recunoașterii."""
    global selected_language
    selected_language = LANGUAGES[language_combobox.get()]
    clear_text()  


root = tk.Tk()
root.title("Recunoaștere Vocală Live")
root.geometry("800x600")


text_display = tk.Text(root, wrap=tk.WORD, height=25, padx=10, pady=10)
text_display.pack(fill=tk.BOTH, expand=True)


language_combobox = ttk.Combobox(root, values=list(LANGUAGES.keys()), state="readonly")
language_combobox.set("Română")
language_combobox.bind("<<ComboboxSelected>>", change_language)
language_combobox.pack(pady=10)

# Butoane de control
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

start_button = tk.Button(button_frame, text="Pornește Recunoașterea", command=start_recognition)
start_button.pack(side=tk.LEFT, padx=10)

stop_button = tk.Button(button_frame, text="Oprește Recunoașterea", command=stop_recognition)
stop_button.pack(side=tk.LEFT, padx=10)

save_button = tk.Button(button_frame, text="Salvează Text", command=save_text)
save_button.pack(side=tk.LEFT, padx=10)

clear_button = tk.Button(button_frame, text="Șterge Text", command=clear_text)
clear_button.pack(side=tk.LEFT, padx=10)


pyaudio_instance = pyaudio.PyAudio()
audio_stream = pyaudio_instance.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    stream_callback=audio_callback
)
audio_stream.start_stream()


root.mainloop()


audio_stream.stop_stream()
audio_stream.close()
pyaudio_instance.terminate()
