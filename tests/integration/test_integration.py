from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.user import User
from edge_sim_py.components.user_access_patterns.circular_duration_and_interval_access_pattern import CircularDurationAndIntervalAccessPattern


def test_integration_start_flows(small_app_2_user_4_services):

    user = small_app_2_user_4_services["user"][0]
    app = small_app_2_user_4_services["application"]
    CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[1])

    for _ in range(6):  # 3 requests true [1,3,5]

        for agent in DataPacket.all():
            agent.step()

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

    assert datapacket._current_flow == flow


def test_integration_complete_Networkflow(small_app_2_user_4_services):

    user = small_app_2_user_4_services["user"][0]
    app = small_app_2_user_4_services["application"]
    CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[1])

    for _ in range(4):  # 2 requests true [1,3]

        for agent in DataPacket.all():
            print(agent.get_hops())
            agent.step()

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

    assert datapacket1.size == 20
    assert datapacket1._is_processing is True
    assert datapacket1._processing_remaining_time == 2

    assert datapacket1.total_delay == 5
    assert datapacket1.transmission_delay_total == 2
    assert datapacket1.processing_delay_total == 2
    assert datapacket1.propagation_delay_total == 1
    assert datapacket1.queue_delay_total == 0
    assert datapacket1.get_hops()[0] == LinkHop(
        hop_index=0,
        link_index=0,
        source=1,
        target=2,
        start_time=1,
        end_time=5,
        queue_delay=0,
        transmission_delay=2,
        processing_delay=2,
        propagation_delay=1,
        min_bandwidth=10,
        max_bandwidth=10,
        avg_bandwidth=10,
        data_input=20,
        data_output=21,
    )


def test_integration_complete_Networkflow_Processing(small_app_2_user_4_services):

    user = small_app_2_user_4_services["user"][0]
    model = small_app_2_user_4_services["model"]
    app = small_app_2_user_4_services["application"]
    CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[1])

    total_links = 0
    while True:

        for agent in DataPacket.all():
            agent.step()

        for agent in Service.all():
            agent.step()

        for agent in Topology.all():
            agent.step()

        for agent in NetworkFlow.all():
            agent.step()

        user.step()

        model.schedule.steps += 1

        total_links = sum(len(link_hop) - 1 for link_hop in DataPacket.all()[0]._total_path)
        if len(DataPacket.all()) > 1:
            if len(DataPacket.all()[1].get_hops()) == total_links:
                break

    total_datapackets = model.schedule.steps // 2 if model.schedule.steps % 2 == 0 else model.schedule.steps // 2 + 1
    assert len(DataPacket.all()) == total_datapackets

    assert len(DataPacket.all()[0].get_hops()) == total_links
    assert len(DataPacket.all()[1].get_hops()) == total_links

    assert DataPacket.all()[0].get_hops()[-1].target == 8
    assert DataPacket.all()[1].get_hops()[-1].target == 8

    assert DataPacket.all()[0].processing_delay_total == 14
    assert DataPacket.all()[1].processing_delay_total == 14
    assert DataPacket.all()[0].propagation_delay_total == 6
    assert DataPacket.all()[1].propagation_delay_total == 6

    for datapacket in DataPacket.all():

        total_delay = 0
        hops = datapacket.get_hops()
        for i, hop in enumerate(hops):

            total_delay += hop.transmission_delay + hop.queue_delay + hop.processing_delay + hop.propagation_delay

            assert hop.start_time + hop.transmission_delay + hop.queue_delay + hop.processing_delay == hop.end_time

            if i < len(hops) - 1:
                next_hop = hops[i + 1]
                assert hop.end_time == next_hop.start_time

        assert total_delay == datapacket.total_delay


def test_integration_2_user_bandwidth(small_app_2_user_4_services):

    users = small_app_2_user_4_services["user"]
    model = small_app_2_user_4_services["model"]
    app = small_app_2_user_4_services["application"]

    CircularDurationAndIntervalAccessPattern(user=users[0], app=app, start=1, duration_values=[1], interval_values=[100])
    CircularDurationAndIntervalAccessPattern(user=users[1], app=app, start=1, duration_values=[1], interval_values=[100])

    total_links = 0
    while True:

        for agent in DataPacket.all():
            agent.step()

        for agent in Service.all():
            agent.step()

        for agent in Topology.all():
            agent.step()

        for agent in NetworkFlow.all():
            agent.step()

        for user in User.all():
            user.step()

        model.schedule.steps += 1

        total_links = sum(len(link_hop) - 1 for link_hop in DataPacket.all()[0]._total_path)
        if len(DataPacket.all()) > 1:
            if len(DataPacket.all()[1].get_hops()) == total_links:
                break

    data_user1 = DataPacket.all()[0]
    data_user2 = DataPacket.all()[1]

    assert len(DataPacket.all()) == 2
    assert len(NetworkFlow.all()) == sum(len(dp.get_hops()) for dp in DataPacket.all())

    for i, hop in enumerate(data_user1.get_hops()):
        if i > 0:
            assert hop == data_user2.get_hops()[i]
            assert hop.max_bandwidth == 5
        else:
            assert hop.source != data_user2.get_hops()[0].source
            assert hop.target == data_user2.get_hops()[0].target
            assert data_user1.get_hops()[0].min_bandwidth == 10
            assert data_user2.get_hops()[0].min_bandwidth == 10
