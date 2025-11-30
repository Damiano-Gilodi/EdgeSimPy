from unittest.mock import MagicMock, patch
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
