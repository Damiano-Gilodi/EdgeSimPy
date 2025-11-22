from edge_sim_py.components.application import Application
from edge_sim_py.components.data_packet import DataPacket


def test_data_packet_to_dict():

    app = Application(1)

    expected = {
        "attributes": {
            "id": 1,
            "size": 10,
            "queue_delay_total": 0,
            "transmission_delay_total": 0,
            "processing_delay_total": 0,
            "propagation_delay_total": 0,
            "hops": [
                {
                    "service_id_start": 1,
                    "service_id_target": 2,
                    "path": [],
                    "size_start": 10,
                    "size_target_processing": 0,
                    "queue_delay": 0,
                    "transmission_delay": 0,
                    "target_processing_delay": 0,
                    "propagation_delay": 0,
                }
            ],
        },
        "relationships": {
            "application": app,
        },
    }

    data = DataPacket(obj_id=1, size=10)
    data.connect_to_app(app)
    data.add_hop(1, 2, [], 10, 0, 0, 0, 0, 0)

    assert data._to_dict() == expected


def test_data_packet_collect():

    app = Application(1)

    expected = {
        "Instance ID": 1,
        "Application": app.id,
        "Size": 10,
        "Queue delay total": 0,
        "Transmission delay total": 0,
        "Processing delay total": 0,
        "Propagation delay total": 0,
        "Hops": [
            {
                "service_id_start": 1,
                "service_id_target": 2,
                "path": [],
                "size_start": 10,
                "size_target_processing": 0,
                "queue_delay": 0,
                "transmission_delay": 0,
                "target_processing_delay": 0,
                "propagation_delay": 0,
            }
        ],
    }

    data = DataPacket(obj_id=1, size=10)
    data.connect_to_app(app)
    data.add_hop(1, 2, [], 10, 0, 0, 0, 0, 0)

    assert data.collect() == expected
