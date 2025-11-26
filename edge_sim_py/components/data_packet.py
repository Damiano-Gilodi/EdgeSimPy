"""Contains data packet-related functionality."""

# EdgeSimPy components
from typing import TYPE_CHECKING
from edge_sim_py.component_manager import ComponentManager

# Mesa modules
from mesa import Agent  # type: ignore[import]

if TYPE_CHECKING:
    from edge_sim_py.components.application import Application


class DataPacket(ComponentManager, Agent):
    """Class that represents an data packet."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances: list["DataPacket"] = []
    _object_count = 0

    def __init__(self, obj_id: int | None = None, size: int = 0):
        """Creates a DataPacket object.

        Args:
            obj_id (int, optional): Object identifier.
            size (int, optional): Size of the data packet in bytes.

        Returns:
            object: Created DataPacket object.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Data packet size
        self.size = size

        # Delays
        self.queue_delay_total = 0
        self.transmission_delay_total = 0
        self.processing_delay_total = 0
        self.propagation_delay_total = 0

        self.total_delay = 0

        # Hops
        self.link_hops: list = []

    def _to_dict(self) -> dict:

        return {}

    def connect_to_app(self, app: "Application"):

        return
