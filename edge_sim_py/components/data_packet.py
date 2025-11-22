import copy
from mesa import Agent  # type: ignore
from edge_sim_py.component_manager import ComponentManager
from typing import Optional

from edge_sim_py.components.application import Application


class DataPacket(ComponentManager, Agent):
    """Class that represents a data packet."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances: list["DataPacket"] = []
    _object_count = 0

    def __init__(self, obj_id: Optional[int] = None, size: int = 0):

        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        self.applications: list[Application] = []

        self.size = size

        self.queue_delay_total = 0
        self.transmission_delay_total = 0
        self.processing_delay_total = 0
        self.propagation_delay_total = 0

        self.hops: list[dict] = []

    def add_hop(
        self,
        start_service_id: int,
        target_service_id: int,
        path: list = [],
        size_start: int = 0,
        size_target_processing: int = 0,
        queue_delay: int = 0,
        transmission_delay: int = 0,
        target_processing_delay: int = 0,
        propagation_delay: int = 0,
    ):

        hop_info = {
            "service_id_start": start_service_id,
            "service_id_target": target_service_id,
            "path": path,
            "size_start": size_start,
            "size_target_processing": size_target_processing,
            "queue_delay": queue_delay,
            "transmission_delay": transmission_delay,
            "target_processing_delay": target_processing_delay,
            "propagation_delay": propagation_delay,
        }
        self.hops.append(hop_info)

        self.queue_delay_total += queue_delay
        self.transmission_delay_total += transmission_delay
        self.processing_delay_total += target_processing_delay
        self.propagation_delay_total += propagation_delay

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "size": self.size,
                "queue_delay_total": self.queue_delay_total,
                "transmission_delay_total": self.transmission_delay_total,
                "processing_delay_total": self.processing_delay_total,
                "propagation_delay_total": self.propagation_delay_total,
                "hops": copy.deepcopy(self.hops),
            },
            "relationships": {
                "applications": [{"class": type(app).__name__, "id": app.id} for app in self.applications],
            },
        }

        return dictionary

    def connect_to_app(self, app: Application) -> object:
        """Creates a relationship between the data packet and a given Application object.

        Args:
            service (Application): Application object.

        Returns:
            object: Updated Application object.
        """
        self.applications.append(app)
        app.data_packets = self

        return self
