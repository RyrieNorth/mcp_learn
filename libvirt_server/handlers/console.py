from utils.libvirt_server import LibvirtServer

def handle_console(args):
    server = LibvirtServer()
    server.console.connect(args.vm)