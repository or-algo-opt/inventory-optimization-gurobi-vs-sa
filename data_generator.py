import numpy as np
import config

def generate_demand_data():
    """
    生成区域仓的每日随机需求。
    返回：(真实需求矩阵, 预测需求矩阵)
    """
    np.random.seed(42) 
    # 1. 模拟真实需求
    actual_demand = np.random.normal(loc=50, scale=15, size=(config.NUM_RDC, config.NUM_PERIODS))
    actual_demand = np.maximum(actual_demand, 0).astype(int)
    
    # 2. 模拟带有偏差的需求预测
    # 为了科学控制变量，在真实需求上叠加均值为 0、标准差为 10% 的正态分布随机噪声
    forecast_error = np.random.normal(loc=0, scale=0.1, size=(config.NUM_RDC, config.NUM_PERIODS))
    forecast_demand = actual_demand * (1 + forecast_error)
    forecast_demand = np.maximum(forecast_demand, 0).astype(int)
    
    return actual_demand, forecast_demand

def get_initial_inventory():
    return [50] * config.NUM_RDC