import pandas as pd

# Load the CSV file
file_path = '/home/fabrizio/Scrivania/QAOA-SAT-SCH-OLC/results_cobyla_3000/analysis_result.csv'
data = pd.read_csv(file_path)

# Remove whitespace from column names
data.columns = data.columns.str.strip()

theoretical_solution = 0.024691358024691357

# Find the best value of `prob_opt` for each `p`
best_prob_opt = data.groupby('p')['prob_opt'].max().reset_index()
best_prob_opt = best_prob_opt.rename(columns={'prob_opt': 'best_prob_opt'})

# Find the row index where `prob_opt` is max for each `p`
best_prob_opt_idx = data.groupby('p')['prob_opt'].idxmax()

# Use these indices to get the corresponding best values of `prob_unfeas` and `energy`
best_prob_unfeas = data.loc[best_prob_opt_idx, ['p', 'prob_unfeas']].reset_index(drop=True)
best_energy = data.loc[best_prob_opt_idx, ['p', 'energy']].reset_index(drop=True)

# Merge the best values of `prob_opt`, `prob_unfeas`, and `energy` with the original DataFrame
data = data.merge(best_prob_opt, on='p')
data = data.merge(best_prob_unfeas, on='p', suffixes=('', '_best'))
data = data.merge(best_energy, on='p', suffixes=('', '_best'))

# Calculate the RPD as a percentage increase over the theoretical solution
data['RPD'] = ((data['best_prob_opt'] - theoretical_solution) / theoretical_solution) * 100

# Group by 'p' and calculate the means of 'prob_opt', 'prob_unfeas', and 'energy'
grouped_data = data.groupby('p').agg(
    mean_prob_opt=pd.NamedAgg(column='prob_opt', aggfunc='mean'),
    mean_prob_unfeas=pd.NamedAgg(column='prob_unfeas', aggfunc='mean'),
    mean_energy=pd.NamedAgg(column='energy', aggfunc='mean'),
    best_prob_opt=pd.NamedAgg(column='best_prob_opt', aggfunc='max'),
    best_prob_unfeas=pd.NamedAgg(column='prob_unfeas_best', aggfunc='first'),  # Using the best_unfeas values
    best_energy=pd.NamedAgg(column='energy_best', aggfunc='first'),
    RPD=pd.NamedAgg(column='RPD', aggfunc='first')
).reset_index()

# Round the numerical values to 3 decimal places, but avoid trailing zeros
grouped_data = grouped_data.round(3)

# Convert the DataFrame to a LaTeX table, removing trailing zeros
latex_table = grouped_data.to_latex(index=False, float_format="%.3f")

# Save the LaTeX table to a file
with open('table.tex', 'w') as file:
    file.write(latex_table)

print("The LaTeX table has been saved to 'table.tex'.")
