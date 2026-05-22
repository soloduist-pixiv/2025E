exec(open('figures/_style_header.py').read())

with open('figures/problem_2_results.json') as f:
    data = json.load(f)

productions = ['72', '63', '54', '45', '36']
cost_data = [data['cost_distribution'][p] for p in productions]

fig, ax = plt.subplots(figsize=(9, 5.5))

bp = ax.boxplot(cost_data, labels=[f'{p} t/d' for p in productions],
                patch_artist=True, widths=0.6,
                medianprops=dict(color='white', linewidth=2),
                whiskerprops=dict(linewidth=1.5),
                capprops=dict(linewidth=1.5),
                flierprops=dict(marker='o', markersize=5))

for patch, color in zip(bp['boxes'], [PALETTE[i] for i in range(5)]):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)

means = [np.mean(d) for d in cost_data]
ax.scatter(range(1, 6), means, marker='D', color='white', edgecolors='black',
           s=60, zorder=5, label='均值')

ax.set_xlabel('日产氨量', fontsize=13)
ax.set_ylabel('吨氨成本 (元/t)', fontsize=13)
ax.legend(fontsize=11)

fig.tight_layout()
fig.savefig('figures/fig_q2_24scenes_cost.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q2_24scenes_cost.pdf')
