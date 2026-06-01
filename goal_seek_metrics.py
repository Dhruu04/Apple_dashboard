"""
Metrics Calculator for Apple Dashboard Goal Seek
Calculates key financial metrics from data for comparison and goal seeking.
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_metrics(df: pd.DataFrame, opex_rate: float = 15.0, include_inventory: bool = True) -> Dict[str, float]:
    """
    Calculate comprehensive financial metrics from dashboard data.
    
    Args:
        df: DataFrame with financial data
        opex_rate: Operating expenses as percentage of revenue
        include_inventory: Whether to include inventory-related metrics
        
    Returns:
        Dictionary of calculated metrics
    """
    
    metrics = {}
    
    # Revenue and Volume Metrics
    total_units = df['Sales Units'].sum() if 'Sales Units' in df.columns else 0
    total_revenue = df['Total Revenue (€)'].sum() if 'Total Revenue (€)' in df.columns else 0
    
    metrics['Total Units'] = total_units
    metrics['Total Revenue (€)'] = total_revenue
    metrics['Avg Revenue Per Unit (€)'] = total_revenue / total_units if total_units > 0 else 0
    
    # Cost Metrics
    if 'Total Cost (€)' in df.columns:
        total_cogs = df['Total Cost (€)'].sum()
    elif 'Unit Material Cost (€)' in df.columns and 'Unit Labor Cost (€)' in df.columns and 'Sales Units' in df.columns:
        total_unit_cost = (df['Unit Material Cost (€)'] + df['Unit Labor Cost (€)']).mean()
        total_cogs = total_unit_cost * total_units
    else:
        total_cogs = 0
    
    metrics['Total COGS (€)'] = total_cogs
    metrics['Avg Unit Cost (€)'] = total_cogs / total_units if total_units > 0 else 0
    
    # Material and Labor Breakdown
    if 'Unit Material Cost (€)' in df.columns:
        avg_material = df['Unit Material Cost (€)'].mean()
        total_material = avg_material * total_units
        metrics['Total Material Cost (€)'] = total_material
        metrics['Avg Material Cost Per Unit (€)'] = avg_material
    
    if 'Unit Labor Cost (€)' in df.columns:
        avg_labor = df['Unit Labor Cost (€)'].mean()
        total_labor = avg_labor * total_units
        metrics['Total Labor Cost (€)'] = total_labor
        metrics['Avg Labor Cost Per Unit (€)'] = avg_labor
    
    # Gross Profit Metrics
    if 'Gross Profit (€)' in df.columns:
        total_gross_profit = df['Gross Profit (€)'].sum()
    else:
        total_gross_profit = total_revenue - total_cogs
    
    metrics['Total Gross Profit (€)'] = total_gross_profit
    metrics['Gross Margin %'] = (total_gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # OPEX Metrics
    total_opex = total_revenue * (opex_rate / 100)
    metrics['Total OPEX (€)'] = total_opex
    metrics['OPEX % of Revenue'] = opex_rate
    
    # EBIT Metrics (Operating Profit)
    ebit = total_gross_profit - total_opex
    metrics['EBIT (€)'] = ebit
    metrics['EBIT Margin %'] = (ebit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Production and Inventory Metrics
    if include_inventory:
        if 'Production Units' in df.columns:
            total_production = df['Production Units'].sum()
            metrics['Total Production Units'] = total_production
        
        if 'Ending Inventory' in df.columns:
            total_ending_inv_units = df['Ending Inventory'].sum()
            metrics['Total Ending Inventory Units'] = total_ending_inv_units
        
        if 'Ending Inv Value (€)' in df.columns:
            total_ending_inv_value = df['Ending Inv Value (€)'].sum()
            metrics['Total Ending Inventory Value (€)'] = total_ending_inv_value
        elif 'Ending Inventory' in df.columns and 'Total Unit Cost (€)' in df.columns:
            avg_unit_cost = (df['Unit Material Cost (€)'] + df['Unit Labor Cost (€)']).mean()
            total_ending_inv_value = df['Ending Inventory'].sum() * avg_unit_cost
            metrics['Total Ending Inventory Value (€)'] = total_ending_inv_value
        
        if 'Production Spend (€)' in df.columns:
            total_prod_spend = df['Production Spend (€)'].sum()
            metrics['Total Production Spend (€)'] = total_prod_spend
    
    # Unit Economics
    if 'Unit Gross Margin %' in df.columns:
        avg_unit_margin = df['Unit Gross Margin %'].mean()
        metrics['Avg Unit Gross Margin %'] = avg_unit_margin
    
    # Pricing Metrics
    if 'Selling Price (€)' in df.columns:
        avg_selling_price = df['Selling Price (€)'].mean()
        metrics['Avg Selling Price (€)'] = avg_selling_price
    
    return metrics


def calculate_impact_metrics(
    baseline_metrics: Dict[str, float], 
    scenario_metrics: Dict[str, float]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate the impact (changes) between baseline and scenario metrics.
    
    Args:
        baseline_metrics: Baseline metrics dictionary
        scenario_metrics: Scenario metrics dictionary
        
    Returns:
        Dictionary with impact analysis (absolute change, percentage change)
    """
    
    impact = {}
    
    for key in scenario_metrics.keys():
        if key in baseline_metrics:
            baseline = baseline_metrics[key]
            scenario = scenario_metrics[key]
            
            if baseline != 0:
                pct_change = (scenario - baseline) / abs(baseline) * 100
            else:
                pct_change = 0 if scenario == 0 else 100
            
            impact[key] = {
                'baseline': baseline,
                'scenario': scenario,
                'absolute_change': scenario - baseline,
                'percent_change': pct_change
            }
    
    return impact


