import config

def simulate_real_execution(order_plan, actual_demand, initial_inventory):
    """
    根据给出的补货计划（order_plan），在真实的实际需求（actual_demand）下模拟运行，计算真实成本。
    
    Args:
        order_plan (dict): 区域仓的补货决策字典 (i, t) -> 补货量
        actual_demand (np.ndarray): 真实的客户需求
        initial_inventory (list): 初始库存
        
    Returns:
        float: 真实环境下的总成本
        dict: 真实的期末库存记录
    """
    total_cost = 0.0
    current_inventory = initial_inventory.copy()
    real_inv_record = {}

    for t in range(config.NUM_PERIODS):
        for i in range(config.NUM_RDC):
            order_qty = order_plan.get((i, t), 0)
            
            # 加上运输成本和固定发车费（假设只要补货就发车）
            if order_qty > 0:
                total_cost += config.FIXED_ORDER_COST + order_qty * config.TRANSPORT_COST
                
            # 真实情况下的消耗
            demand = actual_demand[i, t]
            available_inv = current_inventory[i] + order_qty
            
            if available_inv >= demand:
                current_inventory[i] = available_inv - demand
                shortage = 0
            else:
                current_inventory[i] = 0
                shortage = demand - available_inv
                
            real_inv_record[(i, t)] = current_inventory[i]
            
            # 真实库存费与缺货罚款
            total_cost += current_inventory[i] * config.HOLDING_COST
            total_cost += shortage * config.SHORTAGE_COST
            
    return total_cost, real_inv_record