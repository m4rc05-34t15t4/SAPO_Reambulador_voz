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
    global PORTA_COM
    if PORTA_COM:
        return PORTA_COM
    try:
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        ports = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6"]

    for p in ports:
        try:
            with serial.Serial(p, BAUD_RATE, timeout=0.2) as ser:
                for _ in range(5):
                    line = ser.readline()
                    if line and line.decode("ascii", errors="ignore").strip().startswith('$GPRMC'):
                        PORTA_COM = p
                        return p
        except Exception:
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
    
    # Usar exclusivamente o GPS nativo conectado ao QGIS
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
    except Exception:
        pass

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
    def __init__(self, gps_position, is_screen_center=False):
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

        layout = QVBoxLayout()

        # Adicionar alerta visual se estiver utilizando o centro da tela
        if is_screen_center:
            alert_label = QLabel("⚠️ GPS Desconectado:\nUtilizando CENTRO DA TELA", self)
            alert_label.setWordWrap(True)
            alert_label.setMaximumWidth(310)
            alert_label.setStyleSheet("""
                QLabel {
                    background-color: #FFF3CD;
                    color: #856404;
                    border: 2px solid #FFEEBA;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            alert_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(alert_label)

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

def conectar_gpsgate_virtual(com_port=None, baud_rate=4800):
    return None

def processar_nmea_gprmc(sentence):
    return {}
    
def insert_point_from_gps_main(self):

    # Obtenção das coordenadas do GPS (com fallback instantâneo para centro da tela)
    d_gps = get_gps_position()
    is_screen_center = False

    if not d_gps:
        center_pt = get_center_tela()
        if not center_pt:
            QMessageBox.warning(None, 'Erro', 'Não foi possível obter a posição do GPS nem o centro da tela.')
            return
        d_gps = {
            "point": center_pt,
            "velocidade": 0.0,
            "direcao": 0.0,
            "elevacao": 0.0,
            "hdop": 0.0,
            "vdop": 0.0,
            "pdop": 0.0,
            "satelites_usados": 0,
            "satelites_visiveis": 0,
            "data_hora_utc": ""
        }
        is_screen_center = True

    gps_position = d_gps["point"]

    # Abrir diálogo para inserir descrição e coordenadas com alerta visual caso seja centro da tela
    dialog = CoordinatesInputDialog(gps_position, is_screen_center=is_screen_center)
    if dialog.exec_() == QDialog.Accepted:
        description = dialog.description.text()
        # Pegar as coordenadas do campo combinado
        modified_coordinates = dialog.get_coordinates()
        if modified_coordinates:
            d_gps["point"] = modified_coordinates
            add_point_feature(self, description, d_gps)
            # Abrir ferramenta de aquisição de ponto
            activate_point_tool(self)