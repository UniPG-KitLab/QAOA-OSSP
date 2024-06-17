import os
import time
import numpy as np
import csv
import json
from create_circuit_over_list_coloring import OverconstrainedListColoring
from utils import create_directories

class Experiment:
    def __init__(self, fname: str, minp: int, maxp: int, n_samples: int = 200, n_point_opt: int = 10, penalty: int = 1, optimizer: str = "COBYLA", log_to_file: bool = False, save_samples: bool = False):
        self.fname = fname
        self.minp = minp
        self.maxp = maxp
        self.n_samples = n_samples
        self.penalty = penalty
        self.optimizer = optimizer
        self.log_to_file = log_to_file
        self.save_samples = save_samples
        self.o = OverconstrainedListColoring("Benchmark/test_16_qubit/" + fname, optimizer)
        self.o.penalty = penalty
        self.n_point_opt = n_point_opt
        
        # Remove extension from fname for naming
        self.split_name = os.path.splitext(os.path.basename(fname))[0]

        # Create the results and optionally the log and sampler directories
        self.res_filename, log_file_path, sampler_dir = create_directories(create_log=self.log_to_file, create_sampler=self.save_samples)
        self.log_filename = log_file_path if self.log_to_file else None
        self.sampler_dir = sampler_dir if self.save_samples else None

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

    def log(self, message):
        """
        Logs a message to the terminal or to a file.

        Args:
            message (str): Message to log.
        """
        if self.log_to_file:
            with open(self.log_filename, "a") as flog:
                print(message, file=flog)
        else:
            print(message)

    def run(self):
        self.log(f"Solving {self.fname} with penalty {self.penalty} using {self.optimizer}\n")
        
        self.o.find_optimal_solution()

        if not os.path.exists(self.res_filename):
            with open(self.res_filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Filename", "Penalty", "P", "Function_Value", "Optimal_X", "Distribution"])

        self.log(f"Optimal solution value {self.o.f_optimum} found")

        for p in range(self.minp, self.maxp + 1):
            self.log(f"Phase {p}")

            self.o.create_qaoa_circuit(p)
            self.o.create_hamiltonian()
            self.log("Start sampling")

            st = time.time()
            xx = [self.sample(p) for _ in range(self.n_samples)]
            deltat = time.time() - st

            if self.save_samples and self.sampler_dir:
                sample_filename = os.path.join(self.sampler_dir, f"sample_{self.split_name}_{self.penalty}_{p}.csv")
                with open(sample_filename, "w", newline='') as f:
                    for x, m in xx:
                        print(",".join(str(d) for d in x), ",", m, file=f)

            self.log(f"End sampling after {deltat} s")

            # Sort result by energy 
            xx.sort(key=lambda c: c[1])
            best_results = [] 

            for i in range(self.n_point_opt):
                x_start = xx[i][0]

                self.log(f"Start {self.optimizer} run {i+1}")
                
                st = time.time()
                opt = self.o.optimize_circuit_energy(x_start)
                deltat = time.time() - st
                best_results.append(opt)
                
                self.log(f"End {self.optimizer} run {i+1} after {deltat} s with energy {opt[1]}")
            
            best_opt = min(best_results, key=lambda opt: opt[1])

            self.log("Start post-processing")

            st = time.time()
            self.o.create_qaoa_circuit(p)
            n_shots = 2048
            counts = self.o.simulate_qc(best_opt[0], shots=n_shots)
            res = self.o.analyze_data(counts)
            deltat = time.time() - st

            self.log(f"End post-processing after {deltat} s")

            distr = res["distr"].most_common()
            
            # Serialize array 
            opt_x_str = json.dumps(best_opt[0].tolist())

            # Serialize distribution 
            str_distr = json.dumps(",".join(f"{k},{n}" for k, n in distr))

            with open(self.res_filename, "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([self.fname, self.penalty, p, f"{best_opt[1]:.3f}", opt_x_str, str_distr])

probs16 = [
    "Problem_5Sat3Gs_0_1.json",
    "Problem_5Sat3Gs_0_4.json",
    "Problem_5Sat3Gs_0_6.json",
    "Problem_5Sat3Gs_1_4.json",
    "Problem_5Sat3Gs_1_5.json",
    "Problem_5Sat3Gs_1_8.json",
    "Problem_5Sat3Gs_2_0.json",
    "Problem_5Sat3Gs_2_1.json",
    "Problem_5Sat3Gs_2_3.json"
]

penalties = [5]

for prob in probs16:
    for pen in penalties:
        experiment = Experiment(prob, minp=1, maxp=1, n_samples=500, n_point_opt=10, penalty=pen, optimizer="COBYLA", log_to_file=True, save_samples=False)
        experiment.run()
