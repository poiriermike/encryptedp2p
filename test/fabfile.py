from fabric.api import env, run, put, get
from fabric.decorators import roles, runs_once, parallel
import re

# HOSTS WILL NEED TO BE CHANGED FOR NEW GENI INSTANCES!!!
env.hosts = [
  "slice313.pcvm3-1.geni.case.edu",
    #"slice313.pcvm1-1.geni.it.cornell.edu",
    "slice313.pcvm3-1.instageni.metrodatacenter.com",
    "slice313.pcvm2-2.instageni.rnoc.gatech.edu",
    "slice313.pcvm3-2.instageni.illinois.edu",
    "slice313.pcvm5-7.lan.sdn.uky.edu",
    "slice313.pcvm3-1.instageni.lsu.edu",
    "slice313.pcvm2-2.instageni.maxgigapop.net",
    "slice313.pcvm1-1.instageni.iu.edu",
    "slice313.pcvm3-4.instageni.rnet.missouri.edu",
    "slice313.pcvm3-7.instageni.nps.edu",
    "slice313.pcvm2-1.instageni.nysernet.org",
    "slice313.pcvm3-11.genirack.nyu.edu",
    "slice313.pcvm5-1.instageni.northwestern.edu",
    "slice313.pcvm5-2.instageni.cs.princeton.edu",
    "slice313.pcvm3-3.instageni.rutgers.edu",
    "slice313.pcvm1-6.instageni.sox.net",
    "slice313.pcvm3-1.instageni.stanford.edu",
    "slice313.pcvm2-1.instageni.idre.ucla.edu",
    "slice313.pcvm4-1.utahddc.geniracks.net",
    "slice313.pcvm1-1.instageni.wisc.edu",
  ]

env.roledefs.update({
'server' : ["slice313.pcvm3-1.geni.case.edu"],
'clients' : [    
"slice313.pcvm3-1.instageni.metrodatacenter.com",
"slice313.pcvm2-2.instageni.rnoc.gatech.edu",
"slice313.pcvm3-2.instageni.illinois.edu",
#"slice313.pcvm1-1.geni.it.cornell.edu",
"slice313.pcvm3-1.instageni.metrodatacenter.com",
"slice313.pcvm2-2.instageni.rnoc.gatech.edu",
"slice313.pcvm3-2.instageni.illinois.edu",
"slice313.pcvm5-7.lan.sdn.uky.edu",
"slice313.pcvm3-1.instageni.lsu.edu",
"slice313.pcvm2-2.instageni.maxgigapop.net",
"slice313.pcvm1-1.instageni.iu.edu",
"slice313.pcvm3-4.instageni.rnet.missouri.edu",
"slice313.pcvm3-7.instageni.nps.edu",
"slice313.pcvm2-1.instageni.nysernet.org",
"slice313.pcvm3-11.genirack.nyu.edu",
"slice313.pcvm5-1.instageni.northwestern.edu",
"slice313.pcvm5-2.instageni.cs.princeton.edu",
"slice313.pcvm3-3.instageni.rutgers.edu",
"slice313.pcvm1-6.instageni.sox.net",
"slice313.pcvm3-1.instageni.stanford.edu",
"slice313.pcvm2-1.instageni.idre.ucla.edu",
"slice313.pcvm4-1.utahddc.geniracks.net",
"slice313.pcvm1-1.instageni.wisc.edu",
]
})

env.key_filename="./id_rsa"
env.use_ssh_config = True
env.ssh_config_path = './ssh-config'

def pingtest():
    run('ping -c 3 www.yahoo.com')

@parallel
def get_ip():
    run("ifconfig | grep \"inet addr\" > myip.txt")
    get('myip.txt')

@parallel
def upload_neighbours():
    """
    Upload the neighbours.txt file after condense.py has been run
    """
    put(env.host_string + "/neighbours.txt")
@parallel
@roles('clients')
def upload_client():
    put("client.py")

@roles('server')
def upload_server():
    put("server.py")

@roles('server')
def run_server():
    run("python server.py -p 6060")

@roles('clients')
@parallel
def run_client():
    run("python client.py -f neighbours.txt")