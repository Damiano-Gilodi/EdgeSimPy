"""Contains data packet-related functionality."""

# EdgeSimPy components
import copy
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.network_flow import NetworkFlow

# Mesa modules
from mesa import Agent  # type: ignore[import]

from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service

if TYPE_CHECKING:
    from edge_sim_py.components.application import Application
    from edge_sim_py.components.user import User


@dataclass(frozen=True)
class LinkHop:
    """Class that represents a link hop in the data packet's path."""

    hop_index: int
    link_index: int

    source: int
    target: int

    start_time: int
    end_time: int

    queue_delay: int
    transmission_delay: int
    processing_delay: int
    propagation_delay: int

    min_bandwidth: float
    max_bandwidth: float
    avg_bandwidth: float

    data_input: int
    data_output: int


class DataPacket(ComponentManager, Agent):
    """Class that represents an data packet."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances: list["DataPacket"] = []
    _object_count = 0

    def __init__(self, user: "User", application: "Application", size: int = 1, obj_id: int | None = None):
        """Creates a DataPacket object.

        Args:
            obj_id (int, optional): Object identifier.
            size (int, optional): Size of the data packet in bytes.

        Returns:
            object: Created DataPacket object.
        """
        if size <= 0:
            raise ValueError("DataPacket size must be a positive integer.")

        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Data packet size change in services processing
        self.size = size

        # Application
        self.application: "Application" = application

        # User
        self.user: "User" = user

        # Delays
        self._queue_delay_total = 0
        self._transmission_delay_total = 0
        self._processing_delay_total = 0
        self._propagation_delay_total = 0

        self._total_delay = 0

        # Total path (list of hop nodes between services)
        self._total_path: list[list[int]] = []

        # Hops
        self._current_hop = 0
        self._current_link = 0

        # Processing
        self._is_processing = False
        self._processing_remaining_time = 0

        # Hops
        self._link_hops: list[LinkHop] = []

    def get_metrics(self) -> dict:

        return {}

    def get_hops(self) -> list[LinkHop]:
        return copy.deepcopy(self._link_hops)

    def _launch_next_flow(self, start_step):
        """Method that lauches the next flow.

        Args:
            start_step (int): Time step in which the flow started.
        """
        hop = self._current_hop
        link = self._current_link

        flow = NetworkFlow(
            topology=self.application.model.topology,
            source=self._total_path[hop][link],
            target=self._total_path[hop][link + 1],
            path=self._total_path[hop][link : link + 2],
            start=start_step,
            data_to_transfer=self.size,
            metadata={"type": "data_packet", "object": self, "index_hop": hop, "index_link": link},
        )

        self.application.model.initialize_agent(flow)

    def _on_flow_finished(self, flow: NetworkFlow):
        """Method that executes when a data packet flow finishes.

        Args:
            flow (NetworkFlow): Finished flow.
        """

        hop = flow.metadata["index_hop"]
        link = flow.metadata["index_link"]

        # In intermediate node
        if link + 1 < len(self._total_path[hop]) - 1:

            self._add_link_hop(flow)

            self._current_hop = hop
            self._current_link = link + 1
            self._launch_next_flow(start_step=flow.end)
            return

        # In last node hop
        if hop + 1 < len(self._total_path):

            service: "Service" = self.application.services[hop]
            switch_id = self._total_path[hop + 1][0]

            switch = NetworkSwitch.find_by_id(switch_id)
            servers = switch.edge_servers

            for server in servers:
                if server == service.server:

                    self._add_link_hop(flow, service=service)

                    service._start_processing(data_packet=self)

            self._current_hop = hop + 1
            self._current_link = 0

    def _add_link_hop(self, flow: NetworkFlow, service: "Service | None" = None):
        """Method that adds a link hop to the data packet.

        Args:
            flow (NetworkFlow): Network flow.
            service (Service, optional): Service associated with the flow. Defaults to None.
        """

        hop = flow.metadata["index_hop"]
        link = flow.metadata["index_link"]

        link_hop = LinkHop(
            hop_index=hop,
            link_index=link,
            source=flow.source.id,
            target=flow.target.id,
            start_time=flow.start,
            end_time=flow.end,
            queue_delay=flow._queue_delay,
            transmission_delay=flow.end - flow.start,
            processing_delay=service.processing_time if service else 0,
            propagation_delay=flow.topology[flow.path[0]][flow.path[1]]["delay"],
            min_bandwidth=min(flow._bandwidth_history),
            max_bandwidth=max(flow._bandwidth_history),
            avg_bandwidth=sum(flow._bandwidth_history) / len(flow._bandwidth_history),
            data_input=self.size,
            data_output=service.processing_output if service else self.size,
        )

        self._link_hops.append(link_hop)
