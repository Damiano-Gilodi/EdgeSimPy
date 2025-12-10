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


def test_collect():

    app = Application(obj_id=0)
    service = MagicMock(spec=Service)
    service.id = 1
    app.services = [service]
    u = MagicMock(spec=User)
    u.id = 2
    app.users = [u]

    data_packet = MagicMock(spec=DataPacket)
    data_packet.id = 3

    app._user_data_packets = {str(u.id): [data_packet]}

    assert app.collect() == {
        "Id": 0,
        "Label": "",
        "Services": [1],
        "Users": [2],
        "Data packets": {"2": [3]},
    }


def test_connection_between_application_users():

    app = Application(obj_id=1)
    u = MagicMock(spec=User)
    u.id = 1
    u.communication_paths = {"1": []}

    with pytest.raises(ValueError, match="Connection between application users is not allowed."):
        app._register_datapacket(user=u, size=20)
