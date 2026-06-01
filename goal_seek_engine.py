"""
Goal Seek Engine for Apple Dashboard
Enables dynamic 'what-if' analysis to find variable adjustments needed to hit target metrics.
"""

import pandas as pd
import numpy as np
from scipy.optimize import minimize_scalar, minimize
from typing import Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    """Available metrics to target with goal seek."""
    REVENUE = "Total Revenue"
    GROSS_PROFIT = "Gross Profit"
    GROSS_MARGIN_PCT = "Gross Margin %"
    EBIT = "EBIT"
    EBIT_MARGIN_PCT = "EBIT Margin %"
    COGS = "COGS"
    UNIT_COST = "Unit Cost"
    PRODUCTION_SPEND = "Production Spend"
    OPEX = "OPEX"


class AdjustmentVariable(Enum):
    """Available variables that can be adjusted to reach target."""
    SELLING_PRICE = "selling_price"
    SALES_VOLUME = "sales_volume"
    UNIT_MATERIAL_COST = "unit_material_cost"
    UNIT_LABOR_COST = "unit_labor_cost"
    LABOR_RATE = "labor_rate"
    OPEX_RATE = "opex_rate"
    MATERIAL_COST_RATIO = "material_cost_ratio"


@dataclass
class GoalSeekConfig:
    """Configuration for a goal seek operation."""
    target_metric: MetricType
    target_value: float
    adjustment_variable: AdjustmentVariable
    current_value: float
    min_value: float = 0.01
    max_value: float = 10000.0
    tolerance: float = 0.01  # Within 1% of target
    max_iterations: int = 1000


