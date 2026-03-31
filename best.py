import pandas as pd

df = pd.read_csv("/home/fabrizio/Scrivania/QAOA-SAT-SCH-OLC/results_SPSA_1000/analysis_result.csv")

# indice della riga con prob_opt massimo per ciascun (istanza, fase)
idx = df.groupby(['problem', 'p'])['prob_opt'].idxmax()

best_by_instance_phase = (
    df.loc[idx, ['problem', 'p', 'iter', 'prob_opt']]
      .rename(columns={'problem': 'instance', 'prob_opt': 'best_prob_opt'})
      .sort_values(['instance', 'p'])
      .reset_index(drop=True)
)

best_by_instance_phase.to_csv("best_prob_opt_by_instance_phase.csv", index=False)
print(best_by_instance_phase.head())
