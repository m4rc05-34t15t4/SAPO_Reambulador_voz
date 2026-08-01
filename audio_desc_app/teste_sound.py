import sounddevice as sd
from scipy.io.wavfile import write
import datetime

# Defina o tempo de gravação em segundos
DURATION = 10  # segundos
SAMPLE_RATE = 44100  # Hz (padrão de CD)

# Lista todos os dispositivos de entrada e saída
print("=== Dispositivos de Áudio ===")
print(sd.query_devices())

device_name_part = "Q20"  # Parte do nome do microfone
devices = sd.query_devices()
index = None

for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0 and device_name_part.lower() in dev['name'].lower():
        index = i
        break

if index is None:
    raise RuntimeError("Dispositivo de entrada Bluetooth não encontrado!")

print(f"Usando dispositivo: {devices[index]['name']} (índice {index})")

# Continue com a gravação
sd.default.device = (index, None)

# Se você souber o índice do microfone Bluetooth, defina aqui
# Caso contrário, o padrão do sistema será usado (None)
input_device_index = None  # Substitua pelo índice correto se quiser forçar

# Nome do arquivo com timestamp
filename = f"gravacao_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

print(f"Gravando por {DURATION} segundos...")
recorded_audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=input_device_index)
sd.wait()
print("Gravação finalizada.")

# Salva o arquivo
write(filename, SAMPLE_RATE, recorded_audio)
print(f"Arquivo salvo como: {filename}")
