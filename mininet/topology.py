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
video_file = "./assets/video3.mp4"

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
        h7 = self.addHost( 'h7' )
        h8 = self.addHost( 'h8' )
        s1 = self.addSwitch( 's1' )

        # Add links
        self.addLink( s1, h1 )
        self.addLink( s1, h2 )
        self.addLink( s1, h3 )
        self.addLink( s1, h4 )
        self.addLink( s1, h5 )
        self.addLink( s1, h6 )
        self.addLink( s1, h7 )
        self.addLink( s1, h8 )

def issue_command(host, custom_cmd, run_bg=True):
    # add '&' at end to make command run in background
    if(run_bg):
        host.cmd(custom_cmd+' &')
    else:
        host.cmd(custom_cmd)

def generate_normal_traffic(net, video_service=True, open_video_player=True, file_transfer_service=True, http_service=True,
                            ddos_service=False):
    h1, h2, h3, h4, h5, h6, h7, h8 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8')

    if video_service:
        # h1 -> video streaming server
        issue_command(h1, "ffmpeg -re -stream_loop -1 -i {} -vcodec copy -f mpegts - | nc -l -p 9999".format(video_file))
        # h2 -> video streaming client
        if open_video_player:
            issue_command(h2, "nc -v {} 9999 | ffplay -i -".format(h1.IP())) # videoplayer crashes, so run this manually command using xterm if needed
        else:
            issue_command(h2, "nc -v {} 9999 > /dev/null".format(h1.IP()))

    if file_transfer_service:
        # h3 -> file server
        issue_command(h3, "python3 -m http.server 9998")
        # h4 -> file download from file server
        issue_command(h4, "while true; do wget http://{}:9998/{} -O ./assets/temp/random; sleep 5; done".format(h3.IP(), data_file))

    if http_service:
        # h5 -> hosting web server
        issue_command(h5, "python3 -m http.server 9997")
        # h6 -> accesses web page
        issue_command(h6, "while true; do curl {}:9997; sleep 2; done".format(h5.IP()))

    # for DoS attack, use hping3 tool >> hping3 -c 10000 -d 120 -S -w 64 -p 80 --flood <target_ip>
    if ddos_service:
        # TODO: trigger DoS attack through external mechanism
        # h7 -> ddos attack node that generates TCP SYN flood (do it randomly, chance of 50%)
        # h8 -> vulnerable node that h7 aims to attack
        if random.randint(1, 1000) <= 50:
            issue_command(h7, "echo \"DoS attack issued\"", run_bg=False)
            # issue_command(h7, "hping3 -c 1000 -d 10 -S -w 8 -p 80 -i u7000 --rand-source {}".format(h8.IP()))
    

if __name__ == '__main__':
    setLogLevel('info')

    topo = MyTopo()

    net = Mininet(topo, build=False)
    net.addController(c1)
    net.build()
    # net.addNAT() # to connect to internet
    net.start()

    generate_normal_traffic(net, video_service=False, open_video_player=False, file_transfer_service=False, http_service=False,
                            ddos_service=False)

    CLI( net )

    net.stop()