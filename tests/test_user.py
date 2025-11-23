import copy
from unittest.mock import MagicMock, patch
from edge_sim_py.components import data_packet
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.user import User


def test_user_create_first_flow_hop():

    app = MagicMock()
    app.id = 1
    app.data_packet = MagicMock()
    app.data_packet.size = 100

    service1 = MagicMock()
    service2 = MagicMock()
    service1.server = MagicMock()
    service2.server = MagicMock()

    app.services = [service1, service2]

    user = User(1)
    model = MagicMock()
    user.model = model

    with patch("edge_sim_py.components.user.NetworkFlow") as MockFlow:

        fake_path = [[1, 2, 3], [4, 5, 6]]
        with patch.object(user, "set_communication_path", return_value=fake_path):

            user._create_first_flow_hop(app, current_step=5)

            MockFlow.assert_called_once_with(
                topology=model.topology,
                source=app.services[0].server,
                target=app.services[1].server,
                start=5,
                path=[1, 2, 3],
                data_to_transfer=100,
                metadata={
                    "type": "data_hop",
                    "object": app.data_packet,
                    "paths": fake_path,
                    "hop_index": 0,
                    "user": user,
                    "app": app,
                },
            )

            model.initialize_agent.assert_called_once_with(MockFlow.return_value)
