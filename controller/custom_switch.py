from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_3_parser
from ryu.lib.packet import arp, ethernet, icmp, ipv4, packet
from ryu.lib import hub
import time
import logging
logging.getLogger().setLevel(logging.DEBUG)


class L3Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L3Switch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.ping_interval = 10 # Ping interval in seconds
        self.ping_timer = 0
        self.packet_count = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        # Get necessary data from the event
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        print("msg...pkt")

        # Parse the packet
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        if eth_pkt.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)
            self.handle_arp(datapath, in_port, eth_pkt, arp_pkt)
        elif eth_pkt.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            self.handle_ip(datapath, in_port, eth_pkt, ip_pkt)

    def handle_arp(self, datapath, in_port, eth_pkt, arp_pkt):
        # Learn the MAC address to port mapping
        src_mac = eth_pkt.src
        src_ip = arp_pkt.src_ip
        self.mac_to_port.setdefault(datapath.id, {})
        self.mac_to_port[datapath.id][src_mac] = in_port

        # Send an ARP reply if this is an ARP request for our IP address
        if arp_pkt.opcode == arp.ARP_REQUEST and src_ip == '10.0.0.1':
            dst_mac = eth_pkt.dst
            dst_ip = arp_pkt.dst_ip
            actions = [parser.OFPActionOutput(in_port)]
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=msg.data
            )
            datapath.send_msg(out)

    def handle_ip(self, datapath, in_port, eth_pkt, ip_pkt):
        # Learn the MAC address to port mapping
        src_mac = eth_pkt.src
        src_ip = ip_pkt.src
        self.mac_to_port.setdefault(datapath.id, {})
        self.mac_to_port[datapath.id][src_mac] = in_port

        # Periodically ping the switch and send packet stats to the controller using OFPStats
        current_time = time.time()
        if current_time - self.ping_timer > self.ping_interval:
            self.send_packet_stats(datapath)
            self.ping_timer = current_time

        # Handle ICMP echo request packets
        if ip_pkt.proto == inet.IPPROTO_ICMP and isinstance(ip_pkt.icmp, icmp.icmp_echo):
            dst_ip = ip_pkt.dst
            dst_mac = self.get_mac(datapath.id, dst_ip)

            # Forward the packet to the destination host
            if dst_mac:
                actions = [parser.OFPActionOutput(self.mac_to_port[datapath.id][dst_mac])]
                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=msg.buffer_id,
                    in_port=in_port,
                    actions=actions,
                    data=msg.data
                )
                datapath.send_msg(out)

        # Handle other IP packets
        else:
            # Flood the packet to all ports except the incoming port
            actions = []
            for port in self.mac_to_port[datapath.id].values():
                if port != in_port:
                    actions.append(parser.OFPActionOutput(port))
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=msg.data
            )
            datapath.send_msg(out)
        
    def send_packet_stats(self, datapath):
        # Create an OFPStatsRequest message for packet statistics
        req = parser.OFPStatsRequest(datapath, 0, parser.OFPPacketStatsRequest())

        # Send the message to the switch and wait for the response
        reply = datapath.send_msg(req)

        # Print the packet statistics to the console
        for stat in reply.body:
            print("Received %d packets from port %d" % (stat.packet_count, stat.port_no))
