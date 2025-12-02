from unittest.mock import MagicMock, patch

import pytest

from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
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


def test_on_flow_finished_intermediate_node():

    dp = DataPacket(user=MagicMock(), application=MagicMock())
    dp.total_path = [[1, 2, 3, 4], [4, 5, 6]]

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 1}
    flow.end = 3

    fake_link_hop = MagicMock()

    with patch.object(dp, "launch_next_flow") as mock_launch:
        with patch.object(dp, "add_link_hop", return_value=fake_link_hop):

            dp.on_flow_finished(flow)

            mock_launch.assert_called_once_with(start_step=3)


def test_on_flow_finished_hop_complete():

    dp = DataPacket(user=MagicMock(), application=MagicMock())
    dp.total_path = [[1, 2, 3, 4], [4, 5, 6]]

    switch = MagicMock(spec=NetworkSwitch)
    server = MagicMock(spec=EdgeServer)
    switch.edge_servers = [server]

    service = MagicMock(spec=Service)
    service.server = server

    dp.application.services = [service]

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 2}

    fake_link_hop = MagicMock()

    with patch("edge_sim_py.components.network_switch.NetworkSwitch.find_by_id", return_value=switch):
        with patch.object(dp, "add_link_hop", return_value=fake_link_hop):

            dp.on_flow_finished(flow)

            service.start_processing.assert_called_once_with(data_packet=dp)


def test_add_link_hop_intermediate_node():

    app = MagicMock(spec=Application)
    model = MagicMock()
    app.model = model

    dp = DataPacket(user=MagicMock(), application=app)
    dp.total_path = [[1, 2, 3, 4], [4, 5, 6]]
    dp.size = 5

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 1}

    flow.source = MagicMock(spec=NetworkSwitch)
    flow.target = MagicMock(spec=NetworkSwitch)
    flow.source.id = 2
    flow.target.id = 3

    flow.start = 0
    flow.end = 3

    flow.queue_delay = 3

    flow.path = [2, 3]
    flow.topology = {2: {3: {"delay": 8}}}

    flow.bandwidth_history = [10, 20, 30]

    link_hop = LinkHop(
        hop_index=0,
        link_index=1,
        source="2",
        target="3",
        start_time=0,
        end_time=3,
        queue_delay=3,
        transmission_delay=3,
        processing_delay=0,
        propagation_delay=8,
        min_bandwidth=10,
        max_bandwidth=30,
        avg_bandwidth=20,
        data_input=5,
        data_output=5,
    )

    dp.on_flow_finished(flow)

    assert dp.getHops() == [link_hop]


def test_add_link_hop_complete():

    app = MagicMock(spec=Application)
    model = MagicMock()
    app.model = model
    service = MagicMock(spec=Service)
    service.processing_time = 4
    service.processing_output = 10
    app.services = [service]

    dp = DataPacket(user=MagicMock(), application=app)
    dp.total_path = [[1, 2, 3, 4], [4, 5, 6]]
    dp.size = 5

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 2}

    flow.source = MagicMock(spec=NetworkSwitch)
    flow.target = MagicMock(spec=NetworkSwitch)
    flow.source.id = 3
    flow.target.id = 4

    flow.start = 0
    flow.end = 3

    flow.queue_delay = 3

    flow.path = [3, 4]
    flow.topology = {3: {4: {"delay": 8}}}

    flow.bandwidth_history = [10, 20, 30]

    server = MagicMock(spec=EdgeServer)
    switch = MagicMock(spec=NetworkSwitch)
    switch.edge_servers = [server]
    service.server = server

    with patch("edge_sim_py.components.network_switch.NetworkSwitch.find_by_id", return_value=switch):

        link_hop = LinkHop(
            hop_index=0,
            link_index=2,
            source="3",
            target="4",
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

        dp.on_flow_finished(flow)

        assert dp.getHops() == [link_hop]
