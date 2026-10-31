"""
基于模拟退火（Simulated Annealing）的元启发式求解模块。
目标：自动搜索多级网络中最优的 (s, S) 补货参数，以最小化真实环境下的总成本。
"""

import random
import math
import config
import simulator

def evaluate_params(params, forecast_demand, actual_demand, initial_inventory):
    """
    评估函数：给定一组 (s, S) 参数，在预测需求下生成补货计划，并在真实需求下计算真实成本。
    
    Args:
        params (tuple): (s, S) 参数对
        forecast_demand (np.ndarray): 预测需求（用于做决策）
        actual_demand (np.ndarray): 真实需求（用于结算成本）
        initial_inventory (list): 初始库存
        
    Returns:
        float: 真实环境下的总成本
    """
    s, S = params
    order_plan = {}
    current_inventory = initial_inventory.copy()
    
    # 1. 基于预测需求，使用 (s, S) 策略生成补货计划
    for t in range(config.NUM_PERIODS):
        for i in range(config.NUM_RDC):
            if current_inventory[i] <= s:
                # 理想情况下需要补足的差额
                target_order = S - current_inventory[i]
                
                # 限制1：不能超过中心仓给每个仓的均摊供给上限
                dc_limit = config.MAX_DC_SUPPLY / config.NUM_RDC
                
                # 限制2：不能超过区域仓的剩余可用库容（防爆仓）
                capacity_limit = config.MAX_RDC_CAPACITY - current_inventory[i]
                
                # 综合取最小值，并保证补货量非负
                order_qty = max(0, min(target_order, dc_limit, capacity_limit))
            else:
                order_qty = 0
                
            order_plan[(i, t)] = order_qty
            
            # 在预测需求下更新库存状态（假设缺货直接丢失，不允许负库存）
            current_inventory[i] = max(0, current_inventory[i] + order_qty - forecast_demand[i, t])
            
    # 2. 用真实需求结算成本（Simulator 仿真）
    real_cost, _ = simulator.simulate_real_execution(order_plan, actual_demand, initial_inventory)
    return real_cost


def simulated_annealing(forecast_demand, actual_demand, initial_inventory):
    """
    模拟退火主循环，搜索最优的 (s, S) 参数。
    """
    print(">>> [Metaheuristic] 启动模拟退火算法搜索最优 (s, S) 参数...")
    
    # --- 算法超参数 ---
    T0 = 1000.0      # 初始温度
    T_end = 0.1      # 终止温度
    alpha = 0.95     # 降温系数
    max_iter = 50    # 每个温度下的迭代次数
    random.seed(42) 
    
    # --- 初始化当前解 ---
    # 随机初始化一个 s 和 S (保证 s < S)
    current_s = random.randint(10, 40)
    current_S = random.randint(60, 120)
    current_params = (current_s, current_S)
    current_cost = evaluate_params(current_params, forecast_demand, actual_demand, initial_inventory)
    
    # 记录全局最优解
    best_params = current_params
    best_cost = current_cost
    
    T = T0
    step = 0
    
    while T > T_end:
        for _ in range(max_iter):
            step += 1
            # 1. 产生新解（在当前解附近随机扰动）
            new_s = max(0, current_s + random.randint(-5, 5))
            new_S = max(new_s + 10, current_S + random.randint(-10, 10))
            new_S = min(new_S, config.MAX_RDC_CAPACITY) # 不能超过最大仓容
            
            new_params = (new_s, new_S)
            
            # 2. 计算新解的成本
            new_cost = evaluate_params(new_params, forecast_demand, actual_demand, initial_inventory)
            
            # 3. Metropolis 接受准则
            if new_cost < current_cost:
                # 新解更好，直接接受
                current_params = new_params
                current_cost = new_cost
                current_s, current_S = new_s, new_S
            else:
                # 新解更差，以一定概率接受（跳出局部最优）
                delta = new_cost - current_cost
                if random.random() < math.exp(-delta / T):
                    current_params = new_params
                    current_cost = new_cost
                    current_s, current_S = new_s, new_S
                    
            # 4. 更新全局最优解
            if current_cost < best_cost:
                best_params = current_params
                best_cost = current_cost
                print(f"    [SA] 发现更优参数: (s={best_params[0]}, S={best_params[1]}), 真实成本: {best_cost:.2f}")
                
        # 降温
        T *= alpha
        
    print(f">>> [Metaheuristic] 搜索完毕！最优参数: (s={best_params[0]}, S={best_params[1]})")
    print(f">>> [Metaheuristic] 最低真实总成本: {best_cost:.2f}\n")
    
    return best_params, best_cost