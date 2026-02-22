import numpy as np
import pandas as pd

class ExecutionEngine:
    def __init__(self, symbol, side, total_quantity, start_time, end_time):
        self.symbol = symbol
        self.side = side
        self.total_quantity = total_quantity
        self.start_time = start_time
        self.end_time = end_time

    def get_twap_schedule(self, num_intervals):
        """Standard linear distribution of shares."""
        shares_per_interval = self.total_quantity // num_intervals
        remainder = self.total_quantity % num_intervals
        
        schedule = [shares_per_interval] * num_intervals
        schedule[-1] += remainder
        return schedule

    def get_vwap_schedule(self, volume_profile):
        """Slices shares proportional to the market volume profile."""
        total_volume = sum(volume_profile)
        weights = [v / total_volume for v in volume_profile]
        
        schedule = [int(self.total_quantity * w) for w in weights]
        
        # Adjust for rounding errors
        diff = self.total_quantity - sum(schedule)
        schedule[-1] += diff
        return schedule

    def get_almgren_chriss_schedule(self, num_intervals, volatility, liquidity_param, risk_aversion=0.1):
        """
        Calculates the optimal trajectory minimizing: (Market Impact Cost + Volatility Risk).
        Uses the hyperbolic sine solution for the optimal trajectory.
        """
        # Simplified closed-form for Almgren-Chriss
        # kappa is the 'urgency' parameter
        kappa = np.sqrt(risk_aversion * (volatility**2) / liquidity_param)
        
        # Calculate shares remaining at each step n
        # X_n = X * sinh(kappa * (T - t)) / sinh(kappa * T)
        times = np.arange(num_intervals + 1)
        T = num_intervals
        
        if kappa == 0:
            return self.get_twap_schedule(num_intervals)

        # Remaining trajectory
        trajectory = [
            self.total_quantity * np.sinh(kappa * (T - t)) / np.sinh(kappa * T) 
            for t in times
        ]
        
        # Convert trajectory (remaining) to trades (slices)
        schedule = []
        for i in range(len(trajectory) - 1):
            trade = int(trajectory[i] - trajectory[i+1])
            schedule.append(trade)
            
        # Ensure total adds up
        diff = self.total_quantity - sum(schedule)
        schedule[-1] += diff
        return schedule

if __name__ == "__main__":
    # Self-test block
    engine = ExecutionEngine("AAPL", "buy", 100000, 0, 10)
    
    print("TWAP Schedule:", engine.get_twap_schedule(5))
    
    vol_prof = [1000, 2000, 5000, 2000, 1000]
    print("VWAP Schedule:", engine.get_vwap_schedule(vol_prof))
    
    # AC parameters: low risk aversion vs high risk aversion
    ac_slow = engine.get_almgren_chriss_schedule(5, 0.02, 0.0001, risk_aversion=0.01)
    ac_fast = engine.get_almgren_chriss_schedule(5, 0.02, 0.0001, risk_aversion=0.5)
    
    print("Almgren-Chriss (Patient):", ac_slow)
    print("Almgren-Chriss (Urgent):", ac_fast)