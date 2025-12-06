import random
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.topology import Topology


def partially_connected_quadratic_mesh(network_nodes: list, link_specifications: list = []) -> object:
    """Creates a square-mesh topology (4-neighborhood) for nodes placed on a quadratic grid."""

    topology = Topology()
    topology.add_nodes_from(network_nodes)

    # map coordinates
    coords = {node.coordinates: node for node in network_nodes}

    # 4-neighborhood directions
    offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for node in network_nodes:
        x, y = node.coordinates

        for dx, dy in offsets:
            neigh_coord = (x + dx, y + dy)
            if neigh_coord in coords:
                neighbor = coords[neigh_coord]

                if not topology.has_edge(node, neighbor):
                    link = NetworkLink()
                    link.topology = topology
                    link.nodes = [node, neighbor]

                    topology.add_edge(node, neighbor)
                    topology._adj[node][neighbor] = link
                    topology._adj[neighbor][node] = link

    # Apply link specifications
    if len(link_specifications) > 0:
        total_links = len(topology.edges())
        expected = sum([spec["number_of_objects"] for spec in link_specifications])
        if expected != total_links:
            raise Exception(f"You must specify the properties for {total_links} links or ignore link_specifications.")

        links = (link for link in random.sample(NetworkLink.all(), NetworkLink.count()))
        for spec in link_specifications:
            for _ in range(spec["number_of_objects"]):
                link = next(links)
                for key, value in spec.items():
                    if key != "number_of_objects":
                        link[key] = value

    return topology
