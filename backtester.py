import pandas as pd
import numpy as np
from orderbook import OrderBookSimulator
from market_impact import MarketImpactModel

class Backtester:
    def __init__(self, market_data, symbol, stats):
        self.data = market_data[symbol]
        self.symbol = symbol
        self.stats = stats[symbol]
        self.obs = OrderBookSimulator()
        self.mim = MarketImpactModel(sigma_daily=self.stats['volatility'])

    def run_simulation(self, strategy_name, schedule):
        """
        Runs execution schedule with granular cost decomposition.
        """
        execution_log = []
        arrival_price = self.data.iloc[0]['Close']
        
        current_permanent_impact = 0.0
        total_shares = sum(schedule)
        
        # Cumulative cost buckets in dollars
        total_spread_cost = 0.0
        total_slippage_cost = 0.0
        total_impact_cost = 0.0
        total_notional = 0.0

        for i, shares in enumerate(schedule):
            if i >= len(self.data) or shares <= 0:
                continue
            
            row = self.data.iloc[i]
            adjusted_mid = row['Close'] + current_permanent_impact
            
            snapshot = self.obs.get_snapshot(row, self.stats['avg_volume'])
            snapshot['mid'] = adjusted_mid
            snapshot['ask'] = np.round(adjusted_mid + (snapshot['spread'] / 2), 4)
            snapshot['bid'] = np.round(adjusted_mid - (snapshot['spread'] / 2), 4)
            
            # 1. Spread Cost: Cost to cross the bid-ask spread
            spread_cost_per_share = snapshot['spread'] / 2
            total_spread_cost += (shares * spread_cost_per_share)
            
            # 2. Slippage Cost: Cost of walking the book depth
            fill_at_book = self.obs.calculate_fill('buy', shares, snapshot)
            slippage_per_share = abs(fill_at_book - snapshot['ask'])
            total_slippage_cost += (shares * slippage_per_share)
            
            # 3. Market Impact: Temporary spike + Permanent shift
            impacted_price, perm_shift = self.mim.apply_impact(
                fill_at_book, 
                shares, 
                self.stats['avg_volume'] * len(self.data),
                row['Volume'], 
                side='buy'
            )
            
            impact_cost_per_share = abs(impacted_price - fill_at_book)
            total_impact_cost += (shares * impact_cost_per_share)
            
            current_permanent_impact += perm_shift
            total_notional += (shares * impacted_price)

            execution_log.append({
                'interval': i,
                'shares': shares,
                'fill_price': impacted_price,
                'perm_impact': current_permanent_impact
            })

        avg_price = total_notional / total_shares if total_shares > 0 else arrival_price
        shortfall_bps = ((avg_price / arrival_price) - 1) * 10000
        
        # Convert dollar costs to Basis Points (bps) relative to arrival notional
        arrival_notional = total_shares * arrival_price
        
        return {
            'strategy': strategy_name,
            'avg_fill_price': avg_price,
            'arrival_price': arrival_price,
            'implementation_shortfall_bps': shortfall_bps,
            'spread_cost_bps': (total_spread_cost / arrival_notional) * 10000,
            'slippage_cost_bps': (total_slippage_cost / arrival_notional) * 10000,
            'impact_cost_bps': (total_impact_cost / arrival_notional) * 10000,
            'log': pd.DataFrame(execution_log)
        }

if __name__ == "__main__":
    from data_loader import DataLoader
    loader = DataLoader(symbols=['AAPL'])
    data = loader.fetch_data(period='1d', interval='5m')
    stats = loader.get_combined_market_stats(data)
    
    bt = Backtester(data, 'AAPL', stats)
    test_res = bt.run_simulation("Test", [500] * 5)
    print(f"IS (bps): {test_res['implementation_shortfall_bps']:.2f}")
    print(f"Spread: {test_res['spread_cost_bps']:.2f} | Slippage: {test_res['slippage_cost_bps']:.2f} | Impact: {test_res['impact_cost_bps']:.2f}")