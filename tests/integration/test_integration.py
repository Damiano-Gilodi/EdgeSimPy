from edge_sim_py.components.application import Application
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.data_packet import DataPacket, LinkHop
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.user import User
from edge_sim_py.components.user_access_patterns.circular_duration_and_interval_access_pattern import CircularDurationAndIntervalAccessPattern
from tests.integration.conftest import _dynamic_dummy_mobility, provisioning_algorithm


def test_integration_start_flows(small_app_2_user_4_services):

    user = small_app_2_user_4_services["user"][0]
    app = small_app_2_user_4_services["application"][0]

    CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[1])
    user._connect_to_application(app=app, delay_sla=10)

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
    app = small_app_2_user_4_services["application"][0]

    CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[1])
    user._connect_to_application(app=app, delay_sla=10)

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
    app = small_app_2_user_4_services["application"][0]

    CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[1])
    user._connect_to_application(app=app, delay_sla=10)

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
    app = small_app_2_user_4_services["application"][0]

    CircularDurationAndIntervalAccessPattern(user=users[0], app=app, start=1, duration_values=[1], interval_values=[100])
    CircularDurationAndIntervalAccessPattern(user=users[1], app=app, start=1, duration_values=[1], interval_values=[100])
    users[0]._connect_to_application(app=app, delay_sla=10)
    users[1]._connect_to_application(app=app, delay_sla=10)

    total_links = 0
    while True:

        for agent in DataPacket.all():
            agent.step()

        for agent in Service.all():
            agent.step()

        for agent in Topology.all():
            agent.step()

        for agent in NetworkFlow.all():
            print(agent.id, agent.start, agent.end, agent.data_to_transfer)
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


def test_integration_2_user_2_app(small_app_2_user_4_services):

    users = small_app_2_user_4_services["user"]
    model = small_app_2_user_4_services["model"]
    apps = small_app_2_user_4_services["application"]

    CircularDurationAndIntervalAccessPattern(user=users[0], app=apps[0], start=1, duration_values=[1], interval_values=[100])
    CircularDurationAndIntervalAccessPattern(user=users[1], app=apps[1], start=1, duration_values=[1], interval_values=[100])
    users[0]._connect_to_application(app=apps[0], delay_sla=6)  # sla defined with only propagation delay
    users[1]._connect_to_application(app=apps[1], delay_sla=7)  # sla defined with only propagation delay

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

        total_links0 = sum(len(link_hop) - 1 for link_hop in DataPacket.all()[0]._total_path)
        total_links1 = sum(len(link_hop) - 1 for link_hop in DataPacket.all()[1]._total_path)
        if len(DataPacket.all()) > 1:
            if len(DataPacket.all()[0].get_hops()) == total_links0 and len(DataPacket.all()[1].get_hops()) == total_links1:
                break

    data_user1 = DataPacket.all()[0]
    data_user2 = DataPacket.all()[1]

    assert data_user1._total_path != data_user2._total_path

    assert len(DataPacket.all()) == 2
    assert len(NetworkFlow.all()) == sum(len(dp.get_hops()) for dp in DataPacket.all())

    assert data_user1.get_hops()[0].source != data_user2.get_hops()[0].source

    assert data_user1.get_hops()[1].source == data_user2.get_hops()[-1].target
    assert data_user1.get_hops()[-1].target == data_user2.get_hops()[2].source

    assert users[0].delay_slas["1"] == data_user1.propagation_delay_total
    assert users[1].delay_slas["2"] == data_user2.propagation_delay_total
    assert data_user1.total_delay >= users[0].delay_slas["1"]
    assert data_user2.total_delay >= users[1].delay_slas["2"]

    for data in DataPacket.all():
        for i, hop in enumerate(data.get_hops()):
            if i < len(data.get_hops()) - 1:
                next_hop = data.get_hops()[i + 1]
                assert hop.end_time == next_hop.start_time
                assert hop.target == next_hop.source

    assert all(flow.status == "finished" for flow in NetworkFlow.all())


def test_integration_user_dynamic_mobility(small_app_2_user_4_services):

    # user1 static (0,0)
    # user2 dynamic 1:(4,0), 2:(0,0)
    users = small_app_2_user_4_services["user"]
    model = small_app_2_user_4_services["model"]
    apps = small_app_2_user_4_services["application"]

    CircularDurationAndIntervalAccessPattern(user=users[0], app=apps[0], start=1, duration_values=[2], interval_values=[100])
    CircularDurationAndIntervalAccessPattern(user=users[1], app=apps[1], start=1, duration_values=[2], interval_values=[100])
    users[0]._connect_to_application(app=apps[0], delay_sla=6)  # sla defined with only propagation delay
    users[1]._connect_to_application(app=apps[1], delay_sla=7)  # sla defined with only propagation delay

    users[1].mobility_model = _dynamic_dummy_mobility

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

        total_links0 = sum(len(link_hop) - 1 for link_hop in DataPacket.all()[0]._total_path)
        total_links1 = sum(len(link_hop) - 1 for link_hop in DataPacket.all()[1]._total_path)
        if len(DataPacket.all()) > 2:
            if len(DataPacket.all()[2].get_hops()) == total_links0 and len(DataPacket.all()[3].get_hops()) == total_links1:
                break

    data_user1 = DataPacket.all()[0]
    data_user2 = DataPacket.all()[1]

    second_data_user1 = DataPacket.all()[2]
    second_data_user2 = DataPacket.all()[3]  # data after change location

    assert data_user1._total_path == second_data_user1._total_path
    assert data_user2._total_path != second_data_user2._total_path

    assert second_data_user2.get_hops()[0].source == second_data_user1.get_hops()[0].source

    assert data_user2.get_hops()[0].source == 3
    assert data_user2.get_hops()[0].target == 5
    assert data_user2.get_hops()[1].source == 5

    assert second_data_user2.get_hops()[0].source == 1
    assert second_data_user2.get_hops()[0].target == 4
    assert second_data_user2.get_hops()[1].source == 4

    assert second_data_user2.get_hops()[1].target == data_user2.get_hops()[1].target

    for i, hop in enumerate(data_user2.get_hops()):
        if i > 1:
            assert hop.source == second_data_user2.get_hops()[i].source
            assert hop.target == second_data_user2.get_hops()[i].target


