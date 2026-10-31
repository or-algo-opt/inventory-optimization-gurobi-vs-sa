"""
基于 Gurobi 的精确求解模块 (MILP)。
构建多级、多周期的库存网络混合整数线性规划模型，以最小化总成本。
"""

import gurobipy as gp
from gurobipy import GRB
import config
import time

def solve_inventory_milp(demand_matrix, initial_inventory):
    """
    使用 Gurobi 求解多级库存 MILP 模型。
    
    Args:
        demand_matrix (np.ndarray): 区域仓需求矩阵 (NUM_RDC x NUM_PERIODS)
        initial_inventory (list): 初始库存列表
        
    Returns:
        tuple: (总成本, 每个周期每个区域仓的库存字典, 每个周期的补货字典, 求解耗时)
    """
    print(">>> [Gurobi] 开始构建 MILP 模型...")
    start_time = time.time()
    
    # 1. 初始化模型
    model = gp.Model("Multi-Echelon_Inventory")
    model.setParam('OutputFlag', 0) # 关闭 Gurobi 控制台冗余输出，保持终端清爽

    # 2. 定义决策变量
    # x[i, t]: 第 t 周期，中心仓向 区域仓 i 补货的数量
    x = model.addVars(config.NUM_RDC, config.NUM_PERIODS, vtype=GRB.INTEGER, name="x")
    # I[i, t]: 第 t 周期末，区域仓 i 的期末库存量
    I = model.addVars(config.NUM_RDC, config.NUM_PERIODS, vtype=GRB.INTEGER, name="I")
    # S[i, t]: 第 t 周期末，区域仓 i 的缺货量
    S = model.addVars(config.NUM_RDC, config.NUM_PERIODS, vtype=GRB.INTEGER, name="S")

    # 0-1 变量 y[i, t]: 第 t 周期是否发起补货
    y = model.addVars(config.NUM_RDC, config.NUM_PERIODS, vtype=GRB.BINARY, name="y")

    # 3. 设置目标函数：最小化 运输成本 + 持有成本 + 缺货惩罚成本 + 固定订货成本
    obj_expr = gp.LinExpr()
    for i in range(config.NUM_RDC):
        for t in range(config.NUM_PERIODS):
            obj_expr += config.TRANSPORT_COST * x[i, t]
            obj_expr += config.HOLDING_COST * I[i, t]
            obj_expr += config.SHORTAGE_COST * S[i, t]
            obj_expr += config.FIXED_ORDER_COST * y[i, t]
    
    model.setObjective(obj_expr, GRB.MINIMIZE)

    # 4. 添加约束条件
    for i in range(config.NUM_RDC):
        for t in range(config.NUM_PERIODS):
            # (1) 库存平衡约束: 
            # 上期库存 + 补货量 - 当期需求 = 期末库存 - 期末缺货量
            prev_inv = initial_inventory[i] if t == 0 else I[i, t-1]
            model.addConstr(prev_inv + x[i, t] - demand_matrix[i, t] == I[i, t] - S[i, t], name=f"InvBal_{i}_{t}")

            # 服务水平 / 安全库存约束
            # 强制要求期末库存不能低于 10 件（应对突发波动）
            model.addConstr(I[i, t] >= 10, name=f"SafetyStock_{i}_{t}") 

            # 如果补货量 > 0，则 y 必须为 1
            model.addConstr(x[i, t] <= config.MAX_DC_SUPPLY * y[i, t], name=f"OrderTrigger_{i}_{t}")

            # (2) 区域仓容量约束
            model.addConstr(I[i, t] <= config.MAX_RDC_CAPACITY, name=f"Capacity_{i}_{t}")
            
        # (3) 中心仓总供给约束 (每个周期所有区域仓的补货总和不能超过中心仓能力)
        for t in range(config.NUM_PERIODS):
            model.addConstr(gp.quicksum(x[i, t] for i in range(config.NUM_RDC)) <= config.MAX_DC_SUPPLY, name=f"DC_Limit_{t}")

    print(">>> [Gurobi] 模型构建完成，开始求解...")
    model.optimize()

    solve_time = time.time() - start_time
    total_cost = model.ObjVal if model.status == GRB.OPTIMAL else float('inf')
    
    # 提取结果，方便后续可视化
    inv_result = {(i, t): I[i, t].X for i in range(config.NUM_RDC) for t in range(config.NUM_PERIODS)}
    order_result = {(i, t): x[i, t].X for i in range(config.NUM_RDC) for t in range(config.NUM_PERIODS)}
    
    print(f">>> [Gurobi] 求解结束！状态: OPTIMAL, 总成本: {total_cost:.2f}, 耗时: {solve_time:.4f}s\n")
    
    return total_cost, inv_result, order_result, solve_time