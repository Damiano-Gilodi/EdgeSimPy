from unittest.mock import MagicMock, patch
from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.user import User


def test_user_start_flow():

    user = User()
    app = MagicMock(spec=Application)
    app.id = 1
    mock_dp = MagicMock(spec=DataPacket)
    user.communication_paths = {"1": [[1, 2]]}

    model = MagicMock()
    user.model = model

    switch = MagicMock(spec=NetworkSwitch)
    with patch.object(user, "_generate_datapacket", return_value=mock_dp):
        with patch("edge_sim_py.components.network_switch.NetworkSwitch.find_by_id", return_value=switch):

            user._start_flow(app)

            assert mock_dp._total_path == [[switch, switch]]

            user.model.inizialize_agent.assert_called_once_with(mock_dp)


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
