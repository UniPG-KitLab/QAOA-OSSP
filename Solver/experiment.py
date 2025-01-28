import os
import time
import numpy as np
import csv
import json
from create_circuit_over_list_coloring import OverconstrainedListColoring
from utils import create_directories

class Experiment:
    def __init__(self, fname: str, minp: int, maxp: int, n_samples: int = 100, n_point_opt: int = 10,
                 penalty: int = 1, optimizer: str = "COBYLA", log_to_file: bool = False, save_samples: bool = False):
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
        self.o = OverconstrainedListColoring("../Benchmark/test_16_qubit/" + fname, optimizer)
        self.o.penalty = penalty
        self.n_point_opt = n_point_opt

        # Remove extension from the filename for naming purposes
        self.split_name = os.path.splitext(os.path.basename(fname))[0]

        # Create the results and optionally the log and sampler directories
        self.res_filename, log_file_path, sampler_dir = create_directories(
            create_log=self.log_to_file, create_sampler=self.save_samples)
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
        x = np.random.random(size=2 * p) * np.pi // self.penalty
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
        total_start_time = time.time()  # Algo total time 
        self.log(f"Solving {self.fname} with penalty {self.penalty} using {self.optimizer}\n")

        self.o.find_optimal_solution()

        
        if not os.path.exists(self.res_filename):
            with open(self.res_filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Filename", "Penalty", "P", "Iter", "Function_Value",
                                 "Optimal_X", "Distribution", "Num_Evaluations", "Phase_Time", "Total_Time"])

        self.log(f"Theoretical optimal solution value {self.o.f_optimum} found with prob. {self.o.prob_optimum:.3f}")

        previous_runs_gamma = []
        previous_runs_beta = []

        for p in range(self.minp, self.maxp + 1):
            phase_start_time = time.time()  # Phase time
            self.log(f"\nPhase {p}")

            # Create the QAOA circuit for the current phase
            self.o.create_qaoa_circuit(p)
            self.o.create_hamiltonian()

            if p == 1:
                # Generate n_samples (100) random pairs (gamma, beta)
                x_samples = []
                energies = []
                self.log(f"Generating {self.n_samples} random parameter pairs for p={p}")
                for idx in range(self.n_samples):
                    x, energy = self.sample(p)
                    x_samples.append(x)
                    energies.append(energy)
                    self.log(f"Sample {idx+1}: Energy = {energy:.6f}")

                # Take the best 10 pairs with the lowest energy
                best_indices = np.argsort(energies)[:self.n_point_opt]
                best_x_samples = [x_samples[i] for i in best_indices]
                best_energies = [energies[i] for i in best_indices]

                self.log("\nBest parameter pairs selected based on energy:")
                for rank, idx in enumerate(best_indices):
                    self.log(f"Rank {rank+1}: Sample {idx+1}, Energy = {energies[idx]:.6f}")

                previous_runs_gamma = []
                previous_runs_beta = []

                # Apply COBYLA to the best n pairs
                for i in range(self.n_point_opt):
                    x_start = best_x_samples[i]
                    energy = best_energies[i]

                    self.log(f"\nOptimization Run {i+1} (p={p}):")
                    self.log(f"Starting energy: {energy:.6f}")

                    # Start optimization
                    self.log(f"Start {self.optimizer} run #{i+1}")
                    opt_st = time.time()
                    opt_x, opt_fun, num_evaluations = self.o.optimize_circuit_energy(x_start)
                    opt_deltat = time.time() - opt_st

                    # Convert opt_fun to scalar if necessary
                    opt_fun_scalar = opt_fun.item() if isinstance(opt_fun, np.ndarray) else opt_fun

                    self.log(f"End optimization run {i+1} after {opt_deltat:.2f} s with improvement {opt_fun_scalar - energy:.6f}, number of evaluations: {num_evaluations}")

                    # Save optimized gamma and beta for next phase
                    previous_runs_gamma.append(opt_x[:p].tolist())
                    previous_runs_beta.append(opt_x[p:].tolist())

                    # Post-processing and simulation
                    self.log("Start post-processing")
                    st = time.time()
                    self.o.create_qaoa_circuit(p)
                    n_shots = 2048
                    counts = self.o.simulate_qc(opt_x, shots=n_shots)
                    res = self.o.analyze_data(counts)
                    postproc_deltat = time.time() - st

                    self.log(f"End post-processing after {postproc_deltat:.2f} s")

                    # Save reuslts
                    min_energy = res['min'].item() if isinstance(res['min'], np.ndarray) else res['min']
                    prob_opt = res['num_opt'] / n_shots

                    self.log(f"Results: best found {min_energy}, final energy {opt_fun_scalar:.6f}, prob. of optimum {prob_opt:.6f}")
                    distr = res["distr"].most_common()

                    opt_x_str = json.dumps(opt_x.tolist())
                    str_distr = json.dumps(",".join(f"{k},{n}" for k, n in distr))

                    # Calcolate comulative time 
                    total_time = time.time() - total_start_time
                    phase_time = time.time() - phase_start_time

                    # Write results to the CSV file
                    with open(self.res_filename, "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([self.fname, self.penalty, p, i+1, f"{opt_fun_scalar:.6f}",
                                         opt_x_str, str_distr, num_evaluations, f"{phase_time:.2f}", f"{total_time:.2f}"])

            else:
                # For p > 1
                x_samples = []
                energies = []
                self.log(f"Extending previous parameters with new random values for p={p}")

                num_new_vectors = self.n_samples // self.n_point_opt

                # Generate new parameter vectors
                for i in range(self.n_point_opt):
                    gamma_prev = previous_runs_gamma[i]
                    beta_prev = previous_runs_beta[i]

                    # Generate new vectors by adding a new random (gamma, beta) pair
                    for j in range(num_new_vectors):
                        gamma_new_value = np.random.random() * np.pi // self.penalty
                        beta_new_value = np.random.random() * np.pi // self.penalty
                        gamma_new = np.append(gamma_prev, gamma_new_value)
                        beta_new = np.append(beta_prev, beta_new_value)
                        x_start = np.concatenate([gamma_new, beta_new])
                        x_samples.append(x_start)
                        energy = self.o.estimate_qc(x_start)
                        energies.append(energy)
                        sample_idx = i * num_new_vectors + j + 1
                        self.log(f"Sample {sample_idx}: Energy = {energy:.6f}")

                # Take the vectors with the lowest energy
                best_indices = np.argsort(energies)[:self.n_point_opt]
                best_x_samples = [x_samples[i] for i in best_indices]
                best_energies = [energies[i] for i in best_indices]

                self.log("\nBest parameter sets selected based on energy:")
                for rank, idx in enumerate(best_indices):
                    self.log(f"Rank {rank+1}: Sample {idx+1}, Energy = {energies[idx]:.6f}")

                previous_runs_gamma = []
                previous_runs_beta = []

                # Apply COBYLA to the best vectors
                for i in range(self.n_point_opt):
                    x_start = best_x_samples[i]
                    energy = best_energies[i]

                    self.log(f"\nOptimization Run {i+1} (p={p}):")
                    self.log(f"Starting energy: {energy:.6f}")

                    # Start Optimization
                    self.log(f"Start {self.optimizer} run #{i+1}")
                    opt_st = time.time()
                    opt_x, opt_fun, num_evaluations = self.o.optimize_circuit_energy(x_start)
                    opt_deltat = time.time() - opt_st

                    # Convert opt_fun to scalar if necessary
                    opt_fun_scalar = opt_fun.item() if isinstance(opt_fun, np.ndarray) else opt_fun

                    self.log(f"End optimization run {i+1} after {opt_deltat:.2f} s with improvement {opt_fun_scalar - energy:.6f}, number of evaluations: {num_evaluations}")

                    # Save optimized gamma and beta for next phase
                    previous_runs_gamma.append(opt_x[:p].tolist())
                    previous_runs_beta.append(opt_x[p:].tolist())

                    self.log("Start post-processing")
                    st = time.time()
                    self.o.create_qaoa_circuit(p)
                    n_shots = 2048
                    counts = self.o.simulate_qc(opt_x, shots=n_shots)
                    res = self.o.analyze_data(counts)
                    postproc_deltat = time.time() - st

                    self.log(f"End post-processing after {postproc_deltat:.2f} s")

                    # Save results
                    min_energy = res['min'].item() if isinstance(res['min'], np.ndarray) else res['min']
                    prob_opt = res['num_opt'] / n_shots

                    self.log(f"Results: best found {min_energy}, final energy {opt_fun_scalar:.6f}, prob. of optimum {prob_opt:.6f}")
                    distr = res["distr"].most_common()

                    opt_x_str = json.dumps(opt_x.tolist())
                    str_distr = json.dumps(",".join(f"{k},{n}" for k, n in distr))

                    # Calcola il tempo cumulativo
                    total_time = time.time() - total_start_time
                    phase_time = time.time() - phase_start_time

                    # Write results to the CSV file
                    with open(self.res_filename, "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([self.fname, self.penalty, p, i+1, f"{opt_fun_scalar:.6f}",
                                         opt_x_str, str_distr, num_evaluations, f"{phase_time:.2f}", f"{total_time:.2f}"])

            
            # End of one phase
            phase_end_time = time.time()
            phase_duration = phase_end_time - phase_start_time
            self.log(f"Time taken for phase {p}: {phase_duration:.2f} seconds")

        # End of all phase
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        self.log(f"\nTotal execution time: {total_duration:.2f} seconds")

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

penalties = [1.5]

for prob in probs16:
    for pen in penalties:
        experiment = Experiment(prob, minp=1, maxp=10, n_samples=100, n_point_opt=10, penalty=pen, optimizer="COBYLA", log_to_file=True, save_samples=False)
        experiment.run()
