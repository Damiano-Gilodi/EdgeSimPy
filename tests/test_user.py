from unittest.mock import MagicMock, patch
from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.user import User


def test_user_start_flow():

    user = User()
    app = MagicMock(spec=Application)
    app.id = 1
    mock_dp = MagicMock(spec=DataPacket)
    user.communication_paths = {"1": [1, 2]}

    with patch.object(user, "_generate_datapacket", return_value=mock_dp):

        user._start_flow(app, current_step=0)

        assert mock_dp.total_path == [1, 2]
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

    app._register_datapacket.assert_called_with(user=user, size=1)

    with patch("random.randint", return_value=10):

        user.set_packet_size_strategy(mode="random", min=1, max=100)

        user._generate_datapacket(app)

        app._register_datapacket.assert_called_with(user=user, size=10)
