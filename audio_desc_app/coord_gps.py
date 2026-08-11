from util import *
import serial

def converter_nos_km(nos):
    return float(nos) * 1.852

def verificar_porta_com():
    try:
        import serial.tools.list_ports
        portas = [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        portas = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6']
    for p in portas:
        try:
            with serial.Serial(p, 4800, timeout=0.2) as ser:
                for _ in range(5):
                    line = ser.readline()
                    if line and line.decode("ascii", errors="ignore").strip().startswith('$GPRMC'):
                        print_log(f"GPS conectado na Porta: {p}", "info")
                        return p
        except Exception:
            pass
    return None

def conectar_gpsgate_virtual(com_port="COM3", baud_rate=4800):
    """
    Conecta ao GpsGate Directed usando a porta COM virtual e captura sentenças NMEA.
    Exibe latitude, longitude, status, velocidade e direção.
    """
    try:
        with serial.Serial(com_port, baud_rate, timeout=0.2) as ser:
            dados = {}
            for _ in range(10):
                line = ser.readline()
                if line:
                    try:
                        sentence = line.decode("ascii", errors="ignore").strip()
                        if sentence.startswith('$GPRMC'):
                            dados = processar_nmea_gprmc(sentence)
                            if "latitude" in dados and "longitude" in dados:
                                return dados
                    except Exception:
                        pass
            return dados if ("latitude" in dados and "longitude" in dados) else None
    except Exception as e:
        print_log(f"Erro ao conectar GPS à porta {com_port}", "danger")

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
        print(f"Erro ao obter dados da senteça {sentence}, {e}")
        return {}

if __name__ == "__main__":
    PORTA = verificar_porta_com()
    if not PORTA:
        print('Erro na porta')
    else:
        conectar_gpsgate_virtual(com_port="COM2", baud_rate=4800)  # Substitua COM3 pela sua porta COM virtual
