from pprint import pprint
from utils.libvirt_server import LibvirtServer

def handle_img_info(args):
    server = LibvirtServer()
    pprint(server.vm.parse_qemu_img_info(args.path))

def handle_list_domains(args):
    server = LibvirtServer()
    pprint(server.vm.list_domains())

def handle_domain_info(args):
    server = LibvirtServer()
    pprint(server.vm.domain_info(domain_name=args.vm_name, device_types=args.devices))

def handle_start(args):
    server = LibvirtServer()
    pprint(server.vm.start(domain_name=args.vm_name))

def handle_shutdown(args):
    server = LibvirtServer()
    pprint(server.vm.shutdown(domain_name=args.vm_name))

def handle_destroy(args):
    server = LibvirtServer()
    pprint(server.vm.destroy(domain_name=args.vm_name))

def handle_pause(args):
    server = LibvirtServer()
    pprint(server.vm.pause(domain_name=args.vm_name))

def handle_resume(args):
    server = LibvirtServer()
    pprint(server.vm.resume(domain_name=args.vm_name))

def handle_reboot(args):
    server = LibvirtServer()
    pprint(server.vm.reboot(domain_name=args.vm_name))

def handle_reset(args):
    server = LibvirtServer()
    pprint(server.vm.reset(domain_name=args.vm_name))

def handle_ctrl_alt_delete(args):
    server = LibvirtServer()
    pprint(server.vm.send_ctrl_alt_del(domain_name=args.vm_name))

def handle_undefine(args):
    server = LibvirtServer()
    pprint(server.vm.undefine(domain_name=args.vm_name))

def handle_set_auto_start(args):
    server = LibvirtServer()
    pprint(server.vm.set_auto_start(domain_name=args.vm_name, state=args.state))

def handle_set_memory(args):
    server = LibvirtServer()
    pprint(server.vm.set_memory(domain_name=args.vm_name, memory=args.memory))

def handle_set_vcpu(args):
    server = LibvirtServer()
    pprint(server.vm.set_vcpu(domain_name=args.vm_name, vcpus=args.vcpu))

def handle_save(args):
    server = LibvirtServer()
    pprint(server.vm.save(domain_name=args.vm_name, save_path=args.path))

def handle_restore(args):
    server = LibvirtServer()
    pprint(server.vm.restore(args.path))

def handle_delete(args):
    server = LibvirtServer()
    pprint(server.vm.delete(domain_name=args.vm_name))

def handle_create_domain(args):
    server = LibvirtServer()
    kwargs = {
        "name": args.name,
        "ram": args.ram,
        "vcpu": args.vcpu,
        "net_name": args.net,
        "boot_disk": args.disk,
        "running": args.running
    }

    if args.arch is not None:
        kwargs["os_arch"] = args.arch
    if args.emulator is not None:
        kwargs["emulator"] = args.emulator
    if args.cdrom is not None:
        kwargs["cdrom"] = args.cdrom

    result = server.vm.domain_create(**kwargs)
    pprint(result)

def handle_cputime(args):
    server = LibvirtServer()
    pprint(server.vm.domain_cputime(domain_name=args.vm_name, interval=args.interval))

def handle_state(args):
    server = LibvirtServer()
    pprint(server.vm.domain_state(domain_name=args.vm_name))

def handle_ipaddrs(args):
    server = LibvirtServer()
    pprint(server.vm.domain_ipaddrs(domain_name=args.vm_name))

def handle_netstats(args):
    server = LibvirtServer()
    pprint(server.vm.domain_netstats(domain_name=args.vm_name, to_mib=args.to_mib))

def handle_diskstats(args):
    server = LibvirtServer()
    pprint(server.vm.domain_diskstats(domain_name=args.vm_name, to_mib=args.to_mib))

def handle_hostname(args):
    server = LibvirtServer()
    pprint(server.vm.domain_hostname(domain_name=args.vm_name))

def handle_full_stats(args):
    server = LibvirtServer()
    pprint(server.vm.domain_full_stats(domain_name=args.vm_name, to_mib=args.to_mib))

