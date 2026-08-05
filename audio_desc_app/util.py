from colorama import init, Fore, Back, Style

# Inicializa o colorama (necessário para Windows)
init()
"""
print(Fore.RED + "Este texto é vermelho")
print(Fore.GREEN + "Este texto é verde")
print(Fore.BLUE + "Este texto é azul")
print(Back.YELLOW + "Este texto tem fundo amarelo" + Style.RESET_ALL)
print(Style.BRIGHT + "Este texto está em negrito" + Style.RESET_ALL)
print(Style.DIM + "Este texto está em estilo mais apagado" + Style.RESET_ALL)
print("Texto normal novamente")
print(Style.RESET_ALL)# Encerrando com reset (garante que nada fique "preso" no estado anterior)
"""

blue_light = '\033[94m'
pink_light = '\033[38;5;218m'  # Rosa claro suave em ANSI

def print_log(msg, color="sucess", negrito=False, reset=Style.RESET_ALL):

    cor = Fore.GREEN
    if color == "danger":
        cor = Fore.RED
    elif color == "alert":
        cor = Fore.YELLOW
    elif color == "info":
        cor = blue_light
    elif color == "pink" or color == "transcricao":
        cor = pink_light
    elif color == "sucess":
        cor = Fore.GREEN

    N = Style.BRIGHT if negrito else ""

    print(cor+N+str(msg)+reset)