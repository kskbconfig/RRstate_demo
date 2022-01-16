#!/usr/bin/python3
import os
import yaml
import math
import json
import textwrap
import ipaddress
import subprocess
import hashlib
import base64

nodes = yaml.load( open("envs.yaml").read() , Loader=yaml.SafeLoader )
supernode_config = yaml.load( open("supernode.yaml").read() , Loader=yaml.SafeLoader )
common_var = {l.split("=",1)[0]:l.split("=",1)[1] for l in filter(lambda x:"=" in x,open("_common_env").read().split("\n"))}
lentancy_metrix=json.loads( open("edge_lentancy_metrix.json").read())

def get_cost(src,dst):
    total_l = lentancy_metrix[src][dst] + lentancy_metrix[dst][src]
    return max(1 + int( total_l * 1000 ),0)

def toHex(n):
    return "{:X}".format(int(n))

def create_tunnel(n):
    my_env = os.environ.copy()
    my_env["HOME"] = os.getcwd()
    c1 = ["cloudflared","tunnel","create", n ]
    c2 = ["cloudflared","tunnel","route","dns", n , n + ".kskb.eu.org"]
    print(" ".join(c1))
    process = subprocess.Popen(c1,env=my_env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE )
    out,err = process.communicate(input=b'\n')
    exit_code = process.wait()
    if exit_code != 0:
        raise Exception("code:" + str(exit_code) + ", out:" + out.decode() + ", err:" + err.decode())
    print(out.decode())
    process = subprocess.Popen(c2,env=my_env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE )
    out,err = process.communicate(input=b'\n')
    exit_code = process.wait()
    if exit_code != 0:
        raise Exception("code:" + str(exit_code) + ", out:" + out.decode() + ", err:" + err.decode())
    print(out.decode() , err.decode())
    
tunnels = {}

def load_tunnel(n):
    if n in tunnels:
        return tunnels[n]
    for f in os.listdir(".cloudflared"):
        if f.endswith(".json") == False:
            continue
        t = json.loads(open(".cloudflared/" + f).read())
        tn = t["TunnelName"]
        tunnels[tn] = t
        if tn == n:
            return t
    create_tunnel(n)
    return load_tunnel(n)

def wg_priv2pub(priv):
    return subprocess.Popen(["wg","pubkey"], stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE ).communicate(input=priv.encode())[0].strip().decode()

frps_config = {}


for filename in os.listdir("_common_ow/etc/bird/nodes_template"):
    file_path = os.path.join("_common_ow/etc/bird/nodes_template", filename)
    try:
        if file_path[-5:] == ".conf":
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))

