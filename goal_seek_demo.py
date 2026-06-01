"""
Goal Seek Feature - Demo Script
Shows practical examples of how to use the Goal Seek engine
"""

import pandas as pd
import numpy as np
from goal_seek_engine import GoalSeekEngine, GoalSeekConfig, MetricType, AdjustmentVariable
from goal_seek_metrics import calculate_metrics, calculate_impact_metrics, format_metric_value


def create_sample_data():
    """Create sample Apple dashboard data for demonstration."""
    
    products = ['iPhone', 'iPad Pro', 'MacBook Pro', 'Apple Watch', 'AirPods Pro']
    months = ['Oct 2026', 'Nov 2026', 'Dec 2026', 'Jan 2027', 'Feb 2027', 'Mar 2027']
    countries = ['Italy', 'Sweden']
    
    # Create sample data
    rows = []
    for country in countries:
        for product in products:
            for month in months:
                rows.append({
                    'Country': country,
                    'Product': product,
                    'Month': month,
                    'Sales Units': np.random.randint(5000, 50000),
                    'Production Units': np.random.randint(5000, 50000),
                    'Beginning Inventory': np.random.randint(1000, 10000),
                    'Ending Inventory': np.random.randint(1000, 10000),
                    'Selling Price (€)': np.random.uniform(200, 2000),
                    'Unit Material Cost (€)': np.random.uniform(50, 800),
                    'Unit Labor Cost (€)': np.random.uniform(10, 100),
                    'Total Unit Cost (€)': np.random.uniform(60, 900),
                    'Unit Gross Margin %': np.random.uniform(20, 60),
                    'Total Revenue (€)': 0,  # Will be calculated
                    'Total Material Cost (€)': 0,
                    'Total Labor Cost (€)': 0,
                    'Total Cost (€)': 0,
                    'Production Spend (€)': 0,
                    'Gross Profit (€)': 0,
                    'Ending Inv Value (€)': 0
                })
    
    df = pd.DataFrame(rows)
    
    # Calculate derived columns
    df['Total Revenue (€)'] = df['Sales Units'] * df['Selling Price (€)']
    df['Total Material Cost (€)'] = df['Production Units'] * df['Unit Material Cost (€)']
    df['Total Labor Cost (€)'] = df['Production Units'] * df['Unit Labor Cost (€)']
    df['Total Cost (€)'] = df['Sales Units'] * df['Total Unit Cost (€)']
    df['Production Spend (€)'] = df['Production Units'] * df['Total Unit Cost (€)']
    df['Gross Profit (€)'] = df['Total Revenue (€)'] - df['Total Cost (€)']
    df['Ending Inv Value (€)'] = df['Ending Inventory'] * df['Total Unit Cost (€)']
    
    return df


def demo_revenue_goal_seek():
    """Demo 1: Find what selling price is needed to reach €1B revenue."""
    
    print("\n" + "="*70)
    print("DEMO 1: Increase Revenue to €1 Billion")
    print("="*70)
    
    df = create_sample_data()
    
    print("\n📊 Current State:")
    baseline_metrics = calculate_metrics(df, opex_rate=15.0)
    print(f"  Current Revenue: {format_metric_value(baseline_metrics['Total Revenue (€)'], 'Total Revenue (€)')}")
    print(f"  Current Gross Profit: {format_metric_value(baseline_metrics['Total Gross Profit (€)'], 'Total Gross Profit (€)')}")
    print(f"  Current Gross Margin: {baseline_metrics['Gross Margin %']:.2f}%")
    
    print("\n🎯 Goal Seek Configuration:")
    print("  Target Metric: Total Revenue")
    print("  Target Value: €1,000,000,000")
    print("  Adjust Variable: Selling Price")
    
    # Create config
    current_avg_price = df['Selling Price (€)'].mean()
    config = GoalSeekConfig(
        target_metric=MetricType.REVENUE,
        target_value=1_000_000_000,
        adjustment_variable=AdjustmentVariable.SELLING_PRICE,
        current_value=current_avg_price,
        min_value=current_avg_price * 0.5,
        max_value=current_avg_price * 5.0,
        tolerance=0.01,
        max_iterations=500
    )
    
    # Run goal seek
    engine = GoalSeekEngine(df, calculate_metrics)
    result = engine.seek(config, opex_rate=15.0)
    
    print("\n✅ Goal Seek Result:")
    print(f"  Success: {result.success}")
    print(f"  Required Price Change: {format_metric_value(result.new_value, 'Avg Selling Price (€)')}")
    print(f"  Change from Current: {((result.new_value - result.original_value) / result.original_value * 100):+.2f}%")
    print(f"  Original Revenue: {format_metric_value(result.original_metric_value, 'Total Revenue (€)')}")
    print(f"  Final Revenue: {format_metric_value(result.final_metric_value, 'Total Revenue (€)')}")
    print(f"  Error: {result.error_pct:.4f}%")
    print(f"  Iterations: {result.iterations}")
    
    # Show impact
    adjusted_df = engine.get_adjusted_data()
    scenario_metrics = calculate_metrics(adjusted_df, opex_rate=15.0)
    
    print("\n📈 Impact Analysis:")
    revenue_change = scenario_metrics['Total Revenue (€)'] - baseline_metrics['Total Revenue (€)']
    profit_change = scenario_metrics['Total Gross Profit (€)'] - baseline_metrics['Total Gross Profit (€)']
    
    print(f"  Revenue Change: {format_metric_value(revenue_change, 'Change')}")
    print(f"  Gross Profit Change: {format_metric_value(profit_change, 'Change')}")
    print(f"  New Gross Margin: {scenario_metrics['Gross Margin %']:.2f}%")
    print(f"  Margin Change: {scenario_metrics['Gross Margin %'] - baseline_metrics['Gross Margin %']:+.2f}%")


