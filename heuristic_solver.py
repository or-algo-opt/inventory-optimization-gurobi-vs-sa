"""
基于启发式的 (s, S) 库存策略求解模块。
在 Gurobi 面对大规模问题无法求解时，这种简单的策略在工业界极为常用。
"""

import config
import time

def solve_inventory_heuristic(demand_matrix, initial_inventory):
    """
    使用 (s, S) 策略模拟库存运转。
    规则：每天结束若库存 <= s,则补货到 S。
    
    Args:
        demand_matrix (np.ndarray): 区域仓需求矩阵
        initial_inventory (list): 初始库存列表
        
    Returns:
        tuple: (总成本, 库存结果字典, 补货结果字典, 耗时)
    """
    print(">>> [Heuristic] 开始模拟 (s, S) 补货策略...")
    start_time = time.time()
    
    total_cost = 0.0
    current_inventory = initial_inventory.copy()
    
    inv_result = {}
    order_result = {}
    
    s = config.HEURISTIC_s
    S = config.HEURISTIC_S
    
    for t in range(config.NUM_PERIODS):
        for i in range(config.NUM_RDC):
            # 1. 期初补货决策 (基于上一周期末的库存)
            if current_inventory[i] <= s:
                target_order = S - current_inventory[i]
                
                # 限制 1：不能超过中心仓均摊的运力
                dc_limit = config.MAX_DC_SUPPLY / config.NUM_RDC
                
                # 限制 2：不能超过区域仓的剩余可用库容
                rdc_capacity_left = config.MAX_RDC_CAPACITY - current_inventory[i]
                
                # 取两者的最小值，同时保证不能是负数
                order_qty = min(target_order, dc_limit, rdc_capacity_left)
                order_qty = max(order_qty, 0) 
            else:
                order_qty = 0
                
            order_result[(i, t)] = order_qty

            # 加上固定发车成本和单件运输成本
            if order_qty > 0:
                total_cost += config.FIXED_ORDER_COST
                total_cost += order_qty * config.TRANSPORT_COST
            
            # 2. 满足需求，计算期末库存和缺货
            demand = demand_matrix[i, t]
            available_inv = current_inventory[i] + order_qty
            
            if available_inv >= demand:
                # 需求满足，有剩余库存
                current_inventory[i] = available_inv - demand
                shortage = 0
            else:
                # 产生缺货
                current_inventory[i] = 0
                shortage = demand - available_inv
                
            inv_result[(i, t)] = current_inventory[i]
            
            # 3. 累加持有成本和缺货成本
            total_cost += current_inventory[i] * config.HOLDING_COST
            total_cost += shortage * config.SHORTAGE_COST

    solve_time = time.time() - start_time
    print(f">>> [Heuristic] 模拟结束！总成本: {total_cost:.2f}, 耗时: {solve_time:.4f}s\n")
    
    return total_cost, inv_result, order_result, solve_time