from pprint import pprint
from utils.libvirt_server import LibvirtServer

def handle_net_list(args):
    server = LibvirtServer()
    pprint(server.net.list_networks())

def handle_net_info(args):
    server = LibvirtServer()
    pprint(server.net.get_network_info(args.net))

def handle_net_create(args):
    server = LibvirtServer()
    result = server.net.create_network(
        net_name=args.net_name,
        br_name=args.br_name,
        gateway=args.gateway,
        netmask=args.netmask,
        dhcp_start=args.dhcp_start,
        dhcp_end=args.dhcp_end
    )
    pprint(result)
    
def handle_net_delete(args):
    server = LibvirtServer()
    pprint(server.net.delete_network(args.net))
    
def handle_br_create(args):
    server = LibvirtServer()
    pprint(server.br.create(args.br_name))
    
def handle_br_delete(args):
    server = LibvirtServer()
    pprint(server.br.delete(args.br_name))

def handle_bridge(args):
    server = LibvirtServer()

    if args.bridge_cmd == "list-all":
        pprint(server.br.list_interface())

    elif args.bridge_cmd == "show-ifaces":
        pprint(server.br.list_br_interface(args.br_name))

    else:
        print("Unknown bridge subcommand")


def handle_br_bind(args):
    server = LibvirtServer()
    result = server.br.interface_operation(args.br_name, args.interfaces, "add")
    pprint(result)


def handle_br_unbind(args):
    server = LibvirtServer()
    result = server.br.interface_operation(args.br_name, args.interfaces, "del")
    pprint(result)
