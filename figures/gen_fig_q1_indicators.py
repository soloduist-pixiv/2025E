exec(open('figures/_style_header.py').read())

with open('figures/problem_1_results.json') as f:
    data = json.load(f)

gi = data['green_indicators']
indicators = ['自发自用比例', '绿电比例', '上网电量比例']
actual = [gi['r1'], gi['r2'], gi['r3']]
threshold = [60, 30, 20]
threshold_type = ['>=', '>=', '<=']

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(indicators))
w = 0.35

bars1 = ax.bar(x - w/2, actual, w, color=PALETTE[0], label='实际值')
bars2 = ax.bar(x + w/2, threshold, w, color=PALETTE[1], alpha=0.7, label='要求值')

for i, (a, t, tp) in enumerate(zip(actual, threshold, threshold_type)):
    passed = (a >= t) if tp == '>=' else (a <= t)
    marker = 'PASS' if passed else 'FAIL'
    color = '#2E9E44' if passed else '#E53935'
    ax.text(i - w/2, a + 1.5, f'{a:.1f}%', ha='center', fontsize=10, color=PALETTE[0], fontweight='bold')
    ax.text(i + w/2, t + 1.5, f'{t}%', ha='center', fontsize=10, color=PALETTE[1])
    ax.text(i, max(a, t) + 6, marker, ha='center', fontsize=11, color=color, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(indicators, fontsize=12)
ax.set_ylabel('比例 (%)', fontsize=13)
ax.set_ylim(0, 85)
ax.legend(fontsize=12)

fig.tight_layout()
fig.savefig('figures/fig_q1_indicators.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q1_indicators.pdf')
