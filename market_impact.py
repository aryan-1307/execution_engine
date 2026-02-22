import numpy as np

class MarketImpactModel:
    def __init__(self, sigma_daily=0.02, gamma=0.3, eta=0.1):
        """
        sigma_daily: Annualized or daily volatility of the asset.
        gamma: Coefficient for permanent impact (typical range 0.1 - 0.5).
        eta: Coefficient for temporary impact (typical range 0.05 - 0.2).
        """
        self.sigma = sigma_daily
        self.gamma = gamma
        self.eta = eta

    def permanent_impact(self, trade_size, daily_volume):
        """
        Calculates the permanent price shift. 
        Formula: delta_P = gamma * sigma * (size / volume)^0.5
        """
        if daily_volume == 0: return 0
        impact_pct = self.gamma * self.sigma * np.sqrt(trade_size / daily_volume)
        return impact_pct

    def temporary_impact(self, trade_size, interval_volume):
        """
        Calculates the temporary price spike (Execution Cost).
        Formula: delta_P = eta * sigma * (size / interval_volume)^0.5
        """
        if interval_volume == 0: return 0
        # Temporary impact usually scales with the volume of the specific interval
        impact_pct = self.eta * self.sigma * np.sqrt(trade_size / interval_volume)
        return impact_pct

    def apply_impact(self, current_price, trade_size, daily_volume, interval_volume, side='buy'):
        """
        Adjusts the price based on trade characteristics.
        Returns (impacted_price, permanent_shift).
        """
        direction = 1 if side.lower() == 'buy' else -1
        
        perm = self.permanent_impact(trade_size, daily_volume)
        temp = self.temporary_impact(trade_size, interval_volume)
        
        # Total impact on the execution price
        total_impact_pct = (perm + temp) * direction
        impacted_price = current_price * (1 + total_impact_pct)
        
        # The amount the price "sticks" for the next interval
        permanent_shift = current_price * perm * direction
        
        return np.round(impacted_price, 4), np.round(permanent_shift, 4)

if __name__ == "__main__":
    # Self-test block
    impact_engine = MarketImpactModel(sigma_daily=0.015) # 1.5% daily vol
    
    price = 100.0
    order_size = 50000
    avg_daily_vol = 1000000
    bin_vol = 50000 # volume in a 5-min window
    
    exec_price, perm_shift = impact_engine.apply_impact(
        price, order_size, avg_daily_vol, bin_vol, side='buy'
    )
    
    print(f"Original Price: {price}")
    print(f"Executed Price (with impact): {exec_price}")
    print(f"Permanent Price Shift: {perm_shift}")
    print(f"Total Impact Cost (bps): {np.round((exec_price/price - 1) * 10000, 2)}")