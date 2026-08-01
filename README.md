# 🐸 SAPO - Reambulação e Descrição por Voz para QGIS

O **SAPO (Sistema de Apoio e Reambulação Operacional)** é um plugin desenvolvido para o **QGIS** que combina a coleta de dados de campo via **GPS** com a gravação e transcrição automática de áudio por voz utilizando **Inteligência Artificial (OpenAI Whisper)**.

O sistema gera e sincroniza em tempo real camadas geográficas em formato **GeoJSON**, armazenando metadados completos de GPS e transcrições de áudio.

---

## 🌟 Funcionalidades Principais

- 🎙️ **Gravação por Voz Inteligente**: Segure a tecla `Espaço` no aplicativo auxiliar para gravar descrições de campo por áudio.
- 🤖 **Transcrição Automática Offline**: Transcrição de áudio via **OpenAI Whisper** local sem necessidade de conexão com a internet.
- 📍 **Captura Completa de GPS**: Salva coordenadas (`Latitude`, `Longitude`), `Direção`, `Velocidade`, `Elevação`, `HDOP`, `VDOP`, `PDOP`, `Satélites Usados/Visíveis` e `Data/Hora UTC`.
- 🗺️ **Sincronização em Tempo Real**: Atualização automática da camada `Pontos_Audio` no QGIS via observador de arquivos (`QFileSystemWatcher`) assim que o áudio é salvo.
- 🎨 **Preservação de Estilo e Contagem**: Mantém a simbologia visual configurada no QGIS e a contagem de elementos (`[N]`) ao atualizar as camadas.
- 📄 **Estrutura 100% GeoJSON**: Padrão aberto, leve e totalmente integrado.

---

## 📁 Estrutura do Repositório

```text
SAPO_Reambulador_voz/
├── sapo.py                      # Arquivo principal do plugin QGIS
├── metadata.txt                 # Metadados do plugin QGIS
├── modulos/                     # Módulos internos do plugin (Interface, GPS, Utilitários)
│   ├── desc_gps_app.py
│   ├── audio_desc_app.py
│   └── utilidades.py
├── audio_desc_app/              # Aplicação Standalone de Áudio/Whisper (Python / .exe)
│   ├── main.py
│   ├── gravar_audio.py
│   ├── transcrever_audio_whisper.py
│   ├── gravar_geojson.py
│   ├── configurar_ambiente_dev.bat   # Script 1: Configura o ambiente virtual Python
│   ├── gerar_exe.bat                 # Script 2: Compila o executável (.exe)
│   └── requirements.txt
├── icons/                       # Ícones e recursos visuais do plugin
└── libs/                        # Dependências auxiliares do plugin
```

---

## 🛠️ Guia de Instalação e Compilação

Para configurar o ambiente de desenvolvimento e gerar o executável do aplicativo de voz (`sapo_audio_desc_point.exe`), siga os passos abaixo:

### **Pré-requisitos**
- Python 3.10 ou superior instalado no Windows.
- QGIS 3.x instalado.

---

### 1️⃣ **Passo 1: Configurar o Ambiente Virtual**

Abra o terminal ou navegue até a pasta `audio_desc_app` e execute o arquivo `configurar_ambiente_dev.bat`:

```cmd
cd audio_desc_app
configurar_ambiente_dev.bat
```

> **O que este script faz?**
> - Cria a pasta do ambiente virtual local `.venv_dev`.
> - Atualiza o `pip`.
> - Instala todas as bibliotecas necessárias listadas no `requirements.txt` (Torch, PyAudio, OpenAI-Whisper, PyInstaller, Shapely, etc.).

---

### 2️⃣ **Passo 2: Gerar o Executável (.exe)**

Após a conclusão da configuração do ambiente, execute o arquivo `gerar_exe.bat`:

```cmd
gerar_exe.bat
```

> **O que este script faz?**
> - Encerra automaticamente qualquer instância antiga do aplicativo rodando em segundo plano.
> - Compila o aplicativo utilizando o PyInstaller de forma limpa.
> - Empacota a IA Whisper e o motor FFmpeg.
> - Gera o executável final `sapo_audio_desc_point.exe` e salva na pasta principal do plugin.

---

## 🚀 Como Usar no QGIS

1. **Instalação do Plugin:**
   Copie a pasta `SAPO_Reambulador_voz` para o diretório de plugins do seu perfil do QGIS:
   `C:\Users\<SeuUsuario>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`

2. **Ativação:**
   Abra o QGIS, vá em **Complementos > Gerenciar e Instalar Complementos** e ative o **Sapo Plugin**.

3. **Inserir Ponto Descrição:**
   Clique no botão **"Inserir Ponto Descrição"** na barra de ferramentas para capturar o ponto GPS e abrir a janela de inserção de texto.

4. **Gravação de Áudio por Voz:**
   Clique no botão **"Start App Audio Descrição"** para abrir a janela do gravador. Segure a tecla `Espaço` para gravar o áudio e solte para transcrever. O ponto de áudio aparecerá automaticamente no mapa do QGIS com a transcrição!

---

## 📜 Licença

Desenvolvido para reambulação e coleta de dados geográficos com tecnologia de IA.
