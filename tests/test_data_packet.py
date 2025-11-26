from unittest.mock import MagicMock

from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.network_switch import NetworkSwitch


def test_to_dict():

    app = MagicMock(spec=Application)
    app.id = 0

    dp = DataPacket(obj_id=1, size=10)
    dp.connect_to_app(app)

    assert dp._to_dict() == {
        "attributes": {
            "id": 1,
            "size": 10,
            "queue_delay_total": 0,
            "transmission_delay_total": 0,
            "processing_delay_total": 0,
            "propagation_delay_total": 0,
            "total_delay": 0,
            "hops": [],
        },
        "relationships": {
            "application": {"class": type(app).__name__, "id": 0},
        },
    }


def test_add_hop():

    dp = DataPacket(obj_id=1, size=10)

    sw1 = MagicMock(spec=NetworkSwitch)
    sw1.id = 0
    sw2 = MagicMock(spec=NetworkSwitch)
    sw2.id = 1

    link_hop = LinkHop(
        hop_index=2,
        link_index=0,
        source="0",
        target="1",
        start_time=0,
        end_time=3,
        queue_delay=5,
        transmission_delay=10,
        processing_delay=0,
        propagation_delay=20,
        bandwidth=100,
        data_input=10,
        data_output=10,
    )

    dp.add_link_hop(link_hop)
    dp.add_link_hop(link_hop)

    assert dp.getHops() == [link_hop, link_hop]