def test_integration_provisioning(small_app_2_user_4_services_provision):

    users = small_app_2_user_4_services_provision["user"]
    model = small_app_2_user_4_services_provision["model"]
    apps = small_app_2_user_4_services_provision["application"]

    CircularDurationAndIntervalAccessPattern(user=users[0], app=apps[0], start=1, duration_values=[2], interval_values=[100])
    CircularDurationAndIntervalAccessPattern(user=users[1], app=apps[1], start=1, duration_values=[2], interval_values=[100])
    users[0]._connect_to_application(app=apps[0], delay_sla=6)  # sla defined with only propagation delay
    users[1]._connect_to_application(app=apps[1], delay_sla=7)  # sla defined with only propagation delay

    while True:

        provisioning_algorithm()

        for agent in DataPacket.all():
            agent.step()

        for agent in EdgeServer.all():
            agent.step()

        for agent in Service.all():
            agent.step()

        for agent in Topology.all():
            agent.step()

        for agent in NetworkFlow.all():
            agent.step()

        for agent in User.all():
            agent.step()

        for agent in ContainerRegistry.all():
            agent.step()

        other_agents = NetworkSwitch.all() + NetworkLink.all() + BaseStation.all() + ContainerLayer.all() + ContainerImage.all() + Application.all()
        for agent in other_agents:
            agent.step()

        model.schedule.steps += 1

        if len(DataPacket.all()) > 0:
            if len(DataPacket.all()[0].get_hops()) == 4 and len(DataPacket.all()[1].get_hops()) == 4:
                break

    for service in Service.all():
        assert service.server == EdgeServer.all()[0]
        assert service._available is True

    assert NetworkFlow.all()[0].source == ContainerRegistry.all()[0].server
    assert NetworkFlow.all()[0].target == EdgeServer.all()[0]

    data_user1 = DataPacket.all()[0]
    data_user2 = DataPacket.all()[1]

    assert data_user1.get_hops()[0].start_time == data_user2.get_hops()[0].start_time
    assert data_user1.get_hops()[-1].end_time == data_user2.get_hops()[-1].end_time

    for i, hop in enumerate(data_user1.get_hops()):
        if i > 0:
            assert hop.source == hop.target
            assert hop.target == data_user2.get_hops()[i].source
            assert data_user2.get_hops()[i].source == data_user2.get_hops()[i].target


def test_integration_migration(small_app_2_user_4_services_provision):

    users = small_app_2_user_4_services_provision["user"]
    model = small_app_2_user_4_services_provision["model"]
    apps = small_app_2_user_4_services_provision["application"]

    CircularDurationAndIntervalAccessPattern(user=users[0], app=apps[0], start=1, duration_values=[2], interval_values=[100])
    CircularDurationAndIntervalAccessPattern(user=users[1], app=apps[1], start=1, duration_values=[2], interval_values=[100])
    users[0]._connect_to_application(app=apps[0], delay_sla=6)  # sla defined with only propagation delay
    users[1]._connect_to_application(app=apps[1], delay_sla=7)  # sla defined with only propagation delay

    while True:

        provisioning_algorithm()

        if model.schedule.steps == 10:
            Service.find_by_id(2).server = EdgeServer.find_by_id(2)

        for agent in DataPacket.all():
            agent.step()

        for agent in EdgeServer.all():
            agent.step()

        for agent in Service.all():
            agent.step()

        for agent in Topology.all():
            agent.step()

        for agent in NetworkFlow.all():
            agent.step()

        for agent in User.all():
            agent.step()

        for agent in ContainerRegistry.all():
            agent.step()

        other_agents = NetworkSwitch.all() + NetworkLink.all() + BaseStation.all() + ContainerLayer.all() + ContainerImage.all() + Application.all()
        for agent in other_agents:
            agent.step()

        model.schedule.steps += 1

        if model.schedule.steps > 20:
            break

    for data in DataPacket.all():
        assert data._status == "dropped"
        assert data._is_processing is False

    data_user1 = DataPacket.all()[0]
    data_user2 = DataPacket.all()[1]

    assert len(data_user1.get_hops()) == 2
    assert len(data_user2.get_hops()) == 1
