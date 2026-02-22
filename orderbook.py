
import pandas as pd
import numpy as np

class OrderBookSimulator:
    def __init__(self, tick_size=0.01):
        self.tick_size = tick_size
        self.base_spread_bps = 0.0005 
        self.depth_factor = 0.1       

    def get_snapshot(self, row, avg_volume):
        """
        Creates a virtual order book snapshot.
        Includes a safety check for zero volume rows.
        """
        mid_price = row['Close']
        # Use a minimum price movement to avoid zero spreads
        volatility_spread = max(self.tick_size, (row['High'] - row['Low']) * 0.1)
        
        dynamic_spread = max(self.tick_size, mid_price * self.base_spread_bps + volatility_spread)
        
        ask_price = np.round(mid_price + (dynamic_spread / 2), 2)
        bid_price = np.round(mid_price - (dynamic_spread / 2), 2)
        
        # Volume safety check
        effective_volume = max(row['Volume'], avg_volume * 0.01)
        available_depth = effective_volume * self.depth_factor
        
        return {
            'bid': bid_price,
            'ask': ask_price,
            'mid': mid_price,
            'spread': ask_price - bid_price,
            'bid_depth': available_depth * 0.5,
            'ask_depth': available_depth * 0.5
        }

    def calculate_fill(self, side, size, snapshot):
        """
        Calculates fill price with a fix for the DivideByZero/Inf issue.
        """
        if side.lower() == 'buy':
            base_price = snapshot['ask']
            depth = snapshot['ask_depth']
        else:
            base_price = snapshot['bid']
            depth = snapshot['bid_depth']

        # Safety 1: No shares to trade
        if size <= 0:
            return base_price
        
        # Safety 2: Zero depth handling
        if depth <= 0:
            # Penalize the trade by 50 ticks if no liquidity is found
            penalty = self.tick_size * 50
            return base_price + penalty if side.lower() == 'buy' else base_price - penalty

        if size <= depth:
            fill_price = base_price
        else:
            # Safety 3: Robust log-based slippage calculation
            # Adding 1 to the ratio ensures log is always defined and >= 0
            excess_ratio = size / depth
            slippage_ticks = np.log2(excess_ratio + 1) * self.tick_size
            
            if side.lower() == 'buy':
                fill_price = base_price + slippage_ticks
            else:
                fill_price = base_price - slippage_ticks
                
        return np.round(fill_price, 4)

if __name__ == "__main__":
    obs = OrderBookSimulator()
    # Test case for zero volume/depth
    bad_row = {'Close': 100.0, 'High': 100.0, 'Low': 100.0, 'Volume': 0}
    snap = obs.get_snapshot(bad_row, 100000)
    
    print(f"Zero-Volume Snapshot: {snap}")
    fill = obs.calculate_fill('buy', 5000, snap)
    print(f"Fill price for 5000 shares (should not be inf): {fill}")