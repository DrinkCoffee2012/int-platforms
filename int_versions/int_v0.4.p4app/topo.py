#!/usr/bin/python

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import subprocess
import sys
import time

from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI

from p4_mininet import P4Switch, P4Host
from src.networking import create_int_collection_network, create_link_to_external_interface
from src.thrift import writeRegister
from src.mininet_topo import MyTopo, read_topo, configure_hosts, configure_switches, _THRIFT_BASE_PORT

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))


# install additional libraries
os.system("dpkg -i /tmp/libraries/bridge-utils_1.5-13+deb9u1_amd64.deb")


parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)
parser.add_argument('--json', help='Path to JSON config file',
                    type=str, action="store", required=True)
parser.add_argument('--cli', help='Path to BM CLI',
                    type=str, action="store", required=True)
args = parser.parse_args()


def setup_start_time(nb_switches):
    offset = int(time.time()*1e9)
    offset -= 1e9 # substract 1sec  to compesate a little earlier bmv2 start
    print("Setting time offset %d" % offset)
    for port in [_THRIFT_BASE_PORT+switch_index  for switch_index in range(nb_switches)]:    #[22222, 22223, 22224]:
        writeRegister(thrift_port=port, register='start_timestamp', idx=0, value=offset)
        
 
def main():
    nb_hosts, nb_switches, links = read_topo()
    topo = MyTopo(args.behavioral_exe,
                  args.json,
                  nb_hosts, nb_switches, links)

    net = Mininet(topo = topo,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None,
                  autoStaticArp=True)

    create_int_collection_network(net.switches)
    create_link_to_external_interface(switch=net.switches[1], external_interface_name='eth1')

    net.start()
    
    #enable Unix time within bmv2 for purpose of INT functionality
    setup_start_time(nb_switches)

    configure_hosts(net, nb_hosts)
    configure_switches(net, nb_switches, args)

    net.get('h1').cmd('python /tmp/host/default_udp_flow.py')
    time.sleep(1)
    print "Ready !"

    CLI(net)
    net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
