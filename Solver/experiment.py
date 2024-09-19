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
                writer.writerow(["Filename", "Penalty", "P", "Iter", "Function_Value", "Optimal_X", "Distribution"])

        self.log(f"Theoretical optimal solution value {self.o.f_optimum} found with prob. {self.o.prob_optimum:.3f}")

        # Manteniamo i parametri ottimizzati da ogni run separatamente
        previous_runs_gamma = []
        previous_runs_beta = []

        for p in range(self.minp, self.maxp + 1):
            self.log(f"Phase {p}")

            self.o.create_qaoa_circuit(p)
            self.o.create_hamiltonian()

            # Per ogni run, ottimizzare separatamente e mantenere i risultati per il run successivo della stessa fase
            for i in range(self.n_point_opt):
                if p == 1:
                    # Fase 1: campioniamo casualmente gamma[0] e beta[0] per ogni run
                    x_start, energy = self.sample(p)
                else:
                    
                    x_start = np.concatenate([
                    np.insert(previous_runs_gamma[i], 0, np.random.random() * np.pi * 2),  # Inserisci gamma[p-1] all'inizio
                    np.insert(previous_runs_beta[i], 0, np.random.random() * np.pi * 2)   # Inserisci beta[p-1] all'inizio
                    ])
                    
                    energy = self.o.estimate_qc(x_start)

                # Debug: stampa dei parametri iniziali per ogni run
                self.log(f"Initial parameters before optimization (p={p}, run={i+1}):")
                self.log(f"Gamma: {x_start[:p]}")
                self.log(f"Beta: {x_start[p:]}")

                self.log(f"Start {self.optimizer} run #{i+1} with initial energy {energy:.3f}")
                st = time.time()
                opt_x, opt_fun = self.o.optimize_circuit_energy(x_start)
                deltat = time.time() - st

                # Converti opt_fun in scalare se è un array
                opt_fun_scalar = opt_fun.item() if isinstance(opt_fun, np.ndarray) else opt_fun
                
                self.log(f"End optimization run {i+1} after {deltat:.2f} s with improvement {opt_fun_scalar-energy:.3f}")
                
                # Debug: stampa dei parametri ottimizzati
                self.log(f"Optimized parameters after run {i+1} (p={p}):")
                self.log(f"Optimized Gamma: {opt_x[:p]}")
                self.log(f"Optimized Beta: {opt_x[p:]}")

                self.log("Start post-processing")
                st = time.time()
                self.o.create_qaoa_circuit(p)
                n_shots = 2048
                counts = self.o.simulate_qc(opt_x, shots=n_shots)
                res = self.o.analyze_data(counts)
                deltat = time.time() - st

                self.log(f"End post-processing after {deltat:.2f} s")
                
                # Salva i gamma e beta ottimizzati per questo run specifico
                if p == 1:
                    # Se siamo nella fase 1, salviamo i gamma e beta ottimizzati per usarli nella fase successiva
                    previous_runs_gamma.append(opt_x[:p].tolist())  # Gamma ottimizzati del run i
                    previous_runs_beta.append(opt_x[p:].tolist())   # Beta ottimizzati del run i
                else:
                    # Se siamo nelle fasi successive, aggiorniamo i gamma e beta del run corrente
                    previous_runs_gamma[i] = opt_x[:p].tolist()  # Aggiorna i gamma del run i
                    previous_runs_beta[i] = opt_x[p:].tolist()   # Aggiorna i beta del run i

                # Salva i risultati dell'ottimizzazione e della simulazione
                min_energy = res['min'].item() if isinstance(res['min'], np.ndarray) else res['min']
                prob_opt = res['num_opt'] / n_shots

                self.log(f"Results: best found {min_energy}, final energy {opt_fun_scalar:.3f}, prob. of optimum {prob_opt:.3f}")
                distr = res["distr"].most_common()

                opt_x_str = json.dumps(opt_x.tolist())
                str_distr = json.dumps(",".join(f"{k},{n}" for k, n in distr))

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