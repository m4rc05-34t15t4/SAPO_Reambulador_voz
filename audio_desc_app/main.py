from util import *
from coord_gps import *
from gravar_audio import *
from transcrever_audio_whisper import * 
from gravar_geojson import * 
from datetime import datetime
import os

PORT_COM = "COM2"
import sys

if getattr(sys, 'frozen', False):
    # Se estiver rodando como .exe (compilado pelo PyInstaller)
    DIRETORIO_ATUAL = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como script .py normal
    DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

DIRETORIO_ANTERIOR = os.path.dirname(DIRETORIO_ATUAL)
AUDIO_PATH = DIRETORIO_ANTERIOR+"/audios/"
PATH_GEOJSON = DIRETORIO_ANTERIOR+"/geojson"
ARQ_GEOJSON = "dados_audio.geojson"
TABLE_NAME = "Pontos_Audio"
VERSAO = "1.0.0"
#PATH_SQLITE = DIRETORIO_ANTERIOR+"/sqlite"
#AUDIO_PATH = "../audios/"
#PATH_SQLITE = "../sqlite"
#ARQ_SQLITE = "dados_audio.sqlite"

if __name__ == "__main__":
    try:
        #print(f"Pressione e segure a tecla 'Espaço' por {TEMPO_MIN_SEGUNDOS} segundos para começar a gravar.")
        #PORT_COM = verificar_porta_com()
        if not PORT_COM:
            raise Exception(f"Erro ao verificar Porta GPS")
        elif not adicionar_ffmpeg_ao_path():
            raise Exception(f"Erro ao configurar o FFmpeg.")
        else:
            print_log(f"Versão: {VERSAO}", "info")
            print_log(f"Pressione e segure a tecla 'Espaço' para começar a gravar.\nSolte a tecla para salvar o áudio.", "alert")
            while True:
                # Aguarda o usuário pressionar a tecla espaço
                keyboard.wait("space")
                press_time = time.time()  # Registra o tempo inicial de pressionamento

                # Verifica se a tecla permanece pressionada por * segundos
                while keyboard.is_pressed("space"):
                    if time.time() - press_time >= 0.5:
                        #print("Tempo atingido, iniciando gravação...")
                        dados_gps = None
                        json_path = os.path.join(DIRETORIO_ANTERIOR, "current_gps.json")
                        try:
                            import json
                            if os.path.exists(json_path):
                                with open(json_path, "r", encoding="utf-8") as f:
                                    dados_gps = json.load(f)
                        except Exception as e:
                            print_log(f"Erro ao ler JSON: {e}", "warning")

                        if not dados_gps or 'longitude' not in dados_gps: 
                            print_log(f"Dados GPS de Teste: ", "warning")
                            dados_gps = {"longitude" : -46.6388, "latitude" : -23.5489, "speed" : 0.0, "course" : 0.0}
                        
                        if dados_gps and 'longitude' in dados_gps:
                            print_log(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "info", negrito=True)
                            frames, audio = record_audio() #Começa a ouvir enquanto o espaço é pressionado
                            if frames != None and audio != None:
                                filename = save_audio(frames, audio) # Salva o áudio ao soltar a tecla
                                if filename and ".wav" in filename:
                                    
                                    transcription = transcribe_audio_whisper(AUDIO_PATH+filename)
                                    print_log(f"Transcrição: {transcription}", "info")
                                    
                                    longitude = float(dados_gps['longitude'])
                                    latitude = float(dados_gps['latitude'])
                                    veloc = float(dados_gps.get('speed', 0.0))
                                    direc = float(dados_gps.get('course', 0.0))
                                    
                                    elevacao = float(dados_gps.get('elevacao', 0.0))
                                    hdop = float(dados_gps.get('hdop', 0.0))
                                    vdop = float(dados_gps.get('vdop', 0.0))
                                    pdop = float(dados_gps.get('pdop', 0.0))
                                    try:
                                        satelites_usados = int(dados_gps.get('satelites_usados', 0))
                                    except TypeError:
                                        satelites_usados = len(dados_gps.get('satelites_usados', []))
                                    try:
                                        satelites_visiveis = int(dados_gps.get('satelites_visiveis', 0))
                                    except TypeError:
                                        satelites_visiveis = len(dados_gps.get('satelites_visiveis', []))
                                    data_hora_utc = str(dados_gps.get('data_hora_utc', ""))
                                    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                    print_log(f"Coord Lat, Long: {latitude}, {longitude} | Direção: {direc} | Veloc: {veloc} | Elev: {elevacao} | Satélites: {satelites_usados}/{satelites_visiveis}", "info")
                                    
                                    observacao = ""

                                    geojson_file = PATH_GEOJSON+"/"+ARQ_GEOJSON
                                    if not os.path.exists(geojson_file):
                                        criar_geojson(geojson_file, TABLE_NAME)
                                    
                                    adicionar_ponto_geojson(geojson_file, filename, transcription, latitude, longitude, direc, veloc, observacao, AUDIO_PATH+filename, elevacao, hdop, vdop, pdop, satelites_usados, satelites_visiveis, data_hora_utc, criado_em)

                        print_log("-----------------", "alert")
                        break
                """
                else:
                    print(f"Tecla liberada antes de atingir {TEMPO_MIN_SEGUNDOS} segundos. Nenhuma gravação realizada.")
                """
    except Exception as e:
        print_log(f"Erro: {e}", "danger")
        input("Pressione Enter para sair...")
