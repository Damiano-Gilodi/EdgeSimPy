from unittest.mock import MagicMock

from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket


def test_to_dict():

    app = MagicMock(spec=Application)
    app.id = 0

    dp = DataPacket(obj_id=1, size=10)
    dp.connect_to_app(app)

    assert dp._to_dict() == {
        "attributes": {
            "id": 1,
            "size": 10,
            "queue_delay_total": 0,
            "transmission_delay_total": 0,
            "processing_delay_total": 0,
            "propagation_delay_total": 0,
            "total_delay": 0,
            "hops": [],
        },
        "relationships": {
            "application": {"class": type(app).__name__, "id": 0},
        },
    }
