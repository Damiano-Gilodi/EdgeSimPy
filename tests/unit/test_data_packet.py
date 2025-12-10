from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.user import User


def test_zero_negative_size():

    app = MagicMock(spec=Application)
    user = MagicMock(spec=User)

    with pytest.raises(ValueError, match="DataPacket size must be a positive integer."):
        DataPacket(user=user, application=app, size=0)

    with pytest.raises(ValueError, match="DataPacket size must be a positive integer."):
        DataPacket(user=user, application=app, size=-1)


def test_launch_next_flow():

    app = MagicMock(spec=Application)
    model = MagicMock()
    app.model = model

    dp = DataPacket(user=MagicMock(), application=app)
    switch1 = MagicMock(spec=NetworkSwitch)
    switch2 = MagicMock(spec=NetworkSwitch)
    dp._total_path = [[MagicMock(), switch1, switch2, MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]
    dp.size = 50
    dp._current_hop = 0
    dp._current_link = 1

    with patch("edge_sim_py.components.data_packet.NetworkFlow") as mock_flow:

        dp._launch_next_flow(start_step=4)

        mock_flow.assert_called_once_with(
            topology=dp.application.model.topology,
            source=switch1,
            target=switch2,
            path=[switch1, switch2],
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
    dp._total_path = [[MagicMock(), MagicMock(), MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 1}
    flow.end = 3

    fake_link_hop = MagicMock()

    with patch.object(dp, "_launch_next_flow") as mock_launch:
        with patch.object(dp, "_add_link_hop", return_value=fake_link_hop):

            dp._on_flow_finished(flow)

            mock_launch.assert_called_once_with(start_step=3)


def test_on_flow_finished_hop_complete():

    dp = DataPacket(user=MagicMock(), application=MagicMock())
    switch = MagicMock(spec=NetworkSwitch)
    dp._total_path = [[MagicMock(), MagicMock(), MagicMock(), switch], [MagicMock(), MagicMock(), MagicMock()]]

    server = MagicMock(spec=EdgeServer)
    switch.edge_servers = [server]

    service = MagicMock(spec=Service)
    service.server = server

    dp.application.services = [service]

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 2}

    with patch.object(dp, "_add_link_hop", return_value=MagicMock()):

        dp._on_flow_finished(flow)

        service._start_processing.assert_called_once_with(data_packet=dp)


def test_on_flow_finished_validation_link():

    dp = DataPacket(user=MagicMock(), application=MagicMock())
    dp._total_path = [[MagicMock(), MagicMock(), MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 3}  # valid link= 0:(1-2), 1:(2-3), 2:(3-4)

    with pytest.raises(IndexError, match="Index link out of range."):
        dp._on_flow_finished(flow)


def test_on_flow_finished_last_link_hop():

    dp = DataPacket(user=MagicMock(), application=MagicMock())
    switch = MagicMock(spec=NetworkSwitch)
    dp._total_path = [[MagicMock(), MagicMock(), MagicMock(), MagicMock()], [MagicMock(), MagicMock(), switch]]

    server = MagicMock(spec=EdgeServer)
    switch.edge_servers = [server]

    service = MagicMock(spec=Service)
    service.server = server

    dp.application.services = [MagicMock(), service]

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 1, "index_link": 1}

    with patch.object(dp, "_add_link_hop", return_value=MagicMock()):

        dp._on_flow_finished(flow)

        service._start_processing.assert_called_once_with(data_packet=dp)


def test_add_link_hop_intermediate_node():

    app = MagicMock(spec=Application)
    model = MagicMock()
    app.model = model

    dp = DataPacket(user=MagicMock(), application=app)
    switch1 = MagicMock(spec=NetworkSwitch)
    switch1.id = 1
    switch2 = MagicMock(spec=NetworkSwitch)
    switch2.id = 2
    dp._total_path = [[MagicMock(), switch1, switch2, MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]
    dp.size = 5

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 1}

    flow.source = switch1
    flow.target = switch2

    flow.start = 0
    flow.end = 4

    flow._queue_delay = 3

    flow.path = [switch1, switch2]
    flow.topology = {switch1: {switch2: {"delay": 8}}}

    flow._bandwidth_history = [10, 20, 30]

    link_hop = LinkHop(
        hop_index=0,
        link_index=1,
        source=1,
        target=2,
        start_time=0,
        end_time=4,
        queue_delay=3,
        transmission_delay=1,
        processing_delay=0,
        propagation_delay=8,
        min_bandwidth=10,
        max_bandwidth=30,
        avg_bandwidth=20,
        data_input=5,
        data_output=5,
    )

    dp._on_flow_finished(flow)

    assert dp.get_hops() == [link_hop]


def test_add_link_hop_complete():

    app = MagicMock(spec=Application)
    model = MagicMock()
    app.model = model
    service = MagicMock(spec=Service)
    service.processing_time = 4
    service.processing_output = 10
    app.services = [service]

    dp = DataPacket(user=MagicMock(), application=app)
    switch1 = MagicMock(spec=NetworkSwitch)
    switch1.id = 1
    switch2 = MagicMock(spec=NetworkSwitch)
    switch2.id = 2
    dp._total_path = [[MagicMock(), MagicMock(), switch1, switch2], [MagicMock(), MagicMock(), MagicMock()]]
    dp.size = 5

    flow = MagicMock(spec=NetworkFlow)
    flow.metadata = {"index_hop": 0, "index_link": 2}

    flow.source = switch1
    flow.target = switch2

    flow.start = 0
    flow.end = 4

    flow._queue_delay = 3

    flow.path = [switch1, switch2]
    flow.topology = {switch1: {switch2: {"delay": 8}}}

    flow._bandwidth_history = [10, 20, 30]

    server = MagicMock(spec=EdgeServer)
    switch2.edge_servers = [server]
    service.server = server

    link_hop = LinkHop(
        hop_index=0,
        link_index=2,
        source=1,
        target=2,
        start_time=0,
        end_time=4,
        queue_delay=3,
        transmission_delay=1,
        processing_delay=4,
        propagation_delay=8,
        min_bandwidth=10,
        max_bandwidth=30,
        avg_bandwidth=20,
        data_input=5,
        data_output=10,
    )

    dp._on_flow_finished(flow)

    assert dp.get_hops() == [link_hop]


def test_collect():

    dp = DataPacket(user=MagicMock(), application=MagicMock())
    switch = MagicMock(spec=NetworkSwitch)
    switch.id = 3
    switch2 = MagicMock(spec=NetworkSwitch)
    switch2.id = 4
    dp._total_path = [[switch, switch2, switch, switch2], [switch2, switch2, switch2]]
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
    dp._link_hops = [link_hop]

    expected_metrics = {
        "Id": dp.id,
        "User": dp.user.id,
        "Application": dp.application.id,
        "Size": dp.size,
        "Queue Delay": 3,
        "Transmission Delay": 3,
        "Processing Delay": 4,
        "Propagation Delay": 8,
        "Total Delay": 18,
        "Total Path": [[3, 4, 3, 4], [4, 4, 4]],
        "Hops": [asdict(link_hop)],
    }

    assert dp.collect() == expected_metrics


def test_to_dict():

    dp = DataPacket(user=MagicMock(), application=MagicMock())
    switch = MagicMock(spec=NetworkSwitch)
    switch.id = 3
    switch2 = MagicMock(spec=NetworkSwitch)
    switch2.id = 4
    dp._total_path = [[switch, switch2, switch, switch2], [switch2, switch2, switch2]]
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
    dp._link_hops = [link_hop]

    expected_metrics = {
        "id": dp.id,
        "user": dp.user.id,
        "application": dp.application.id,
        "size": dp.size,
        "current_hop": dp._current_hop,
        "current_link": dp._current_link,
        "is_processing": dp._is_processing,
        "processing_remaining_time": dp._processing_remaining_time,
        "total_path": [[sw.id for sw in hop] for hop in dp._total_path],
        "hops": [asdict(h) for h in dp._link_hops],
    }

    assert dp._to_dict() == expected_metrics
