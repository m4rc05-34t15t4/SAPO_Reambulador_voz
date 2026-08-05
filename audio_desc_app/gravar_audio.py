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

MICROFONE_SELECIONADO_INDEX = None
MICROFONE_SELECIONADO_NOME = None

def listar_dispositivos_entrada(audio):
    """
    Lista os dispositivos de entrada da API MME do Windows.
    Retorna o Padrão do Sistema e os microfones reais conectados com seus nomes completos (ex: Headset (UGREEN HiTune Max5c)).
    """
    dispositivos_filtrados = []
    nomes_vistos = set()

    # 1. Padrão do Sistema
    try:
        default_info = audio.get_default_input_device_info()
        def_name = default_info.get('name', 'Padrão do Sistema')
        dispositivos_filtrados.append((None, f"Padrão do Sistema ({def_name})"))
        nomes_vistos.add(def_name.lower())
    except Exception:
        dispositivos_filtrados.append((None, "Padrão do Sistema"))

    # 2. Obter índice da Host API 'MME' (dispositivos amigáveis de alto nível do Windows)
    mme_api_index = None
    try:
        for i in range(audio.get_host_api_count()):
            api_info = audio.get_host_api_info_by_index(i)
            if api_info.get('name') == 'MME':
                mme_api_index = i
                break
    except Exception:
        pass

    count = audio.get_device_count()
    for i in range(count):
        try:
            info = audio.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                # Filtra apenas a API MME do Windows para evitar canais brutos do WDM-KS
                if mme_api_index is not None and info.get('hostApi') != mme_api_index:
                    continue

                name = info.get('name', '').strip()
                name_lower = name.lower()

                # Ignorar entradas virtuais/mapeadores genéricos
                if 'mapeador' in name_lower or 'mapper' in name_lower:
                    continue

                if name_lower not in nomes_vistos:
                    nomes_vistos.add(name_lower)
                    dispositivos_filtrados.append((i, name))
        except Exception:
            continue

    return dispositivos_filtrados

import threading
import tkinter as tk
from tkinter import ttk

CONFIG_INDICADOR_VISUAL = True

class IndicadorGravacao:
    """
    Exibe um selo flutuante vermelho com o ícone de microfone no canto superior direito da tela enquanto o usuário grava.
    """
    def __init__(self):
        self.root = None

    def mostrar(self):
        if not CONFIG_INDICADOR_VISUAL:
            return

        def _run():
            try:
                self.root = tk.Tk()
                self.root.overrideredirect(True)
                self.root.attributes('-topmost', True)
                
                sw = self.root.winfo_screenwidth()
                w, h = 175, 45
                x = sw - w - 25
                y = 35
                self.root.geometry(f"{w}x{h}+{x}+{y}")
                self.root.configure(bg="#D32F2F")

                lbl = tk.Label(
                    self.root, 
                    text="🎙️ GRAVANDO...", 
                    font=("Segoe UI", 11, "bold"), 
                    fg="white", 
                    bg="#D32F2F"
                )
                lbl.pack(expand=True, fill="both", padx=5, pady=5)
                self.root.mainloop()
            except Exception:
                pass

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()

    def fechar(self):
        if self.root is not None:
            try:
                self.root.after(0, self.root.destroy)
            except Exception:
                pass
            self.root = None

