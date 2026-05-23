exec(open('figures/_style_header.py').read())

# 读取BSTS时序分解结果
with open('figures/bsts_results.json') as f:
    bsts = json.load(f)

# 选择风电典型场景 W4 (最高风电出力场景, 索引为3) 进行可视化
wi = 3  # W4场景
wind_scenarios = np.array(bsts['wind']['scenarios'])   # shape (24, 6)
wind_epsilon = np.array(bsts['wind']['epsilon'])       # shape (24, 6)
wind_mu = bsts['wind']['mu'][wi]                       # float
wind_seasonal = np.array(bsts['wind']['seasonal'])     # (24,)

original = wind_scenarios[:, wi]
trend = np.full(24, wind_mu)
seasonal = wind_seasonal
irregular = wind_epsilon[:, wi]
reconstructed = trend + seasonal + irregular

# 创建4行叠加子图
fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
hours = np.arange(1, 25)

# 1. 原始与重构出力对比
axes[0].plot(hours, original, 'o-', color=PALETTE[0], label='原始风电出力', linewidth=2.5)
axes[0].plot(hours, reconstructed, '--', color=PALETTE[1], label='BSTS重构出力', linewidth=2)
axes[0].set_ylabel('出力标幺值', fontsize=12)
axes[0].set_title('BSTS 状态分解时序重构 (典型风电场景 W4)', fontsize=14, fontweight='bold')
axes[0].legend(loc='upper right', fontsize=10)
axes[0].grid(True, linestyle='--', alpha=0.5)

# 2. 趋势项 mu(t)
axes[1].plot(hours, trend, '-', color='#E53935', label='基准趋势项 $\mu(t)$ (均值水平)', linewidth=2.5)
axes[1].set_ylabel('趋势值', fontsize=12)
axes[1].legend(loc='upper right', fontsize=10)
axes[1].grid(True, linestyle='--', alpha=0.5)
axes[1].set_ylim(0, 0.5)

# 3. 季节项 tau(t)
axes[2].plot(hours, seasonal, 's-', color='#2E9E44', label='日周期季节项 $\\tau(t)$ (24小时均值归零循环)', linewidth=2)
axes[2].set_ylabel('季节波动', fontsize=12)
axes[2].legend(loc='upper right', fontsize=10)
axes[2].grid(True, linestyle='--', alpha=0.5)

# 4. 随机扰动项 epsilon(t)
axes[3].bar(hours, irregular, color='#D32F2F', alpha=0.75, label='高频随机扰动项 $\\epsilon(t)$ (残差扰动)')
axes[3].set_ylabel('随机扰动', fontsize=12)
axes[3].set_xlabel('时间 (小时)', fontsize=13)
axes[3].legend(loc='upper right', fontsize=10)
axes[3].grid(True, linestyle='--', alpha=0.5)

# 微调布局
plt.xticks(hours)
fig.tight_layout()

# 保存高质量PDF矢量图
fig.savefig('figures/fig_bsts_decomp.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_bsts_decomp.pdf')
