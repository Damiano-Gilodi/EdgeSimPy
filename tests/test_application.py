from unittest.mock import MagicMock
from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.user import User


def test_register_data_packet():

    app = Application()
    u = MagicMock(spec=User)
    u.id = 1
    dp = app.register_data_packet(user=u, size=20)

    assert app._user_data_packets == {"1": [dp]}


def test_collect():

    app = Application(obj_id=0)
    app.services = [MagicMock(spec=DataPacket)]
    u = MagicMock(spec=User)
    u.id = 1
    app.users = [u]
    app._user_data_packets = {"1": [MagicMock(spec=DataPacket)]}

    assert app.collect() == {
        "Id": 0,
        "Label": "",
        "Services": app.services,
        "Users": app.users,
        "Data packets": app._user_data_packets,
    }
