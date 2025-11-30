from unittest.mock import MagicMock, patch

import pytest

from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.user import User


def test_to_dict():

    app = MagicMock(spec=Application)
    app.id = 0
    user = MagicMock(spec=User)
    user.id = 0

    dp = DataPacket(user=user, application=app, obj_id=1, size=10)

    assert dp._to_dict() == {
        "attributes": {
            "id": 1,
            "size": 10,
        },
        "relationships": {
            "application": {"class": type(app).__name__, "id": 0},
            "user": {"class": type(user).__name__, "id": 0},
        },
    }


def test_add_hop():

    app = MagicMock(spec=Application)
    user = MagicMock(spec=User)
    dp = DataPacket(user=user, application=app, obj_id=1, size=10)

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


def test_zero_negative_size():

    app = MagicMock(spec=Application)
    user = MagicMock(spec=User)

    with pytest.raises(ValueError, match="DataPacket size must be a positive integer."):
        DataPacket(user=user, application=app, size=0)

    with pytest.raises(ValueError, match="DataPacket size must be a positive integer."):
        DataPacket(user=user, application=app, size=-1)


def test_collect():

    app = MagicMock(spec=Application)
    app.id = 0
    user = MagicMock(spec=User)
    user.id = 0

    dp = DataPacket(user=user, application=app, obj_id=1, size=10)

    assert dp.collect() == {
        "Id": 1,
        "Application Id": 0,
        "User Id": 0,
        "Size": 10,
        "Queue delay total": 0,
        "Transmission delay total": 0,
        "Processing delay total": 0,
        "Propagation delay total": 0,
        "Total delay": 0,
        "Total path": [],
        "Hops": [],
    }


def test_launch_next_flow():

    app = MagicMock(spec=Application)
    model = MagicMock()
    app.model = model

    dp = DataPacket(user=MagicMock(), application=app)
    dp.total_path = [[1, 2, 3], [4, 5, 6]]
    dp.size = 50
    dp.current_hop = 0
    dp.current_link = 1

    with patch("edge_sim_py.components.data_packet.NetworkFlow") as mock_flow:

        dp.launch_next_flow(start_step=4)

        mock_flow.assert_called_once_with(
            topology=dp.application.model.topology,
            source=2,
            target=3,
            path=[2, 3],
            start=4,
            data_to_transfer=50,
            metadata={
                "type": "data_packet",
                "object": dp,
                "index_hop": 0,
                "index_link": 1,
            },
        )

        dp.application.model.initialize_agent.assert_called_once_with(mock_flow.return_value)
