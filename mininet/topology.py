from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import RemoteController

import itertools
import random
import threading
from time import sleep

# Initialize remote controller
c1 = RemoteController( 'c1', ip='127.0.0.1', port=6633 )

class MyTopo( Topo ):

    def build( self ):

        # Add hosts and switches
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )
        h4 = self.addHost( 'h4' )
        h5 = self.addHost( 'h5' )
        h6 = self.addHost( 'h6' )
        s1 = self.addSwitch( 's1' )

        # Add links
        self.addLink( s1, h1 )
        self.addLink( s1, h2 )
        self.addLink( s1, h3 )
        self.addLink( s1, h4 )
        self.addLink( s1, h5 )
        self.addLink( s1, h6 )
    
def iperf_commands(host_pairs, protocol, time):
    (src, dst) = host_pairs
    client_cmd = 'iperf -c ' + src.IP() + ' -t ' + str(time) + ' -h'
    server_cmd = 'iperf -s &'

    dst.cmd(server_cmd)
    src.cmd(client_cmd)

    # src_output = src.popen(client_cmd, stdout=None)
    # stdout, stderr = src_output.communicate()
    # print(stdout.decode().strip())

def generate_normal_traffic(net):
    # Get a list of all hosts in the network
    hosts = net.hosts

    # Choose multiple random pairs of hosts
    pairs = random.sample(list(itertools.permutations(hosts, 2)), k=2)

    # Generate normal traffic among multiple pairs of nodes using iperf simultaneously
    for src, dst in pairs:
        print(f"Generating normal traffic from {src.name} to {dst.name}")
        # iperf_commands((src, dst), protocol='TCP', time=5)
        net.iperf((src, dst), seconds=5)
    sleep(5)

if __name__ == '__main__':
    setLogLevel('info')

    topo = MyTopo()

    net = Mininet(topo, build=False)
    net.addController(c1)
    net.build()
    net.start()

    # Issue ping_all so that switch learns the table
    # net.pingAll()

    # Generate normal traffic 100 times
    for i in range(1000):
        generate_normal_traffic(net)

    CLI( net )

    net.stop()