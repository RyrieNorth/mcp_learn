import libvirt

VM_STATES = {
    libvirt.VIR_DOMAIN_RUNNING: "running",
    libvirt.VIR_DOMAIN_BLOCKED: "idle",
    libvirt.VIR_DOMAIN_PAUSED: "paused",
    libvirt.VIR_DOMAIN_SHUTDOWN: "in shutdown",
    libvirt.VIR_DOMAIN_SHUTOFF: "shut off",
    libvirt.VIR_DOMAIN_CRASHED: "crashed",
    libvirt.VIR_DOMAIN_NOSTATE: "no state",
}

NET_STATES = {  
    'rx_bytes'   : 0,  
    'rx_packets' : 0,  
    'rx_errs'    : 0,  
    'rx_drop'    : 0,  
    'tx_bytes'   : 0,  
    'tx_packets' : 0,  
    'tx_errs'    : 0,  
    'tx_drop'    : 0  
} 

BLOCK_STATES = {  
    'rd_req'   : 0,  
    'rd_bytes' : 0,  
    'wr_req'   : 0,  
    'wr_bytes' : 0,  
    'errs'     : 0
}

POOL_STATES = {
    libvirt.VIR_STORAGE_POOL_RUNNING: "running",
    libvirt.VIR_STORAGE_POOL_INACTIVE: "in_active"
}

VOLUME_TYPE = {
    0: "file",
    1: "block",
    2: "dir",
    3: "network",
    4: "netdir",
    5: "ploop"
}
