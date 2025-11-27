from unittest.mock import MagicMock, patch
from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.user import User


def test_user_start_flow():

    user = User()
    app = MagicMock(spec=Application)
    app.id = 1
    mock_dp = MagicMock(spec=DataPacket)

    with patch.object(app, "register_data_packet", return_value=mock_dp):
        with patch.object(user, "set_communication_path", return_value=[[1, 2, 3]]):
            with patch("edge_sim_py.components.user.NetworkFlow") as mock_flow:

                mock_dp.total_path = [[1, 2, 3]]
                mock_dp.size = 50
                user._start_flow(app, current_step=0)

                mock_flow.assert_called_once_with(
                    source=1,
                    target=2,
                    path=[1, 2],
                    start=0,
                    data_to_transfer=50,
                    metadata={
                        "type": "data_packet",
                        "object": mock_dp,
                        "index_hop": 0,
                        "index_link": 0,
                    },
                )
