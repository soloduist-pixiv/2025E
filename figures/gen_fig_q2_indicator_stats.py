exec(open('figures/_style_header.py').read())

with open('figures/problem_2_results.json') as f:
    data = json.load(f)

productions = ['72', '63', '54', '45', '36']
all_pass = [data['all_scenarios'][p]['n_all_pass'] * 15 for p in productions]
partial = [data['all_scenarios'][p]['n_partial'] * 15 for p in productions]
all_fail = [data['all_scenarios'][p]['n_all_fail'] * 15 for p in productions]

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(productions))
w = 0.6

ax.bar(x, all_pass, w, color=PALETTE[2], label='全满足')
ax.bar(x, partial, w, bottom=all_pass, color=PALETTE[1], label='部分满足')
ax.bar(x, all_fail, w, bottom=[a+p for a,p in zip(all_pass, partial)], color=PALETTE[4], label='全不满足')

ax.set_xticks(x)
ax.set_xticklabels([f'{p} t/d' for p in productions], fontsize=12)
ax.set_ylabel('天数 (d)', fontsize=13)
ax.set_ylim(0, 380)
ax.axhline(360, color='gray', linestyle=':', linewidth=1)
ax.legend(fontsize=11, loc='upper right')

for i in range(len(productions)):
    total = all_pass[i] + partial[i] + all_fail[i]
    if all_pass[i] > 20:
        ax.text(i, all_pass[i]/2, f'{all_pass[i]}', ha='center', va='center', fontsize=10, color='white', fontweight='bold')

fig.tight_layout()
fig.savefig('figures/fig_q2_indicator_stats.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q2_indicator_stats.pdf')
