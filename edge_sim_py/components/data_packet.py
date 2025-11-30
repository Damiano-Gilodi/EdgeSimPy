"""Contains data packet-related functionality."""

# EdgeSimPy components
import copy
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.network_flow import NetworkFlow

# Mesa modules
from mesa import Agent  # type: ignore[import]

if TYPE_CHECKING:
    from edge_sim_py.components.application import Application
    from edge_sim_py.components.user import User


@dataclass(frozen=True)
class LinkHop:
    """Class that represents a link hop in the data packet's path."""

    hop_index: int
    link_index: int
    source: str
    target: str
    start_time: float
    end_time: float
    queue_delay: float
    transmission_delay: float
    processing_delay: float
    propagation_delay: float
    bandwidth: float
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

        # Data packet size
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
        self.total_path: list[list[int]] = []

        # Hops
        self.current_hop = 0
        self.current_link = 0

        # Hops
        self._link_hops: list = []

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "size": self.size,
            },
            "relationships": {
                "application": {"class": type(self.application).__name__, "id": self.application.id} if self.application else None,
                "user": {"class": type(self.user).__name__, "id": self.user.id} if self.user else None,
            },
        }
        return dictionary

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        metrics = {
            "Id": self.id,
            "Application Id": self.application.id,
            "User Id": self.user.id,
            "Size": self.size,
            "Queue delay total": self._queue_delay_total,
            "Transmission delay total": self._transmission_delay_total,
            "Processing delay total": self._processing_delay_total,
            "Propagation delay total": self._propagation_delay_total,
            "Total delay": self._total_delay,
            "Total path": self.total_path,
            "Hops": [asdict(hop) for hop in self._link_hops],
        }
        return metrics

    def add_link_hop(self, link_hop: LinkHop):
        self._link_hops.append(link_hop)

    def getHops(self) -> list[LinkHop]:
        return copy.deepcopy(self._link_hops)

    def launch_next_flow(self, start_step):
        """Method that lauches the next flow.

        Args:
            start_step (int): Time step in which the flow started.
        """
        hop = self.current_hop
        link = self.current_link

        flow = NetworkFlow(
            topology=self.application.model.topology,
            source=self.total_path[hop][link],
            target=self.total_path[hop][link + 1],
            path=self.total_path[hop][link : link + 2],
            start=start_step,
            data_to_transfer=self.size,
            metadata={"type": "data_packet", "object": self, "index_hop": hop, "index_link": link},
        )

        self.application.model.initialize_agent(flow)
