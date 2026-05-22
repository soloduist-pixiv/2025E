"""主程序：串联所有子问题求解"""
import sys
import json
import os
sys.path.insert(0, 'code')

def main():
    print("=" * 70)
    print("绿电直连型电氢氨园区优化运行 - 完整求解")
    print("=" * 70)

    # 问题一
    print("\n\n" + "=" * 70)
    from problem1 import solve_problem1
    r1 = solve_problem1()

    # 问题二
    print("\n\n" + "=" * 70)
    from problem2 import solve_problem2
    r2 = solve_problem2()

    # 问题三
    print("\n\n" + "=" * 70)
    from problem3 import solve_problem3
    r3 = solve_problem3()

    # 问题四
    print("\n\n" + "=" * 70)
    from problem4 import solve_problem4
    r4 = solve_problem4()

    # 灵敏度分析
    print("\n\n" + "=" * 70)
    from sensitivity_analysis import run_sensitivity
    r5 = run_sensitivity()

    # 汇总结果
    all_results = {
        'problem1': r1,
        'problem2_summary': {
            'best_typical': r2['best_typical'],
            'annual_analysis': r2['annual_analysis'],
        },
        'problem3_summary': {
            'annual_analysis': r3['annual_analysis'],
            'comparison_with_q2': r3['comparison_with_q2'],
        },
        'problem4_summary': {
            'offgrid_annual_Q': r4['offgrid_no_storage']['annual_Q'],
            'storage_best_C_bat': r4['storage_optimization']['best_C_bat_MWh'],
            'grid_vs_offgrid': r4['grid_vs_offgrid'],
        },
        'sensitivity': r5,
    }

    os.makedirs('figures', exist_ok=True)
    with open('figures/all_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n\nSaved: figures/all_results.json")
    print("\n✅ 全部求解完成!")


if __name__ == '__main__':
    main()
