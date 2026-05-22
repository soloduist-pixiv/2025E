exec(open('figures/_style_header.py').read())

with open('figures/problem_3_results.json') as f:
    data = json.load(f)

costs_all = data['cost_distribution']
productions = ['72', '63', '54', '45', '36']
n_scenes = 24

matrix = np.zeros((len(productions), n_scenes))
for i, p in enumerate(productions):
    matrix[i, :] = costs_all[p]

fig, ax = plt.subplots(figsize=(11, 4.5))

im = ax.imshow(matrix, aspect='auto', cmap='coolwarm', interpolation='nearest')

ax.set_yticks(range(len(productions)))
ax.set_yticklabels([f'{p} t/d' for p in productions], fontsize=11)
ax.set_xticks(np.arange(0, 24, 4))
ax.set_xticklabels([f'S{i+1}' for i in range(0, 24, 4)], fontsize=10)
ax.set_xlabel('风光场景编号', fontsize=13)

cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('吨氨成本 (元/t)', fontsize=12)

for spine in ax.spines.values():
    spine.set_visible(True)

fig.tight_layout()
fig.savefig('figures/fig_q3_alpha_heatmap.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q3_alpha_heatmap.pdf')
