from unittest.mock import MagicMock
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.service import Service


def test_start_processing():

    service = Service()
    service.processing_time = 4
    service.processing_output = 10

    dp = MagicMock(spec=DataPacket)
    dp._is_processing = False
    dp._processing_remaining_time = 0
    dp.size = 0

    service._start_processing(dp)

    assert dp._is_processing is True
    assert dp._processing_remaining_time == service.processing_time + 1
    assert dp.size == service.processing_output
