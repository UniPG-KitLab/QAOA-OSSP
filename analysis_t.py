import pandas as pd
import os
import re

def analysis(filename):
    df_in = pd.read_csv(filename)
    data = []
    nr, nc = df_in.shape

    # Function to extract the first number from the filename
    def extract_first_number(filename):
        match = re.search(r'_(\d+)_', filename)
        return int(match.group(1)) if match else None

    # Iterate over each row in the DataFrame
    for i in range(nr):
        # Convert the "Distribution" column from string to a dictionary
        d = eval(df_in["Distribution"][i]).split(",")
        distr = {int(d[j]): int(d[j + 1]) for j in range(0, len(d), 2)}
        tot = sum(distr.values())
        
        # Determine the theoretical minimum based on the first number in the filename
        theor_min = extract_first_number(df_in["Filename"][i])
        
        # Calculate probabilities and frequencies
        p_opt = distr.get(theor_min, 0) / tot
        p_unfeas = sum(distr[f] for f in distr if f >= 1000) / tot
        minimum = min(distr.keys())
        freq_min = distr[minimum]
        mode, freq_mode = max(((f, distr[f]) for f in distr), key=lambda c: c[1])
        
        # Retrieve additional fields from the input CSV
        penalty = df_in["Penalty"][i]
        p_value = df_in["P"][i]
        iteration = df_in["Iter"][i]
        function_value = df_in["Function_Value"][i]
        num_evaluations = df_in["Num_Evaluations"][i]
        phase_time = df_in["Phase_Time"][i]
        total_time = df_in["Total_Time"][i]

        # Create a dictionary for the row
        row = {
            "problem": df_in["Filename"][i],
            "penalty": penalty,
            "p": p_value,
            "iter": iteration,
            "energy": function_value,
            "prob_opt": p_opt,
            "prob_unfeas": p_unfeas,
            "min": minimum,
            "freq_min": freq_min / tot,
            "mode": mode,
            "freq_mode": freq_mode / tot,
            "num_evaluations": num_evaluations,
            "phase_time": phase_time,
            "total_time": total_time
        }
        data.append(row)

    # Create the output DataFrame and save to CSV
    df_out = pd.DataFrame(data)
    input_dir = os.path.dirname(filename)
    output_filename = os.path.join(input_dir, f"analysis_{os.path.basename(filename)}")
    df_out.to_csv(output_filename, index=False)
    print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    filename = '/home/fabrizio/Scrivania/QAOA-SAT-SCH-OLC/results_1_costruzione_p12/result.csv'
    analysis(filename)
