#!/usr/bin/env python3
import sys
import argparse
import argcomplete

from utils.logger import set_log_level

from handlers.console import handle_console
from handlers.host import (
    handle_host_name,
    handle_host_cpu,
    handle_host_numa,
    handle_host_info
)
from handlers.net import (
    handle_net_list,
    handle_net_info,
    handle_net_create,
    handle_net_delete,
    handle_br_create,
    handle_br_delete,
    handle_bridge,
    handle_br_bind,
    handle_br_unbind
)
from handlers.pool import (
    handle_pool_list,
    handle_pool_info,
    handle_pool_create,
    handle_pool_delete
)
from handlers.vm import (
    handle_img_info,
    handle_list_domains,
    handle_domain_info,
    handle_start,
    handle_shutdown,
    handle_destroy,
    handle_pause,
    handle_resume,
    handle_reboot,
    handle_reset,
    handle_ctrl_alt_delete,
    handle_undefine,
    handle_set_auto_start,
    handle_set_memory,
    handle_set_vcpu,
    handle_save,
    handle_restore,
    handle_delete,
    handle_create_domain,
    handle_cputime,
    handle_state,
    handle_ipaddrs,
    handle_netstats,
    handle_diskstats,
    handle_hostname,
    handle_full_stats
)
from handlers.vol import (
    handle_list_vols,
    handle_create_vol,
    handle_clone_vol,
    handle_delete_vol,
    handle_download_vol,
    handle_upload_vol
)

set_log_level("WARNING")

