def classFactory(iface):
    from .sapo import Sapo
    return Sapo(iface)