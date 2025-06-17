from pprint import pprint
from utils.libvirt_server import LibvirtServer

def handle_pool_list(args):
    server = LibvirtServer()
    pprint(server.pool.list_pools())
    
def handle_pool_info(args):
    server = LibvirtServer()
    pprint(server.pool.pool_info(args.pool))
    
def handle_pool_create(args):
    server = LibvirtServer()
    pprint(server.pool.create_pool(args.pool_type, args.pool_name, args.pool_path, args.pool_source))
    
def handle_pool_delete(args):
    server = LibvirtServer()
    pprint(server.pool.delete_pool(args.pool))
