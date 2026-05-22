exec(open('figures/_style_header.py').read())

with open('figures/problem_3_results.json') as f:
    data = json.load(f)

alpha_profiles = data['sample_alpha_profiles']
productions = ['72', '63', '54', '45', '36']

matrix = np.array([alpha_profiles[p] for p in productions])

fig, ax = plt.subplots(figsize=(10, 4.5))

im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd', vmin=0, vmax=1, interpolation='nearest')

ax.set_yticks(range(len(productions)))
ax.set_yticklabels([f'{p} t/d' for p in productions], fontsize=11)
ax.set_xticks(np.arange(0, 24, 3))
ax.set_xticklabels([f'{h}:00' for h in range(0, 24, 3)], fontsize=10)
ax.set_xlabel('时刻', fontsize=13)

cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('负荷率', fontsize=12)

for spine in ax.spines.values():
    spine.set_visible(True)

fig.tight_layout()
fig.savefig('figures/fig_q3_dispatch.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q3_dispatch.pdf')
