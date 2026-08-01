import pyaudio
import wave
import keyboard
from datetime import datetime
import time
import os
from util import *

# Configurações para gravação de áudio
CHUNK = 1024  # Tamanho do bloco de áudio
FORMAT = pyaudio.paInt16  # Formato de gravação
CHANNELS = 1  # Mono
RATE = 44100  # Taxa de amostragem
import sys

if getattr(sys, 'frozen', False):
    DIRETORIO_ATUAL = os.path.dirname(sys.executable)
else:
    DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

DIRETORIO_ANTERIOR = os.path.dirname(DIRETORIO_ATUAL)
OUTPUT_DIR = os.path.join(DIRETORIO_ANTERIOR, "audios")
TEMPO_MIN_SEGUNDOS = 1
INDEX_MICROFONE = 1

def get_microfone(audio):
    stream = None
    for i in range(audio.get_device_count()):
        try:
            info = audio.get_device_info_by_index(i)
            print(f"{i}: {info['name']} - Input Channels: {info['maxInputChannels']}")
            stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=i, frames_per_buffer=CHUNK)
            return stream
        except Exception as e:
            print(f"Erro mic: {e}")
    return stream


POSSIVEIS_RATES = [44100, 16000, 8000]
POSSIVEIS_CHANNELS = [1, 2]

def encontrar_microfone_valido():
    audio = pyaudio.PyAudio()
    dispositivos_validos = []

    print("\nDispositivos disponíveis:")
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        entradas = info.get('maxInputChannels', 0)
        nome = info.get('name', 'Desconhecido')
        print(f"ID {i}: {nome} | Entradas: {entradas}")
        if entradas > 0:
            dispositivos_validos.append((i, nome))

    for index, nome in dispositivos_validos:
        for rate in POSSIVEIS_RATES:
            for channels in POSSIVEIS_CHANNELS:
                try:
                    print(f"Tentando microfone ID {index} - {nome} | rate={rate} | channels={channels}")
                    stream = audio.open(format=FORMAT,
                                        channels=channels,
                                        rate=rate,
                                        input=True,
                                        input_device_index=index,
                                        frames_per_buffer=CHUNK)
                    print(f"✅ FUNCIONOU: ID {index} - {nome} | rate={rate} | channels={channels}")
                    return audio, stream, index, rate, channels
                except Exception as e:
                    print(f"❌ Erro com ID {index} | rate={rate} | channels={channels}: {e}")

    audio.terminate()
    raise Exception("Nenhum microfone válido encontrado.")

def record_audio():
    """Grava o áudio enquanto a tecla espaço é pressionada."""
    #audio, stream, index, rate, channels = encontrar_microfone_valido()
    
    #print(audio, stream, index, rate, channels)

    #selecionar lista de microfone
    
    #get_microfone(audio)
    #stream = None
    try:

        audio = pyaudio.PyAudio()
        #stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=INDEX_MICROFONE, frames_per_buffer=CHUNK)
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = []
        print_msg_start_gravar = False
        try:
            while keyboard.is_pressed("space"):
                data = stream.read(CHUNK)
                frames.append(data)
                if not print_msg_start_gravar:
                    print("Gravando... Pressione e segure 'Espaço'.")
                    print_msg_start_gravar = True
        except Exception as e:
            print(f"Erro durante a gravação: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            return frames, audio
    
    except Exception as e:
        print_log(f"Erro no Microfone: {e}", "danger")
        return None, None

def save_audio(frames, audio):
    """Salva os frames de áudio em um arquivo WAV."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not frames:
        #print("Nenhum áudio foi gravado.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    nome = f"audio_{timestamp}.wav"
    filename = f"{OUTPUT_DIR}/{nome}"
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    print_log(f"Áudio salvo: {filename}", "info")
    return nome

if __name__ == "__main__":
    #print(f"Pressione e segure a tecla 'Espaço' por {TEMPO_MIN_SEGUNDOS} segundos para começar a gravar.")
    print_log(f"Pressione e segure a tecla 'Espaço' para começar a gravar.\nSolte a tecla para salvar o áudio.", "info")
    while True:
        # Aguarda o usuário pressionar a tecla espaço
        keyboard.wait("space")
        press_time = time.time()  # Registra o tempo inicial de pressionamento

        # Verifica se a tecla permanece pressionada por 1 segundos
        while keyboard.is_pressed("space"):
            if time.time() - press_time >= TEMPO_MIN_SEGUNDOS:
                print_log("Tempo atingido, iniciando gravação...", "info")
                frames, audio = record_audio()  # Começa a ouvir enquanto o espaço é pressionado
                if frames != None and audio != None:
                    save_audio(frames, audio)      # Salva o áudio ao soltar a tecla
                break
        """
        else:
            print(f"Tecla liberada antes de atingir {TEMPO_MIN_SEGUNDOS} segundos. Nenhuma gravação realizada.")
        """