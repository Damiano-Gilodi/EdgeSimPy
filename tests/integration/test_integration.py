from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_switch import NetworkSwitch


def test_integration_start_flows(small_app_1_user_4_services):

    user = small_app_1_user_4_services["user"]
    app = small_app_1_user_4_services["application"]

    for i in range(5):  # 3 requests true

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
