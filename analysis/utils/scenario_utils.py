from adapters.cavia.find_valid_scenarios import find_or_load_scenarios, get_scenario_paths
from adapters.cavia.utils.path import PKL_PATH
import pickle
import re
from pathlib import Path

import networkx as nx  # type: ignore
import pandas as pd  # type: ignore


def build_objective_cost_dataset():
    valid_scenarios = find_or_load_scenarios(PKL_PATH, force_rescan=True)

    rows = []

    for scenario_rel_path, apps in valid_scenarios.items():
        for app_name in apps:
            phys_path, app_path, pkl_path = get_scenario_paths(scenario_rel_path, app_name)
            row = extract_objective_cost_from_scenario(app_path, pkl_path)
            rows.append(row)

    return pd.DataFrame(rows)


def extract_objective_cost_from_scenario(app_graph_path, pkl_path):
    app_graph_path = Path(app_graph_path)
    pkl_path = Path(pkl_path)

    G_app = nx.read_graphml(app_graph_path)

    with open(pkl_path, "rb") as f:
        data_pkl = pickle.load(f)

    x_ui = data_pkl.get("x_ui", {})
    c_i = data_pkl.get("c_i", {})

    x_ui_filtered = {k: v for k, v in x_ui.items() if v > 0.5}

    service_cpu = {}
    for node_id, data in G_app.nodes(data=True):
        service_cpu[int(node_id)] = int(data.get("0", 0))

    node_weight_sum = 0.0
    service_weighted_node_weight_sum = 0.0

    used_nodes = set()
    zero_cost_nodes_used = 0

    for (service_id, node_id), _ in x_ui_filtered.items():
        u = int(service_id)
        i = int(node_id)

        w_i = c_i.get(i, 0.0)
        q_u = service_cpu.get(u, 0)

        node_weight_sum += w_i
        service_weighted_node_weight_sum += q_u * w_i

        used_nodes.add(i)

    zero_cost_nodes_used = sum(1 for i in used_nodes if c_i.get(i, 0.0) == 0.0)

    scenario = app_graph_path.parent.parent.name
    app_ms = app_graph_path.stem
    app_group = re.sub(r"^\d+", "", app_ms)

    return {
        "Scenario": scenario,
        "App_ms": app_ms,
        "App_group": app_group,
        "Assignment_Cost": node_weight_sum,
        "Service_Weighted_Assignment_Cost": service_weighted_node_weight_sum,
        "Num_Services": len(x_ui_filtered),
        "Used_Nodes_Count": len(used_nodes),
        "Zero_Cost_Used_Nodes": zero_cost_nodes_used,
    }


def build_resource_stress_dataset():
    valid_scenarios = find_or_load_scenarios(PKL_PATH, force_rescan=True)

    rows = []

    for scenario_rel_path, apps in valid_scenarios.items():
        for app_name in apps:
            phys_path, app_path, pkl_path = get_scenario_paths(scenario_rel_path, app_name)
            row = extract_resource_stress_from_scenario(phys_path, app_path, pkl_path)
            rows.append(row)

    return pd.DataFrame(rows)


def extract_resource_stress_from_scenario(physical_graph_path, app_graph_path, pkl_path):
    physical_graph_path = Path(physical_graph_path)
    app_graph_path = Path(app_graph_path)
    pkl_path = Path(pkl_path)

    G_phys = nx.read_graphml(physical_graph_path)
    G_app = nx.read_graphml(app_graph_path)

    with open(pkl_path, "rb") as f:
        data_pkl = pickle.load(f)

    x_ui = data_pkl.get("x_ui", {})
    x_ui_filtered = {k: v for k, v in x_ui.items() if v > 0.5}

    server_cpu = {}
    for node_id, data in G_phys.nodes(data=True):
        server_cpu[int(node_id)] = int(data.get("0", 0))

    service_cpu = {}
    for node_id, data in G_app.nodes(data=True):
        service_cpu[int(node_id)] = int(data.get("0", 0))

    cpu_ratios = []
    total_service_cpu = 0.0
    total_server_cpu = 0.0
    used_nodes = set()

    for (service_id, node_id), _ in x_ui_filtered.items():
        u = int(service_id)
        i = int(node_id)

        q_u = service_cpu.get(u, 0)
        Q_i = server_cpu.get(i, 0)

        if Q_i > 0:
            cpu_ratios.append(q_u / Q_i)
            total_service_cpu += q_u
            total_server_cpu += Q_i
            used_nodes.add(i)

    scenario = app_graph_path.parent.parent.name
    app_ms = app_graph_path.stem
    app_group = re.sub(r"^\d+", "", app_ms)

    if len(cpu_ratios) == 0:
        mean_cpu_stress = 0.0
        max_cpu_stress = 0.0
    else:
        mean_cpu_stress = sum(cpu_ratios) / len(cpu_ratios)
        max_cpu_stress = max(cpu_ratios)

    aggregate_cpu_stress = total_service_cpu / total_server_cpu if total_server_cpu > 0 else 0.0

    return {
        "Scenario": scenario,
        "App_ms": app_ms,
        "App_group": app_group,
        "Mean_CPU_Stress": mean_cpu_stress,
        "Max_CPU_Stress": max_cpu_stress,
        "Aggregate_CPU_Stress": aggregate_cpu_stress,
        "Num_Services": len(x_ui_filtered),
        "Used_Nodes_Count": len(used_nodes),
    }
