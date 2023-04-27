# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub

from database.mongo import MongoDB
from configuration import get_controller_timeperiod

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = []
        self.flow_stats = {}
        self.total_pkt_cnts = 0
        self.timeperiod = get_controller_timeperiod()
        self.init_database()
        self.monitor_thread = hub.spawn(self._monitor)
    
    def init_database(self):
        self.logger.info("\n===================================\n")
        self.logger.info("** CONNECTING TO MONGO-DB ATLAS ...")
        self.mongoDB = MongoDB("majordb", "test1")
        self.logger.info("** TESTING DATABASE CONNECTION ...")
        self.mongoDB.issue_ping()
        self.logger.info("\n===================================\n")
    
    def _monitor(self):
        while True:
            self.logger.info("\n===================================\n")
            self.logger.info("** STATS REQUEST SENT ...")
            for datapath in self.datapaths:
                self.send_flow_stats_request(datapath)
            hub.sleep(self.timeperiod)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths.append(datapath)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
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

    def send_flow_stats_request(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath, 0, ofproto.OFPTT_ALL,
                                        ofproto.OFPP_ANY, ofproto.OFPG_ANY,
                                        0, 0, parser.OFPMatch())
        datapath.send_msg(req)
    
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_handler(self, ev):
        # Extract the OFPStatsReply object from the event
        reply = ev.msg.body

        # Define the print_flow_stats function
        def print_flow_stats(flow_stats):
            print("  OFPFlowStats:")

            # To print out all possible parameters, use this
            # for attr, value in flow_stats.__dict__.items():
            #     if not attr.startswith('_'):
            #         print(f"    {attr}: {value}")

            """
            length: The total length of the flow stats message, in bytes, including the header.
            table_id: The ID of the table where the flow entry is installed. (basically switch ID)
            duration_sec: The number of seconds that the flow has been active.
            duration_nsec: The number of nanoseconds that the flow has been active beyond duration_sec.
            priority: The priority of the flow entry.
            idle_timeout: The number of seconds that the flow can be idle before being removed from the table.
            hard_timeout: The number of seconds that the flow can exist before being removed from the table, 
                        regardless of whether it is idle or not.
            flags: A bitfield of flags indicating the properties of the flow entry. 
                        Currently defined flags are OFPFF_SEND_FLOW_REM, which indicates that a flow removed 
                        message should be sent when the flow is removed, and OFPFF_CHECK_OVERLAP, which indicates 
                        that the flow entry should be checked for overlap with other entries in the table.
            cookie: A value that can be used by the controller to store state associated with the flow entry.
            packet_count: The number of packets that have matched the flow entry.
            byte_count: The number of bytes that have been matched by the flow entry.
            match: The OFPMatch object that represents the match fields for the flow entry.
            instructions: A list of OFPInstruction objects that represent the instructions for processing packets 
                        that match the flow entry. In this case, there is a single instruction, an OFPInstructionActions 
                        object, which specifies a single output action that sends packets out a specific port.
            """

            print(f"    length: {flow_stats.length}")
            print(f"    duration_sec: {flow_stats.duration_sec}")
            print(f"    cookie: {flow_stats.cookie}")
            print(f"    packet_count: {flow_stats.packet_count}")
            print(f"    byte_count: {flow_stats.byte_count}")
            print("    match:")
            for field, value in flow_stats.match.items():
                print(f"      {field}: {value}")
            print("    instructions:")
            for instruction in flow_stats.instructions:
                print(f"      - {instruction.__class__.__name__}:")
                for attr, value in instruction.__dict__.items():
                    if not attr.startswith('_'):
                        print(f"        {attr}: {value}")

        # Define the print_stats_reply function
        def print_stats_reply(reply):
            print("OFPStatsReply:")
            for stat in reply:
                print_flow_stats(stat)

        # Call the print_stats_reply function on the OFPStatsReply object
        print_stats_reply(reply)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)