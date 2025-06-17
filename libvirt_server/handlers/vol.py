from pprint import pprint
from utils.libvirt_server import LibvirtServer

def handle_list_vols(args):
    server = LibvirtServer()
    pprint(server.vol.list_volumes(args.pool))
    
def handle_create_vol(args):
    server = LibvirtServer()
    pprint(server.vol.create(args.pool, args.name, args.size, args.path))
    
def handle_clone_vol(args):
    server = LibvirtServer()
    pprint(server.vol.clone(args.pool, args.source, args.destination))
    
def handle_delete_vol(args):
    server = LibvirtServer()
    pprint(server.vol.delete(args.pool, args.name))
    
def handle_download_vol(args):
    server = LibvirtServer()
    pprint(server.vol.transfer(args.pool, args.name, args.path, "download"))
        
def handle_upload_vol(args):
    server = LibvirtServer()
    pprint(server.vol.create_and_upload(args.pool, args.name, args.vol_path, args.local_path))