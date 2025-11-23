from unittest.mock import MagicMock, patch

from edge_sim_py.components.network_flow import NetworkFlow


def test_generate_next_hop():

    user = MagicMock()
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
        source=user,
        target=service1,
        start=0,
        path=[],
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

        flow._generate_next_hop(current_step=flow.end)

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
