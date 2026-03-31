import os
import csv
import sys
import re
from Solver.create_circuit_over_list_coloring import OverconstrainedListColoring

def extract_final_number(filename):
    """ Extract the final number in the filename """
    match = re.search(r'_(\d+)\.json$', filename)
    return int(match.group(1)) if match else None

def instance_evaluation(file):
    print(f"Evaluating instance: {file}")
    oclc = OverconstrainedListColoring(file)

    oclc.find_optimal_solution()

    # Name
    instance_name = os.path.splitext(os.path.basename(file))[0]
    # Qubuit
    num_qubits = oclc.num_qubits
    # Min theor 
    min_theor = oclc.f_optimum
    # Prob opt 
    prob_opt = oclc.prob_optimum

    print(f"Instance Name: {instance_name}")
    print(f"Num Qubits: {num_qubits}")
    print(f"Theoretical Minimum: {min_theor}")
    print(f"Probability of Optimal Solution: {prob_opt}")

    return instance_name, num_qubits, min_theor, prob_opt

def save_to_csv(data, output_file):
    # Write data to CSV
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Instance Name", "Num Qubits", "Theoretical Minimum", "Probability of Optimal Solution"])
        writer.writerows(data)

def main(instance_folder, output_file):
    results = []

    # List all JSON files 
    instance_files = [os.path.join(instance_folder, f) for f in os.listdir(instance_folder) if f.endswith('.json')]

    # Sort files based on the final number in their name
    instance_files.sort(key=lambda x: extract_final_number(x))

    for instance_file in instance_files:
        result = instance_evaluation(instance_file)
        results.append(result)
        print(f"Result: {result}")
    
    save_to_csv(results, output_file)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <instance_folder> <output_file>")
        sys.exit(1)

    instance_folder = sys.argv[1]
    output_file = sys.argv[2]

    if os.path.isdir(output_file):
        print(f"Error: {output_file} is a directory. Please provide a valid file path.")
        sys.exit(1)

    main(instance_folder, output_file)