def build_parser():
    parser = argparse.ArgumentParser(description="Libvirt CLI Tool")
    subparsers = parser.add_subparsers(dest="command")
        
    # console abc
    console = subparsers.add_parser("console", help="Attach to VM console")
    console.add_argument("vm", help="Name or UUID of the VM")
    console.set_defaults(func=handle_console)
    
    # host
    parser_host = subparsers.add_parser("hostinfo", help="Host related operations")
    host_sub = parser_host.add_subparsers(dest="host_cmd", required=True)
    
    # host hostname
    host_name = host_sub.add_parser("hostname", help="Show host's hostname")
    host_name.set_defaults(func=handle_host_name)
    
    # host cpu
    host_cpu = host_sub.add_parser("cpu", help="Show CPU info")
    host_cpu.set_defaults(func=handle_host_cpu)
    
    # host numa
    host_numa = host_sub.add_parser("numa", help="Show host's NUMA and memory info")
    host_numa.set_defaults(func=handle_host_numa)
    
    # host info
    host_info = host_sub.add_parser("show", help="Show full host system info")
    host_info.set_defaults(func=handle_host_info)

    # net
    parser_net = subparsers.add_parser("net", help="Net related operations")
    net_sub = parser_net.add_subparsers(dest="net_cmd", required=True)

    # net list
    net_list = net_sub.add_parser("list", help="List all virtual networks")
    net_list.set_defaults(func=handle_net_list)

    # net info
    net_info = net_sub.add_parser("info", help="Show host's virtual network info")
    net_info.add_argument("net", help="Name or UUID of the net")
    net_info.set_defaults(func=handle_net_info)

    # net create --net-name xxx --br-name xxx --gateway x.x.x.x --netmask x.x.x.x --dhcp-start x.x.x.x --dhcp-end x.x.x.x
    net_create = net_sub.add_parser("create", help="Create a network")    
    net_create.add_argument("--net-name", "--name", "-n", required=True, help="Name of the virtual network")
    net_create.add_argument("--br-name", "--br", required=True, help="Name of the bridge interface")
    net_create.add_argument("--gateway", required=True, help="Gateway IP address")
    net_create.add_argument("--netmask", required=True, help="Subnet mask")
    net_create.add_argument("--dhcp-start", "--start", required=True, help="DHCP range start IP")
    net_create.add_argument("--dhcp-end", "--end", required=True, help="DHCP range end IP")
    net_create.set_defaults(func=handle_net_create)

    # net delete xxx
    net_delete = net_sub.add_parser("delete", help="Delete a virtual network")
    net_delete.add_argument("net", help="Name of the net")
    net_delete.set_defaults(func=handle_net_delete)

    # bridge
    parser_bridge = subparsers.add_parser("bridge", help="Bridge related operations")
    bridge_sub = parser_bridge.add_subparsers(dest="bridge_cmd", required=True)

    # bridge create br0
    br_create = bridge_sub.add_parser("create", help="Create a bridge interface")
    br_create.add_argument("br_name", help="Name of the bridge")
    br_create.set_defaults(func=handle_br_create)

    # bridge delete br0
    br_delete = bridge_sub.add_parser("delete", help="Delete a bridge interface")
    br_delete.add_argument("br_name", help="Name of the bridge")
    br_delete.set_defaults(func=handle_br_delete)

    # bridge list
    bridge_list = bridge_sub.add_parser("list", help="List all interfaces")
    bridge_list.set_defaults(func=handle_bridge)

    # bridge show-ifaces br0
    bridge_show = bridge_sub.add_parser("show-ifaces", help="Show interfaces attached to a bridge")
    bridge_show.add_argument("br_name", help="Name of the bridge")
    bridge_show.set_defaults(func=handle_bridge)

    # bridge bind br0 -i/--interfces eth0 eth1
    br_bind = bridge_sub.add_parser("bind", help="Bind interfaces to bridge")
    br_bind.add_argument("br_name")
    br_bind.add_argument("-i", "--interfaces", nargs="+", required=True)
    br_bind.set_defaults(func=handle_br_bind)

    # bridge unbind br0 -i/--interfces eth0 eth1
    br_unbind = bridge_sub.add_parser("unbind", help="Bind interfaces to bridge")
    br_unbind.add_argument("br_name")
    br_unbind.add_argument("-i", "--interfaces", nargs="+", required=True)
    br_unbind.set_defaults(func=handle_br_unbind)

    # pool
    parser_pool = subparsers.add_parser("pool", help="Storage pool related operations")
    pool_sub = parser_pool.add_subparsers(dest="pool_cmd", required=True)
    
    # pool list
    pool_list = pool_sub.add_parser("list", help="List all storage pools")
    pool_list.set_defaults(func=handle_pool_list)

    # pool info
    pool_info = pool_sub.add_parser("info", help="Show host's storage pool details")
    pool_info.add_argument("pool", help="Name or UUID of the storage pool")
    pool_info.set_defaults(func=handle_pool_info)

    # pool create --pool-type xxx --pool-name xxx --pool-path xxx --pool-source/None
    pool_create = pool_sub.add_parser("create", help="Create a storage pool")
    pool_create.add_argument("--pool-type", required=True, help="Type of the storage pool")
    pool_create.add_argument("--pool-name", required=True, help="Name of the storage pool")
    pool_create.add_argument("--pool-path", required=True, help="Physical path of the storage pool")
    pool_create.add_argument("--pool-source", required=False, help="Extra storage pool configs")
    pool_create.set_defaults(func=handle_pool_create)

    pool_delete = pool_sub.add_parser("delete", help="Delete a storage pool")
    pool_delete.add_argument("pool", help="Name or UUID of the storage pool")
    pool_delete.set_defaults(func=handle_pool_delete)

    # vm
    parser_vm = subparsers.add_parser("vm", help="Virtual machine related operations")
    vm_sub = parser_vm.add_subparsers(dest="vm_cmd", required=True)

    # vm img-info xxx
    vm_img_info = vm_sub.add_parser("img-info", help="Show image or disk details")
    vm_img_info.add_argument("path", help="Image or disk path")
    vm_img_info.set_defaults(func=handle_img_info)

    # vm list
    vm_list = vm_sub.add_parser("list", help="List all virual machines")
    vm_list.set_defaults(func=handle_list_domains)

    # vm show xxx 
    # vm show xx --devices/-d xxx
    vm_show = vm_sub.add_parser("show", help="Show all virual machines details")
    vm_show.add_argument("vm_name", help="Name of the VM")
    vm_show.add_argument("-d", "--devices", nargs="+", required=False, help="Name of the devices, such as disk / interface / graphics")
    vm_show.set_defaults(func=handle_domain_info)

    # vm start xxx
    vm_start = vm_sub.add_parser("start", help="Start a VM")
    vm_start.add_argument("vm_name", help="Name of the VM")
    vm_start.set_defaults(func=handle_start)

    # vm start xxx
    vm_shutdown = vm_sub.add_parser("stop", help="Shutdown a VM")
    vm_shutdown.add_argument("vm_name", help="Name of the VM")
    vm_shutdown.set_defaults(func=handle_shutdown)

    # vm destroy xxx
    vm_destroy = vm_sub.add_parser("destroy", help="Force shutdown a VM")
    vm_destroy.add_argument("vm_name", help="Name of the VM")
    vm_destroy.set_defaults(func=handle_destroy)

    # vm pause xxx
    vm_pause = vm_sub.add_parser("pause", help="Pause a VM")
    vm_pause.add_argument("vm_name", help="Name of the VM")
    vm_pause.set_defaults(func=handle_pause)

    # vm resume xxx
    vm_resume = vm_sub.add_parser("resume", help="Resume a VM")
    vm_resume.add_argument("vm_name", help="Name of the VM")
    vm_resume.set_defaults(func=handle_resume)

    # vm reboot xxx
    vm_reboot = vm_sub.add_parser("reboot", help="Resume a VM")
    vm_reboot.add_argument("vm_name", help="Name of the VM")
    vm_reboot.set_defaults(func=handle_reboot)

    # vm reset xxx
    vm_reset = vm_sub.add_parser("reset", help="Force reboot a VM")
    vm_reset.add_argument("vm_name", help="Name of the VM")
    vm_reset.set_defaults(func=handle_reset)

    # vm ctrl_alt_delete xxx
    vm_ctrl_alt_delete = vm_sub.add_parser("ctrl_alt_delete", help="Send reboot key to VM")
    vm_ctrl_alt_delete.add_argument("vm_name", help="Name of the VM")
    vm_ctrl_alt_delete.set_defaults(func=handle_ctrl_alt_delete)

    # vm undefine xxx
    vm_undefine = vm_sub.add_parser("undefine", help="Undefine a VM")
    vm_undefine.add_argument("vm_name", help="Name of the VM")
    vm_undefine.set_defaults(func=handle_undefine)

    # vm autostart xxx --state/-s on/off
    vm_autostart = vm_sub.add_parser("autostart", help="Set VM autostart")
    vm_autostart.add_argument("vm_name", help="Name of the VM")
    vm_autostart.add_argument("--state", "-s", required=False, help="On/Off autostart")
    vm_autostart.set_defaults(func=handle_set_auto_start)

    # vm set-memory xxx --memory/-m xxx
    vm_set_memory = vm_sub.add_parser("set-memory", help="Set VM max memory")
    vm_set_memory.add_argument("vm_name", help="Name of the VM")
    vm_set_memory.add_argument("--memory", "-m", type=int, help="Max VM memory")
    vm_set_memory.set_defaults(func=handle_set_memory)

    # vm set-vcpu xxx --cpu/-c xxx
    vm_set_vcpu = vm_sub.add_parser("set-vcpu", help="Set VM max vcpu")
    vm_set_vcpu.add_argument("vm_name", help="Name of the VM")
    vm_set_vcpu.add_argument("--vcpu", "-c", type=int, help="Max VM vcpu")
    vm_set_vcpu.set_defaults(func=handle_set_vcpu)

    # vm save xxx --path/-p xxx
    vm_save = vm_sub.add_parser("save", help="Save vm current state")
    vm_save.add_argument("vm_name", help="Name of the VM")
    vm_save.add_argument("--path", "-p", help="VM state img save path")
    vm_save.set_defaults(func=handle_save)

    # vm restore --path/-p
    vm_restore = vm_sub.add_parser("restore", help="Restore vm current state")
    vm_restore.add_argument("--path", "-p", help="VM state img save path")
    vm_restore.set_defaults(func=handle_restore)
    
    # vm delete xxx
    vm_delete = vm_sub.add_parser("delete", help="Delete a VM")
    vm_delete.add_argument("vm_name", help="Name of the VM")
    vm_delete.set_defaults(func=handle_delete)
    
    # vm create --name xxx --ram xxx --vcpu xxx --net-name xxx (--os_arch xxx) --emulator xxx --disk xxx (--cdrom xxx) --running
    vm_create = vm_sub.add_parser("create", help="Create a VM")
    vm_create.add_argument("--name", "-n", required=True, help="Name of the VM")
    vm_create.add_argument("--ram", "-m", required=True, type=int, help="VM max memory")
    vm_create.add_argument("--vcpu", "-c", required=True, type=int, help="VM vcpus")
    vm_create.add_argument("--net", required=True, help="Name of the virtual network" )
    vm_create.add_argument("--arch", required=False, help="VM architecture, such as x86_64 or aarch64")
    vm_create.add_argument("--emulator", "-e", required=False, help="VM emulator program, such as /usr/libexec/qemu-kvm, /usr/bin/qemu-system-x86-64")
    vm_create.add_argument("--disk", "-d", required=True, help="VM boot disk")
    vm_create.add_argument("--cdrom", "-cd", required=False, help="VM boot cdrom")
    vm_create.add_argument("--running", "-run", action="store_true", help="Create and run the VM if set")
    vm_create.set_defaults(func=handle_create_domain)

    # vm cputime xxx --interval/-i xxx
    vm_cputime = vm_sub.add_parser("cputime", help="Show VM cputime by interval")
    vm_cputime.add_argument("vm_name", help="Name of the VM")
    vm_cputime.add_argument("--interval", "-i", type=float, help="Interval time, default unit is second")
    vm_cputime.set_defaults(func=handle_cputime)

    # vm state xxx 
    vm_state = vm_sub.add_parser("state", help="Show VM state")
    vm_state.add_argument("vm_name", help="Name of the VM")
    vm_state.set_defaults(func=handle_state)

    # vm ipaddrs xxx
    vm_ipaddrs = vm_sub.add_parser("ipaddrs", help="Show VM ipaddress")
    vm_ipaddrs.add_argument("vm_name", help="Name of the VM")
    vm_ipaddrs.set_defaults(func=handle_ipaddrs)
    
    # vm netstats xxx
    vm_netstats = vm_sub.add_parser("netstats", help="Show VM netstats")
    vm_netstats.add_argument("vm_name", help="Name of the VM")
    vm_netstats.add_argument("--to-mib", action="store_true", help="Show bytes to mib if set")
    vm_netstats.set_defaults(func=handle_netstats)
    
    # vm diskstats xxx
    vm_diskstats = vm_sub.add_parser("diskstats", help="Show VM diskstats")
    vm_diskstats.add_argument("vm_name", help="Name of the VM")
    vm_diskstats.add_argument("--to-mib", action="store_true", help="Show bytes to mib if set")
    vm_diskstats.set_defaults(func=handle_diskstats)

    # vm hostname xxx
    vm_hostname = vm_sub.add_parser("hostname", help="Show VM hostname")
    vm_hostname.add_argument("vm_name", help="Name of the VM")
    vm_hostname.set_defaults(func=handle_hostname)

    # vm showall xxx
    vm_showall = vm_sub.add_parser("showall", help="Show VM full details")
    vm_showall.add_argument("vm_name", help="Name of the VM")
    vm_showall.add_argument("--to-mib", action="store_true", help="Show bytes to mib if set")
    vm_showall.set_defaults(func=handle_full_stats)

    # vol
    parser_vol = subparsers.add_parser("vol", help="Volumes related operations")
    vol_sub = parser_vol.add_subparsers(dest="vol_cmd", required=True)
    
    # vol list --pool xxx
    vol_list = vol_sub.add_parser("list", help="List all volumes from getting storage pool")
    vol_list.add_argument("--pool", help="Storage pool name")
    vol_list.set_defaults(func=handle_list_vols)

    # vol create --pool xxx --name/-n xxx --size/-s xxx --path/-p xxx
    vol_create = vol_sub.add_parser("create", help="Create a storage pool volume")
    vol_create.add_argument("--pool", required=True, help="Name of the storage pool")
    vol_create.add_argument("--name", "-n", required=True, help="Name of the volume")
    vol_create.add_argument("--size", "-s", required=True, type=int, help="Size of the volume, default unit is MiB")
    vol_create.add_argument("--path", "-p", required=True, help="Volume storage path")
    vol_create.set_defaults(func=handle_create_vol)

    # vol clone --pool xxx --src xxx --dest xxx
    vol_clone = vol_sub.add_parser("clone", help="Clone a storage pool volume")
    vol_clone.add_argument("--pool", required=True, help="Name of the storage pool")
    vol_clone.add_argument("--source", "--src", "-s", required=True, help="Name of the source volume")
    vol_clone.add_argument("--destination", "--dest", "--dst", "-d", required=True, help="Name of the clone volume")
    vol_clone.set_defaults(func=handle_clone_vol)

    # vol delete --pool xxx --name/-n xxx
    vol_delete = vol_sub.add_parser("delete", help="Delete a storage pool volume")
    vol_delete.add_argument("--pool", required=True, help="Name of the storage pool")
    vol_delete.add_argument("--name", "-n", required=True, help="Name of the storage pool volume")
    vol_delete.set_defaults(func=handle_delete_vol)

    # vol download --pool xxx --name/-n xxx --path/-p xxx
    vol_download = vol_sub.add_parser("download", help="Download a storage pool volume")
    vol_download.add_argument("--pool", required=True, help="Name of the storage pool"),
    vol_download.add_argument("--name", "-n", required=True, help="Name of the storage pool volume")
    vol_download.add_argument("--path", "-p", required=True, help="Download path")
    vol_download.set_defaults(func=handle_download_vol)

    # vol upload --pool xxx --name/-n xxx --vol-path xxx --local-path xxx
    vol_upload = vol_sub.add_parser("upload", help="Upload a storage pool volume")
    vol_upload.add_argument("--pool", required=True, help="Name of the storage pool"),
    vol_upload.add_argument("--name", "-n", required=True, help="Name of the storage pool volume")
    vol_upload.add_argument("--vol-path", required=True, help="Volume upload storage path")
    vol_upload.add_argument("--local-path", required=True, help="Volume upload local path")
    vol_upload.set_defaults(func=handle_upload_vol)
    
    return parser

def main():
    parser = build_parser()

    argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