def abrir_janela_selecao_microfone():
    """
    Abre uma caixa de diálogo gráfica para o usuário escolher de qual microfone virá o áudio
    e configurar se deseja o selo visual na tela.
    """
    global MICROFONE_SELECIONADO_INDEX, MICROFONE_SELECIONADO_NOME, CONFIG_INDICADOR_VISUAL
    audio = pyaudio.PyAudio()
    dispositivos = listar_dispositivos_entrada(audio)
    audio.terminate()

    if not dispositivos:
        MICROFONE_SELECIONADO_INDEX = None
        MICROFONE_SELECIONADO_NOME = "Padrão do Sistema"
        return MICROFONE_SELECIONADO_INDEX, MICROFONE_SELECIONADO_NOME

    index_padrao = 0
    keywords = ["ugreen", "hitune", "max5c", "bluetooth", "headset", "headphone", "fone", "hands-free", "wireless"]
    for idx, (dev_idx, dev_name) in enumerate(dispositivos):
        if any(kw in dev_name.lower() for kw in keywords):
            index_padrao = idx
            break

    try:
        resultado = {"index": dispositivos[index_padrao][0], "nome": dispositivos[index_padrao][1]}

        root = tk.Tk()
        root.title("SAPO - Selecionar Microfone e Opções")
        root.geometry("500x240")
        root.resizable(False, False)
        root.attributes('-topmost', True)

        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

        style = ttk.Style()
        style.theme_use('clam')

        lbl = ttk.Label(root, text="🎤 Escolha o Microfone para Gravação de Áudio:", font=("Segoe UI", 11, "bold"))
        lbl.pack(pady=(15, 8))

        nomes = [f"{name}" for idx, name in dispositivos]
        combo = ttk.Combobox(root, values=nomes, state="readonly", font=("Segoe UI", 10), width=48)
        combo.current(index_padrao)
        combo.pack(pady=5)

        var_indicador = tk.BooleanVar(value=CONFIG_INDICADOR_VISUAL)

        chk_indicador = ttk.Checkbutton(root, text="Exibir selo visual (🎙️ Gravando) no canto superior direito", variable=var_indicador)
        chk_indicador.pack(anchor="w", padx=35, pady=(12, 10))

        def on_confirmar():
            global CONFIG_INDICADOR_VISUAL
            idx_selecionado = combo.current()
            if idx_selecionado >= 0:
                resultado["index"] = dispositivos[idx_selecionado][0]
                resultado["nome"] = dispositivos[idx_selecionado][1]
            CONFIG_INDICADOR_VISUAL = var_indicador.get()
            root.destroy()

        btn = ttk.Button(root, text="  Confirmar e Iniciar  ", command=on_confirmar)
        btn.pack(pady=(10, 10))

        root.protocol("WM_DELETE_WINDOW", on_confirmar)
        root.mainloop()

        MICROFONE_SELECIONADO_INDEX = resultado["index"]
        MICROFONE_SELECIONADO_NOME = resultado["nome"]
    except Exception as e:
        print_log(f"Aviso ao abrir janela GUI: {e}. Usando microfone padrão.", "warning")
        MICROFONE_SELECIONADO_INDEX = dispositivos[index_padrao][0]
        MICROFONE_SELECIONADO_NOME = dispositivos[index_padrao][1]

    return MICROFONE_SELECIONADO_INDEX, MICROFONE_SELECIONADO_NOME

def record_audio():
    """Grava o áudio enquanto a tecla espaço é pressionada."""
    global MICROFONE_SELECIONADO_INDEX, MICROFONE_SELECIONADO_NOME
    try:
        audio = pyaudio.PyAudio()
        if MICROFONE_SELECIONADO_NOME is None:
            MICROFONE_SELECIONADO_INDEX, MICROFONE_SELECIONADO_NOME = abrir_janela_selecao_microfone()

        open_kwargs = {
            "format": FORMAT,
            "channels": CHANNELS,
            "rate": RATE,
            "input": True,
            "frames_per_buffer": CHUNK
        }
        if MICROFONE_SELECIONADO_INDEX is not None:
            open_kwargs["input_device_index"] = MICROFONE_SELECIONADO_INDEX

        try:
            stream = audio.open(**open_kwargs)
        except Exception as e:
            print_log(f"Aviso ({MICROFONE_SELECIONADO_NOME}): {e}. Tentando entrada padrão...", "warning")
            stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        indicador = IndicadorGravacao()
        frames = []
        print_msg_start_gravar = False
        try:
            while keyboard.is_pressed("space"):
                if not print_msg_start_gravar:
                    indicador.mostrar()
                    print("Gravando... Pressione e segure 'Espaço'.")
                    print_msg_start_gravar = True

                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
        except Exception as e:
            print(f"Erro durante a gravação: {e}")
        finally:
            indicador.fechar()
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