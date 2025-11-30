from unittest.mock import MagicMock
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.service import Service


def test_start_processing():

    service = Service()
    service.processing_time = 4
    service.processing_output = 10

    dp = MagicMock(spec=DataPacket)
    dp.is_processing = False
    dp.processing_remaining_time = 0
    dp.size = 0

    service.start_processing(dp)

    assert dp.is_processing is True
    assert dp.processing_remaining_time == service.processing_time
    assert dp.size == service.processing_output
    assert service.processing_queue == [dp]