def demo_margin_goal_seek():
    """Demo 2: Find what material cost reduction is needed for 40% gross margin."""
    
    print("\n" + "="*70)
    print("DEMO 2: Achieve 40% Gross Margin")
    print("="*70)
    
    df = create_sample_data()
    
    print("\n📊 Current State:")
    baseline_metrics = calculate_metrics(df, opex_rate=15.0)
    print(f"  Current Gross Margin: {baseline_metrics['Gross Margin %']:.2f}%")
    print(f"  Current Revenue: {format_metric_value(baseline_metrics['Total Revenue (€)'], 'Total Revenue (€)')}")
    
    print("\n🎯 Goal Seek Configuration:")
    print("  Target Metric: Gross Margin %")
    print("  Target Value: 40%")
    print("  Adjust Variable: Material Costs")
    
    # Create config
    current_material = df['Unit Material Cost (€)'].mean()
    config = GoalSeekConfig(
        target_metric=MetricType.GROSS_MARGIN_PCT,
        target_value=40.0,
        adjustment_variable=AdjustmentVariable.MATERIAL_COST_RATIO,
        current_value=current_material,
        min_value=current_material * 0.3,
        max_value=current_material * 2.0,
        tolerance=0.1,
        max_iterations=500
    )
    
    # Run goal seek
    engine = GoalSeekEngine(df, calculate_metrics)
    result = engine.seek(config, opex_rate=15.0)
    
    print("\n✅ Goal Seek Result:")
    print(f"  Success: {result.success}")
    print(f"  Required Material Cost: {format_metric_value(result.new_value, 'Unit Material Cost (€)')}")
    print(f"  Cost Reduction Needed: {((result.original_value - result.new_value) / result.original_value * 100):+.2f}%")
    print(f"  Original Margin: {result.original_metric_value:.2f}%")
    print(f"  Final Margin: {result.final_metric_value:.2f}%")
    print(f"  Error: {result.error_pct:.4f}%")
    
    # Show impact
    adjusted_df = engine.get_adjusted_data()
    scenario_metrics = calculate_metrics(adjusted_df, opex_rate=15.0)
    
    print("\n📈 Impact Analysis:")
    print(f"  New Gross Profit: {format_metric_value(scenario_metrics['Total Gross Profit (€)'], 'Total Gross Profit (€)')}")
    print(f"  Profit Change: {format_metric_value(scenario_metrics['Total Gross Profit (€)'] - baseline_metrics['Total Gross Profit (€)'], 'Change')}")


def demo_ebit_goal_seek():
    """Demo 3: Find what volume is needed to achieve €250M EBIT."""
    
    print("\n" + "="*70)
    print("DEMO 3: Achieve €250M EBIT (Operating Profit)")
    print("="*70)
    
    df = create_sample_data()
    
    print("\n📊 Current State:")
    baseline_metrics = calculate_metrics(df, opex_rate=15.0)
    ebit = baseline_metrics['Total Gross Profit (€)'] - (baseline_metrics['Total Revenue (€)'] * 0.15)
    print(f"  Current EBIT: {format_metric_value(ebit, 'EBIT (€)')}")
    print(f"  Current Units: {format_metric_value(baseline_metrics['Total Units'], 'Total Units')}")
    
    print("\n🎯 Goal Seek Configuration:")
    print("  Target Metric: EBIT (Operating Profit)")
    print("  Target Value: €250,000,000")
    print("  Adjust Variable: Sales Volume")
    
    # Create config
    current_volume = df['Sales Units'].mean()
    config = GoalSeekConfig(
        target_metric=MetricType.EBIT,
        target_value=250_000_000,
        adjustment_variable=AdjustmentVariable.SALES_VOLUME,
        current_value=current_volume,
        min_value=current_volume * 0.5,
        max_value=current_volume * 3.0,
        tolerance=0.01,
        max_iterations=500
    )
    
    # Run goal seek
    engine = GoalSeekEngine(df, calculate_metrics)
    result = engine.seek(config, opex_rate=15.0)
    
    print("\n✅ Goal Seek Result:")
    print(f"  Success: {result.success}")
    print(f"  Required Unit Sales: {format_metric_value(result.new_value, 'Total Units')}")
    print(f"  Volume Increase Needed: {((result.new_value - result.original_value) / result.original_value * 100):+.2f}%")
    print(f"  Original EBIT: {format_metric_value(result.original_metric_value, 'EBIT (€)')}")
    print(f"  Final EBIT: {format_metric_value(result.final_metric_value, 'EBIT (€)')}")
    print(f"  Error: {result.error_pct:.4f}%")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("GOAL SEEK ENGINE - DEMONSTRATION")
    print("="*70)
    print("This script demonstrates the Goal Seek feature with realistic scenarios")
    
    demo_revenue_goal_seek()
    demo_margin_goal_seek()
    demo_ebit_goal_seek()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\n💡 Key Takeaways:")
    print("  1. Goal Seek finds optimal values for single variables")
    print("  2. Supports multiple target metrics and adjustment variables")
    print("  3. Shows exact changes needed to reach goals")
    print("  4. Provides before/after impact analysis")
    print("\n📖 For more examples, see GOAL_SEEK_GUIDE.md")


if __name__ == "__main__":
    main()
