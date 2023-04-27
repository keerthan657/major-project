from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import RemoteController

# Initialize remote controller
c1 = RemoteController( 'c1', ip='127.0.0.1', port=6633 )

class MyTopo( Topo ):

    def build( self ):

        # Add hosts and switches
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )
        s1 = self.addSwitch( 's1' )

        # Add links
        self.addLink( s1, h1 )
        self.addLink( s1, h2 )
        self.addLink( s1, h3 )

def generate_normal_traffic(net):
    # Get a list of all hosts in the network
    hosts = net.hosts

    # Choose two random hosts
    src, dst = random.sample(hosts, 2)

    # Generate normal traffic between the two hosts using iperf
    print(f"Generating normal traffic from {src.name} to {dst.name}")
    net.iperf((src, dst), seconds=5)

if __name__ == '__main__':
    setLogLevel('info')

    topo = MyTopo()

    net = Mininet(topo, build=False)
    net.addController(c1)
    net.build()
    net.start()

    # Generate normal traffic 100 times
    for i in range(10):
        generate_normal_traffic(net)

    CLI( net )

    net.stop()