def format_metric_value(value: float, metric_name: str = "") -> str:
    """
    Format metric value for display with appropriate units.
    
    Args:
        value: The metric value to format
        metric_name: Name of the metric to determine formatting
        
    Returns:
        Formatted string representation
    """
    
    # Percentage metrics
    if '%' in metric_name or 'Margin' in metric_name or 'OPEX %' in metric_name:
        return f"{value:,.2f}%"
    
    # Currency metrics
    if '€' in metric_name or 'Revenue' in metric_name or 'Cost' in metric_name or 'Profit' in metric_name or 'Spend' in metric_name or 'EBIT' in metric_name:
        if abs(value) >= 1_000_000:
            return f"€{value/1_000_000:,.2f}M"
        elif abs(value) >= 1_000:
            return f"€{value/1_000:,.2f}K"
        else:
            return f"€{value:,.2f}"
    
    # Unit metrics
    if 'Units' in metric_name or 'Production' in metric_name:
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:,.2f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:,.2f}K"
        else:
            return f"{value:,.0f}"
    
    # Default formatting
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.2f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:,.2f}K"
    else:
        return f"{value:,.2f}"


def create_comparison_summary(
    baseline_metrics: Dict[str, float],
    scenario_metrics: Dict[str, float],
    goal_seek_result: Dict = None
) -> pd.DataFrame:
    """
    Create a summary table comparing baseline and scenario metrics.
    
    Args:
        baseline_metrics: Baseline metrics
        scenario_metrics: Scenario metrics
        goal_seek_result: Optional goal seek result details
        
    Returns:
        DataFrame with comparison summary
    """
    
    # Key metrics to display in summary
    key_metrics = [
        'Total Revenue (€)',
        'Total COGS (€)',
        'Total Gross Profit (€)',
        'Gross Margin %',
        'Total OPEX (€)',
        'EBIT (€)',
        'EBIT Margin %',
        'Avg Selling Price (€)',
        'Avg Unit Cost (€)',
        'Total Units',
        'Total Production Units',
        'Total Ending Inventory Value (€)'
    ]
    
    summary_rows = []
    
    for metric in key_metrics:
        if metric in baseline_metrics and metric in scenario_metrics:
            baseline_val = baseline_metrics[metric]
            scenario_val = scenario_metrics[metric]
            
            if baseline_val != 0:
                pct_change = (scenario_val - baseline_val) / abs(baseline_val) * 100
            else:
                pct_change = 0
            
            summary_rows.append({
                'Metric': metric,
                'Baseline': baseline_val,
                'Scenario': scenario_val,
                'Change': scenario_val - baseline_val,
                'Change %': pct_change
            })
    
    return pd.DataFrame(summary_rows)
