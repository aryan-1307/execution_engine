import pandas as pd
import numpy as np
from execution_strategies import ExecutionEngine
from backtester import Backtester

class QuantSimulator:
    def __init__(self, market_data, stats):
        self.market_data = market_data
        self.stats = stats

    def run_full_comparison(self, symbol, total_quantity):
        """
        Runs the standard strategy battle plus risk-aversion sensitivity.
        """
        df = self.market_data[symbol]
        num_intervals = len(df)
        
        engine = ExecutionEngine(
            symbol=symbol,
            side='buy',
            total_quantity=total_quantity,
            start_time=0,
            end_time=num_intervals
        )
        
        # 1. Standard Schedules
        strategies = {
            'TWAP': engine.get_twap_schedule(num_intervals),
            'VWAP': engine.get_vwap_schedule(df['Volume'].tolist())
        }
        
        # 2. Almgren-Chriss Sensitivity Test (Low, Med, High Risk Aversion)
        risk_profiles = {
            'AC_Aggressive': 0.01,  # Low risk aversion, trade slower
            'AC_Balanced': 0.1,    # Medium risk aversion
            'AC_Urgent': 0.5       # High risk aversion, trade faster
        }
        
        for name, lambda_val in risk_profiles.items():
            strategies[name] = engine.get_almgren_chriss_schedule(
                num_intervals=num_intervals,
                volatility=self.stats[symbol]['volatility'],
                liquidity_param=0.0001,
                risk_aversion=lambda_val
            )
        
        bt = Backtester(self.market_data, symbol, self.stats)
        results = []
        
        for name, schedule in strategies.items():
            res = bt.run_simulation(name, schedule)
            
            # Incorporating new cost breakdown from upgraded backtester
            results.append({
                'Symbol': symbol,
                'Strategy': name,
                'Avg_Fill': res['avg_fill_price'],
                'IS_Bps': res['implementation_shortfall_bps'],
                'Spread_Bps': res['spread_cost_bps'],
                'Slippage_Bps': res['slippage_cost_bps'],
                'Impact_Bps': res['impact_cost_bps'],
                'Total_Shares': total_quantity
            })
            
        return results

    def run_batch_simulation(self, symbol_list, volume_pct=0.02):
        """
        Orchestrates multi-asset testing.
        """
        all_results = []
        for symbol in symbol_list:
            if symbol not in self.market_data:
                continue
            
            avg_vol = self.stats[symbol]['avg_volume']
            # Target size: 2% of total period volume
            total_quantity = int(avg_vol * volume_pct * len(self.market_data[symbol]))
            
            res = self.run_full_comparison(symbol, total_quantity)
            all_results.extend(res)
            
        return pd.DataFrame(all_results)

if __name__ == "__main__":
    from data_loader import DataLoader
    loader = DataLoader(symbols=['AAPL'])
    data = loader.fetch_data(period='1d', interval='5m')
    stats = loader.get_combined_market_stats(data)
    
    sim = QuantSimulator(data, stats)
    report = sim.run_batch_simulation(['AAPL'])
    print(report[['Strategy', 'IS_Bps', 'Impact_Bps']])