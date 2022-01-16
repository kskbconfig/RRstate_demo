#!/usr/bin/python3
import shlex
import sys
import os
out=[]
uml_vars = []

import_from_env = ["GIT_REPO_ADDR" , "NODE_NAME","SSH_KEY"]

import socket
import ipaddress
import struct
def getlocalIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    l = s.getsockname()
    s.close()
    return ipaddress.ip_address(l[0]) +100

def getgw():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                # If not default route or not RTF_GATEWAY, skip it
                continue
            return ipaddress.ip_address(struct.pack("<L", int(fields[2], 16)))
        
uml_vars += [["UML_IF_RAW_IPV4" , str(getlocalIP()) + "/24"]]
uml_vars += [["UML_IF_RAW_IPV4_GW" , str(getgw())]]
uml_vars += [["UML_IF_RAW_MACADDR" , "02:42:" + ":".join([hex(i)[2:].zfill(2) for i in getlocalIP().packed])]]

for v in uml_vars:
    out += ["declare -x " + v[0] + "=" + shlex.quote(v[1])]

for en in import_from_env:
    out += ["declare -x " + en + "=" + shlex.quote(os.environ[en])]

for envf in sys.argv[1:]:
    env = open(envf).read().split("\n")
    for v in env:
        if "=" not in v:
            continue
        k,v = v.split("=",1)
        out += ["declare -x " + k + "=" + shlex.quote(v)]
print("\n".join(out))