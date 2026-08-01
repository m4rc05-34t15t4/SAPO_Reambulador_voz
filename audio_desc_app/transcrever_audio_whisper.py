import os
import whisper
import sys
import shutil

os.environ["XDG_CACHE_HOME"] = "/whisper"

def get_ffmpeg_path():
    # Verifica se o script está rodando a partir de um executável gerado pelo PyInstaller
    if getattr(sys, 'frozen', False):
        # Caminho para o FFmpeg dentro do pacote gerado pelo PyInstaller
        base_path = sys._MEIPASS
    else:
        # Caminho do FFmpeg durante o desenvolvimento
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Defina o caminho completo para o FFmpeg
    ffmpeg_folder = os.path.join(base_path, 'ffmpeg', 'bin')
    ffmpeg_bin = os.path.join(ffmpeg_folder, 'ffmpeg.exe') if sys.platform == 'win32' else os.path.join(ffmpeg_folder, 'ffmpeg')
    
    return ffmpeg_bin

def adicionar_ffmpeg_ao_path():
    ffmpeg_bin = get_ffmpeg_path()
    if not os.path.exists(ffmpeg_bin):
        print("Erro: FFmpeg não encontrado na pasta do programa.")
        return False
    
    # Adiciona o caminho do FFmpeg à variável de ambiente PATH
    current_path = os.getenv('PATH')
    os.environ['PATH'] = f"{current_path}{os.pathsep}{os.path.dirname(ffmpeg_bin)}"
    
    # Verificar se o FFmpeg foi corretamente adicionado ao PATH
    if shutil.which("ffmpeg"):
        print("FFmpeg está pronto para ser usado.")
    else:
        print("Erro ao adicionar FFmpeg ao PATH.")
        return False
    
    return True

def get_model_path():                                                                                 
    """Determina o caminho do modelo baseado no ambiente."""
    if getattr(sys, 'frozen', False):  # Se rodando como executável (PyInstaller)
        model_path = os.path.join(sys._MEIPASS, "whisper", "small.pt")
    else:  # Ambiente de desenvolvimento
        model_path = None  # Usa o cache padrão do Whisper

    return model_path

def transcribe_audio_whisper(audio_file_path):
    # Carrega o modelo (use "small" para velocidade, "large" para mais precisão)
    model = None
    try:
        model_path = get_model_path()
        
        if model_path and os.path.exists(model_path):
            model = whisper.load_model(model_path)  # Usa o modelo salvo
        else:
            model = whisper.load_model("small", download_root=model_path)
    except Exception as e:
        print(f"Erro: {e}")
        model = whisper.load_model("small", download_root=None)
    
    # Transcreve o áudio
    result = model.transcribe(audio_file_path, language="pt")
    # Retorna o texto transcrito
    return result['text']

# Exemplo de uso
if __name__ == "__main__":
    #audio_path = "C:/Marcos_Batista/python/audios/audio_20250117_095912_covertido.wav"
    audio_path = r"C:\Marcos_Batista\python\reambulacao_audio_desc/audios/audio_20250123_074114.wav"
    transcription = transcribe_audio_whisper(audio_path)
    print(f"Texto transcrito: {transcription}")
