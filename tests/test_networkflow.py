from unittest.mock import MagicMock
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.network_flow import NetworkFlow


def test_step_flow_data_packet():

    flow = NetworkFlow()
    flow.status = "active"
    flow.bandwidth = {0: 10, 1: 10, 2: 10}
    flow.data_to_transfer = 0

    dp = MagicMock(spec=DataPacket)
    flow.metadata = {
        "type": "data_packet",
        "object": dp,
        "index_hop": 0,
        "index_link": 1,
    }

    model = MagicMock()
    flow.model = model

    flow.step()

    dp._on_flow_finished.assert_called_once_with(flow)

    flow.model.schedule.remove.assert_called_once_with(flow)
