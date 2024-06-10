import pandas as pd
import os
import argparse

def analysis(filename):
    df_in = pd.read_csv(filename)
    data = []
    nr, nc = df_in.shape

    # Iterate over each row in the DataFrame
    for i in range(nr):
        # Convert the "Distribution" column from string to a dictionary
        d = eval(df_in["Distribution"][i]).split(",")
        distr = {int(d[j]): int(d[j + 1]) for j in range(0, len(d), 2)}
        tot = sum(distr.values())
        
        # Determine the theoretical minimum based on the filename
        theor_min = 0 if df_in["Filename"][i].endswith("_0.json") else 1
        
        # Calculate probabilities and frequencies
        p_opt = distr.get(theor_min, 0) / tot
        p_unfeas = sum(distr[f] for f in distr if f >= 1000) / tot
        minimum = min(distr.keys())
        freq_min = distr[minimum]
        mode, freq_mode = max(((f, distr[f]) for f in distr), key=lambda c: c[1])
        
        # Create a dictionary for the row
        row = {
            "problem": 0 if df_in["Filename"][i].endswith("_0.json") else 1,
            "penalty": df_in["Penalty"][i],
            "p": df_in["P"][i],
            "prob_opt": p_opt,
            "prob_unfeas": p_unfeas,
            "min": minimum,
            "freq_min": freq_min / tot,
            "mode": mode,
            "freq_mode": freq_mode / tot
        }
        data.append(row)

    df_out = pd.DataFrame(data)

    output_filename = f"result_analysis_{os.path.basename(filename)}"

    df_out.to_csv(output_filename, index=False)
    print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a CSV file for analysis.')
    parser.add_argument('filename', required=True, type=str, help='the CSV file to be processed')
    args = parser.parse_args()

    analysis(args.filename)
