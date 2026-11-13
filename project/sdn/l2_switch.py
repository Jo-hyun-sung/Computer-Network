"""OS-Ken L2 학습 스위치 (P4, OpenFlow 1.3).

Mininet 스위치를 OS-Ken 컨트롤러가 제어하게 하는 기본 앱입니다.
표준 learning switch: 출발지 MAC을 보고 어느 포트에 있는지 배우고, 목적지가
알려진 포트면 그 포트로만, 모르면 전체로 보냅니다.

12주차에 이 앱을 확장해 경보가 오면 공격자 포트/ MAC에 차단 규칙(drop)을 설치합니다.

실행:
    PYTHONPATH=<project> osken-manager sdn.l2_switch
그리고 다른 터미널에서:
    sudo python3 env/run.py arp_spoof --controller remote
"""

from __future__ import annotations

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                       set_ev_cls)
from os_ken.lib.packet import ethernet, packet
from os_ken.ofproto import ofproto_v1_3


class L2Switch(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mac_to_port = {}  # dpid -> {mac: port}

    def add_flow(self, dp, priority, match, actions, buffer_id=None):
        ofp, parser = dp.ofproto, dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        kw = dict(datapath=dp, priority=priority, match=match, instructions=inst)
        if buffer_id is not None:
            kw["buffer_id"] = buffer_id
        dp.send_msg(parser.OFPFlowMod(**kw))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def features_handler(self, ev):
        dp = ev.msg.datapath
        ofp, parser = dp.ofproto, dp.ofproto_parser
        # table-miss: 모르는 패킷은 컨트롤러로
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions)
        self.logger.info("switch %s 연결됨", dp.id)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp, parser = dp.ofproto, dp.ofproto_parser
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        src, dst = eth.src, eth.dst

        self.mac_to_port.setdefault(dp.id, {})
        self.mac_to_port[dp.id][src] = in_port  # 학습

        out_port = self.mac_to_port[dp.id].get(dst, ofp.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]

        # 목적지를 알면 흐름 규칙을 설치해 다음부터는 컨트롤러를 안 거침
        if out_port != ofp.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(dp, 1, match, actions,
                          buffer_id=msg.buffer_id if msg.buffer_id != ofp.OFP_NO_BUFFER else None)
            if msg.buffer_id != ofp.OFP_NO_BUFFER:
                return

        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        dp.send_msg(parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data=data))
