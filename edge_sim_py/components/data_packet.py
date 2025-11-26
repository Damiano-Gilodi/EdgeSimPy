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

        # Application
        self.application: "Application" | None = None

        # Delays
        self._queue_delay_total = 0
        self._transmission_delay_total = 0
        self._processing_delay_total = 0
        self._propagation_delay_total = 0

        self._total_delay = 0

        # Hops
        self.__link_hops: list = []

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "size": self.size,
                "queue_delay_total": self._queue_delay_total,
                "transmission_delay_total": self._transmission_delay_total,
                "processing_delay_total": self._processing_delay_total,
                "propagation_delay_total": self._propagation_delay_total,
                "total_delay": self._total_delay,
                "hops": self.__link_hops,
            },
            "relationships": {
                "application": {"class": type(self.application).__name__, "id": self.application.id} if self.application else None,
            },
        }
        return dictionary

    def connect_to_app(self, app: "Application"):
        """Connects the data packet to a given application, establishing all the relationship attributes in both objects.

        Args:
            app (Application): Application to connect to.
        """
        # Link the data packet to the application
        self.application = app
        app.data_packet = self