@dataclass
class GoalSeekResult:
    """Result of a goal seek operation."""
    success: bool
    target_metric: str
    target_value: float
    adjustment_variable: str
    original_value: float
    new_value: float
    original_metric_value: float
    final_metric_value: float
    iterations: int
    error_pct: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display."""
        return {
            'Success': self.success,
            'Target Metric': self.target_metric,
            'Target Value': self.target_value,
            'Adjustment Variable': self.adjustment_variable,
            'Original Value': self.original_value,
            'Required Change': self.new_value,
            'Change %': ((self.new_value - self.original_value) / self.original_value * 100) if self.original_value != 0 else 0,
            'Original Metric': self.original_metric_value,
            'Final Metric': self.final_metric_value,
            'Error %': self.error_pct,
            'Iterations': self.iterations
        }


class GoalSeekEngine:
    """
    Core engine for performing goal seek calculations.
    
    Usage:
        engine = GoalSeekEngine(data_df, metrics_calculator)
        result = engine.seek(config)
    """
    
    def __init__(self, data_df: pd.DataFrame, metrics_calculator: Callable):
        """
        Initialize the goal seek engine.
        
        Args:
            data_df: DataFrame with sales, costs, and pricing data
            metrics_calculator: Function that calculates metrics from data
        """
        self.data_df = data_df.copy()
        self.original_df = data_df.copy()
        self.metrics_calculator = metrics_calculator
        self.iteration_count = 0
        
    def get_metric_value(self, metric: MetricType, data: pd.DataFrame = None) -> float:
        """Get the current value of a specific metric."""
        if data is None:
            data = self.data_df
        
        metrics = self.metrics_calculator(data)
        
        if metric == MetricType.REVENUE:
            return metrics.get('Total Revenue (€)', 0)
        elif metric == MetricType.GROSS_PROFIT:
            return metrics.get('Total Gross Profit (€)', 0)
        elif metric == MetricType.GROSS_MARGIN_PCT:
            return metrics.get('Gross Margin %', 0)
        elif metric == MetricType.EBIT:
            return metrics.get('EBIT (€)', 0)
        elif metric == MetricType.EBIT_MARGIN_PCT:
            return metrics.get('EBIT Margin %', 0)
        elif metric == MetricType.COGS:
            return metrics.get('Total COGS (€)', 0)
        elif metric == MetricType.UNIT_COST:
            return metrics.get('Avg Unit Cost (€)', 0)
        elif metric == MetricType.PRODUCTION_SPEND:
            return metrics.get('Total Production Spend (€)', 0)
        elif metric == MetricType.OPEX:
            return metrics.get('Total OPEX (€)', 0)
        
        return 0.0
    
    def apply_adjustment(self, variable: AdjustmentVariable, value: float, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Apply an adjustment to the data and return modified DataFrame.
        
        Args:
            variable: The variable to adjust
            value: The new value for the variable
            data: DataFrame to adjust (uses self.data_df if None)
            
        Returns:
            Modified DataFrame with the adjustment applied
        """
        if data is None:
            data = self.data_df.copy()
        else:
            data = data.copy()
        
        if variable == AdjustmentVariable.SELLING_PRICE:
            # Scale all selling prices by the factor
            cols_to_adjust = ['Selling Price (€)']
            for col in cols_to_adjust:
                if col in data.columns:
                    # Calculate the scaling factor
                    original_avg = data[col].mean()
                    if original_avg != 0:
                        scale_factor = value / original_avg
                        data[col] = data[col] * scale_factor
                    
        elif variable == AdjustmentVariable.SALES_VOLUME:
            # Scale sales volume
            if 'Sales Units' in data.columns:
                original_avg = data['Sales Units'].mean()
                if original_avg != 0:
                    scale_factor = value / original_avg
                    data['Sales Units'] = data['Sales Units'] * scale_factor
                    data['Production Units'] = data['Production Units'] * scale_factor
                    data['Beginning Inventory'] = data['Beginning Inventory'] * scale_factor
                    data['Ending Inventory'] = data['Ending Inventory'] * scale_factor
                    
        elif variable == AdjustmentVariable.UNIT_MATERIAL_COST:
            if 'Unit Material Cost (€)' in data.columns:
                original_avg = data['Unit Material Cost (€)'].mean()
                if original_avg != 0:
                    scale_factor = value / original_avg
                    data['Unit Material Cost (€)'] = data['Unit Material Cost (€)'] * scale_factor
                    
        elif variable == AdjustmentVariable.UNIT_LABOR_COST:
            if 'Unit Labor Cost (€)' in data.columns:
                original_avg = data['Unit Labor Cost (€)'].mean()
                if original_avg != 0:
                    scale_factor = value / original_avg
                    data['Unit Labor Cost (€)'] = data['Unit Labor Cost (€)'] * scale_factor
                    
        elif variable == AdjustmentVariable.LABOR_RATE:
            # This would be handled externally, but we can support it
            if 'Unit Labor Cost (€)' in data.columns:
                # Assume labor cost is roughly proportional to labor rate
                original_labor = data['Unit Labor Cost (€)'].mean()
                if original_labor != 0:
                    scale_factor = value / original_labor
                    data['Unit Labor Cost (€)'] = data['Unit Labor Cost (€)'] * scale_factor
                    
        elif variable == AdjustmentVariable.OPEX_RATE:
            # OPEX rate is handled separately, just return data
            pass
            
        elif variable == AdjustmentVariable.MATERIAL_COST_RATIO:
            if 'Unit Material Cost (€)' in data.columns:
                original_avg = data['Unit Material Cost (€)'].mean()
                if original_avg != 0:
                    scale_factor = value / original_avg
                    data['Unit Material Cost (€)'] = data['Unit Material Cost (€)'] * scale_factor
        
        # Recalculate derived columns
        if 'Unit Material Cost (€)' in data.columns and 'Unit Labor Cost (€)' in data.columns:
            data['Total Unit Cost (€)'] = data['Unit Material Cost (€)'] + data['Unit Labor Cost (€)']
            
            if 'Selling Price (€)' in data.columns:
                data['Unit Gross Margin %'] = (
                    (data['Selling Price (€)'] - data['Total Unit Cost (€)']) / 
                    data['Selling Price (€)'] * 100
                ).replace([np.inf, -np.inf], 0).fillna(0)
        
        # Recalculate financial columns
        if 'Sales Units' in data.columns and 'Selling Price (€)' in data.columns:
            data['Total Revenue (€)'] = data['Sales Units'] * data['Selling Price (€)']
            
        if 'Sales Units' in data.columns and 'Total Unit Cost (€)' in data.columns:
            data['Total Cost (€)'] = data['Sales Units'] * data['Total Unit Cost (€)']
            data['Gross Profit (€)'] = data['Total Revenue (€)'] - data['Total Cost (€)']
            
        if 'Production Units' in data.columns and 'Total Unit Cost (€)' in data.columns:
            data['Production Spend (€)'] = data['Production Units'] * data['Total Unit Cost (€)']
            
        return data
    
    def objective_function(self, adjustment_value: float, config: GoalSeekConfig, opex_rate: float = 15.0) -> float:
        """
        Calculate the error between target and current metric value.
        Used by the optimizer to find the best adjustment value.
        
        Args:
            adjustment_value: The value to test for the adjustment variable
            config: The goal seek configuration
            opex_rate: Current OPEX rate (for EBIT calculations)
            
        Returns:
            Absolute error between target and achieved metric
        """
        self.iteration_count += 1
        
        # Apply adjustment
        adjusted_df = self.apply_adjustment(config.adjustment_variable, adjustment_value)
        
        # For OPEX and EBIT metrics, we need to add OPEX calculation
        if config.target_metric in [MetricType.EBIT, MetricType.EBIT_MARGIN_PCT]:
            total_revenue = adjusted_df['Total Revenue (€)'].sum()
            total_opex = total_revenue * (opex_rate / 100)
            total_gross_profit = adjusted_df['Gross Profit (€)'].sum()
            ebit = total_gross_profit - total_opex
            
            if config.target_metric == MetricType.EBIT:
                current_value = ebit
            else:  # EBIT_MARGIN_PCT
                current_value = (ebit / total_revenue * 100) if total_revenue > 0 else 0
        else:
            current_value = self.get_metric_value(config.target_metric, adjusted_df)
        
        # Calculate error
        error = abs(current_value - config.target_value)
        return error
    
    def seek(self, config: GoalSeekConfig, opex_rate: float = 15.0) -> GoalSeekResult:
        """
        Perform goal seek to find the adjustment needed to reach target.
        
        Args:
            config: Goal seek configuration
            opex_rate: Current OPEX rate percentage
            
        Returns:
            GoalSeekResult with details of the solution
        """
        self.iteration_count = 0
        
        # Get original metric value
        original_metric_value = self.get_metric_value(config.target_metric, self.data_df)
        
        # Run optimization
        try:
            result = minimize_scalar(
                lambda x: self.objective_function(x, config, opex_rate),
                bounds=(config.min_value, config.max_value),
                method='bounded',
                options={'xatol': config.tolerance, 'maxiter': config.max_iterations}
            )
            
            if result.success or result.fun < config.tolerance:
                optimal_value = result.x
                
                # Apply optimal adjustment and get final metric value
                final_df = self.apply_adjustment(config.adjustment_variable, optimal_value)
                
                if config.target_metric in [MetricType.EBIT, MetricType.EBIT_MARGIN_PCT]:
                    total_revenue = final_df['Total Revenue (€)'].sum()
                    total_opex = total_revenue * (opex_rate / 100)
                    total_gross_profit = final_df['Gross Profit (€)'].sum()
                    ebit = total_gross_profit - total_opex
                    
                    if config.target_metric == MetricType.EBIT:
                        final_metric_value = ebit
                    else:
                        final_metric_value = (ebit / total_revenue * 100) if total_revenue > 0 else 0
                else:
                    final_metric_value = self.get_metric_value(config.target_metric, final_df)
                
                error_pct = abs(final_metric_value - config.target_value) / config.target_value * 100 if config.target_value != 0 else 0
                
                # Update the working dataframe
                self.data_df = final_df
                
                return GoalSeekResult(
                    success=True,
                    target_metric=config.target_metric.value,
                    target_value=config.target_value,
                    adjustment_variable=config.adjustment_variable.value,
                    original_value=config.current_value,
                    new_value=optimal_value,
                    original_metric_value=original_metric_value,
                    final_metric_value=final_metric_value,
                    iterations=self.iteration_count,
                    error_pct=error_pct
                )
            else:
                return GoalSeekResult(
                    success=False,
                    target_metric=config.target_metric.value,
                    target_value=config.target_value,
                    adjustment_variable=config.adjustment_variable.value,
                    original_value=config.current_value,
                    new_value=config.current_value,
                    original_metric_value=original_metric_value,
                    final_metric_value=original_metric_value,
                    iterations=self.iteration_count,
                    error_pct=999.0
                )
        except Exception as e:
            print(f"Goal seek error: {str(e)}")
            return GoalSeekResult(
                success=False,
                target_metric=config.target_metric.value,
                target_value=config.target_value,
                adjustment_variable=config.adjustment_variable.value,
                original_value=config.current_value,
                new_value=config.current_value,
                original_metric_value=original_metric_value,
                final_metric_value=original_metric_value,
                iterations=self.iteration_count,
                error_pct=999.0
            )
    
    def get_adjusted_data(self) -> pd.DataFrame:
        """Get the currently adjusted dataframe."""
        return self.data_df.copy()
    
    def get_original_data(self) -> pd.DataFrame:
        """Get the original dataframe."""
        return self.original_df.copy()
    
    def reset(self):
        """Reset to original data."""
        self.data_df = self.original_df.copy()
        self.iteration_count = 0
