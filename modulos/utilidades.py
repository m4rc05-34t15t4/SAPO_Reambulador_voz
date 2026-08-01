import json
import sqlite3
import os
import sys
import subprocess
import importlib
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QMessageBox

def is_program_running_windows(program_name):
    try:
        output = subprocess.check_output("tasklist", universal_newlines=True, encoding="cp1252")
        return program_name.lower() in output.lower()
    except subprocess.CalledProcessError:
        return False


def converter_nos_km(nos):
    return float(nos) * 1.852

def ler_arquivo_json(caminho_arquivo):
    """Lê um arquivo JSON e retorna os dados como um dicionário."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
        return dados
    except FileNotFoundError:
        QMessageBox.warning(None, 'Erro', f"O arquivo {caminho_arquivo} não foi encontrado.")
    except json.JSONDecodeError:
        QMessageBox.warning(None, 'Erro', f"Erro: O arquivo {caminho_arquivo} não está em um formato JSON válido.")
    except Exception as e:
        QMessageBox.warning(None, 'Erro', f"Erro inesperado: {e}")
