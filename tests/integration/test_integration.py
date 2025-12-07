from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.topology import Topology


def test_integration_start_flows(small_app_1_user_4_services):

    user = small_app_1_user_4_services["user"]
    app = small_app_1_user_4_services["application"]

    for i in range(5):  # 3 requests true [1,3,5]

        user.step()

        user.model.schedule.steps += 1

    assert len(NetworkFlow.all()) == 3
    assert len(DataPacket.all()) == 3

    datapacket = DataPacket.all()[0]
    assert datapacket.size == 20
    assert datapacket.user == user
    assert datapacket.application == app

    assert app._user_data_packets == {"1": DataPacket.all()}

    assert user.communication_paths[str(app.id)] == [[1, 2], [2, 4], [4, 5, 6], [6, 5, 8]]
    assert datapacket._total_path == [[NetworkSwitch.find_by_id(i) for i in p] for p in user.communication_paths[str(app.id)]]

    flow = NetworkFlow.all()[0]
    net_switch1 = NetworkSwitch.find_by_id(1)
    net_switch2 = NetworkSwitch.find_by_id(2)
    assert flow.source == net_switch1
    assert flow.target == net_switch2
    assert flow.path == [net_switch1, net_switch2]
    assert flow.start == 1
    assert flow.data_to_transfer == 20
    assert flow.metadata == {"type": "data_packet", "object": DataPacket.all()[0], "index_hop": 0, "index_link": 0}


def test_integration_complete_Networkflow(small_app_1_user_4_services):

    user = small_app_1_user_4_services["user"]
    app = small_app_1_user_4_services["application"]
    services = sorted(small_app_1_user_4_services["services"], key=lambda b: b.id)

    for i in range(3):  # 2 requests true [1,3]

        for agent in Topology.all():
            agent.step()

        for agent in NetworkFlow.all():
            agent.step()

        user.step()

        user.model.schedule.steps += 1

    assert len(NetworkFlow.all()) == 2
    assert len(DataPacket.all()) == 2

    datapacket1 = DataPacket.all()[0]
    datapacket2 = DataPacket.all()[1]

    assert len(datapacket1.get_hops()) == 1
    assert len(datapacket2.get_hops()) == 0

    assert datapacket1.size == 21
    assert datapacket1._is_processing is True
    assert datapacket1._processing_remaining_time == 5
    assert services[0]._processing_queue == [datapacket1]

    assert datapacket1.total_delay == 8
    assert datapacket1.transmission_delay_total == 2
    assert datapacket1.processing_delay_total == 5
    assert datapacket1.propagation_delay_total == 1
    assert datapacket1.queue_delay_total == 0
    assert datapacket1.get_hops()[0] == LinkHop(
        hop_index=0,
        link_index=0,
        source=1,
        target=2,
        start_time=1,
        end_time=3,
        queue_delay=0,
        transmission_delay=2,
        processing_delay=5,
        propagation_delay=1,
        min_bandwidth=10,
        max_bandwidth=10,
        avg_bandwidth=10,
        data_input=20,
        data_output=21,
    )
