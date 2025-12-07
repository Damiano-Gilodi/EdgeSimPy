import pytest

from edge_sim_py.components.application import Application
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.flow_scheduling import max_min_fairness
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.user import User
from edge_sim_py.components.user_access_patterns.circular_duration_and_interval_access_pattern import CircularDurationAndIntervalAccessPattern
from edge_sim_py.dataset_generator.edge_servers import jetson_tx2
from edge_sim_py.dataset_generator.map import hexagonal_grid
from edge_sim_py.dataset_generator.network_switches import sample_switch
from edge_sim_py.dataset_generator.network_topologies import partially_connected_hexagonal_mesh


def reset_components():

    for cls in (Topology, NetworkLink, BaseStation, NetworkSwitch, EdgeServer, Service, User, Application, DataPacket, NetworkFlow):
        cls._instances = []
        cls._object_count = 0


class DummySchedule:
    def __init__(self):
        self.steps = 0
        self.agents = []

    def remove(self, agent):
        self.agents.remove(agent)


class DummyModel:
    def __init__(self):
        self.schedule = DummySchedule()
        self.topology = None
        self.network_flow_scheduling_algorithm = max_min_fairness

    def initialize_agent(self, agent):
        self.schedule.agents.append(agent)
        agent.model = self


def dummy_model():
    return DummyModel()


@pytest.fixture
def basic_topology():

    reset_components()

    # Creating the map coordinates
    map_coordinates = hexagonal_grid(x_size=3, y_size=3)

    # Creating the Base Stations and Network Switches
    # For every map coordinate 1 Base Station and 1 Network Switch
    for coordinates in map_coordinates:

        base_station = BaseStation()
        base_station.wireless_delay = 0
        base_station.coordinates = coordinates

        network_switch = sample_switch()
        base_station._connect_to_network_switch(network_switch=network_switch)

    # Creating Network Links and Topology
    topology = partially_connected_hexagonal_mesh(
        network_nodes=NetworkSwitch.all(),
        link_specifications=[
            {"number_of_objects": 16, "delay": 1, "bandwidth": 10},
        ],
    )

    return {
        "base_stations": BaseStation.all(),
        "network_switches": NetworkSwitch.all(),
        "topology": topology,
    }


@pytest.fixture
def small_app_1_user_4_services(basic_topology):
    """A small app with 1 user and 4 services

    data packet size = 20
    server n:4, processing time = 5+n, processing output = 10+n
    requests start = 1, duration = 1, interval = 1
    user position = (0,0) no mobility
    """
    # Creating the Edge Server
    servers = _servers_base_station(number_of_servers=4)

    # Creating the services
    services = _services_processing(number_of_services=4)

    # Assigning the services to the edge servers
    for server, service in zip(servers, services):
        server.services.append(service)
        service.server = server
        service._available = True

    # Creating the user
    user = User()
    user.set_packet_size_strategy(mode="fixed", size=20)
    user._set_initial_position(coordinates=(0, 0))
    user.mobility_model = _static_dummy_mobility

    # Creating the application
    app = Application()
    for service in services:
        app.connect_to_service(service=service)

    user._connect_to_application(app=app, delay_sla=10)

    CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[1])

    # Creating the model
    dummy_model = DummyModel()
    dummy_model.topology = basic_topology["topology"]

    basic_topology["topology"].model = dummy_model
    user.model = dummy_model
    app.model = dummy_model

    return {
        "user": user,
        "application": app,
        "services": services,
    }


def _servers_base_station(number_of_servers: int):

    if len(BaseStation.all()) < number_of_servers:
        raise Exception("Not enough base stations")

    # Connecting the edge server to a random base station with no attached edge server
    base_stations = sorted(BaseStation.all(), key=lambda b: b.id)

    step = len(base_stations) / number_of_servers

    for i in range(number_of_servers):
        index = int(i * step + step / 2)
        base_station = base_stations[index]

        server = jetson_tx2()
        base_station._connect_to_edge_server(server)

    return EdgeServer.all()


def _services_processing(number_of_services: int):

    for i in range(number_of_services):

        Service(
            obj_id=i,
            cpu_demand=1,
            memory_demand=1200,
            state=0,
            processing_time=5 + i,
            processing_output=21 + i,
        )

    return Service.all()


def _static_dummy_mobility(user):
    user.coordinates_trace.append(user.coordinates)
