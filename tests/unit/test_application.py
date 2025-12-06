from unittest.mock import MagicMock

import pytest
from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.user import User


def test_register_data_packet():

    app = Application()
    u = MagicMock(spec=User)
    u.id = 1

    app.users = [u]
    u.applications = [app]

    dp = app._register_datapacket(user=u, size=20)

    assert app._user_data_packets == {"1": [dp]}


def test_collect_with_data_packet():

    app = Application(obj_id=0)
    service = MagicMock(spec=Service)
    service.id = 1
    app.services = [service]
    u = MagicMock(spec=User)
    u.id = 2
    app.users = [u]

    data_packet = MagicMock(spec=DataPacket)

    link_hop = LinkHop(
        hop_index=0,
        link_index=2,
        source=3,
        target=4,
        start_time=0,
        end_time=3,
        queue_delay=3,
        transmission_delay=3,
        processing_delay=4,
        propagation_delay=8,
        min_bandwidth=10,
        max_bandwidth=30,
        avg_bandwidth=20,
        data_input=5,
        data_output=10,
    )

    data_packet.id = 3
    data_packet.user = u
    data_packet._queue_delay_total = 3
    data_packet._transmission_delay_total = 3
    data_packet._processing_delay_total = 4
    data_packet._propagation_delay_total = 8
    data_packet._total_delay = 18
    switch = MagicMock(spec=NetworkSwitch)
    switch.id = 3
    switch2 = MagicMock(spec=NetworkSwitch)
    switch2.id = 4
    data_packet._total_path = [[switch, switch2], [switch2, switch]]
    data_packet._link_hops = [link_hop]

    app._user_data_packets = {"1": [data_packet]}

    assert app.collect() == {
        "Id": 0,
        "Label": "",
        "Services": [1],
        "Users": [2],
        "Data packets": {
            "1": [
                {
                    "Id": 3,
                    "User": 2,
                    "Queue Delay": 3,
                    "Transmission Delay": 3,
                    "Processing Delay": 4,
                    "Propagation Delay": 8,
                    "Total Delay": 18,
                    "Total Path": [[3, 4], [4, 3]],
                    "Hops": [
                        {
                            "hop_index": 0,
                            "link_index": 2,
                            "source": 3,
                            "target": 4,
                            "start_time": 0,
                            "end_time": 3,
                            "queue_delay": 3,
                            "transmission_delay": 3,
                            "processing_delay": 4,
                            "propagation_delay": 8,
                            "min_bandwidth": 10,
                            "max_bandwidth": 30,
                            "avg_bandwidth": 20,
                            "data_input": 5,
                            "data_output": 10,
                        }
                    ],
                },
            ],
        },
    }


def test_connection_between_application_users():

    app = Application(obj_id=1)
    u = MagicMock(spec=User)
    u.id = 1
    u.communication_paths = {"1": []}

    with pytest.raises(ValueError, match="Connection between application users is not allowed."):
        app._register_datapacket(user=u, size=20)
