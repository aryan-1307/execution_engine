import pandas as pd
import os

class ExecutionReport:
    def __init__(self, results_df):
        self.results = results_df

    def generate_summary(self):
        """
        Generates a professional institutional-grade research summary.
        """
        print("\n" + "="*80)
        print("INSTITUTIONAL EXECUTION RESEARCH REPORT: 30-DAY CONSOLIDATED STUDY")
        print("="*80)
        
        # Formatting the aggregate table for the terminal
        summary = self.results.sort_values(by=['Symbol', 'IS_Bps'])
        
        headers = ["Symbol", "Strategy", "IS (bps)", "Impact", "Slippage", "Spread"]
        print(f"{headers[0]:<10} {headers[1]:<15} {headers[2]:>10} {headers[3]:>10} {headers[4]:>10} {headers[5]:>10}")
        print("-" * 80)

        for _, row in summary.iterrows():
            print(f"{row['Symbol']:<10} {row['Strategy']:<15} {row['IS_Bps']:>10.2f} "
                  f"{row['Impact_Bps']:>10.2f} {row['Slippage_Bps']:>10.2f} {row['Spread_Bps']:>10.2f}")

        print("\n" + "="*80)
        print("QUANTITATIVE INSIGHTS & STRATEGY SELECTION")
        print("-" * 80)

        for symbol in self.results['Symbol'].unique():
            symbol_data = self.results[self.results['Symbol'] == symbol]
            
            # 1. Best Strategy (Lowest Mean IS)
            best_strat = symbol_data.loc[symbol_data['IS_Bps'].idxmin()]
            
            # 2. Risk Sensitivity Analysis
            ac_results = symbol_data[symbol_data['Strategy'].str.contains('AC_')]
            best_ac = ac_results.loc[ac_results['IS_Bps'].idxmin()]
            
            print(f"ASSET: {symbol}")
            print(f"  > Optimal Strategy: {best_strat['Strategy']} ({best_strat['IS_Bps']:.2f} bps)")
            print(f"  > Best Risk Profile: {best_ac['Strategy']} is optimal for {symbol} liquidity.")
            print(f"  > Cost Attribution: Impact accounts for { (best_strat['Impact_Bps']/best_strat['IS_Bps'])*100 if best_strat['IS_Bps'] > 0 else 0 :.1f}% of total cost.")
            print("-" * 40)

        print(f"\nFinal study exported to: {os.getcwd()}/final_execution_analysis.csv")
        print("="*80 + "\n")

if __name__ == "__main__":
    # Self-test block with dummy research data
    test_df = pd.DataFrame([
        {'Symbol': 'AAPL', 'Strategy': 'TWAP', 'IS_Bps': 15.2, 'Impact_Bps': 8.1, 'Slippage_Bps': 2.1, 'Spread_Bps': 5.0},
        {'Symbol': 'AAPL', 'Strategy': 'AC_Urgent', 'IS_Bps': 12.1, 'Impact_Bps': 5.0, 'Slippage_Bps': 2.1, 'Spread_Bps': 5.0},
        {'Symbol': 'MSFT', 'Strategy': 'VWAP', 'IS_Bps': 10.5, 'Impact_Bps': 4.0, 'Slippage_Bps': 1.5, 'Spread_Bps': 5.0}
    ])
    reporter = ExecutionReport(test_df)
    reporter.generate_summary()