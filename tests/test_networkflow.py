from unittest.mock import MagicMock, patch

from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.network_flow import NetworkFlow


def test_generate_next_hop():

    app = MagicMock()
    service1 = MagicMock()
    service1.id = 1
    service2 = MagicMock()
    service2.id = 2
    service3 = MagicMock()
    service3.id = 3
    app.services = [service1, service2, service3]
    app.processing_services = {"1": (1, 10), "2": (2, 30), "3": (3, 50)}

    flow = NetworkFlow(
        topology=MagicMock(),
        status="finished",
        source=MagicMock(),
        target=service1,
        start=0,
        path=MagicMock(),
        data_to_transfer=0,
        metadata={
            "type": "data_hop",
            "object": MagicMock(),
            "paths": MagicMock(),
            "hop_index": 0,
            "user": MagicMock(),
            "app": app,
        },
    )
    flow.end = 10
    model = MagicMock()
    flow.model = model

    with patch("edge_sim_py.components.network_flow.NetworkFlow") as MockFlow:

        flow._generate_next_hop()

        delay_output, size_output = app.processing_services[str(flow.target.id)]
        next_hop_index = flow.metadata["hop_index"] + 1

        MockFlow.assert_called_once_with(
            topology=flow.topology,
            source=flow.target,
            target=app.services[next_hop_index],
            start=flow.end,
            path=flow.metadata["paths"][next_hop_index],
            data_to_transfer=size_output,
            metadata={
                "type": "data_hop",
                "object": flow.metadata["object"],
                "paths": flow.metadata["paths"],
                "hop_index": next_hop_index,
                "user": flow.metadata["user"],
                "app": flow.metadata["app"],
            },
        )

        flow.model.initialize_agent.assert_called_once_with(MockFlow.return_value)


def test_generate_next_hop_no_more_hops():

    app = MagicMock()
    service1 = MagicMock()
    service1.id = 1
    service2 = MagicMock()
    service2.id = 2
    app.services = [service1, service2]
    app.processing_services = {"1": (1, 10), "2": (2, 30)}

    flow = NetworkFlow(
        topology=MagicMock(),
        status="finished",
        source=service1,
        target=service2,
        start=0,
        path=[],
        data_to_transfer=0,
        metadata={
            "type": "data_hop",
            "object": MagicMock(),
            "paths": MagicMock(),
            "hop_index": 1,  # Last hop
            "user": MagicMock(),
            "app": app,
        },
    )
    flow.end = 10
    model = MagicMock()
    flow.model = model

    with patch("edge_sim_py.components.network_flow.NetworkFlow") as MockFlow:

        flow._generate_next_hop()

        MockFlow.assert_not_called()


def test_update_data_packet():

    data = MagicMock(DataPacket)
    data.size = 100
    app = MagicMock()
    data.connect_to_app(app)

    service1 = MagicMock()
    service1.id = 1
    service2 = MagicMock()
    service2.id = 2
    service3 = MagicMock()
    service3.id = 3
    app.services = [service1, service2, service3]
    app.processing_services = {"1": (1, 10), "2": (2, 30), "3": (3, 50)}

    flow = NetworkFlow(
        topology=MagicMock(),
        status="finished",
        source=MagicMock(),
        target=service1,
        start=0,
        path=[1, 2, 3],
        data_to_transfer=data.size,
        metadata={
            "type": "data_hop",
            "object": data,
            "paths": MagicMock(),
            "queue_delay": 5,
            "hop_index": 0,
            "user": MagicMock(),
            "app": app,
        },
    )
    flow.end = 10
    model = MagicMock()
    flow.model = model

    flow._update_data_packet()
    delay_processing, size_output = app.processing_services[str(flow.target.id)]

    prop_delay = 0
    for i in range(0, len(flow.path) - 1):
        link = flow.topology[flow.path[i]][flow.path[i + 1]]
        prop_delay += link["delay"]

    data.add_hop.assert_called_once_with(
        start_service_id=flow.source.id,
        target_service_id=flow.target.id,
        path=flow.path,
        size_start=data.size,
        size_target_processing=size_output,
        queue_delay=flow.metadata["queue_delay"],
        transmission_delay=flow.end - flow.start,
        target_processing_delay=delay_processing,
        propagation_delay=prop_delay,
    )
