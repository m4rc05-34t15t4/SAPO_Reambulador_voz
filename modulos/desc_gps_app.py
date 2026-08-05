CAMADA_PONTO_DESC_TEXT = 'aux_reambulacao_p'
PORTA_COM = None
BAUD_RATE = 4800

import os
import sys
import serial
import uuid
from pathlib import Path
from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsPointXY
from PyQt5.QtGui import QMovie
from qgis.PyQt.QtWidgets import QMessageBox, QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt, QSize
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QDialog, QVBoxLayout
from qgis.gui import QgsMapToolEmitPoint, QgsMapToolIdentify

sys.path.append(Path(__file__).parent.parent)
from modulos.utilidades import *

def verificar_porta_com():
    portas = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6"]
    for p in portas:
        try:
            with serial.Serial(p, BAUD_RATE, timeout=1) as ser:
                if ser.readline().decode("ascii", errors="ignore").strip().startswith('$GPRMC'):
                    return p
        except Exception as e:
            pass
    return None

def get_center_tela():
    # Obter a instância atual do mapa
    canvas = iface.mapCanvas()
    # Obter a extensão atual do mapa
    extent = canvas.extent()
    # Calcular o centro da extensão
    center_x = (extent.xMinimum() + extent.xMaximum()) / 2
    center_y = (extent.yMinimum() + extent.yMaximum()) / 2

    return QgsPointXY(center_x, center_y)

def get_gps_position():
    from qgis.core import QgsApplication
    
    # 1. Tentar pegar do GPS nativo conectado ao QGIS (Garmin Spanner, etc)
    try:
        registry = QgsApplication.gpsConnectionRegistry()
        connections = registry.connectionList()
        if connections:
            conn = connections[0]
            info = conn.currentGPSInformation()
            
            # Verifica se o GPS está enviando um sinal válido
            if info.isValid():
                gps_data = {
                    "point": QgsPointXY(info.longitude, info.latitude),
                    "velocidade": getattr(info, 'speed', 0.0),
                    "direcao": getattr(info, 'direction', 0.0),
                    "elevacao": getattr(info, 'elevation', 0.0),
                    "hdop": getattr(info, 'hdop', 0.0),
                    "vdop": getattr(info, 'vdop', 0.0),
                    "pdop": getattr(info, 'pdop', 0.0),
                    "satelites_usados": len(getattr(info, 'satellitesUsed', []) or []),
                    "satelites_visiveis": len(getattr(info, 'satellitesInView', []) or [])
                }
                
                utc_dt = getattr(info, 'utcDateTime', None)
                if utc_dt and hasattr(utc_dt, 'isValid') and utc_dt.isValid():
                    gps_data["data_hora_utc"] = utc_dt.toString("yyyy-MM-dd HH:mm:ss")
                else:
                    gps_data["data_hora_utc"] = ""
                    
                return gps_data
    except Exception as e:
        pass # Se falhar, segue para o método antigo (porta serial direta)

    # 2. Fallback para o método antigo (GpsGate virtual via Porta COM)
    dados_gps = conectar_gpsgate_virtual(com_port=PORTA_COM, baud_rate=4800) 
    if(dados_gps and 'latitude' in dados_gps and 'longitude' in dados_gps):
        longitude = float(dados_gps['longitude'])
        latitude = float(dados_gps['latitude'])
        if dados_gps['long_dir'] == "W":
            longitude = -1 * longitude
        if dados_gps['lat_dir'] == "S":
            latitude = -1 * latitude
        veloc = converter_nos_km(dados_gps['speed'])
        direc = float(dados_gps['course'])
        
        return {
            "point": QgsPointXY(longitude, latitude),
            "velocidade": veloc,
            "direcao": direc,
            "elevacao": 0.0,
            "hdop": 0.0,
            "vdop": 0.0,
            "pdop": 0.0,
            "satelites_usados": 0,
            "satelites_visiveis": 0,
            "data_hora_utc": ""
        }
    else:
        return None

