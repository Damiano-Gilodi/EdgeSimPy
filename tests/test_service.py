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

    service._start_processing(dp)

    assert dp.is_processing is True
    assert dp.processing_remaining_time == service.processing_time
    assert dp.size == service.processing_output
    assert service.processing_queue == [dp]


def test_step_processing():

    service = Service()
    service.processing_time = 4
    service.processing_output = 10

    model = MagicMock()
    service.model = model
    service.model.schedule.steps = 3

    dp = MagicMock(spec=DataPacket)
    dp.is_processing = True
    dp.processing_remaining_time = 1
    dp.size = 0

    service.processing_queue = [dp]

    service.step()

    assert dp.processing_remaining_time == 0
    assert dp.is_processing is False
    assert service.processing_queue == []
    dp._launch_next_flow.assert_called_once_with(start_step=4)
