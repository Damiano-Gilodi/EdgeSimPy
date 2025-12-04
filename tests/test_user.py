import random
from unittest.mock import MagicMock, patch

from numpy import size
from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.user import User


def test_user_start_flow():

    user = User()
    app = MagicMock(spec=Application)
    app.id = 1
    mock_dp = MagicMock(spec=DataPacket)

    with patch.object(app, "register_data_packet", return_value=mock_dp):
        with patch.object(user, "set_communication_path", return_value=MagicMock()):

            user._start_flow(app, current_step=0)

            mock_dp.launch_next_flow.assert_called_once_with(start_step=0)


def test_set_packet_size_strategy():

    user = User()

    user.set_packet_size_strategy(mode="fixed", size=1)

    assert user.packet_size_strategy == {
        "mode": "fixed",
        "size": 1,
        "min": 0,
        "max": 0,
    }

    user.set_packet_size_strategy(mode="random", min=1, max=100)

    assert user.packet_size_strategy == {
        "mode": "random",
        "size": 0,
        "min": 1,
        "max": 100,
    }


def test_generate_datapacket():

    user = User()
    app = MagicMock(spec=Application)

    user.set_packet_size_strategy(mode="fixed", size=1)

    user._generate_datapacket(app)

    app.register_data_packet.assert_called_with(user=user, size=1)

    with patch("random.randint", return_value=10):

        user.set_packet_size_strategy(mode="random", min=1, max=100)

        user._generate_datapacket(app)

        app.register_data_packet.assert_called_with(user=user, size=10)
