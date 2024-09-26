from qiskit import QuantumCircuit
import numpy as np
import json
from qiskit.primitives import StatevectorSampler, StatevectorEstimator
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp
import time
import scipy.optimize as so
from collections import Counter
from qiskit_algorithms.optimizers import ADAM

sim = StatevectorSampler()
est = StatevectorEstimator()

class OverconstrainedListColoring:
	
    def __init__(self, fname, optimizer="COBYLA"):
        """
        Initialize the OverconstrainedListColoring object from a JSON file.

        Args:
            fname (str): Filename of the JSON file containing graph data.
            optimizer (str): Optimizer to use ("COBYLA" or "SGD"). 
        """
        with open(fname, "r") as f:
            js = json.load(f)
        self.num_vertices = len(js['nodes'])
        self.num_colors = js['colors']
        self.colors_for_vertex = [None] * self.num_vertices

        for k, a in js['allowed_colors'].items():
            ik = int(k)
            h = js['nodes'].index(ik)
            self.colors_for_vertex[h] = a

        self.edges = js['edges']
        self.num_qubits = sum((1 + len(c)) for c in self.colors_for_vertex)
        self.optimizer = optimizer

    def find_optimal_solution(self):
        """
        Perform exhaustive search to find the optimal solution.
        """
        n = self.num_vertices
        num_colors = [1 + len(self.colors_for_vertex[v]) for v in range(n)]
        colors = [0] * n
        end = False
        f_min = 1e300
        freq_min = 0
        freq_unfeas = 0
        nsol = 0

        while not end:
            nsol += 1
            f = self.objective_function(colors)
            if f < f_min:
                f_min = f
                best = colors.copy()
                freq_min = 1
            elif f == f_min:
                freq_min += 1
            if f >= 1000:
                freq_unfeas += 1
            i = 0
            while i < n:
                colors[i] += 1
                if colors[i] == num_colors[i]:
                    colors[i] = 0
                    i += 1
                else:
                    break
            if i == n: end = True

        self.optimum = best
        self.f_optimum = f_min
        self.prob_optimum = freq_min / nsol
        self.prob_unfeas = freq_unfeas / nsol

    def decode_solution(self, x):
        """
        Decode a binary string solution into a list of colors for each vertex

        Args: 
            x (list[int]): List of binary values representing the solution.

        Returns:
            list[int] | None: List of colors for each vertex or None if the solution is invalid.
        """
        x = [int(t) for t in x]
        colors = [None] * self.num_vertices

        for v in range(self.num_vertices):
            x1 = [x[i] for i in self.qubits[v]]
            assert (sum(x1)==1)
            nb = sum(x1)
            colors[v] = x1.index(1)

        return colors

    def objective_function(self, colors):
        """
        Calculate the objective function valure for given coloring

        Args:
            colors (list[int]): List of colors for each vertex

        Returns:
            float: Objective function value
        """
        t1 = sum(colors[v] == 0 for v in range(self.num_vertices))  # not colored vertices
        t2 = sum((colors[u] == colors[v]) and (colors[u] != 0) for u, v, _ in self.edges)  # number of violations
        return t1 + 1000 * t2

    def invalid(self, colors):
        """
        Check if a given coloring is invalid.

        Parameters:
            colors (list[int]): List of colors for each vertex.

        Returns:
            bool: True if the coloring is invalid, False otherwise.
        """
        return any((colors[u] == colors[v]) and (colors[u] != 0) for u, v, _ in self.edges)

    def create_qaoa_circuit(self, p):
        """
        Create QAOA circuit for the given number of layers

        Args:
            p (int): Number of QAOA layers
        """
        self.gamma = ParameterVector("gamma", p)
        self.beta = ParameterVector("beta", p)
        self.qubits = []
        k = 0

        for v in range(self.num_vertices):
            nc = 1 + len(self.colors_for_vertex[v])
            self.qubits.append(list(range(k, k + nc)))
            k += nc

        self.qc = QuantumCircuit(k)
        self.prepare_initial_state()

        for i in range(p):
            self.create_ps_level(self.gamma[i], self.penalty)
            self.create_mix_level(self.beta[i])

        self.qc_m = self.qc.copy()
        self.qc_m.measure_all()

    def prepare_initial_state(self):
        """
        Prepare the initial state for the QAOA circuit.
        """
        for v in range(self.num_vertices):
            self.Wn(self.qubits[v])

    def create_ps_level(self, gamma_p, penalty):
        for v in range(self.num_vertices):
            q = self.qubits[v][0]
            self.qc.rz(gamma_p, q)

        for u, v, _ in self.edges:
            inters = set(self.colors_for_vertex[u]).intersection(set(self.colors_for_vertex[v]))
            for k in inters:
                k1 = self.colors_for_vertex[u].index(k)
                q1 = self.qubits[u][k1 + 1]
                k2 = self.colors_for_vertex[v].index(k)
                q2 = self.qubits[v][k2 + 1]
                self.qc.rzz(-penalty * gamma_p / 2, q1, q2)
                self.qc.rz(penalty * gamma_p / 2, q1)
                self.qc.rz(penalty * gamma_p / 2, q2)

    def create_mix_level(self, beta_p: float):
        """
        Create the mixig level of QAOA circuit

        Args:
            beta_p (float): parameter of QAOA
        """
        for v in range(self.num_vertices):
            col = self.qubits[v]
            ncol = len(col)

            # odd
            for i in range(0, ncol - 1, 2):
                self.qc.rxx(-2 * beta_p, col[i], col[i + 1])
                self.qc.ryy(-2 * beta_p, col[i], col[i + 1])

            # even
            for i in range(1, ncol, 2):
                self.qc.rxx(-2 * beta_p, col[i], col[(i + 1) % ncol])
                self.qc.ryy(-2 * beta_p, col[i], col[(i + 1) % ncol])

            # final
            if ncol % 2 == 1:
                self.qc.rxx(-2 * beta_p, col[ncol - 1], col[0])
                self.qc.ryy(-2 * beta_p, col[ncol - 1], col[0])

    def create_hamiltonian(self):
        """
        Create the Hamiltonian for the problem 
        """
        def add_term_to_ham(ham, coeff, n, i1, i2=None):
            term = ["I"] * n
            term[n - 1 - i1] = "Z"

            if i2 is not None:
                term[n - 1 - i2] = "Z"
            term = "".join(term)
            if term in ham:
                ham[term] += coeff
            else:
                ham[term] = coeff

        ham_dict = {}
        n = self.num_qubits

        for v in range(self.num_vertices):
            q = self.qubits[v][0]
            add_term_to_ham(ham_dict, -0.5, n, q)

        for u, v, _ in self.edges:
            inters = set(self.colors_for_vertex[u]).intersection(set(self.colors_for_vertex[v]))

            for k in inters:
                k1 = self.colors_for_vertex[u].index(k)
                q1 = self.qubits[u][k1 + 1]
                k2 = self.colors_for_vertex[v].index(k)
                q2 = self.qubits[v][k2 + 1]
                add_term_to_ham(ham_dict, self.penalty / 4, n, q1, q2)
                add_term_to_ham(ham_dict, -self.penalty / 4, n, q1)
                add_term_to_ham(ham_dict, -self.penalty / 4, n, q2)

        self.ham = SparsePauliOp(list(ham_dict.keys()), list(ham_dict.values()))

    def test_ham(self, s):
        """
        Test the Hamiltonian with a given bite-string

        Args:
            s (str): Bitstring representing the solution.

        Returns:
            float: Energy value of the Hamiltonian for the given bitstring.
        """
        n = self.num_qubits
        qc_h = QuantumCircuit(n)

        for i in range(n):
            if s[i] == '1':
                qc_h.x(n - 1 - i)

        pub = (qc_h, self.ham, None)
        res = est.run([pub]).result()[0]

        return res.data.evs

    def simulate_qc(self, params, shots=1024):
        """
        Simulate the QAOA circuit 

        Args:
            params (list[float]): List of QAOA parameters (gamma and beta).
            shots (int): Number of shots for the simulation.
        Returns:
            Measurement counts from the simulation.
        """
        pub = (self.qc_m, params)
        st = time.time()
        res = sim.run([pub], shots=shots).result()[0]
        et = time.time()
        return res.data.meas.get_counts()

    def estimate_qc(self, params):
        """
        Estimate the energy of the QAOA circuit.

        Args:
            params (list[float]): List of QAOA parameters (gamma and beta).

        Returns:
            float: Estimated energy value.
        """
        pub = (self.qc, self.ham, params)
        st = time.time()
        res = est.run([pub]).result()[0]
        et = time.time()
        
        return res.data.evs
    
    def analyze_data(self, counts):
        """
        Analyze the data obtained from the quantum circuit sampler

        Args:
            counts (dict): Measurement counts from the quantum circuit.

        Returns:
            dict: Dictionary containing the analysis results.
        """
        sols = [self.decode_solution(k[::-1]) for k in counts.keys()]
        freqs = list(counts.values())
        obj_f = [self.objective_function(s) for s in sols]
        c = Counter()

        for y, n in zip(obj_f, freqs):
            c.update({y: n})

        return {
            "distr": c,
            "mean": np.average(obj_f, weights=freqs),
            "min": np.min(obj_f),
            "num_opt": sum(freqs[i] for i in range(len(sols)) if obj_f[i] == self.f_optimum),
            "num_unfeas": sum(freqs[i] for i in range(len(sols)) if obj_f[i] >= 1000)
        }

    def optimize_circuit_energy(self, x_init, lr=0.05, max_iter=1000):
        """
        Optimize the QAOA circuit to minimize the energy.

        Args:
            x_init (list[float]): Initial parameters for optimization.
        
        Returns:
            tuple: (x, f(x)) where x is the optimal angles and f(x) is the value of the objective function.
        """
        if self.optimizer == "COBYLA":
            return self.optimize_circuit_energy_cobyla(x_init)
        elif self.optimizer== "ADAM":
            return self.optimize_circuit_energy_ADAM(x_init, lr, max_iter)
        else:
            raise ValueError(f"Unknown optimizer: {self.optimizer}")

    def optimize_circuit_energy_cobyla(self, x_init):
        """
        Optimize the QAOA circuit to minimize the energy using COBYLA.

        Args:
            x_init (list[float]): Initial parameters for optimization.
        
        Returns:
            tuple: (x, f(x)) where x is the optimal angles and f(x) is the value of the objective function.
        """
        def objfun(x):
            return self.estimate_qc(x)

        opt = so.minimize(objfun, x_init, method="COBYLA")
        return opt.x, opt.fun, opt.nfev
    
    def optimize_circuit_energy_ADAM(self, x_init, lr=0.05, max_iter=200):
        """
        Optimize the QAOA circuit to minimize the energy using ADAM.

        Args:
            x_init (list[float]): Initial parameters for optimization.
            lr (float): Learning rate for ADAM.
            max_iter (int): Maximum number of iterations.

        Returns:
            tuple: (x, f(x)) where x is the optimal angles and f(x) is the value of the objective function.
        """
        optimizer = ADAM(maxiter=max_iter, lr=lr)
        
        def objfun(x):
            return np.array([self.estimate_qc(x)])
        
        result = optimizer.minimize(fun=objfun, x0=x_init)
        
        return result.x, result.fun
            
    def CGp(self, control_index, target_index, p: float):
        """
        Ref: https://onlinelibrary.wiley.com/doi/pdf/10.1002/qute.201900015
        """
        thetadash = np.arcsin(np.sqrt(p))
        self.qc.u(thetadash, 0, 0, target_index)
        self.qc.cx(control_index, target_index)
        self.qc.u(-thetadash, 0, 0, target_index)

    def Wn(self, indices):
        """
        Ref: https://onlinelibrary.wiley.com/doi/pdf/10.1002/qute.201900015
        """
        n = len(indices)
        if n < 2 or n > 8:
            raise Exception("Wn not defined for n=" + str(n) + ".")

        self.qc.x(indices[0])

        if n == 2:
            self.qc.h(indices[1])
            self.qc.cx(indices[1], indices[0])
        elif n == 3:
            self.CGp(indices[0], indices[1], 1 / 3)
            self.qc.cx(indices[1], indices[0])
			#
            self.CGp(indices[1], indices[2], 1 / 2)
            self.qc.cx(indices[2], indices[1])
        elif n == 4:
            self.CGp(indices[0], indices[1], 1 / 4)
            self.qc.cx(indices[1], indices[0])
			#
            self.CGp(indices[1], indices[2], 1 / 3)
            self.qc.cx(indices[2], indices[1])
			#
            self.CGp(indices[2], indices[3], 1 / 2)
            self.qc.cx(indices[3], indices[2])
        elif n == 5:
            self.CGp(indices[0], indices[1], 2 / 5)
            self.qc.cx(indices[1], indices[0])
			#
            self.CGp(indices[0], indices[2], 1 / 2)
            self.qc.cx(indices[2], indices[0])
			#
            self.CGp(indices[1], indices[3], 1 / 3)
            self.qc.cx(indices[3], indices[1])
			#
            self.CGp(indices[3], indices[4], 1 / 2)
            self.qc.cx(indices[4], indices[3])
        elif n == 6:
            self.CGp(indices[0], indices[1], 3 / 6)
            self.qc.cx(indices[1], indices[0])
			#
            self.CGp(indices[0], indices[2], 1 / 3)
            self.qc.cx(indices[2], indices[0])
			#
            self.CGp(indices[1], indices[3], 2 / 3)
            self.qc.cx(indices[3], indices[1])
			#
            self.CGp(indices[2], indices[4], 1 / 2)
            self.qc.cx(indices[4], indices[2])
			#
            self.CGp(indices[1], indices[5], 1 / 2)
            self.qc.cx(indices[5], indices[1])
        elif n == 7:
            self.CGp(indices[0], indices[1], 3 / 7)
            self.qc.cx(indices[1], indices[0])
			#
            self.CGp(indices[0], indices[2], 1 / 3)
            self.qc.cx(indices[2], indices[0])
			#
            self.CGp(indices[1], indices[3], 1 / 2)
            self.qc.cx(indices[3], indices[1])
			#
            self.CGp(indices[2], indices[4], 1 / 2)
            self.qc.cx(indices[4], indices[2])
			#
            self.CGp(indices[1], indices[5], 1 / 2)
            self.qc.cx(indices[5], indices[1])
			#
            self.CGp(indices[3], indices[6], 1 / 2)
            self.qc.cx(indices[6], indices[3])
        elif n == 8:
            self.CGp(indices[0], indices[1], 1 / 2)
            self.qc.cx(indices[1], indices[0])
			#
            self.CGp(indices[0], indices[2], 1 / 2)
            self.qc.cx(indices[2], indices[0])
			#
            self.CGp(indices[1], indices[3], 1 / 2)
            self.qc.cx(indices[3], indices[1])
			#
            self.CGp(indices[0], indices[4], 1 / 2)
            self.qc.cx(indices[4], indices[0])
			#
            self.CGp(indices[2], indices[5], 1 / 2)
            self.qc.cx(indices[5], indices[2])
			#
            self.CGp(indices[1], indices[6], 1 / 2)
            self.qc.cx(indices[6], indices[1])
			#
            self.CGp(indices[3], indices[7], 1 / 2)
            self.qc.cx(indices[7], indices[3])