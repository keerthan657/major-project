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

# video file path for Video Streaming service
# video resolution should be low (360p) & should be in 'mp4' format
# can be varied depending on system specs
video_file = "./assets/video2.mp4"

# data file path for File Transfer service
# this can be any size file
data_file = "./assets/random_data"

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

def issue_command(host, custom_cmd, run_bg=True):
    # add '&' at end to make command run in background
    if(run_bg):
        host.cmd(custom_cmd+' &')
    else:
        host.cmd(custom_cmd)

def generate_normal_traffic(net, video_service=True, open_vlc=True, file_transfer_service=True, mail_service=True,
                            http_web_service=True, dns_service=True):
    h1, h2, h3, h4, h5, h6 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

    if video_service:
        # h1 -> video streaming server
        issue_command(h1, "ffmpeg -re -i {} -vcodec copy -f mpegts - | nc -l -p 9999".format(video_file))
        # h2 -> video streaming client
        if open_vlc:
            issue_command(h2, "nc -v {} 9999 | vlc-wrapper -".format(h1.IP()))
        else:
            issue_command(h2, "nc -v {} 9999".format(h1.IP()))

    if file_transfer_service:
        # h3 -> file server
        issue_command(h3, "python3 -m http.server 9998")
        # h4 -> file download from file server
        issue_command(h4, "while true; do wget http://{}:9998/{} -O ./assets/temp/random; sleep 5; done".format(h3.IP(), data_file))

    # h5 -> mail server
    # h6 -> sends mails to mail server
    

if __name__ == '__main__':
    setLogLevel('info')

    topo = MyTopo()

    net = Mininet(topo, build=False)
    net.addController(c1)
    net.build()
    net.start()

    generate_normal_traffic(net, video_service=False, open_vlc=True, file_transfer_service=False, mail_service=True,
                            http_web_service=True, dns_service=True)

    CLI( net )

    net.stop()