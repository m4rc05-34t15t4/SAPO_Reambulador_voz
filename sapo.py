import os
import sys
import subprocess
from PyQt5.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.PyQt.QtGui import QIcon

# Caminho da pasta de libs dentro do plugin
plugin_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(plugin_dir))
libs_path = os.path.join(plugin_dir, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

import importlib
import modulos.utilidades
import modulos.desc_gps_app
import modulos.audio_desc_app

importlib.reload(modulos.utilidades)
importlib.reload(modulos.desc_gps_app)
importlib.reload(modulos.audio_desc_app)

from modulos.utilidades import *
from modulos.desc_gps_app import * 
from modulos.audio_desc_app import * 

"""
def carregar_modulo(arquivo):
    modulo_path = os.path.join(os.path.dirname(__file__), arquivo)  # Caminho completo do módulo
    spec = importlib.util.spec_from_file_location("modulo_extra", modulo_path)
    modulo_extra = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo_extra)
    # Importa tudo para o escopo atual (equivalente a `from modulo_extra import *`)
    globals().update({name: getattr(modulo_extra, name) for name in dir(modulo_extra) if not name.startswith("_")})
    return modulo_extra

#carregar_modulo("modulos/utilidades.py")
#carregar_modulo("modulos/desc_gps_app.py")
#carregar_modulo("modulos/audio_desc_app.py")
"""

class Sapo:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Criar ações (botões) na barra de ferramentas
        self.logo_app = None
        self.play_action = None
        self.start_app_desc_app = None
        self.desc_gps = None
        self.gps_layer = None
        self.toolbar = None  # Definir a toolbar personalizada
        self.selection_tool = None

    def initGui(self):
        """Inicializa o plugin e adiciona os botões à barra de ferramentas."""
        
        # 🔍 PROCURA se a toolbar "Sapo Plugin" já existe
        for tb in self.iface.mainWindow().findChildren(QToolBar):
            if tb.windowTitle() == "Sapo Plugin":
                self.toolbar = tb
                break

        # 🟢 Se não existe, cria
        if not self.toolbar:
            self.toolbar = QToolBar("Sapo Plugin")
            self.toolbar.setStyleSheet("""
                QToolBar {
                    background-color: #90EE90;
                    border: 2px solid #32CD32;
                    padding: 5px;
                }
            """)
            self.iface.addToolBar(self.toolbar) # Adiciona a toolbar personalizada ao QGIS


        # Criar botão para desc gps app
        icon_desc_gps = os.path.join(self.plugin_dir, 'icons', 'sapo_falando.png')
        self.desc_gps = QAction(QIcon(icon_desc_gps), "Inserir Ponto Descrição", self.iface.mainWindow())
        self.desc_gps.triggered.connect(self.insert_point_from_gps)
        self.toolbar.addAction(self.desc_gps)

        # Criar botão para tocar start app audio descrição
        icon_play = os.path.join(self.plugin_dir, 'icons', 'wave-sound.png')
        self.start_app_desc_app = QAction(QIcon(icon_play), "Start App Audio Descrição", self.iface.mainWindow())
        self.start_app_desc_app.triggered.connect(self.start_audio_desc_app)
        self.toolbar.addAction(self.start_app_desc_app)

        # Criar botão para tocar áudio
        icon_play = os.path.join(self.plugin_dir, 'icons', 'sapo_fone.png')
        self.play_action = QAction(QIcon(icon_play), "Play Áudio Descrição", self.iface.mainWindow())
        self.play_action.triggered.connect(self.play_audio)
        self.toolbar.addAction(self.play_action)

        # Iniciar timer para exportar GPS para JSON (1 segundo)
        from PyQt5.QtCore import QTimer
        self.gps_timer = QTimer()
        self.gps_timer.timeout.connect(self.update_gps_json)
        self.gps_timer.start(1000)

        # Configurar observador automático de arquivo (QFileSystemWatcher) para recarregar Pontos_Audio em tempo real
        self.setup_audio_watcher()

    def setup_audio_watcher(self):
        try:
            from PyQt5.QtCore import QFileSystemWatcher
            geojson_dir = os.path.join(self.plugin_dir, "geojson")
            if not os.path.exists(geojson_dir):
                os.makedirs(geojson_dir)
            audio_geojson = os.path.join(geojson_dir, "dados_audio.geojson")
            
            self.audio_watcher = QFileSystemWatcher()
            self.audio_watcher.addPath(geojson_dir)
            if os.path.exists(audio_geojson):
                self.audio_watcher.addPath(audio_geojson)
                
            self.audio_watcher.directoryChanged.connect(self.reload_audio_layer)
            self.audio_watcher.fileChanged.connect(self.reload_audio_layer)
        except Exception:
            pass

    def reload_audio_layer(self, path=None):
        try:
            layer_name = "Pontos_Audio"
            geojson_path = os.path.join(self.plugin_dir, "geojson", "dados_audio.geojson")
            if not os.path.exists(geojson_path):
                return

            layers = QgsProject.instance().mapLayersByName(layer_name)
            if not layers:
                # Se a camada não estiver no mapa, não forçamos recarga automática se o usuário não a carregou
                return

            from qgis.PyQt.QtXml import QDomDocument
            style_doc = QDomDocument()
            has_style = False
            show_count = True
            
            for l in layers:
                node = QgsProject.instance().layerTreeRoot().findLayer(l.id())
                if node:
                    show_count = bool(node.customProperty("showFeatureCount", True))
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

            # Re-adicionar arquivo ao watcher caso tenha sido sobrescrito
            if hasattr(self, 'audio_watcher') and os.path.exists(geojson_path):
                if geojson_path not in self.audio_watcher.files():
                    self.audio_watcher.addPath(geojson_path)
        except Exception:
            pass

    def unload(self):
        """Remove os botões da barra de ferramentas ao desinstalar o plugin."""
        try:
            if hasattr(self, 'gps_timer') and self.gps_timer:
                self.gps_timer.stop()
            # Remover ações da toolbar
            if self.logo_app:
                self.toolbar.removeAction(self.logo_app)
            if self.desc_gps:
                self.toolbar.removeAction(self.desc_gps)
            if self.play_action:
                self.toolbar.removeAction(self.play_action)
            if self.start_app_desc_app:
                self.toolbar.removeAction(self.start_app_desc_app)

            # Remover a toolbar personalizada, se aplicável
            if self.toolbar:
                self.iface.mainWindow().removeToolBar(self.toolbar)  # Remove do QGIS
                self.toolbar.deleteLater()  # Libera memória 
        except RuntimeError:
            # Ocorre quando a toolbar já foi destruída pelo C++ (comum ao usar o Plugin Reloader)
            pass
    
    #funcoes
    
    def update_gps_json(self):
        try:
            import json
            d_gps = get_gps_position()
            if d_gps and "point" in d_gps:
                data = {
                    "longitude": d_gps["point"].x(),
                    "latitude": d_gps["point"].y(),
                    "speed": d_gps.get("velocidade", 0.0),
                    "course": d_gps.get("direcao", 0.0),
                    "elevacao": d_gps.get("elevacao", 0.0),
                    "hdop": d_gps.get("hdop", 0.0),
                    "vdop": d_gps.get("vdop", 0.0),
                    "pdop": d_gps.get("pdop", 0.0),
                    "satelites_usados": d_gps.get("satelites_usados", 0),
                    "satelites_visiveis": d_gps.get("satelites_visiveis", 0),
                    "data_hora_utc": d_gps.get("data_hora_utc", "")
                }
                json_path = os.path.join(self.plugin_dir, "current_gps.json")
                tmp_path = json_path + ".tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.replace(tmp_path, json_path)
        except Exception:
            pass
    
    def play_audio(self):
        play_audio_main(self)

    def insert_point_from_gps(self):
        insert_point_from_gps_main(self)

    def start_audio_desc_app(self):
        try:
            programa = "sapo_audio_desc_point.exe"
            if is_program_running_windows(programa):
                QMessageBox.information(None, "Info", f"programa está em execução!.")
            else:
                caminho_exe = r"\sapo_audio_desc_point\sapo_audio_desc_point.exe"
                subprocess.Popen(plugin_dir+caminho_exe)
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"{str(e)}.")
