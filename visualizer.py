"""
结果可视化模块。
包含策略对比图以及单节点运营细节图（需求、补货、库存联动）。
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import config

mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
mpl.rcParams['axes.unicode_minus'] = False 

def plot_inventory_levels(inv_dict_gurobi, inv_dict_sa, inv_dict_heur):
    """
    绘制区域仓 0 在三种策略下的库存水位对比图。
    """
    periods = range(config.NUM_PERIODS)
    
    inv_gurobi = [inv_dict_gurobi[(0, t)] for t in periods]
    inv_sa = [inv_dict_sa[(0, t)] for t in periods]
    inv_heur = [inv_dict_heur[(0, t)] for t in periods]

    plt.figure(figsize=(10, 5))
    
    # 1. 画 Gurobi
    plt.plot(periods, inv_gurobi, marker='o', label='Gurobi (MILP 精确解)', color='#1f77b4', linewidth=2)
    # 2. 画 SA 优化
    plt.plot(periods, inv_sa, marker='^', label='(s, S) 策略 (模拟退火优化)', color='#2ca02c', linestyle='-.')
    # 3. 画 固定启发式
    plt.plot(periods, inv_heur, marker='s', label='(s, S) 策略 (固定经验值)', color='#ff7f0e', linestyle='--', alpha=0.6)
    
    plt.title('RDC 0 Inventory Level Strategy Comparison', fontsize=14)
    plt.xlabel('Period (Days)', fontsize=12)
    plt.ylabel('Inventory Level (Units)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('inventory_comparison.png', dpi=150)
    print(">>> [Visualizer] 策略对比图已保存为 'inventory_comparison.png'")
    plt.close()

def plot_operational_details(demand_matrix, inv_dict, order_dict, rdc_id=0):
    """
    绘制指定区域仓的运营细节三联图（需求、补货、库存联动）。
    """
    periods = range(config.NUM_PERIODS)
    
    demand = [demand_matrix[rdc_id, t] for t in periods]
    orders = [order_dict[(rdc_id, t)] for t in periods]
    inventory = [inv_dict[(rdc_id, t)] for t in periods]

    # 创建 3 行 1 列的子图，共享 X 轴
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 10), sharex=True)

    # 1. 需求图 (实际消耗)
    bars_demand = axes[0].bar(periods, demand, color='#d62728', alpha=0.7, label='Customer Demand')
    axes[0].set_ylabel('Demand (Units)', fontsize=11)
    axes[0].set_title(f'RDC {rdc_id} Operational Details (Gurobi Solution)', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right')
    axes[0].grid(axis='y', alpha=0.3)
    # 在柱状图上显示数值
    axes[0].bar_label(bars_demand, padding=2, fontsize=9) 

    # 2. 补货图 (决策结果)
    bars_orders = axes[1].bar(periods, orders, color='#2ca02c', alpha=0.7, label='Replenishment Order')
    axes[1].set_ylabel('Order Qty (Units)', fontsize=11)
    axes[1].legend(loc='upper right')
    axes[1].grid(axis='y', alpha=0.3)
    # 在柱状图上显示数值
    axes[1].bar_label(bars_orders, padding=2, fontsize=9)

    # 3. 库存图 (最终状态)
    axes[2].plot(periods, inventory, marker='o', color='#1f77b4', linewidth=2, label='Ending Inventory')
    axes[2].set_xlabel('Period (Days)', fontsize=12)
    axes[2].set_ylabel('Inventory (Units)', fontsize=11)
    axes[2].legend(loc='upper right')
    axes[2].grid(axis='y', alpha=0.3)
    # 在折线图的每个点上显示数值
    for x, y in zip(periods, inventory):
        axes[2].text(x, y + 2, f'{int(y)}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1f77b4')

    plt.xticks(periods) # 强制显示所有天的刻度
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('operational_details.png', dpi=150)
    print(">>> [Visualizer] 运营细节联动图（带数值）已保存为 'operational_details.png'")
    plt.close()

def plot_multi_rdc_network(inv_dict, order_dict):
    """
    绘制多级网络全局图。
    上图：所有区域仓的库存水位曲线。
    下图：中心仓每日向所有区域仓发货的总量（体现中心仓压力）。
    """
    periods = range(config.NUM_PERIODS)
    
    # 创建 2 行 1 列的子图
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 8), sharex=True)

    # 1. 绘制所有区域仓的库存曲线（上半部分）
    for i in range(config.NUM_RDC):
        inv_line = [inv_dict[(i, t)] for t in periods]
        axes[0].plot(periods, inv_line, marker='o', label=f'RDC {i} Inventory')
    
    axes[0].set_ylabel('Inventory Level (Units)', fontsize=11)
    axes[0].set_title('Multi-Echelon Network Status (Gurobi Solution)', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right', ncol=2) # ncol=2 让图例分两列排布，不遮挡曲线
    axes[0].grid(axis='y', alpha=0.3)

    # 2. 计算并绘制中心仓每日总发货量（下半部分）
    dc_total_shipments = []
    for t in periods:
        # 中心仓在某天的发货量 = 所有区域仓当天补货量之和
        daily_ship = sum(order_dict[(i, t)] for i in range(config.NUM_RDC))
        dc_total_shipments.append(daily_ship)
        
    bars_dc = axes[1].bar(periods, dc_total_shipments, color='#9467bd', alpha=0.7, label='DC Total Shipment')
    axes[1].set_xlabel('Period (Days)', fontsize=12)
    axes[1].set_ylabel('Total Shipped (Units)', fontsize=11)
    axes[1].legend(loc='upper right')
    axes[1].grid(axis='y', alpha=0.3)
    
    # 在柱状图上显示数字
    axes[1].bar_label(bars_dc, padding=2, fontsize=9)

    plt.xticks(periods)
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('multi_rdc_network.png', dpi=150)
    print(">>> [Visualizer] 多级网络全局图已保存为 'multi_rdc_network.png'")
    plt.close()