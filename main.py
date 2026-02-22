import sys
import pandas as pd
from datetime import datetime, timedelta
from data_loader import DataLoader
from simulator import QuantSimulator
from report import ExecutionReport

def run_trading_system():
    """
    Master controller upgraded for 30-day longitudinal research.
    """
    print("\nInitializing Institutional Multi-Day Execution Study...")
    
    symbols = ['AAPL', 'MSFT', 'NVDA', 'SPY']
    lookback_days = 30
    
    # 1. Ingest Multi-Day Data
    loader = DataLoader(symbols=symbols)
    # Fetching 30 days of 5-minute data
    market_data = loader.fetch_data(period=f'{lookback_days}d', interval='5m')
    
    if not market_data:
        print("Error: No data retrieved.")
        return

    stats = loader.get_combined_market_stats(market_data)
    all_daily_results = []

    # 2. Multi-Day Simulation Loop
    # We group the data by date to simulate independent trading sessions
    print(f"\nStarting 30-day simulation loop for {symbols}...")
    
    for symbol in symbols:
        if symbol not in market_data:
            continue
            
        df_full = market_data[symbol]
        # Get unique trading dates
        trading_days = df_full.index.normalize().unique()
        
        for day in trading_days:
            # Isolate data for this specific day
            day_str = day.strftime('%Y-%m-%d')
            df_day = df_full[df_full.index.normalize() == day]
            
            if len(df_day) < 10: # Skip half-days or data gaps
                continue

            # Target 2% of the average daily volume
            total_quantity = int(stats[symbol]['avg_volume'] * 0.02)
            
            # Temporary daily market data map for the simulator
            daily_context = {symbol: df_day}
            simulator = QuantSimulator(daily_context, stats)
            
            day_results = simulator.run_full_comparison(symbol, total_quantity)
            
            # Tag results with the date for longitudinal analysis
            for res in day_results:
                res['Date'] = day_str
                all_daily_results.append(res)

    # 3. Consolidate and Aggregate
    if all_daily_results:
        raw_df = pd.DataFrame(all_daily_results)
        
        # Calculate the mean performance across all 30 days per strategy per stock
        agg_results = raw_df.groupby(['Symbol', 'Strategy']).agg({
            'IS_Bps': 'mean',
            'Spread_Bps': 'mean',
            'Slippage_Bps': 'mean',
            'Impact_Bps': 'mean',
            'Avg_Fill': 'mean'
        }).reset_index()
        
        # 4. Final Reporting
        reporter = ExecutionReport(agg_results)
        reporter.generate_summary()
        
        # Save both the aggregate and the raw daily logs
        agg_results.to_csv("final_execution_analysis.csv", index=False)
        raw_df.to_csv("daily_execution_logs.csv", index=False)
    
    print("\nMulti-day study complete. Results saved.")

if __name__ == "__main__":
    try:
        run_trading_system()
    except Exception as e:
        print(f"\nSystem Error: {e}")
        import traceback
        traceback.print_exc()