def add_point_feature(self, description, d_gps):
    import json
    import os
    import uuid
    from datetime import datetime
    from qgis.core import QgsProject, QgsVectorLayer

    layer_name = CAMADA_PONTO_DESC_TEXT
    geojson_dir = os.path.join(self.plugin_dir, "geojson")
    if not os.path.exists(geojson_dir):
        os.makedirs(geojson_dir)
        
    geojson_path = os.path.join(geojson_dir, layer_name + ".geojson")

    # Funções de higienização de valores
    def clean_float(val):
        if val is None or val == "" or val == "nan":
            return None
        try:
            import math
            f = float(val)
            return None if (math.isnan(f) or math.isinf(f)) else f
        except (ValueError, TypeError):
            return None

    def clean_int(val):
        if val is None or val == "":
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    # 1. Carrega ou inicializa a estrutura do GeoJSON
    if os.path.exists(geojson_path):
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
        except Exception:
            geojson_data = None
    else:
        geojson_data = None

    if not geojson_data or not isinstance(geojson_data, dict) or "features" not in geojson_data:
        geojson_data = {
            "type": "FeatureCollection",
            "name": layer_name,
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:EPSG::4674"
                }
            },
            "features": []
        }

    # 2. Coordenadas do ponto
    lon = float(d_gps["point"].x())
    lat = float(d_gps["point"].y())

    # 3. Monta a nova feature com TODAS as 12 propriedades explicitamente
    nova_feature = {
        "type": "Feature",
        "properties": {
            "id": str(uuid.uuid4()),
            "descricao": str(description),
            "direcao": clean_float(d_gps.get("direcao")),
            "velocidade": clean_float(d_gps.get("velocidade")),
            "elevacao": clean_float(d_gps.get("elevacao")),
            "hdop": clean_float(d_gps.get("hdop")),
            "vdop": clean_float(d_gps.get("vdop")),
            "pdop": clean_float(d_gps.get("pdop")),
            "satelites_usados": clean_int(d_gps.get("satelites_usados")),
            "satelites_visiveis": clean_int(d_gps.get("satelites_visiveis")),
            "data_hora_utc": str(d_gps.get("data_hora_utc", "") or ""),
            "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        }
    }

    geojson_data["features"].append(nova_feature)

    # 4. Salva no arquivo com indentação limpa
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=4)

    # 5. Gerenciamento no QGIS: Recarrega a camada preservando estilo (simbologia) e contagem de feições
    from qgis.PyQt.QtXml import QDomDocument
    
    existing_layers = QgsProject.instance().mapLayersByName(layer_name)
    show_count = True  # Ativado por padrão
    style_doc = QDomDocument()
    has_style = False

    for l in existing_layers:
        node = QgsProject.instance().layerTreeRoot().findLayer(l.id())
        if node:
            show_count = bool(node.customProperty("showFeatureCount", True))
        # Salva o estilo completo da camada (simbologia, cores, rótulos)
        l.exportNamedStyle(style_doc)
        has_style = True
        QgsProject.instance().removeMapLayer(l)
        
    layer = QgsVectorLayer(geojson_path, layer_name, "ogr")
    if layer.isValid():
        if has_style:
            layer.importNamedStyle(style_doc)
            layer.triggerRepaint()

        QgsProject.instance().addMapLayer(layer)
        layer_node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if layer_node:
            layer_node.setCustomProperty("showFeatureCount", show_count)

    try:
        self.activate_generic_selection_tool()
    except Exception:
        pass


def activate_generic_selection_tool(self):
    # Ativar a ferramenta de seleção genérica
    selection_tool = QgsMapToolIdentify(self.iface.mapCanvas())
    self.iface.mapCanvas().setMapTool(selection_tool)

def activate_point_tool(self):
    # Ativar a ferramenta de aquisição de ponto
    self.selection_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
    self.iface.mapCanvas().setMapTool(self.selection_tool)