for id_str , node_info in nodes.items():
    replace_dict = {}
    node_id = int(id_str)
    v4len = 32 - int(math.log(node_info["len"],2))
    v6len = 64 - int(math.log(node_info["len"],2))
    ipv4 = "10.127.111." + id_str
    ipv6 = "fd10:127:e00f:" + toHex(node_id) + "::1"
    ipv6ll = "fe80::aa:1111:" + toHex(node_id)
    ipv4net = ipaddress.ip_network(ipv4 + "/" + str(v4len), strict=False)
    ipv6net = ipaddress.ip_network(ipv6 + "/" + str(v6len), strict=False)
    if not os.path.exists(node_info["name"]):
        p = subprocess.Popen(['cp','-rp',"template",node_info["name"]])
        p.wait()
    tun = load_tunnel("neo" + node_info["name"] + "42")
    
    frpc_token =  base64.b64encode(hashlib.sha256(node_info["wg"].encode('utf-8')).digest()).decode()[:20]
    
    replace_dict["NODE_ID"] = id_str
    replace_dict["EG_MACADDR"] = common_var["P_EG_MACADDR_PREFIX"] + ":" + toHex(node_id).zfill(2)
    replace_dict["UML_IF_SLIRP_MACADDR"] = "02:42:" + ":".join([hex(i)[2:].zfill(2) for i in ipaddress.ip_address(common_var["UML_IF_SLIRP_IPV4"][:-3]).packed])
    replace_dict["DN42_I_AS"] = common_var["DN42_I_AS_PREFIX"]             + id_str.zfill(4)
    replace_dict["DN42_IPV4_NET_BOARDCAST_LEN"] = v4len
    replace_dict["DN42_IPV6_NET_BOARDCAST_LEN"] = v6len
    replace_dict["DN42_IPV4"] = ipv4
    replace_dict["DN42_IPV6"] = ipv6
    replace_dict["DN42_IPV4_NET_BOARDCAST"] = ipv4net
    replace_dict["DN42_IPV6_NET_BOARDCAST"] = ipv6net
    replace_dict["DN42_IPV6_LL"] = ipv6ll
    replace_dict["DN42_REGION"] = node_info["regcode"]
    replace_dict["DN42AP_TITLE"] = "KusakabeSi's DN42 Peering Portal (" + node_info["name ab"] + ")"
    replace_dict["BIRDLG_SERVERS"] = node_info["name full"] + "<127.0.0.1>"
    replace_dict["BIRDLG_NAVBAR_BRAND"] = f'Peer with me ({ node_info["name full"] })!'
    replace_dict["BIRDLG_NAVBAR_BRAND_URL"] = "https://neo" + node_info["name"] + "42.kskb.eu.org/autopeer/"
    replace_dict["HTML_AUTOPEER"] = "https://neo" + node_info["name"] + "42.kskb.eu.org/autopeer/"
    replace_dict["HTML_LG"] = "https://neo" + node_info["name"] + "42.kskb.eu.org/"
    replace_dict["HTML_LOCATION"] = node_info["name full"]
    replace_dict["EG_PRIVKEY"] = node_info["eg"]
    replace_dict["WG_PRIVKEY"] = node_info["wg"]
    replace_dict["WG_PUBKEY"] = wg_priv2pub(node_info["wg"])
    replace_dict["CLOUDFLARED"] = 1
    replace_dict["CLOUDFLARED_TUNNEL_CRET"] = json.dumps(tun)
    replace_dict["FRPC_REMOTE_PORT"] = 16000 + node_id
    replace_dict["FRPC_USER"] = node_info["name"] + "42"
    replace_dict["FRPC_TOKEN"] = frpc_token
    replace_dict["REBOOT_BOOTON_URL"] = f'https://dn42{ node_info["name"] }.azurewebsites.net/'
    if "env" in node_info:
        for env_k,env_v in node_info["env"].items():
            replace_dict[env_k] = env_v
    frps_config[node_info["name"] + "42"] = frpc_token
    
    supernode_config["Peers"] += [{"nodeid":node_id,"name":node_info["name"],"pubkey":wg_priv2pub(node_info["eg"]),"pskey":""}]
    
    open("_common_ow/etc/bird/nodes_template/" + node_info["name"] + ".conf","w").write(textwrap.dedent(f"""\
                                                                                                 protocol bgp internal_{node_info["name"]} from dnnodes {{
                                                                                                   source address ${{DN42_IPV6_LL}};
                                                                                                   neighbor {ipv6ll}%vec1 as ${{DN42_E_AS}};
                                                                                                   ipv4 {{
                                                                                                     cost ${{DN42_COST_{ node_info["name"] }}};
                                                                                                   }};
                                                                                                   ipv6 {{
                                                                                                     cost ${{DN42_COST_{ node_info["name"] }}};
                                                                                                   }};
                                                                                                 }};"""))
    template = open("env.template").read().split("\n")
    output = []
    for l in template:
        if "=" in l:
            k,v = l.split("=",1)
            if k in replace_dict:
                v = str(replace_dict[k])
            l =k + "=" + v
        output += [l]
    for id_str_sub , node_info_sub in nodes.items():
        if id_str == id_str_sub:
            continue
        output += [f'DN42_COST_{ node_info_sub["name"] }={ get_cost(id_str,id_str_sub) }']
        
    if "env" in node_info:
        for env_k,env_v in node_info["env"].items():
            output += [f'{ env_k }={env_v}']
    open(node_info["name"] + "/env","w").write("\n".join(output))
    

open("supernode_out" + ".yaml","w").write(yaml.dump(supernode_config, default_flow_style=False))
for k,v in frps_config.items():
    print("FRP_USER_" + k + "=" + v)
