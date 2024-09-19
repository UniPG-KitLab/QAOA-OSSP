import os
import time
import numpy as np
import csv
import json
from create_circuit_over_list_coloring import OverconstrainedListColoring
from utils import create_directories

class Experiment:
    def __init__(self, fname: str, minp: int, maxp: int, n_samples: int = 200, n_point_opt: int = 10, penalty: int = 1, optimizer: str = "COBYLA", log_to_file: bool = False, save_samples: bool = False):
        """
        Initialize the Experiment class with parameters.

        Args:
            fname (str): The filename of the problem instance.
            minp (int): Minimum number of QAOA layers.
            maxp (int): Maximum number of QAOA layers.
            n_samples (int): Number of random samples per phase.
            n_point_opt (int): Number of optimization points per phase.
            penalty (int): Penalty term for the problem constraints.
            optimizer (str): Optimizer to use for the QAOA circuit.
            log_to_file (bool): Whether to log results to a file.
            save_samples (bool): Whether to save samples to a file.
        """
        self.fname = fname
        self.minp = minp
        self.maxp = maxp
        self.n_samples = n_samples
        self.penalty = penalty
        self.optimizer = optimizer
        self.log_to_file = log_to_file
        self.save_samples = save_samples
        self.o = OverconstrainedListColoring("Benchmark/test_16_qubit/" + fname, optimizer)  # Load the problem instance
        self.o.penalty = penalty
        self.n_point_opt = n_point_opt
        
        # Remove extension from the filename for naming purposes
        self.split_name = os.path.splitext(os.path.basename(fname))[0]

        # Create the results and optionally the log and sampler directories
        self.res_filename, log_file_path, sampler_dir = create_directories(create_log=self.log_to_file, create_sampler=self.save_samples)
        self.log_filename = log_file_path if self.log_to_file else None
        self.sampler_dir = sampler_dir if self.save_samples else None

    def sample(self, p: int):
        """
        Generate random QAOA parameters and estimate the circuit's energy.

        Args:
            p (int): The number of QAOA layers.

        Returns:
            tuple: The QAOA parameters and the estimated energy of the circuit.
        """
        x = np.random.random(size=2 * p) * np.pi * 2  # Generate random QAOA parameters (2p parameters: gamma and beta)
        m = self.o.estimate_qc(x)  
        return x, m

    def log(self, message):
        """
        Log messages to the console or to a file, depending on the log_to_file flag.

        Args:
            message (str): The message to log.
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
                writer.writerow(["Filename", "Penalty", "P", "Iter", "Function_Value", "Optimal_X", "Distribution"])

        self.log(f"Theoretical optimal solution value {self.o.f_optimum} found with prob. {self.o.prob_optimum:.3f}")

        previous_runs_gamma = []
        previous_runs_beta = []

        for p in range(self.minp, self.maxp + 1):
            self.log(f"Phase {p}")

            # Create the QAOA circuit for the current phase
            self.o.create_qaoa_circuit(p)
            self.o.create_hamiltonian()

            # For each run, optimize separately and save results for the next phase
            for i in range(self.n_point_opt):
                if p == 1:
                    # For phase 1, sample random gamma[0] and beta[0] parameters for each run
                    x_start, energy = self.sample(p)
                else:
                    # For phase 2 and beyond, insert new random gamma[p-1] and beta[p-1] at the start of the arrays
                    x_start = np.concatenate([
                        np.insert(previous_runs_gamma[i], 0, np.random.random() * np.pi * 2),  # Insert gamma[p-1] at the start
                        np.insert(previous_runs_beta[i], 0, np.random.random() * np.pi * 2)    # Insert beta[p-1] at the start
                    ])
                    energy = self.o.estimate_qc(x_start)

                # Log initial parameters before optimization
                self.log(f"Initial parameters before optimization (p={p}, run={i+1}):")
                self.log(f"Gamma: {x_start[:p]}")
                self.log(f"Beta: {x_start[p:]}")

                # Start the optimization for the current run
                self.log(f"Start {self.optimizer} run #{i+1} with initial energy {energy:.3f}")
                st = time.time()
                opt_x, opt_fun = self.o.optimize_circuit_energy(x_start)
                deltat = time.time() - st

                # Convert the optimization result to a scalar if it is an array
                opt_fun_scalar = opt_fun.item() if isinstance(opt_fun, np.ndarray) else opt_fun
                
                self.log(f"End optimization run {i+1} after {deltat:.2f} s with improvement {opt_fun_scalar-energy:.3f}")
                
                # Log the optimized gamma and beta values after each run
                self.log(f"Optimized parameters after run {i+1} (p={p}):")
                self.log(f"Optimized Gamma: {opt_x[:p]}")
                self.log(f"Optimized Beta: {opt_x[p:]}")

                # Post-process and simulate the optimized quantum circuit
                self.log("Start post-processing")
                st = time.time()
                self.o.create_qaoa_circuit(p)
                n_shots = 2048
                counts = self.o.simulate_qc(opt_x, shots=n_shots)
                res = self.o.analyze_data(counts)
                deltat = time.time() - st

                self.log(f"End post-processing after {deltat:.2f} s")
                
                # Save the optimized gamma and beta values for this specific run
                if p == 1:
                    # For phase 1, store gamma and beta values for use in subsequent phases
                    previous_runs_gamma.append(opt_x[:p].tolist())  # Store optimized gamma values
                    previous_runs_beta.append(opt_x[p:].tolist())   # Store optimized beta values
                else:
                    # For subsequent phases, update the gamma and beta for the current run
                    previous_runs_gamma[i] = opt_x[:p].tolist()  # Update gamma values
                    previous_runs_beta[i] = opt_x[p:].tolist()   # Update beta values

                # Save optimization results and simulation output
                min_energy = res['min'].item() if isinstance(res['min'], np.ndarray) else res['min']
                prob_opt = res['num_opt'] / n_shots

                self.log(f"Results: best found {min_energy}, final energy {opt_fun_scalar:.3f}, prob. of optimum {prob_opt:.3f}")
                distr = res["distr"].most_common()

                opt_x_str = json.dumps(opt_x.tolist())
                str_distr = json.dumps(",".join(f"{k},{n}" for k, n in distr))

                # Write results to the CSV file
                with open(self.res_filename, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.fname, self.penalty, p, i+1, f"{opt_fun_scalar:.3f}", opt_x_str, str_distr])

            self.log(f"Final results for {self.split_name}, best prob. opt {prob_opt:.3f}")


probs16 = [
    "Problem_5Sat3Gs_0_4.json", 
    "Problem_5Sat3Gs_0_6.json",
    "Problem_5Sat3Gs_0_12.json",
    "Problem_5Sat3Gs_1_4.json",
    "Problem_5Sat3Gs_1_5.json",
    "Problem_5Sat3Gs_1_8.json"     
]

probs18 = [
    "Problem_3Sat2Gs_0_0.json",
    "Problem_3Sat2Gs_1_4.json",
    "Problem_5Sat3Gs_0_0.json",
    "Problem_5Sat3Gs_0_1.json",
    "Problem_5Sat3Gs_1_1.json",
    "Problem_5Sat3Gs_1_7.json",
    "Problem_6Sat2Gs_2_0.json",
    "Problem_6Sat2Gs_2_1.json",
    "Problem_6Sat2Gs_2_3.json"
]

probs20 = [
    "Problem_4Sat2Gs_1_5.json",
    "Problem_4Sat2Gs_1_6.json",
    "Problem_4Sat2Gs_2_2.json",
    "Problem_4Sat2Gs_2_4.json",
    "Problem_5Sat4Gs_0_5.json",
    "Problem_6Sat3Gs_0_2.json",
    "Problem_6Sat3Gs_0_3.json",
    "Problem_6Sat3Gs_0_7.json",
    "Problem_6Sat3Gs_0_22.json"
]

penalties = [1,2,3,4,5,6]

for prob in probs16:
    for pen in penalties:
        experiment = Experiment(prob, minp=1, maxp=8, n_samples=100, n_point_opt=10, penalty=pen, optimizer="COBYLA", log_to_file=False, save_samples=False)
        experiment.run()
