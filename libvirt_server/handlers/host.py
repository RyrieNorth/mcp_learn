from pprint import pprint
from utils.libvirt_server import LibvirtServer

def handle_host_name(args):
    server = LibvirtServer()
    pprint(server.host.get_hostname())

def handle_host_cpu(args):
    server = LibvirtServer()
    pprint(server.host.get_host_cpu_info())
    
def handle_host_numa(args):
    server = LibvirtServer()
    pprint(server.host.get_numa_memory_info())
    
def handle_host_info(args):
    server = LibvirtServer()
    pprint(server.host.get_host_full_info())