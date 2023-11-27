from pydub import AudioSegment
import numpy as np
import librosa
import os
import tkinter as tk
from tkinter import filedialog


def detect_speech_starts(audio_file, threshold=0.2, min_silence_duration=0.1, window_size=2048, hop_length=512):
    # Ses dosyasını yükle
    y, sr = librosa.load(audio_file, sr=None)

    # Sesi enerjiye dönüştür
    energy = librosa.feature.rms(y=y, frame_length=window_size, hop_length=hop_length)[0]

    # Enerjiyi normalize et
    energy = (energy - np.min(energy)) / (np.max(energy) - np.min(energy))

    # Belirli bir enerji eşiği üzerindeki zaman noktalarını bul
    speech_starts = np.where(energy > threshold)[0]
    speech_ends = np.where(energy < 0.001)[0]
    # Ardışık konuşma başlangıçlarını birleştir
    sentence_ends = []
    current_end = 0

    for end in speech_ends:
        if current_end == 0:
            current_end = end * hop_length / sr
        elif (end * hop_length / sr) - current_end > min_silence_duration:
            sentence_ends.append(current_end)
            current_end = 0

    return np.array(sentence_ends)  # Zamanı saniyeye çevir



def delete_and_add_silence_between_sentences(audio_file, start, end, silence_duration, first_second_1s):
    # Ses dosyasını yükle
    audio = AudioSegment.from_file(audio_file, format="mp3")
    # Belirtilen zaman aralıklarındaki sesi sessizlikle değiştir
    silence = AudioSegment.silent(duration=silence_duration * 1000)
    silence_1s = AudioSegment.silent(duration=1000)
    custom_audio = []
    output = AudioSegment.silent(duration=0)

    for i in range(len(start)):
        if first_second_1s and i == 0 or i == 1:
            custom_audio.append(audio[(start[i]) * 1000 : (end[i]) * 1000] + silence_1s)
        else:  
            custom_audio.append(audio[(start[i]) * 1000 : (end[i]) * 1000] + silence)


    for i in range(len(start)):
        output += custom_audio[i]

    # Yeni sesi orijinal dosyanın bulunduğu klasöre kaydet
    orijinal_klasor = os.path.dirname(audio_file)
    export_path = os.path.join(orijinal_klasor, "yeni_ses.mp3")
    output.export(export_path, format="mp3")




def find_sentence_starts_and_ends(times, min_silence_duration=0.8):
    sentence_starts = []  # İlk zamanı cümle başlangıcı olarak ekleyelim
    sentence_ends = []

    for i in range(0, len(times)):
        interval = times[i] - times[i - 1]

        # Eğer iki zaman arasındaki aralık çok uzunsa (sessizlik_esigi'nden büyükse), yeni bir cümle başlıyor demektir
        if interval > min_silence_duration:
            sentence_ends.append(times[i])
            sentence_starts.append(times[i - 1])

    return sentence_starts, sentence_ends


root = tk.Tk()
root.title("Cümleler Arası Sessizlik Ekleme Uygulaması")

def select_audio_file():
    file_path = filedialog.askopenfilename(title="Ses Dosyası Seç", filetypes=[("MP3 files", "*.mp3")])
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, file_path)


# Başlat düğmesine tıklandığında yapılacak işlem
def start_process():
    # Seçilen ses dosyası yolu
    audio_file_path = file_path_entry.get()

    speech_starts = detect_speech_starts(audio_file_path)

    # Sessizlik süresi
    silence_duration = slider.get()

    # İlk 2 boşluk 1 saniye
    first_second_1s = first_second_1s_var.get()

    try:

        sentence_starts, sentence_ends = find_sentence_starts_and_ends(speech_starts)
        # Cümler arası sessizlik ekleyerek işlemi başlat
        delete_and_add_silence_between_sentences(audio_file_path, sentence_starts, sentence_ends, silence_duration, first_second_1s)

        # İşlem tamamlandığında bir mesaj göster
        tk.messagebox.showinfo("Tamamlandı", "Cümleler arası sessizlik ekleme işlemi tamamlandı.")
    
    except Exception as e:
        tk.messagebox.showerror("Hata", f"Hata oluştu: {str(e)}")

# Arayüz öğelerini düzenle
file_path_label = tk.Label(root, text="Ses Dosyası:")
file_path_label.grid(row=0, column=0, padx=5, pady=5)

file_path_entry = tk.Entry(root, width=40)
file_path_entry.grid(row=0, column=1, padx=5, pady=5)

file_browse_button = tk.Button(root, text="Gözat", command=select_audio_file)
file_browse_button.grid(row=0, column=2, padx=5, pady=5)

silence_duration_label = tk.Label(root, text="Sessizlik Süresi: ")
silence_duration_label.grid(row=2, column=0, padx=5, pady=5)

slider = tk.Scale(root, from_=0.5, to=2, resolution=0.1, orient=tk.HORIZONTAL, length=200)
slider.set(1.3)  # Başlangıçta 1.3 saniye olarak ayarla
slider.grid(row=2, column=1, padx=5, pady=5)

first_second_1s_var = tk.BooleanVar()
first_second_1s_var.set(True)
first_second_1s_checkbox = tk.Checkbutton(root, text="İlk 2 cümle arasına otomatik 1 saniye sessizlik ekle", variable=first_second_1s_var)
first_second_1s_checkbox.grid(row=3, column=1, pady=5, padx=5)

start_button = tk.Button(root, text="Başlat", command=start_process)
start_button.grid(row=4, column=1, pady=10)


# Tkinter uygulamasını başlatın
root.mainloop()
