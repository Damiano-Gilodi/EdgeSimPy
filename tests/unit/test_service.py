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
    assert dp._processing_remaining_time == service.processing_time
    assert dp.size == service.processing_output
    assert service._processing_queue == [dp]


def test_step_processing():

    service = Service()
    service.processing_time = 4
    service.processing_output = 10

    model = MagicMock()
    service.model = model
    service.model.schedule.steps = 3

    dp = MagicMock(spec=DataPacket)
    dp._is_processing = True
    dp._processing_remaining_time = 1
    dp.size = 0
    dp._total_path = [[MagicMock(), MagicMock(), MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]
    dp._current_hop = 0

    dp._link_hops = [MagicMock()]
    dp._link_hops[-1].end_time = 3

    service._processing_queue = [dp]

    service.step()

    assert dp._processing_remaining_time == 0
    assert dp._is_processing is False
    assert service._processing_queue == []
    assert service._output_queue == [dp]

    service.step()

    dp._launch_next_flow.assert_called_once_with(start_step=7)
    assert service._output_queue == []
