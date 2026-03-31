# 🚀 QAOA -- Oversubscribed Satellite Scheduling Problem (OSSP)

![Python](https://img.shields.io/badge/Python-3.x-blue) ![Quantum](https://img.shields.io/badge/Quantum-QAOA-purple) ![Status](https://img.shields.io/badge/Status-Research-green)

------------------------------------------------------------------------

## 📌 Overview

This repository implements a **Quantum Approximate Optimization Algorithm (QAOA)** approach to solve the **Oversubscribed Satellite Scheduling Problem (OSSP)**.

The implementation is based on the paper:

> 📄 [Applying QAOA to the Oversubscribed Satellite Scheduling Problem](https://arc.aiaa.org/doi/10.2514/1.I011645)

------------------------------------------------------------------------

## 🛰️ Problem Description

The **OSSP** consists of assigning communication tasks between
satellites and ground stations under the following constraints:

-   ⏱️ Respect time windows
-   ⚠️ Avoid conflicts (same ground station at overlapping times)\
-   📈 Maximize the number of executed tasks

When resources are insufficient, some tasks must be **discarded**.

------------------------------------------------------------------------

## ⚛️ QAOA Approach

The problem is:

-   formulated as a **QUBO (Quadratic Unconstrained Binary Optimization)**
-   mapped into a **quantum circuit**

### Workflow

1.  Initialize a superposition state\ì
2.  Apply:
    -   Cost Hamiltonian ($H_C$)
    -   Mixing Hamiltonian ($H_B$)
3.  Optimize parameters ($\gamma, \beta$) using a classical optimizer
4.  Measure and extract candidate solutions

------------------------------------------------------------------------

## 🧪 Usage

### ▶️ Run (logs in terminal)

``` bash
python3 Solver/main.py \
  --fname Problem_3Sat3Gs_16qbits_0.json \
  --minp 1 \
  --maxp 3 \
  --nsamples 100 \
  --penalty 2 \
  --optimizer COBYLA
```

------------------------------------------------------------------------

### 📝 Save logs to file

``` bash
python3 Solver/main.py \
  --fname Problem_3Sat3Gs_16qbits_0.json \
  --minp 1 \
  --maxp 3 \
  --nsamples 100 \
  --penalty 2 \
  --optimizer COBYLA \
  --log_to_file
```

------------------------------------------------------------------------

### 💾 Save logs + samples

``` bash
python3 Solver/main.py \
  --fname Problem_3Sat3Gs_16qbits_0.json \
  --minp 1 \
  --maxp 3 \
  --nsamples 100 \
  --penalty 2 \
  --optimizer COBYLA \
  --log_to_file \
  --save_samples
```

------------------------------------------------------------------------

### ❓ Help

``` bash
python3 Solver/main.py --help
```

------------------------------------------------------------------------

## ⚙️ Parameters

  Parameter          Description

------------------ -----------------------------------

  `--fname`          Input problem file (JSON)
  `--minp`           Minimum QAOA depth
  `--maxp`           Maximum QAOA depth
  `--nsamples`       Number of samples
  `--penalty`        Constraint penalty coefficient
  `--optimizer`      Classical optimizer (e.g. COBYLA)
  `--log_to_file`    Save logs to file
  `--save_samples`   Save sampled solutions

------------------------------------------------------------------------

## 📂 Input Format

Problem instances are provided as JSON files containing:

-   Satellites 
-   Ground stations
-   Time windows

------------------------------------------------------------------------

## 🔮 Future Work

-   🚀 Execution on real quantum hardware
-   ⚙️ Improved parameter optimization strategies
-   📊 Benchmarking against classical solvers
-   📈 Scaling to larger problem instances

------------------------------------------------------------------------

## 🤝 Contributing

Contributions are welcome!