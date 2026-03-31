import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


file_path = "/home/fabrizio/Scrivania/QAOA-SAT-SCH-OLC/results_cobyla_3000/analysis_result.csv"
df = pd.read_csv(file_path)


palette = ["#f781bf", "#a65628", "#ffff33", "#4daf4a", "#377eb8", "#984ea3", "#ff7f00", "#e41a1c"]


g = sns.catplot(
    data=df, 
    x="p", 
    y="prob_opt", 
    col="problem", 
    kind="box", 
    height=8, 
    aspect=1.6, 
    hue="p",  
    palette=palette,  
    width=0.9,  
    linewidth=0.5
)


for ax in g.axes.flat:  
    title = ax.get_title().replace("problem = ", "")  # Remove "problem = "
    ax.set_title(title, fontsize=24, pad=20)  

g.set_axis_labels("p", "P_opt", fontsize=24)

plt.subplots_adjust(top=0.77, wspace=0.3, hspace=0.3)
g.fig.suptitle('Variation of P_opt for each phase', fontsize=36, y=0.95)

g.savefig("boxplot_18.png", format="png", dpi=600, bbox_inches='tight')

plt.show()
