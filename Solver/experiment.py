import os
import time
import numpy as np
import csv
import json
import argparse
from create_circuit_over_list_coloring import OverconstrainedListColoring
from utils import create_directories


class Experiment:

    def __init__(self, fname: str, minp: int, maxp: int, n_samples: int = 200, penalty: int = 1, optimizer: str = "COBYLA"):
        self.fname = fname
        self.minp = minp
        self.maxp = maxp
        self.n_samples = n_samples
        self.penalty = penalty
        self.optimizer = optimizer
        self.o = OverconstrainedListColoring("Test2/" + fname, optimizer)
        self.o.penalty = penalty
        split_name = fname.split(".")[0]
        
        # Create the directories using the utility function and save the name csv with the name of optimizer
        self.res_filename, self.log_filename, self.sampler_dir = create_directories(split_name, f"{split_name}_{optimizer}.csv")

    def sample(self, p: int):
        """
        Samples QAOA parameters and estimates the circuit's energy.

        Args:
            p (int): Number of QAOA layers.

        Returns:
            tuple: QAOA parameters and estimated energy.
        """
        x = np.random.random(size=2 * p) * np.pi * 2 
        m = self.o.estimate_qc(x)
        return x, m

    def run(self):
        with open(self.log_filename, "a") as flog:
            print(f"Solving {self.fname} with penalty {self.penalty} using {self.optimizer}", file=flog)
            flog.flush()

            self.o.find_optimal_solution()

            if not os.path.exists(self.res_filename):
                with open(self.res_filename, "w", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Filename", "Penalty", "P", "Function_Value", "Optimal_X", "Distribution"])

            print(f"Optimal solution value {self.o.f_optimum} found", file=flog)
            flog.flush()

            for p in range(self.minp, self.maxp + 1):
                print(f"Phase {p}", file=flog)
                flog.flush()

                self.o.create_qaoa_circuit(p)
                self.o.create_hamiltonian()
                print("Start sampling", file=flog)
                flog.flush()

                st = time.time()
                xx = [self.sample(p) for _ in range(self.n_samples)]
                deltat = time.time() - st

                sample_filename = os.path.join(self.sampler_dir, f"sample_{self.fname}_{self.penalty}_{p}.csv")
                with open(sample_filename, "w", newline='') as f:
                    for x, m in xx:
                        print(",".join(str(d) for d in x), ",", m, file=f)

                print("End sampling after", deltat, "s", file=flog)
                flog.flush()

                x, y = min(xx, key=lambda c: c[1])
                print(f"Best energy {y}", file=flog)
                flog.flush()

                print(f"Start {self.optimizer} optimization", file=flog)
                flog.flush()

                st = time.time()
                opt = self.o.optimize_circuit_energy(x)
                deltat = time.time() - st

                print(f"End {self.optimizer} optimization after {deltat} s with energy {opt[1]}", file=flog)
                flog.flush()

                print("Start post-processing", file=flog)
                flog.flush()

                st = time.time()
                self.o.create_qaoa_circuit(p)
                n_shots = 2048
                counts = self.o.simulate_qc(opt[0], shots=n_shots)
                res = self.o.analyze_data(counts)
                deltat = time.time() - st

                print(f"End post-processing after {deltat} s", file=flog)
                flog.flush()

                distr = res["distr"].most_common()
                
                # Serialize array 
                opt_x_str = json.dumps(opt[0].tolist())

                # Serialize distribution 
                str_distr = json.dumps(",".join(f"{k},{n}" for k, n in distr))

                with open(self.res_filename, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.fname, self.penalty, p, f"{opt[1]:.3f}", opt_x_str, str_distr])
