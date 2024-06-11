import os
import argparse
import json
import random

class SatelliteSchedulingGenerator:
    def __init__(self, n_instances, config_param, out_folder):
        self.n_instances = n_instances
        self.config_param = config_param
        self.out_folder = out_folder

    def generate(self):
        # Check if the configuration file and output folder exist
        if os.path.isfile(self.config_param) and os.path.isdir(self.out_folder):
            # Load configuration parameters from the JSON file
            with open(self.config_param, "r") as infile:
                config_param = json.load(infile)

                # Extract configuration parameters
                n_satellites = config_param["n_satellites"]
                n_ground_stations = config_param["n_ground_stations"]
                n_communications = config_param["n_communications"]
                delta = config_param["delta"]
                h_hours = config_param["h_hours"]
                allowed_ground_stations = config_param["allowed_ground_stations"]

                # Create a list of allowed ground stations for each satellite
                list_ground_stations = [[] for _ in range(n_satellites)]
                for nn in allowed_ground_stations:
                    n = int(nn)
                    list_ground_stations[n] = allowed_ground_stations[nn]

                # Calculate the average duration of each communication window and the allowed variation
                d = int(h_hours / (2 * n_communications))
                dd = int(d * delta)

                for iter in range(self.n_instances):
                    communication_windows = {}
                    for i in range(n_satellites):
                        communication_windows[i] = []

                    GNodes = {}
                    GEdges = []
                    Node2Sat = {}

                    n_graph_nodes = 0

                    # Generate communication windows for each satellite
                    for i in range(n_satellites):
                        tnow = 0
                        TxTrue = random.randint(0, 1)

                        for j in range(2 * n_communications):
                            # Calculate the time update considering the allowed variation
                            dduration = random.randint(-dd, dd)
                            tnow_update = min(tnow + d + dduration, h_hours)

                            if TxTrue == 1:
                                # Add the current communication window
                                communication_windows[i].append([tnow, tnow_update])
                                GNodes[n_graph_nodes] = [tnow, tnow_update]
                                TxTrue = 0
                                Node2Sat[n_graph_nodes] = i
                                n_graph_nodes += 1
                            else:
                                TxTrue = 1

                            tnow = tnow_update

                        print(f"SAT_{i}: {communication_windows[i]}")

                    print(f"G(Nodes)= {GNodes}")

                    scheduling_problem = {}
                    scheduling_problem["colors"] = n_ground_stations
                    scheduling_problem["nodes"] = [i for i in range(n_graph_nodes)]
                    scheduling_problem["allowed_colors"] = {}
                    for i in range(n_graph_nodes):
                        scheduling_problem["allowed_colors"][str(i)] = list_ground_stations[Node2Sat.get(i)]

                    # Generate the edges of the graph based on communication windows and allowed ground stations
                    for j in range(n_graph_nodes):
                        for k in range(j + 1, n_graph_nodes):
                            if (
                                GNodes.get(j)[1] > GNodes.get(k)[0] and
                                GNodes.get(j)[0] < GNodes.get(k)[1]
                            ):
                                GEdges.append([j, k, 1])  # Weight w = 1, but can be a real value in [0,1]

                    scheduling_problem["edges"] = GEdges

                    # Calculate the number of color conflicts
                    num_conflicts = 0
                    for edge in scheduling_problem["edges"]:
                        node1, node2, _ = edge
                        colors_node1 = set(scheduling_problem["allowed_colors"][str(node1)])
                        colors_node2 = set(scheduling_problem["allowed_colors"][str(node2)])
                        # Check if there is at least one common color
                        if not colors_node1.isdisjoint(colors_node2):
                            num_conflicts += 1

                    print(f"G(Edges)= {GEdges}")
                    print(f"Number of color conflicts: {num_conflicts}")

                    # Save the results to the output .json file
                    output_filename = os.path.join(self.out_folder, f"Problem_{n_satellites}Sat{n_ground_stations}Gs_{num_conflicts}_{iter}.json")
                    with open(output_filename, "w", encoding='utf-8') as outfile:
                        json.dump(scheduling_problem, outfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    """
    Random generation of a set of SATELLITE SCHEDULING problems
        :param n_instances: Number of random instances
        :param config_param: input configuration file (.json file)
        :param n_satellites: number of satellites (e.g., 4)
        :param n_ground_stations: number of ground stations (e.g., 3)
        :param n_communications: number of communication windows per satellite (e.g., 2)
        :param h_hours: problem horizon in hours (e.g., 240)
        :param delta: a real number 0 <= delta <= 0.5 (e.g., 0.1)
        :param allowed_ground_stations: the set of pairs (satellite_id, list of allowed ground stations)
        :param out_folder: the directory where the results should be written to
    """

    parser = argparse.ArgumentParser(allow_abbrev=True)
    parser.add_argument('-n_instances', help='Number of random instances', type=int, default=None, action='store', dest='N_INST', required=True)
    parser.add_argument('-config_param', help='Input configuration file (.json file)', type=str, default=None, action='store', dest='CONFIG_PARAM', required=True)
    parser.add_argument('-out_folder', help='Output solution folder', type=str, default=None, action='store', dest='OUT_FOLD', required=True)

    args = parser.parse_args()

    generator = SatelliteSchedulingGenerator(args.N_INST, args.CONFIG_PARAM, args.OUT_FOLD)
    generator.generate()