class CoordinatesInputDialog(QDialog):
    def __init__(self, gps_position):
        super().__init__()
        self.setWindowTitle("Inserir Descrição e Coordenadas")

        estilo_input_text = """
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #4CAF50; /* Cor da borda */
                border-radius: 10px;
                background-color: #F0F0F0;
            }
            QLineEdit:focus {
                border: 2px solid #66AFE9; /* Cor da borda quando focado */
                background-color: #FFFFFF;
            }
        """
        
        self.description = QLineEdit(self)
        self.description.setPlaceholderText("Descrição")
        self.description.setStyleSheet(estilo_input_text)

        # Cria um campo para as coordenadas
        self.coordinates = QLineEdit(self)
        self.coordinates.setPlaceholderText("Coordenadas (longitude,latitude)")
        self.coordinates.setText(f"{gps_position.x()}, {gps_position.y()}")  # Preencher com coordenadas GPS
        self.coordinates.setStyleSheet(estilo_input_text)

        # Botão OK
        self.ok_button = QPushButton("OK", self)

        # Estilizar o botão com QSS
        self.ok_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: #4CAF50; /* Cor de fundo */
                border: none;
                padding: 10px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #45A049; /* Cor quando o mouse estiver sobre o botão */
            }
            QPushButton:pressed {
                background-color: #2E7D32; /* Cor quando o botão estiver pressionado */
            }
        """)

        self.ok_button.clicked.connect(self.accept)

        # Criar um diálogo personalizado
        dialog = QDialog()
        dialog.setWindowTitle("Inserir Descrição")
        layout = QVBoxLayout(dialog)

        # Adicionar GIF animado
        gif_label = QLabel()
        plugin_dir = os.path.dirname(__file__)
        gif = QMovie(os.path.join(plugin_dir, "../icons/sapo_reambulador_digitando_video.gif"))  # Certifique-se de ter um GIF na pasta do plugin
        gif_label.setMovie(gif)
    
        gif.setScaledSize(QSize(310, 310))
        gif_label.setFixedSize(310, 310)  # Ajuste o tamanho do GIF conforme necessário
        gif_label.setAlignment(Qt.AlignCenter)
        gif.start()
        
        layout.addWidget(gif_label)  
        layout.addWidget(self.description)
        layout.addWidget(self.coordinates)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_coordinates(self):
        text = self.coordinates.text()
        try:
            lon, lat = map(float, text.split(','))
            return QgsPointXY(lon, lat)
        except ValueError:
            QMessageBox.warning(None, 'Erro', 'Coordenadas inválidas. Formato esperado: longitude, latitude.', "danger")
            return None

def conectar_gpsgate_virtual(com_port="COM3", baud_rate=4800):
    """
    Conecta ao GpsGate Directed usando a porta COM virtual e captura sentenças NMEA.
    Exibe latitude, longitude, status, velocidade e direção.
    """
    if com_port == None:
        com_port = verificar_porta_com()
        if com_port == None:
            #QMessageBox.warning(None, 'Erro', f"Erro na porta {str(com_port)}", QMessageBox.Ok)
            return None
        else:
            PORTA_COM = com_port

    try:
        with serial.Serial(com_port, baud_rate, timeout=1) as ser:
            #print(f"Conectado ao GpsGate, porta {com_port}")
            dados = {}
            while not "latitude" in dados and not "longitude" in dados:
                line = ser.readline()
                if line:
                    try:
                        sentence = line.decode("ascii", errors="ignore").strip()
                        if sentence.startswith('$GPRMC'):
                            dados = processar_nmea_gprmc(sentence)
                    except UnicodeDecodeError:
                        QMessageBox.warning(None, 'Erro', "Erro ao decodificar os dados recebidos.", "danger")
                else:
                    QMessageBox.warning(None, 'Erro', "Sem dados recebidos. Verifique GPS", "danger")
            return dados
    except Exception as e:
        QMessageBox.warning(None, 'Erro', f"Erro ao conectar GPS à porta {com_port}", "danger")
    except KeyboardInterrupt:
        QMessageBox.warning(None, 'Erro', "Conexão encerrada pelo usuário.", "danger")

def processar_nmea_gprmc(sentence):
    """
    Processa a sentença GPRMC para extrair latitude, longitude, status, velocidade e curso.
    """
    # A sentença GPRMC tem o seguinte formato:
    # $GPRMC,123625,A,0800.2405,S,03451.5462,W,0.0,68.1,220125,22.2,W,A*01
    # $GPRMC,<hora>,<status>,<latitude>,<N/S>,<longitude>,<E/W>,<velocidade>,<curso>,<data>,<variação_magnética>,<direção_magnética>,<validade>*<checksum>
    try:
        parts = sentence.split(',')

        # Extração dos campos com base na posição
        parsed_data = {
            "type": parts[0],               # Tipo de sentença ($GPRMC)
            "time": parts[1],               # Horário UTC (HHMMSS)
            "status": parts[2],             # Status de navegação (A = ativo, V = inválido)
            "latitude": parts[3],           # Latitude (graus e minutos)
            "lat_dir": parts[4],            # Direção da latitude (N/S)
            "longitude": parts[5],          # Longitude (graus e minutos)
            "long_dir": parts[6],           # Direção da longitude (E/W)
            "speed": parts[7],              # Velocidade sobre o solo (nós)
            "course": parts[8],             # Rumo/direção (graus)
            "date": parts[9],               # Data (DDMMYY)
            "mag_var": parts[10],           # Variação magnética (graus)
            "mag_dir": parts[11],           # Direção da variação magnética (E/W)
            "checksum": parts[12]           # Checksum (*09 incluído)
        }
        #print(parsed_data)
        return parsed_data
    except Exception as e:
        QMessageBox.warning(None, 'Erro', f"Erro ao obter dados da senteça {sentence}, {e}")
        return {}
    
def insert_point_from_gps_main(self):

    # Obtenção das coordenadas do GPS
    d_gps = get_gps_position()
    
    if not d_gps:
        QMessageBox.warning(None, 'Erro', 'GPS não disponível ou não conectado.')
        return

    gps_position = d_gps["point"]

    # Abrir diálogo para inserir descrição e coordenadas
    dialog = CoordinatesInputDialog(gps_position)
    if dialog.exec_() == QDialog.Accepted:
        description = dialog.description.text()
        # Pegar as coordenadas do campo combinado
        modified_coordinates = dialog.get_coordinates()
        if modified_coordinates:
            d_gps["point"] = modified_coordinates
            add_point_feature(self, description, d_gps)
            # Abrir ferramenta de aquisição de ponto
            activate_point_tool(self)