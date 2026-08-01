import os
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QMessageBox

def carregar_camada_qgis(path_arquivo, layer_name):
    # Verifica se a camada já está carregada
    for layer in QgsProject.instance().mapLayers().values():
        if layer.name() == layer_name:
            QMessageBox.warning(None, "Alerta", f"A camada {layer_name} já está carregada.")
            return layer

    # Cria a camada do GeoJSON
    layer = QgsVectorLayer(path_arquivo, layer_name, "ogr")

    # Verifica se a camada foi carregada corretamente
    if not layer.isValid():
        QMessageBox.critical(None, "Erro", f"Erro ao carregar a camada {layer_name}.")
        return None

    # Adiciona a camada ao projeto
    QgsProject.instance().addMapLayer(layer)
    QMessageBox.information(None, "Info", f"Camada {layer_name} carregada com sucesso!")
    return layer

"""Executa o áudio do ponto selecionado."""
def play_audio_main(self):
    layer_name = "Pontos_Audio"
    
    # Try to find the layer by name in QGIS
    layers = QgsProject.instance().mapLayersByName(layer_name)
    if not layers:
        geojson_path = os.path.join(self.plugin_dir, "geojson/dados_audio.geojson")
        layer = carregar_camada_qgis(geojson_path, layer_name)
        if not layer:
            QMessageBox.critical(None, "Erro", f"A camada '{layer_name}' não foi encontrada. Tente Novamente ou Carregue manualmente: {geojson_path}.")
            return
    else:
        layer = layers[0]
    selected_features = layer.selectedFeatures()
    if not selected_features:
        QMessageBox.warning(None, "Atenção", "Nenhum elemento selecionado.")
        return

    feature = selected_features[0]
    if "nome_audio" not in feature.fields().names():
        QMessageBox.critical(None, "Erro", "A coluna 'nome_audio' não existe na camada.")
        return

    audio_name = feature["nome_audio"]
    if not audio_name:
        QMessageBox.warning(None, "Atenção", "O elemento selecionado não possui áudio associado.")
        return

    audio_directory = os.path.join(self.plugin_dir, "audios")
    if not audio_directory:
        QMessageBox.critical(None, "Erro", "O diretório de áudio não está configurado. Configure-o primeiro.")
        return

    audio_path = os.path.join(audio_directory, audio_name)
    if not os.path.exists(audio_path):
        QMessageBox.critical(None, "Erro", f"O arquivo de áudio '{audio_path}' não foi encontrado.")
        return

    # Executar o áudio com Windows Media Player
    os.system(f'start wmplayer "{audio_path}"')