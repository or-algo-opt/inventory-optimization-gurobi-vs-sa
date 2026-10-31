import data_generator
import gurobi_solver
import heuristic_solver
import metaheuristic_solver
import simulator
import visualizer
import config

def main():
    print("=" * 60)
    print(" 多级供应链网络库存优化模型 (MILP vs 固定启发式 vs SA元启发式)")
    print("=" * 60 + "\n")
    
    # 1. 生成数据 (真实需求 vs 预测需求)
    actual_demand, forecast_demand = data_generator.generate_demand_data()
    initial_inventory = data_generator.get_initial_inventory()
    print(f"[1] 数据生成完成。初始库存: {initial_inventory}")
    
    # 2. Gurobi 求解 (基于预测需求)
    print("\n[2] 调用 Gurobi 基于【预测需求】求解精确模型...")
    cost_gurobi_forecast, _, order_gurobi, _ = gurobi_solver.solve_inventory_milp(forecast_demand, initial_inventory)
    
    # 3. 固定参数 (s, S) 求解 (基于预测需求)
    print("[3] 调用【固定参数 (s,S)】基于【预测需求】求解...")
    cost_heur_forecast, _, order_heur, _ = heuristic_solver.solve_inventory_heuristic(forecast_demand, initial_inventory)

    # 4. 模拟退火 (SA) 求解 (基于预测需求)
    print("\n[4] 调用【模拟退火 (SA)】搜索最优 (s, S) 参数...")
    best_params, _ = metaheuristic_solver.simulated_annealing(forecast_demand, actual_demand, initial_inventory)
    
    # 用 SA 找到的最优参数生成补货计划
    s_opt, S_opt = best_params
    order_sa = {}
    current_inv = initial_inventory.copy()
    for t in range(config.NUM_PERIODS):
        for i in range(config.NUM_RDC):
            if current_inv[i] <= s_opt:
                oq = S_opt - current_inv[i]
            else:
                oq = 0
            order_sa[(i, t)] = oq
            current_inv[i] = max(0, current_inv[i] + oq - forecast_demand[i, t])

    # 5. 仿真评估 (全部用真实需求检验)
    print("\n[5] 在【真实需求】下模拟执行上述三种补货计划 (Simulation)...")
    real_cost_gurobi, real_inv_gurobi = simulator.simulate_real_execution(order_gurobi, actual_demand, initial_inventory)
    real_cost_heur, real_inv_heur = simulator.simulate_real_execution(order_heur, actual_demand, initial_inventory)
    real_cost_sa, real_inv_sa = simulator.simulate_real_execution(order_sa, actual_demand, initial_inventory)
    
    # 6. 结果对比
    print("\n" + "=" * 60)
    print(" 结果总结 (业务洞察)")
    print("=" * 60)
    print(f" Gurobi MILP (真实执行) : 真实成本 = {real_cost_gurobi:.2f} 元 👈 (全局最优)")
    print(f" SA 优化 (s,S) (真实执行): 真实成本 = {real_cost_sa:.2f} 元 👈 (算法自动寻优)")
    print(f" 固定 (s,S) (真实执行)  : 真实成本 = {real_cost_heur:.2f} 元 👈 (人工经验规则)")
    
    # 7. 画图对比
    print("\n[6] 正在绘制结果图表...")
    # 画策略对比图 (三条线)
    visualizer.plot_inventory_levels(real_inv_gurobi, real_inv_sa, real_inv_heur)
    
    # 画单点运营细节图 (只展示 Gurobi 的)
    visualizer.plot_operational_details(actual_demand, real_inv_gurobi, order_gurobi, rdc_id=0)
    
    # 画多级网络全局图 (只展示 Gurobi 的)
    visualizer.plot_multi_rdc_network(real_inv_gurobi, order_gurobi)

if __name__ == "__main__":
    main()