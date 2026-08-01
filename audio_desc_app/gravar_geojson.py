from util import * 
import os
import uuid
import json
from shapely.geometry import mapping, Point

def criar_geojson(path_geojson, tabela_nome):
    """
    Cria um arquivo GeoJSON vazio com estrutura inicial.
    """
    if not os.path.exists(os.path.dirname(path_geojson)):
        os.makedirs(os.path.dirname(path_geojson))

    if not os.path.exists(path_geojson):
        geojson_data = {
            "type": "FeatureCollection",
            "name": tabela_nome,
            "crs": {
                "type": "name",
                "properties": {
                    "name": "EPSG:4674"
                }
            },
            "features": []
        }

        with open(path_geojson, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=4)
        print_log(f"GeoJSON criado em: {path_geojson}")
    #else:
    #    print_log(f"O arquivo GeoJSON '{path_geojson}' já existe.")

def adicionar_ponto_geojson(path_geojson, nome_audio, transcricao, latitude, longitude, direcao, velocidade, observacao, audio_path, elevacao=0.0, hdop=0.0, vdop=0.0, pdop=0.0, satelites_usados=0, satelites_visiveis=0, data_hora_utc="", criado_em=""):
    """
    Adiciona um ponto com os atributos especificados a um arquivo GeoJSON.
    """
    if not os.path.exists(path_geojson):
        raise FileNotFoundError(f"GeoJSON não encontrado em: {path_geojson}")

    with open(path_geojson, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    # Criar ID único
    id_ponto = str(uuid.uuid4())

    feature = {
        "type": "Feature",
        "geometry": mapping(Point(float(longitude), float(latitude))),
        "properties": {
            "id": id_ponto,
            "nome_audio": nome_audio,
            "transcricao": transcricao,
            "observacao": observacao,
            "direcao": direcao,
            "velocidade": velocidade,
            "elevacao": elevacao,
            "hdop": hdop,
            "vdop": vdop,
            "pdop": pdop,
            "satelites_usados": satelites_usados,
            "satelites_visiveis": satelites_visiveis,
            "data_hora_utc": data_hora_utc,
            "criado_em": criado_em,
            "audio_path": audio_path  # Guardar caminho em vez de BLOB
        }
    }

    geojson_data["features"].append(feature)

    with open(path_geojson, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=4)

    print_log(f"Ponto adicionado ao GeoJSON: ID={id_ponto}")
    

# Exemplo de uso
if __name__ == "__main__":
    nome_geojson = "dados_audio.geojson"
    pasta_geojson = "../geojson"
    path_geojson = os.path.join(pasta_geojson, nome_geojson)
    tabela_nome = "Pontos_Audio"

    nome_audio = "audio_20250210_114110.wav"
    transcricao = "Exemplo de transcrição do áudio."
    latitude = -23.5489
    longitude = -46.6388
    observacao = "Ponto de teste com áudio."
    audio_path = "../audios/audio_20250210_114110.wav"
    orientacao = 0.0
    velocidade = 0.0

    criar_geojson(path_geojson, tabela_nome)
    adicionar_ponto_geojson(path_geojson, nome_audio, transcricao, latitude, longitude, orientacao, velocidade, observacao, audio_path)
