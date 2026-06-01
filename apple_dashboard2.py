# ============================================================================
# APPLE LIVE BUDGET & FINANCIAL MODELER - Professional Dashboard
# ============================================================================
# This application allows financial teams to create, analyze, and compare
# multiple business scenarios for Apple's product portfolio. Users can modify
# prices, volumes, costs, and operating expenses to understand profitability
# impacts in real-time.
# ============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ============================================================================
# SECTION 1: PAGE LAYOUT & STYLING CONFIGURATION
# ============================================================================
# Configure the Streamlit page to use a wide layout (better for dashboards)
# and ensure the sidebar is visible by default.
st.set_page_config(page_title="Apple Live Budget Modeler", layout="wide", initial_sidebar_state="expanded")

# Apply custom CSS styling to match Apple's design language and improve visual hierarchy
# This includes styling for metric containers, report boxes, and data tables.
st.markdown("""
    <style>
    .main {background-color: #f5f5f7;}
    h1, h2, h3 {font-family: 'Helvetica Neue', sans-serif; color: #1d1d1f;}
    div[data-testid="metric-container"] {
        background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    div[data-testid="metric-container"] label, div[data-testid="metric-container"] div {color: #1d1d1f !important;}
    .report-box {
        background-color: #ffffff; border-left: 5px solid #0071e3; padding: 25px; border-radius: 8px;
        color: #1d1d1f; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); font-size: 1.05rem;
    }
    .highlight {color: #0071e3; font-weight: bold;}
    .scenario-box { background-color: #111111; border-radius: 8px; padding: 20px; color: white; border: 1px solid #333; margin-bottom: 15px; }
    .badge-hl { 
        color: #5eafff; background: rgba(94, 175, 255, 0.15); padding: 3px 8px; 
        border-radius: 6px; font-family: monospace; font-weight: 600; 
        border: 1px solid rgba(94, 175, 255, 0.3); font-size: 0.9em;
    }
    .impact-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.95em; color: #e5e5ea; }
    .impact-table th { background-color: #1a1a1c; border-bottom: 2px solid #333; padding: 12px; text-align: left; font-weight: 600; }
    .impact-table td { padding: 12px; border-bottom: 1px solid #222; }
    .val-pos { color: #32d74b; font-weight: bold; }
    .val-neg { color: #ff453a; font-weight: bold; }
    .val-neu { color: #86868b; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 2: INITIALIZE DATA & SESSION STATE
# ============================================================================
# Set up the foundational data that remains constant throughout the session.
# Define the product list, months, and default financial assumptions.

products = ['iPhone', 'iPad Pro', 'MacBook Pro', 'Apple Watch', 'AirPods Pro']
months = ['Oct 2026', 'Nov 2026', 'Dec 2026', 'Jan 2027', 'Feb 2027', 'Mar 2027']

# Initialize session state only once per user session. This ensures data persists
# as users interact with the dashboard without resetting every time a widget changes.
if 'initialized' not in st.session_state:
    # Load Italy sales forecast (units per month for each product)
    st.session_state.df_sales_it = pd.DataFrame({
        'Product': products,
        'Oct 2026': [42000, 8000, 5400, 15000, 22000],
        'Nov 2026': [48000, 9200, 6000, 17000, 25000],
        'Dec 2026': [60000, 10500, 7200, 20000, 30000],
        'Jan 2027': [25000, 5000, 3000, 9000, 12000],
        'Feb 2027': [28000, 5600, 3300, 10000, 14000],
        'Mar 2027': [35000, 6800, 4000, 12000, 18000]
    })
    # Load Sweden sales forecast (units per month for each product)
    st.session_state.df_sales_sw = pd.DataFrame({
        'Product': products,
        'Oct 2026': [46000, 8800, 5940, 16500, 24200],
        'Nov 2026': [52000, 10160, 6600, 18700, 27500],
        'Dec 2026': [65000, 11700, 7920, 22000, 33000],
        'Jan 2027': [27000, 5500, 3300, 10000, 13200],
        'Feb 2027': [30000, 6160, 3630, 11000, 15400],
        'Mar 2027': [38000, 7480, 4400, 13200, 19800]
    })
    # Define selling prices in each market (EUR)
    st.session_state.df_prices = pd.DataFrame({
        'Product': products,
        'Italy Price (€)': [1099.0, 1119.0, 1849.0, 459.0, 249.0],
        'Sweden Price (€)': [1189.0, 1231.0, 2034.0, 505.0, 274.0]
    })
    # Define component costs: PCB, Battery, Display, Packaging per unit
    st.session_state.df_materials = pd.DataFrame({
        'Product': products,
        'PCB (€)': [12.5, 13.5, 18.0, 6.0, 3.0],
        'Battery (€)': [12.0, 23.0, 66.0, 3.9, 1.04],
        'Display/Sensors (€)': [75.0, 150.0, 120.0, 22.0, 17.0],
        'Packaging (€)': [2.5, 3.0, 4.0, 1.5, 1.0]
    })
    # Define manufacturing time required for each product (in minutes per unit)
    st.session_state.df_labor = pd.DataFrame({
        'Product': products,
        'Labor Minutes per Unit': [18, 25, 45, 12, 8]
    })
    # Define inventory buffer policy as % of next month's sales (safety stock strategy)
    st.session_state.df_inventory_policy = pd.DataFrame({
        'Product': products,
        'Target Ending Inv (% of Next Month Sales)': [0.20, 0.15, 0.15, 0.18, 0.25]
    })
    # Define initial inventory at the start of October 2026
    st.session_state.df_opening_inv = pd.DataFrame({
        'Product': products,
        'Italy Opening Units (Oct)': [8400, 1200, 810, 2700, 5500],
        'Sweden Opening Units (Oct)': [9200, 1320, 891, 2970, 6050]
    })
    # Global operating parameters
    st.session_state.labor_rate = 28.00  # EUR per hour for direct manufacturing labor
    st.session_state.opex_rate = 15.00   # Percentage of revenue for operating expenses (SG&A, R&D, etc.)
    st.session_state.scenarios = {}      # Dictionary to store saved scenarios for comparison
    st.session_state.initialized = True  # Mark session as initialized

# ==========================================
# 3. INTERACTIVE SCENARIO BUILDER (WITH RESET)
# ==========================================
st.title("Live Financial & Production Modeler")

with st.expander("Financial Glossary & Methodology", expanded=False):
    glossary_tab1, glossary_tab2, glossary_tab3, glossary_tab4, glossary_tab5 = st.tabs([
        "Revenue & Profitability", 
        "Costs & Manufacturing", 
        "Unit Economics", 
        "Working Capital", 
        "Advanced Metrics"
    ])
    
    with glossary_tab1:
        st.markdown("""
        ### Revenue & Profitability Metrics
        
        #### **Total Gross Revenue** 
        - **Definition:** Total cash generated from all unit sales before any costs are deducted
        - **Formula:** `Selling Price × Sales Volume` (across all products & countries)
        - **Why It Matters:** Top-line indicator of market demand and sales performance; critical for growth assessment
        - **Benchmark:** Track month-over-month growth rate
        
        #### **Gross Profit** 
        - **Definition:** Revenue remaining after deducting all direct manufacturing costs (COGS)
        - **Formula:** `Gross Revenue - COGS (Materials + Direct Labor)`
        - **Why It Matters:** Shows the profitability of the core manufacturing operation before overhead
        - **Strategic Use:** Indicates pricing power and manufacturing efficiency
        
        #### **Gross Margin (%)** 
        - **Definition:** Gross Profit expressed as a percentage of Revenue
        - **Formula:** `(Gross Profit ÷ Revenue) × 100`
        - **Interpretation:** For every €100 in sales, this is the €amount available for overhead and profit
        - **Healthy Range:** 60-90% for electronics manufacturing; 90%+ indicates strong pricing power
        
        #### **OPEX (Operating Expenses)** 
        - **Definition:** Indirect business costs not directly tied to unit production
        - **Components:** SG&A (Sales, General & Admin), R&D, Marketing, Headquarters costs
        - **Formula:** `% of Revenue (typically 5-15%)`
        - **In This Model:** Assumed as **{opex_rate}%** of revenue for scenario consistency
        
        #### **EBIT (Operating Profit)** 
        - **Definition:** Earnings Before Interest and Taxes; the true operating profitability
        - **Formula:** `Gross Profit - OPEX`
        - **Why It Matters:** Shows sustainable profitability from core operations; comparable across companies
        - **EBIT Margin (%):** `(EBIT ÷ Revenue) × 100` — measures operational efficiency
        """)
    
    with glossary_tab2:
        st.markdown("""
        ###  Cost & Manufacturing Metrics
        
        #### **COGS (Cost of Goods Sold)** 
        - **Definition:** Direct costs to produce goods; the sum of materials and direct labor
        - **Components:**
          - **Materials:** PCB, Battery, Display/Sensors, Packaging per unit
          - **Direct Labor:** Manufacturing labor hours converted to cost
        - **Formula:** `COGS = (Unit Material Cost + Unit Labor Cost) × Production Units`
        - **Why It Matters:** Largest controllable cost lever; directly impacts margins
        
        #### **Unit Material Cost** 
        - **Definition:** Component cost per unit of product
        - **Components:** PCB, Battery, Display/Sensors, Packaging
        - **Formula:** `Sum of all component costs for that product`
        - **Optimization:** Supplier negotiations, design simplification, sourcing from low-cost regions
        
        #### **Unit Labor Cost** 
        - **Definition:** Direct manufacturing labor cost per unit
        - **Formula:** `(Labor Minutes per Unit × Labor Rate per Hour) ÷ 60`
        - **In This Model:** Global direct labor rate = **€{labor_rate}/hour**
        - **Reduction Strategies:** Automation, process efficiency, manufacturing in lower-wage regions
        
        #### **Total Unit Cost (COGS per Unit)** 
        - **Definition:** Full direct cost to produce one unit
        - **Formula:** `Unit Material Cost + Unit Labor Cost`
        - **Use Case:** Setting break-even prices, assessing production viability
        
        #### **Unit Gross Margin %** 
        - **Definition:** Profit margin on a per-unit basis
        - **Formula:** `((Selling Price - Unit Cost) ÷ Selling Price) × 100`
        - **Insight:** Shows pricing power at the product level; identify products worth premium distribution
        
        #### **Manufacturing Spend (Production Cash)** 
        - **Definition:** Total cash outlay required to fund factory production
        - **Formula:** `Total Unit Cost × Production Units (which includes inventory buffer)`
        - **Why It Matters:** Working capital requirement; cash tied up in inventory
        - **Strategic Use:** Plan for cash flow, assess working capital needs
        """)
    
    with glossary_tab3:
        st.markdown("""
        ### Unit Economics & Volume Metrics
        
        #### **Production Units vs Sales Units** 
        - **Definition:** Production planned ahead of demand to maintain inventory buffers
        - **Formula:** `Production = Sales + Target Ending Inventory - Beginning Inventory`
        - **Rationale:** Safety stock ensures service level even if demand spikes unexpectedly
        - **Inventory Policy:** Target ending inventory = **% of next month's sales** (set per product)
        
        #### **Beginning Inventory** 
        - **Definition:** Units in stock at the start of each month
        - **First Month (Oct 2026):** Set manually as opening balance
        - **Subsequent Months:** Becomes the prior month's ending inventory
        - **Working Capital Link:** Higher inventory = higher working capital requirement
        
        #### **Ending Inventory** 
        - **Definition:** Units in stock at the end of each month
        - **Formula:** `Beginning Inventory + Production - Sales`
        - **Target Policy:** Set as % of next month's expected sales for demand smoothing
        - **Trade-off:** Provides service level resilience but consumes working capital
        
        #### **Trapped Capital / Inventory Value** 
        - **Definition:** Cash value tied up in unsold inventory at month-end
        - **Formula:** `Ending Inventory × Selling Price (in each month)`
        - **Why It Matters:** Represents cash that cannot be deployed to growth, R&D, or shareholder returns
        - **Optimization:** Reduce through demand forecasting or drop-ship partnerships
        
        #### **Inventory Turnover** 
        - **Definition:** How many times inventory is sold and replaced during the period
        - **Formula:** `Revenue ÷ Average Inventory Value`
        - **Interpretation:** Higher = more efficient use of capital; lower = potential overstock or low demand
        - **Target:** Typically 8-12x annually for high-volume electronics
        """)
    
    with glossary_tab4:
        st.markdown("""
        ### Working Capital & Liquidity Metrics
        
        #### **Working Capital (Inventory Investment)** 
        - **Definition:** Cash invested in inventory to support operations
        - **Formula:** `Ending Inventory Units × Selling Price`
        - **In Dashboard:** Shown as the total cash value of month-end inventory
        - **Business Impact:** High working capital requirement constrains cash for growth and reduces ROI
        
        #### **Cash Conversion Cycle** 
        - **Definition:** Time from cash payment for materials to cash receipt from sales
        - **Components:** Days to make products + Days to sell + Days to collect payment
        - **Optimization:** Faster cycle = less working capital tied up; enables reinvestment
        - **Benchmarking:** Days of inventory + days of receivables - days of payables
        
        #### **Capital Intensity** 
        - **Definition:** Capital required per unit of revenue generated
        - **Formula:** `Inventory Investment ÷ Annual Revenue`
        - **Lower Is Better:** Indicates efficient use of invested capital
        - **Industry Benchmark:** 5-15% for electronics; above 20% signals over-capitalization
        
        #### **Return on Assets (ROA Proxy)** 
        - **Definition:** How efficiently the business generates profit from its invested capital
        - **Formula:** `(EBIT ÷ Manufacturing Spend) × 100`
        - **Interpretation:** Every €1 of manufacturing investment generates this much in operating profit
        - **Target:** >200% annually for high-margin products indicates strong capital efficiency
        """)
    
    with glossary_tab5:
        st.markdown("""
        ### Advanced Risk & Efficiency Metrics
        
        #### **Revenue Concentration Risk** 
        - **Definition:** % of total revenue dependent on a single product
        - **Risk Levels:**
          - 🟢 **Low Risk:** <40% (well diversified)
          - 🟡 **Medium Risk:** 40-50% (monitor closely)
          - 🔴 **High Risk:** >50% (over-concentrated; vulnerable to disruption)
        - **Mitigation:** Diversify product portfolio, enter new markets
        
        #### **Cost Spike Impact** 
        - **Definition:** Profit impact if materials costs increase 10% unexpectedly
        - **Formula:** `Material Costs × 10% = Profit Erosion`
        - **Use Case:** Stress testing; supply chain risk assessment
        - **Interpretation:** Indicates exposure to commodity price inflation
        
        #### **Margin Erosion (%)** 
        - **Definition:** % of gross margin lost if costs spike 10%
        - **Formula:** `(Cost Spike Impact ÷ Total Revenue) × 100`
        - **Strategic Use:** Determine hedging needs and supply chain diversification urgency
        - **Acceptable Level:** <2% = low risk; >5% = high vulnerability
        
        #### **Price Elasticity & Pricing Power** 
        - **Definition:** Ability to maintain gross margin despite cost increases
        - **Indicator:** High gross margin (>70%) suggests strong pricing power
        - **Strategy:** Premium pricing, differentiation, brand positioning for high-margin products
        
        #### **Cost Reduction Opportunity** 
        - **Definition:** Potential profit improvement from operational efficiency
        - **Examples:**
          - 1% material cost reduction = {{material_spend * 0.01}} profit improvement
          - 5% labor efficiency gain = {{labor_spend * 0.05}} savings
          - 10% OPEX reduction = {{opex_total * 0.10}} to bottom line
        - **Focus Areas:** Identify highest-impact levers per product
        
        #### **Breakeven Analysis** 
        - **Definition:** Minimum volume/price needed to cover all costs
        - **Formula:** `Breakeven Volume = OPEX ÷ (Price - Unit Variable Cost)`
        - **Use Case:** Risk assessment, minimum order quantities, market entry decisions
        """)
    

with st.expander("Scenario Modeler: Edit Source Tables", expanded=False):
    st.write("Edit the foundational assumptions below. The entire dashboard will recalculate in real-time.")
    
    if st.button("Reset to Original Base Assumptions"):
        if 'Base Case' in st.session_state.scenarios:
            base = st.session_state.scenarios['Base Case']['inputs']
            st.session_state.df_sales_it = base['sales_it'].copy()
            st.session_state.df_sales_sw = base['sales_sw'].copy()
            st.session_state.df_prices = base['prices'].copy()
            st.session_state.df_materials = base['materials'].copy()
            st.session_state.df_labor = base['labor'].copy()
            st.session_state.df_inventory_policy = base['inventory'].copy()
            st.session_state.df_opening_inv = base['opening'].copy()
            st.session_state.labor_rate = st.session_state.scenarios['Base Case']['labor_rate']
            st.session_state.opex_rate = st.session_state.scenarios['Base Case']['opex_rate']
            st.rerun() 
    
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Monthly Sales", "Selling Prices", "Costs & OPEX", "Inventory Policies", "Opening Inventory"])
    
    with tab1:
        st.write("**Italy Sales Forecast (Units)**")
        st.session_state.df_sales_it = st.data_editor(st.session_state.df_sales_it, hide_index=True, width='stretch')
        st.write("**Sweden Sales Forecast (Units)**")
        st.session_state.df_sales_sw = st.data_editor(st.session_state.df_sales_sw, hide_index=True, width='stretch')
    with tab2:
        st.session_state.df_prices = st.data_editor(st.session_state.df_prices, hide_index=True, width='stretch')
    with tab3:
        st.session_state.df_materials = st.data_editor(st.session_state.df_materials, hide_index=True, width='stretch')
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.session_state.labor_rate = st.number_input("Global Direct Labor Rate (€/hour)", value=st.session_state.labor_rate, step=1.0)
        with col_c2:
            st.session_state.opex_rate = st.number_input("Global OPEX (SG&A, R&D) as % of Revenue", value=st.session_state.opex_rate, step=1.0)
        st.session_state.df_labor = st.data_editor(st.session_state.df_labor, hide_index=True, width='stretch')
    with tab4:
        st.write("**Inventory Buffer Strategy**")
        st.session_state.df_inventory_policy = st.data_editor(st.session_state.df_inventory_policy, hide_index=True, width='stretch')
    with tab5:
        st.write("**Initial Stock (October 1, 2026)**")
        st.session_state.df_opening_inv = st.data_editor(st.session_state.df_opening_inv, hide_index=True, width='stretch')

# ============================================================================
# SECTION 4: FINANCIAL CALCULATION ENGINE
# ============================================================================
# This is the core calculation engine that builds the complete financial model.
# It calculates unit costs, production requirements, revenues, and profitability.

# Define which columns contain material component costs
mat_cols = ['PCB (€)', 'Battery (€)', 'Display/Sensors (€)', 'Packaging (€)']

# Calculate total material cost per unit by summing all component costs
st.session_state.df_materials['Total Unit Material (€)'] = st.session_state.df_materials[mat_cols].sum(axis=1)

# Calculate labor cost per unit by converting labor minutes to hourly cost
st.session_state.df_labor['Total Unit Labor (€)'] = st.session_state.df_labor['Labor Minutes per Unit'] * (st.session_state.labor_rate / 60)

rows = []
for c_idx, country in enumerate(['Italy', 'Sweden']):
    sales_df = st.session_state.df_sales_it if country == 'Italy' else st.session_state.df_sales_sw
    price_col = 'Italy Price (€)' if country == 'Italy' else 'Sweden Price (€)'
    open_inv_col = 'Italy Opening Units (Oct)' if country == 'Italy' else 'Sweden Opening Units (Oct)'
    
    for p_idx, product in enumerate(products):
        sales_arr = [sales_df.loc[sales_df['Product'] == product, m].values[0] for m in months]
        policy = st.session_state.df_inventory_policy.loc[st.session_state.df_inventory_policy['Product'] == product, 'Target Ending Inv (% of Next Month Sales)'].values[0]
        initial_inv = st.session_state.df_opening_inv.loc[st.session_state.df_opening_inv['Product'] == product, open_inv_col].values[0]
        
        price = st.session_state.df_prices.loc[st.session_state.df_prices['Product'] == product, price_col].values[0]
        unit_mat = st.session_state.df_materials.loc[st.session_state.df_materials['Product'] == product, 'Total Unit Material (€)'].values[0]
        unit_lab = st.session_state.df_labor.loc[st.session_state.df_labor['Product'] == product, 'Total Unit Labor (€)'].values[0]
        unit_total_cost = unit_mat + unit_lab
        
        end_inv_arr = []
        prod_arr = []
        
        for i, month in enumerate(months):
            next_sales = sales_arr[i+1] if i < 5 else sales_arr[5]
            target_end_inv = next_sales * policy
            end_inv_arr.append(target_end_inv)
            
            beg_inv = initial_inv if i == 0 else end_inv_arr[i-1]
            required_prod = sales_arr[i] + target_end_inv - beg_inv
            prod_arr.append(required_prod)
            
            rows.append({
                'Country': country, 'Product': product, 'Month': month,
                'Sales Units': sales_arr[i], 'Production Units': required_prod,
                'Beginning Inventory': beg_inv, 'Ending Inventory': target_end_inv,
                'Selling Price (€)': price, 'Unit Material Cost (€)': unit_mat, 
                'Unit Labor Cost (€)': unit_lab, 'Total Unit Cost (€)': unit_total_cost,
                'Unit Gross Margin %': ((price - unit_total_cost) / price * 100) if price > 0 else 0,
                'Total Revenue (€)': sales_arr[i] * price,
                'Total Material Cost (€)': required_prod * unit_mat,
                'Total Labor Cost (€)': required_prod * unit_lab,   
                'Total Cost (€)': sales_arr[i] * unit_total_cost,   
                'Production Spend (€)': required_prod * unit_total_cost, 
                'Gross Profit (€)': sales_arr[i] * (price - unit_total_cost),
                'Ending Inv Value (€)': target_end_inv * unit_total_cost
            })

df = pd.DataFrame(rows)

# CAPTURE BASELINE (Full Depth Save)
if 'Base Case' not in st.session_state.scenarios:
    st.session_state.scenarios['Base Case'] = {
        'df': df.copy(),
        'opex_rate': st.session_state.opex_rate,
        'labor_rate': st.session_state.labor_rate,
        'inputs': {
            'prices': st.session_state.df_prices.copy(),
            'sales_it': st.session_state.df_sales_it.copy(),
            'sales_sw': st.session_state.df_sales_sw.copy(),
            'materials': st.session_state.df_materials.copy(),
            'labor': st.session_state.df_labor.copy(),
            'inventory': st.session_state.df_inventory_policy.copy(),
            'opening': st.session_state.df_opening_inv.copy()
        }
    }

# ==========================================
# 5. SIDEBAR FILTERS & SCENARIO SAVING
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg", width=50)
# Display the Apple logo in the sidebar for brand recognition
st.sidebar.title("Dashboard Filters")
# Create sidebar section for data filtering and currency selection

st.sidebar.markdown("---")
st.sidebar.subheader("Data Filters")

selected_countries = st.sidebar.multiselect("Select Country", ['Italy', 'Sweden'], default=['Italy', 'Sweden'])
selected_products = st.sidebar.multiselect("Select Product", products, default=products)
selected_months = st.sidebar.multiselect("Select Month", months, default=months)

st.sidebar.markdown("---")
st.sidebar.subheader("Currency Settings")
curr_choice = st.sidebar.radio("View Financials In:", ["EUR (€)", "USD ($)", "SEK (kr)"])
fx_map = {"EUR (€)": (1.0, "€"), "USD ($)": (1.08, "$"), "SEK (kr)": (11.0, "kr")}
rate, sym = fx_map[curr_choice]

# SCENARIO MANAGER IN SIDEBAR
st.sidebar.markdown("---")
st.sidebar.subheader("Scenario Manager")
new_scen_name = st.sidebar.text_input("Name new scenario:", f"Scenario {len(st.session_state.scenarios)}")
if st.sidebar.button("Save Current Variables"):
    st.session_state.scenarios[new_scen_name] = {
        'df': df.copy(),
        'opex_rate': st.session_state.opex_rate,
        'labor_rate': st.session_state.labor_rate,
        'inputs': {
            'prices': st.session_state.df_prices.copy(),
            'sales_it': st.session_state.df_sales_it.copy(),
            'sales_sw': st.session_state.df_sales_sw.copy(),
            'materials': st.session_state.df_materials.copy(),
            'labor': st.session_state.df_labor.copy(),
            'inventory': st.session_state.df_inventory_policy.copy(),
            'opening': st.session_state.df_opening_inv.copy()
        }
    }
    st.sidebar.success(f"Saved as '{new_scen_name}'!")
if st.sidebar.button("Clear Saved Scenarios"):
    base = st.session_state.scenarios['Base Case']
    st.session_state.scenarios = {'Base Case': base}
    st.sidebar.info("Cleared custom scenarios.")


# --- NEW FEATURE: LOAD & EDIT SCENARIOS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Load & Edit Scenario")
st.sidebar.caption("Load a previously saved scenario to edit its assumptions.")

# Dropdown to select a scenario
saved_scenarios = list(st.session_state.scenarios.keys())
scenario_to_load = st.sidebar.selectbox("Select scenario to load:", saved_scenarios)

if st.sidebar.button("Load Scenario to Edit"):
    # Retrieve the saved inputs
    target_scenario = st.session_state.scenarios[scenario_to_load]
    
    # Overwrite the active session state with the saved scenario's data
    st.session_state.df_sales_it = target_scenario['inputs']['sales_it'].copy()
    st.session_state.df_sales_sw = target_scenario['inputs']['sales_sw'].copy()
    st.session_state.df_prices = target_scenario['inputs']['prices'].copy()
    st.session_state.df_materials = target_scenario['inputs']['materials'].copy()
    st.session_state.df_labor = target_scenario['inputs']['labor'].copy()
    st.session_state.df_inventory_policy = target_scenario['inputs']['inventory'].copy()
    st.session_state.df_opening_inv = target_scenario['inputs']['opening'].copy()
    st.session_state.opex_rate = target_scenario['opex_rate']
    st.session_state.labor_rate = target_scenario['labor_rate']
    
    st.sidebar.success(f"'{scenario_to_load}' loaded successfully! You can now edit it in the main window.")
    st.rerun() # Refresh the app to show the loaded data

filtered_df = df[
    (df['Country'].isin(selected_countries)) &
    (df['Product'].isin(selected_products)) &
    (df['Month'].isin(selected_months))
]

base_df = st.session_state.scenarios['Base Case']['df']
filtered_base_df = base_df[
    (base_df['Country'].isin(selected_countries)) &
    (base_df['Product'].isin(selected_products)) &
    (base_df['Month'].isin(selected_months))
]

if filtered_df.empty:
    st.warning("Please select at least one Country, Product, and Month from the sidebar.")
    st.stop()

# ==========================================
# 6. KPI CARDS (With Color Fixes)
# ==========================================
col1, col2, col3, col4 = st.columns(4)

total_units = filtered_df['Sales Units'].sum()
total_revenue = filtered_df['Total Revenue (€)'].sum()
total_cogs = filtered_df['Total Cost (€)'].sum()
total_prod_spend = filtered_df['Production Spend (€)'].sum()
total_profit = filtered_df['Gross Profit (€)'].sum()
gross_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
current_opex = total_revenue * (st.session_state.opex_rate / 100)
current_ebit = total_profit - current_opex

b_units = filtered_base_df['Sales Units'].sum()
b_rev = filtered_base_df['Total Revenue (€)'].sum()
b_spend = filtered_base_df['Production Spend (€)'].sum()
b_profit = filtered_base_df['Gross Profit (€)'].sum()
b_margin = (b_profit / b_rev * 100) if b_rev > 0 else 0

# Calculate deltas 
unit_delta = total_units - b_units
revenue_delta = total_revenue - b_rev
margin_delta = gross_margin - b_margin
spend_delta = total_prod_spend - b_spend

# Ensure the mathematical sign (+ or -) is the very first character for Streamlit
rev_sign = "-" if revenue_delta < 0 else ""
spend_sign = "-" if spend_delta < 0 else ""

# For spending metrics, we want GREEN when lower (delta_color="inverse" for negative is good)
# For all other metrics, GREEN when higher (normal logic)
with col1: 
    st.metric(label="Total Units Sold", value=f"{total_units:,.0f}", 
              delta=f"{unit_delta:,.0f} units vs Base", delta_color="normal")
with col2: 
    st.metric(label="Gross Revenue", value=f"{sym}{(total_revenue * rate) / 1000000:,.1f}M", 
              # Using abs() so we don't get double minus signs, and placing rev_sign at the front
              delta=f"{rev_sign}{sym}{abs(revenue_delta*rate) / 1000000:,.1f}M vs Base", delta_color="normal")
with col3: 
    st.metric(label="Blended Margin", value=f"{gross_margin:.1f}%", 
              delta=f"{margin_delta:.1f}% vs Base", delta_color="normal")
with col4: 
    st.metric(label="Mfg Spend (Cash Out)", value=f"{sym}{(total_prod_spend * rate) / 1000000:,.1f}M", 
              # Placing spend_sign at the front so Streamlit triggers "inverse" coloring correctly
              delta=f"{spend_sign}{sym}{abs(spend_delta*rate) / 1000000:,.1f}M vs Base", delta_color="inverse")

st.markdown("---")

# ============= DYNAMIC KEY INSIGHTS (Bullet Point Format) =============
st.markdown("### AI-Assisted Variance Impact Report")
st.caption(f"Tracking the ripple effects of your scenario adjustments vs. the Base Case (Viewing in {curr_choice}).")

try:
    # --- 1. DATA PREPARATION ---
    # Convert absolute deltas to the selected currency
    rev_delta_converted = revenue_delta * rate
    spend_delta_converted = spend_delta * rate
    
    # Calculate percentage changes (with safety checks to avoid dividing by zero)
    rev_pct_change = (revenue_delta / b_rev * 100) if b_rev > 0 else 0
    spend_pct_change = (spend_delta / b_spend * 100) if b_spend > 0 else 0
    unit_pct_change = (unit_delta / b_units * 100) if b_units > 0 else 0

    # --- 2. BUILD BULLET POINTS DYNAMICALLY ---
    bullets = []

    # 1. Top-line Revenue & Volume shift
    if rev_delta_converted != 0 or unit_pct_change != 0:
        direction = "increased" if rev_delta_converted > 0 else "decreased"
        emoji = "📈" if rev_delta_converted > 0 else "📉"
        bullets.append(f"{emoji} <b>Revenue Shift:</b> Top-line revenue {direction} by <b>{sym}{abs(rev_delta_converted)/1000000:.2f}M</b> ({rev_pct_change:+.1f}%). This was driven by a {unit_pct_change:+.1f}% change in total unit sales volume.")

    # 2. Profitability & Margin shift
    if margin_delta != 0:
        direction = "expanded" if margin_delta > 0 else "compressed"
        emoji = "💚" if margin_delta > 0 else "⚠️"
        bullets.append(f"{emoji} <b>Margin Impact:</b> Blended gross margin {direction} by <b>{abs(margin_delta):.1f} percentage points</b>, shifting your new baseline to {gross_margin:.1f}%.")

    # 3. Operational Efficiency (Manufacturing Spend)
    if spend_delta_converted != 0:
        direction = "increased" if spend_delta_converted > 0 else "decreased"
        emoji = "🏭" if spend_delta_converted < 0 else "💸" # Down is good for spend
        eval_text = "improving your cash position" if spend_delta_converted < 0 else "requiring more working capital to fund operations"
        bullets.append(f"{emoji} <b>Manufacturing Cash Flow:</b> Production spend {direction} by <b>{sym}{abs(spend_delta_converted)/1000000:.2f}M</b>, {eval_text}.")

    # 4. Combined Strategic Synthesis
    if rev_delta_converted > 0 and margin_delta < -0.5:
        bullets.append("🔍 <b>Strategic Warning (Growth Trap):</b> You are generating more revenue, but it is costing you margin to do so. Ensure the volume bump justifies the sacrificed profitability per unit.")
    elif rev_delta_converted > 0 and margin_delta > 0:
        bullets.append("🏆 <b>Strategic Win:</b> Excellent scenario alignment! You are successfully scaling revenue while simultaneously expanding profit margins.")
    elif spend_delta_converted < 0 and rev_delta_converted >= 0:
        bullets.append("⚙️ <b>Efficiency Gain:</b> Lean operations achieved. You are maintaining or growing revenue while actively pulling cash out of the manufacturing cycle.")

    # --- 3. RENDERING THE NEW SHAPE ---
    if bullets:
        # We wrap the bullets in a sleek HTML div to match your dark theme
        bullet_html = "".join([f"<li style='margin-bottom: 12px; line-height: 1.5;'>{b}</li>" for b in bullets])
        st.markdown(f"""
        <div style='background-color: #1a1a1c; padding: 25px; border-left: 5px solid #0071e3; border-radius: 8px; color: #e6edf3; font-size: 1.05rem;'>
            <ul style='margin-bottom: 0; padding-left: 20px;'>
                {bullet_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No significant variances detected from the Base Case. Try adjusting prices, volumes, or costs in the Scenario Builder above to see the ripple effects here.")

except Exception as e:
    st.error(f"Insight generation requires more data. Please adjust your filters. (Error: {str(e)})")
    

st.markdown("---")
st.subheader("Strategic Scenario & What-If Analysis")

with st.expander("Scenario Planner - Define Your Target & Find the Path Forward", expanded=True):
    from goal_seek_engine import GoalSeekEngine, GoalSeekConfig, MetricType, AdjustmentVariable
    from goal_seek_metrics import calculate_metrics, calculate_impact_metrics, create_comparison_summary, format_metric_value
    
    # Professional header with currency info
    st.info(
        f"**Active Currency:** {curr_choice} ({sym}) | Exchange Rate: 1 EUR = {rate:.2f} {sym[0]} | "
        f"All numeric entries below should be in {sym}.",
        icon="💱"
    )
    
    # ---- STEP 1: TARGET DEFINITION ----
    st.markdown("### Step 1: Define Your Target Metric & Goal")
    
    gs_col1, gs_col2 = st.columns(2)
    
    with gs_col1:
        target_metric = st.selectbox(
            "Select Target Metric",
            options=[
                "Total Revenue",
                "Gross Profit", 
                "Gross Margin %",
                "EBIT (Operating Profit)",
                "EBIT Margin %",
                "Avg Selling Price",
                "Avg Unit Cost"
            ],
            key="goal_seek_target_metric",
            help="Choose the key performance indicator you want to achieve"
        )
    
    with gs_col2:
        # Show current value for reference
        if target_metric == "Total Revenue":
            current_metric_val = total_revenue
        elif target_metric == "Gross Profit":
            current_metric_val = total_profit
        elif target_metric == "Gross Margin %":
            current_metric_val = gross_margin
        elif target_metric == "EBIT (Operating Profit)":
            current_metric_val = current_ebit
        elif target_metric == "EBIT Margin %":
            current_metric_val = (current_ebit / total_revenue * 100) if total_revenue > 0 else 0
        elif target_metric == "Avg Selling Price":
            current_metric_val = filtered_df['Selling Price (€)'].mean()
        else:  # Avg Unit Cost
            current_metric_val = filtered_df['Total Unit Cost (€)'].mean()
        
        help_text = f"Current Value: {format_metric_value(current_metric_val, target_metric)}"
        
        # --- FIX FOR STREAMLIT WARNING ---
        # Initialize session state manually so we can remove the 'value' parameter from number_input
        if 'prev_target_metric' not in st.session_state:
            st.session_state.prev_target_metric = target_metric
            
        # Update the default value if it's the first run OR if the user changed the target metric
        if 'goal_seek_target_value' not in st.session_state or st.session_state.prev_target_metric != target_metric:
            st.session_state.goal_seek_target_value = float(current_metric_val * 1.1)
            st.session_state.prev_target_metric = target_metric
            
        target_value = st.number_input(
            f"Target Value (in {sym})",
            # value parameter is completely removed to prevent the Session State API warning!
            step=10000.0 if "Margin" not in target_metric else 1.0,
            key="goal_seek_target_value",
            help=help_text
        )
    
    st.markdown("---")
    
    # ---- SUGGESTED TARGETS SECTION ----
    st.markdown("### Quick Target Benchmarks")
    st.caption("Click any button below to instantly populate the target value above")
    
    # Calculate preset values based on selected metric
    if target_metric == "Total Revenue":
        preset_label = "Revenue"
        preset_10 = total_revenue * 1.1 * rate
        preset_20 = total_revenue * 1.2 * rate
        preset_30 = total_revenue * 1.3 * rate
        is_percentage = False
    elif target_metric == "Gross Profit":
        preset_label = "Profit"
        preset_10 = total_profit * 1.1 * rate
        preset_20 = total_profit * 1.2 * rate
        preset_30 = total_profit * 1.3 * rate
        is_percentage = False
    elif target_metric == "EBIT (Operating Profit)":
        preset_label = "EBIT"
        preset_10 = current_ebit * 1.1 * rate
        preset_20 = current_ebit * 1.2 * rate
        preset_30 = current_ebit * 1.3 * rate
        is_percentage = False
    elif target_metric == "Gross Margin %":
        preset_label = "Gross Margin"
        preset_10 = gross_margin * 1.1
        preset_20 = gross_margin * 1.2
        preset_30 = gross_margin * 1.3
        is_percentage = True
    elif target_metric == "EBIT Margin %":
        preset_label = "EBIT Margin"
        ebit_margin = (current_ebit / total_revenue * 100) if total_revenue > 0 else 0
        preset_10 = ebit_margin * 1.1
        preset_20 = ebit_margin * 1.2
        preset_30 = ebit_margin * 1.3
        is_percentage = True
    elif target_metric == "Avg Selling Price":
        preset_label = "Avg Price"
        current_price = filtered_df['Selling Price (€)'].mean() * rate
        preset_10 = current_price * 1.1
        preset_20 = current_price * 1.2
        preset_30 = current_price * 1.3
        is_percentage = False
    else:  # Avg Unit Cost
        preset_label = "Unit Cost"
        current_cost = filtered_df['Total Unit Cost (€)'].mean() * rate
        preset_10 = current_cost * 1.1
        preset_20 = current_cost * 1.2
        preset_30 = current_cost * 1.3
        is_percentage = False
    
    col_preset1, col_preset2, col_preset3 = st.columns(3)
    
    col_preset1, col_preset2, col_preset3 = st.columns(3)
    
    def set_preset_10():
        st.session_state.goal_seek_target_value = preset_10
    
    def set_preset_20():
        st.session_state.goal_seek_target_value = preset_20
    
    def set_preset_30():
        st.session_state.goal_seek_target_value = preset_30
    
    with col_preset1:
        if is_percentage:
            display_10_full = f"{preset_10:.1f}%"
        else:
            display_10_full = f"{sym}{preset_10:,.0f}"
        
        st.button(
            f" +10%\n{display_10_full}",
            key="preset_10_btn",
            width='stretch',
            help="Click to set this as your target",
            on_click=set_preset_10
        )
    
    with col_preset2:
        if is_percentage:
            display_20_full = f"{preset_20:.1f}%"
        else:
            display_20_full = f"{sym}{preset_20:,.0f}"
        
        st.button(
            f" +20%\n{display_20_full}",
            key="preset_20_btn",
            width='stretch',
            help="Click to set this as your target",
            on_click=set_preset_20
        )
    
    with col_preset3:
        if is_percentage:
            display_30_full = f"{preset_30:.1f}%"
        else:
            display_30_full = f"{sym}{preset_30:,.0f}"
        
        st.button(
            f" +30%\n{display_30_full}",
            key="preset_30_btn",
            width='stretch',
            help="Click to set this as your target",
            on_click=set_preset_30
        )
    
    st.markdown("---")
    
    # ---- STEP 2: ADJUSTMENT STRATEGY & SCOPE ----
    st.markdown("### Step 2: Choose Your Adjustment Strategy & Scope")
    
    gs_col3, gs_col4, gs_col5 = st.columns([2, 2, 1])
    
    with gs_col3:
        adjustment_variable = st.selectbox(
            "Select Variable to Adjust",
            options=["Selling Price", "Sales Volume", "Material Costs", "Labor Rate", "OPEX Rate"],
            key="goal_seek_adjustment_var",
            help="Choose which business lever to pull to reach your target"
        )
    
    with gs_col4:
        st.caption("Target Scope (Apply adjustment to specific segments only)")
        adjust_countries = st.multiselect("Countries:", selected_countries, default=selected_countries, key="gs_countries")
        adjust_products = st.multiselect("Products:", selected_products, default=selected_products, key="gs_products")
    
    with gs_col5:
        st.write("") 
        st.write("") 
        run_goal_seek = st.button("▶ Analyze Scenario", key="run_goal_seek_btn", width='stretch', help="Run the analysis")
    
    st.markdown("---")
    
    # ============================================
    # SCENARIO ANALYSIS RESULTS & INSIGHTS
    # ============================================
    if run_goal_seek:
        try:
            # Map UI selections to enums
            metric_map = {
                "Total Revenue": MetricType.REVENUE, "Gross Profit": MetricType.GROSS_PROFIT,
                "Gross Margin %": MetricType.GROSS_MARGIN_PCT, "EBIT (Operating Profit)": MetricType.EBIT,
                "EBIT Margin %": MetricType.EBIT_MARGIN_PCT, "Avg Selling Price": MetricType.UNIT_COST,
                "Avg Unit Cost": MetricType.UNIT_COST
            }
            
            var_map = {
                "Selling Price": AdjustmentVariable.SELLING_PRICE, "Sales Volume": AdjustmentVariable.SALES_VOLUME,
                "Material Costs": AdjustmentVariable.MATERIAL_COST_RATIO, "Labor Rate": AdjustmentVariable.LABOR_RATE,
                "OPEX Rate": AdjustmentVariable.OPEX_RATE
            }
            
            # --- NEW SCOPE LOGIC: Split the dataframe ---
            target_mask = filtered_df['Country'].isin(adjust_countries) & filtered_df['Product'].isin(adjust_products)
            target_df = filtered_df[target_mask].copy()
            static_df = filtered_df[~target_mask].copy()
            
            if target_df.empty:
                st.error("Scope Error: Your selected scope is empty. Please select at least one Country and Product in Step 2.")
                st.session_state.goal_seek_result = None
                st.stop()
            
            # Calculate baseline metrics on the FULL dataset
            baseline_metrics = calculate_metrics(filtered_df, st.session_state.opex_rate)
            
            # Get current value for the adjustment variable based ONLY on the target scope
            if adjustment_variable == "Selling Price":
                current_adjustment_value = target_df['Selling Price (€)'].mean()
            elif adjustment_variable == "Sales Volume":
                current_adjustment_value = target_df['Sales Units'].mean()
            elif adjustment_variable == "Material Costs":
                current_adjustment_value = target_df['Unit Material Cost (€)'].mean()
            elif adjustment_variable == "Labor Rate":
                current_adjustment_value = st.session_state.labor_rate
            else:  # OPEX Rate
                current_adjustment_value = st.session_state.opex_rate
            
            # Determine bounds for the adjustment
            if adjustment_variable in ["Selling Price", "Material Costs"]:
                min_bound = current_adjustment_value * 0.5
                max_bound = current_adjustment_value * 5.0
            elif adjustment_variable == "Sales Volume":
                min_bound = current_adjustment_value * 0.3
                max_bound = current_adjustment_value * 3.0
            elif adjustment_variable in ["Labor Rate", "OPEX Rate"]:
                min_bound = 0.1
                max_bound = current_adjustment_value * 3.0
            
            # Create goal seek config
            gs_config = GoalSeekConfig(
                target_metric=metric_map.get(target_metric, MetricType.REVENUE),
                target_value=target_value,
                adjustment_variable=var_map.get(adjustment_variable, AdjustmentVariable.SELLING_PRICE),
                current_value=current_adjustment_value,
                min_value=min_bound, max_value=max_bound, tolerance=0.001, max_iterations=500
            )
            
            # Create engine and run goal seek
            # --- NEW WRAPPER: Combines the adjusting target data with static data on the fly ---
            def metric_calculator(adj_target_df):
                combined_df = pd.concat([adj_target_df, static_df]) if not static_df.empty else adj_target_df
                return calculate_metrics(combined_df, st.session_state.opex_rate)
            
            engine = GoalSeekEngine(target_df, metric_calculator)
            result = engine.seek(gs_config, st.session_state.opex_rate)
            
            # Store result in session state for display
            st.session_state.goal_seek_result = result
            # Save the final combined dataframe so all downstream charts show the complete picture!
            st.session_state.goal_seek_adjusted_df = pd.concat([engine.get_adjusted_data(), static_df]) if not static_df.empty else engine.get_adjusted_data()
            
        except Exception as e:
            st.error(f"Analysis Error: {str(e)}")
            st.session_state.goal_seek_result = None
    
    # Display Goal Seek Results
    if 'goal_seek_result' in st.session_state and st.session_state.goal_seek_result:
        result = st.session_state.goal_seek_result
        
        if result.success:
            st.success("Scenario Analysis Complete - Solution Found!")
            
            st.markdown("---")
            
            # ---- EXECUTIVE SUMMARY ----
            st.markdown("### Analysis Summary")
            
            pct_change = ((result.new_value - result.original_value) / result.original_value * 100) if result.original_value != 0 else 0
            
            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
            
            with summary_col1:
                st.metric(
                    "Target Metric",
                    result.target_metric,
                    f"Goal: {format_metric_value(result.target_value, result.target_metric)}"
                )
            
            with summary_col2:
                st.metric(
                    "Adjustment Variable",
                    result.adjustment_variable,
                    f"→ {format_metric_value(result.new_value, result.adjustment_variable)}"
                )
            
            with summary_col3:
                change_color = "inverse" if pct_change < 0 else "normal"
                st.metric(
                    "Required Change",
                    f"{pct_change:+.1f}%",
                    f"From {format_metric_value(result.original_value, result.adjustment_variable)}",
                    delta_color=change_color
                )
            
            with summary_col4:
                st.metric(
                    "Feasibility",
                    "Achievable",
                    "Within operating constraints"
                )
            
            st.markdown("---")
            
            # ---- KEY INSIGHTS ----
            st.markdown("### Strategic Insights & Recommendations")
            
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                st.info(
                    f"**What needs to change:** {adjustment_variable} must increase by {abs(pct_change):.1f}% to achieve your target of "
                    f"{format_metric_value(result.target_value, result.target_metric)} in {target_metric}.",
                    icon="💡"
                )
            
            with insight_col2:
                if adjustment_variable == "Selling Price":
                    price_impact = ((result.new_value - result.original_value) / result.original_value * 100)
                    st.warning(
                        f"**Price Elasticity Risk:** A {price_impact:.1f}% price increase may impact demand. "
                        f"Consider implementing this gradually or coupling with value-add initiatives.",
                        icon="⚡"
                    )
                elif adjustment_variable == "Sales Volume":
                    vol_impact = ((result.new_value - result.original_value) / result.original_value * 100)
                    st.info(
                        f"**Volume Strategy:** Need to grow sales by {vol_impact:.1f}%. "
                        f"This requires aggressive marketing or market expansion.",
                        icon="🎯"
                    )
                elif adjustment_variable == "Material Costs":
                    cost_reduction = abs(pct_change)
                    st.info(
                        f"**Supply Chain Optimization:** Must reduce material costs by {cost_reduction:.1f}%. "
                        f"Explore supplier negotiations, alternative materials, or process improvements.",
                        icon="🏭"
                    )
            
            st.markdown("---")
            
            # ---- BEFORE & AFTER COMPARISON (COUNTRY SPLIT) ----
            st.markdown("### Before & After Impact Analysis (Regional Split)")
            
            # Find which countries are currently in our scope
            active_countries = sorted(st.session_state.goal_seek_adjusted_df['Country'].unique())
            
            comp_tab1, comp_tab2, comp_tab3, comp_tab4 = st.tabs([
                "Full Metrics", 
                "Financial Impact", 
                "Product Breakdown",
                "Risk Analysis"
            ])
            
            with comp_tab1:
                st.markdown("**Complete Financial Metrics Comparison**")
                st.caption(f"💱 All values shown in {sym} (Conversion: 1 EUR = {rate:.2f} {sym[0]})")
                
                # Create dynamic side-by-side columns based on active countries
                cols1 = st.columns(len(active_countries))
                
                for i, country in enumerate(active_countries):
                    with cols1[i]:
                        st.markdown(f"#### 📍 {country} Operations")
                        
                        # Filter data specifically for this country
                        c_base_df = filtered_df[filtered_df['Country'] == country]
                        c_scen_df = st.session_state.goal_seek_adjusted_df[st.session_state.goal_seek_adjusted_df['Country'] == country]
                        
                        # Calculate local metrics
                        c_base_metrics = calculate_metrics(c_base_df, st.session_state.opex_rate)
                        c_scen_metrics = calculate_metrics(c_scen_df, st.session_state.opex_rate)
                        
                        comparison_data = []
                        key_metrics_display = [
                            ('Total Revenue (€)', 'Revenue'), ('Total COGS (€)', 'COGS'),
                            ('Total Gross Profit (€)', 'Gross Profit'), ('Gross Margin %', 'Gross Margin %'),
                            ('Total OPEX (€)', 'OPEX'), ('EBIT (€)', 'EBIT'),
                            ('EBIT Margin %', 'EBIT Margin %'), ('Total Units', 'Units Sold'),
                            ('Avg Selling Price (€)', 'Avg Price'), ('Avg Unit Cost (€)', 'Avg Cost'),
                        ]
                        
                        for metric_key, display_name in key_metrics_display:
                            if metric_key in c_base_metrics and metric_key in c_scen_metrics:
                                baseline = c_base_metrics[metric_key]
                                scenario = c_scen_metrics[metric_key]
                                change = scenario - baseline
                                change_pct = (change / baseline * 100) if baseline != 0 else 0
                                
                                # Apply currency conversion
                                if '(€)' in metric_key and '%' not in metric_key:
                                    baseline_display = f"{sym}{baseline * rate:,.0f}"
                                    scenario_display = f"{sym}{scenario * rate:,.0f}"
                                    change_display = f"{sym}{change * rate:,.0f}"
                                else:
                                    baseline_display = format_metric_value(baseline, metric_key)
                                    scenario_display = format_metric_value(scenario, metric_key)
                                    change_display = format_metric_value(change, metric_key)
                                
                                comparison_data.append({
                                    'Metric': display_name, 'Baseline': baseline_display,
                                    'Scenario': scenario_display, 'Change': change_display, 
                                    'Change %': f"{change_pct:+.2f}%"
                                })
                        
                        st.dataframe(pd.DataFrame(comparison_data), width='stretch', hide_index=True)
            
            with comp_tab2:
                st.markdown("**Regional Financial Impact Summary**")
                st.caption(f"💱 All values in {sym}")
                
                cols2 = st.columns(len(active_countries))
                
                for i, country in enumerate(active_countries):
                    with cols2[i]:
                        st.markdown(f"#### 📍 {country} Impact")
                        
                        c_base_df = filtered_df[filtered_df['Country'] == country]
                        c_scen_df = st.session_state.goal_seek_adjusted_df[st.session_state.goal_seek_adjusted_df['Country'] == country]
                        
                        c_base_metrics = calculate_metrics(c_base_df, st.session_state.opex_rate)
                        c_scen_metrics = calculate_metrics(c_scen_df, st.session_state.opex_rate)
                        impact_metrics = calculate_impact_metrics(c_base_metrics, c_scen_metrics)
                        
                        impact_data = []
                        for metric_key in ['Total Revenue (€)', 'Total COGS (€)', 'Total Gross Profit (€)', 'EBIT (€)']:
                            if metric_key in impact_metrics:
                                impact = impact_metrics[metric_key]
                                impact_data.append({
                                    'Metric': metric_key.replace(' (€)', ''),
                                    'Baseline': impact['baseline'], 'Scenario': impact['scenario']
                                })
                        
                        # Localized Chart
                        impact_df = pd.DataFrame(impact_data)
                        fig_impact = go.Figure(data=[
                            go.Bar(name='Baseline', x=impact_df['Metric'], y=impact_df['Baseline'] * rate, marker_color='#8e8e93'),
                            go.Bar(name='Scenario', x=impact_df['Metric'], y=impact_df['Scenario'] * rate, marker_color='#0071e3')
                        ])
                        fig_impact.update_layout(barmode='group', yaxis_title=f"Value ({sym})", height=320, margin=dict(t=30, b=0, l=0, r=0))
                        st.plotly_chart(fig_impact, width='stretch')
                        
                        # Localized Summary Metrics
                        sum_c1, sum_c2, sum_c3 = st.columns(3)
                        revenue_change = c_scen_metrics.get('Total Revenue (€)', 0) - c_base_metrics.get('Total Revenue (€)', 0)
                        profit_change = c_scen_metrics.get('Total Gross Profit (€)', 0) - c_base_metrics.get('Total Gross Profit (€)', 0)
                        ebit_change = c_scen_metrics.get('EBIT (€)', 0) - c_base_metrics.get('EBIT (€)', 0)
                        
                        with sum_c1: st.metric("Rev Impact", f"{sym}{revenue_change * rate:,.0f}", f"{(revenue_change / c_base_metrics.get('Total Revenue (€)', 1) * 100):+.1f}%" if c_base_metrics.get('Total Revenue (€)', 0) > 0 else "N/A")
                        with sum_c2: st.metric("Profit Impact", f"{sym}{profit_change * rate:,.0f}", f"{(profit_change / c_base_metrics.get('Total Gross Profit (€)', 1) * 100):+.1f}%" if c_base_metrics.get('Total Gross Profit (€)', 0) > 0 else "N/A")
                        with sum_c3: st.metric("EBIT Impact", f"{sym}{ebit_change * rate:,.0f}", f"{(ebit_change / c_base_metrics.get('EBIT (€)', 1) * 100):+.1f}%" if c_base_metrics.get('EBIT (€)', 0) > 0 else "N/A")

            with comp_tab3:
                st.markdown("**Product-Level Impact by Region**")
                st.caption(f"💱 All values in {sym}")
                
                cols3 = st.columns(len(active_countries))
                
                for i, country in enumerate(active_countries):
                    with cols3[i]:
                        st.markdown(f"#### 📍 {country} Products")
                        
                        c_base_df = filtered_df[filtered_df['Country'] == country]
                        c_scen_df = st.session_state.goal_seek_adjusted_df[st.session_state.goal_seek_adjusted_df['Country'] == country]
                        
                        baseline_product = c_base_df.groupby('Product').agg({
                            'Sales Units': 'sum', 'Total Revenue (€)': 'sum', 'Total Cost (€)': 'sum',
                            'Gross Profit (€)': 'sum', 'Selling Price (€)': 'first', 'Unit Gross Margin %': 'first'
                        }).reset_index()
                        
                        scenario_product = c_scen_df.groupby('Product').agg({
                            'Sales Units': 'sum', 'Total Revenue (€)': 'sum', 'Total Cost (€)': 'sum',
                            'Gross Profit (€)': 'sum', 'Selling Price (€)': 'first', 'Unit Gross Margin %': 'first'
                        }).reset_index()
                        
                        product_comparison = []
                        for product in baseline_product['Product'].unique():
                            if product in scenario_product['Product'].values:
                                baseline_prod = baseline_product[baseline_product['Product'] == product].iloc[0]
                                scenario_prod = scenario_product[scenario_product['Product'] == product].iloc[0]
                                
                                rev_change = (scenario_prod['Total Revenue (€)'] - baseline_prod['Total Revenue (€)']) * rate
                                profit_change = (scenario_prod['Gross Profit (€)'] - baseline_prod['Gross Profit (€)']) * rate
                                volume_change = scenario_prod['Sales Units'] - baseline_prod['Sales Units']
                                new_price = scenario_prod['Selling Price (€)'] * rate
                                
                                product_comparison.append({
                                    'Product': product, 'New Price': f"{sym}{new_price:,.2f}",
                                    'Vol. Change': f"{volume_change:+,.0f}", 'Rev Impact': f"{sym}{rev_change:,.0f}",
                                    'New Margin': f"{scenario_prod['Unit Gross Margin %']:.1f}%"
                                })
                                
                        st.dataframe(pd.DataFrame(product_comparison), width='stretch', hide_index=True)

            with comp_tab4:
                st.markdown("**Regional Risk Assessment**")
                
                cols4 = st.columns(len(active_countries))
                
                for i, country in enumerate(active_countries):
                    with cols4[i]:
                        st.markdown(f"#### 📍 {country} Risk Profile")
                        
                        c_base_df = filtered_df[filtered_df['Country'] == country]
                        c_scen_df = st.session_state.goal_seek_adjusted_df[st.session_state.goal_seek_adjusted_df['Country'] == country]
                        
                        # Compute local % changes specifically for the adjusted variable
                        if adjustment_variable == "Selling Price":
                            old_val = c_base_df['Selling Price (€)'].mean()
                            new_val = c_scen_df['Selling Price (€)'].mean()
                        elif adjustment_variable == "Sales Volume":
                            old_val = c_base_df['Sales Units'].mean()
                            new_val = c_scen_df['Sales Units'].mean()
                        elif adjustment_variable == "Material Costs":
                            old_val = c_base_df['Unit Material Cost (€)'].mean()
                            new_val = c_scen_df['Unit Material Cost (€)'].mean()
                        else:
                            old_val = result.original_value
                            new_val = result.new_value
                        
                        local_pct_change = ((new_val - old_val) / old_val * 100) if old_val != 0 else 0
                        
                        if local_pct_change == 0:
                            st.success("🟢 No localized adjustments detected. Existing strategy remains active.", icon="✅")
                        else:
                            if adjustment_variable == "Selling Price":
                                price_increase_pct = abs(local_pct_change)
                                if price_increase_pct > 20: st.warning(f"🔴 **High Risk**: {price_increase_pct:.1f}% local price shift is aggressive and may trigger market backlash.", icon="⚠️")
                                elif price_increase_pct > 10: st.info(f"🟡 **Medium Risk**: {price_increase_pct:.1f}% local price shift is noticeable.", icon="⚡")
                                else: st.success(f"🟢 **Low Risk**: {price_increase_pct:.1f}% local price shift is manageable.", icon="✅")
                            
                            elif adjustment_variable == "Sales Volume":
                                vol_increase_pct = abs(local_pct_change)
                                if vol_increase_pct > 30: st.warning(f"🔴 **High Risk**: {vol_increase_pct:.1f}% local volume surge requires massive supply chain capabilities.", icon="⚠️")
                                elif vol_increase_pct > 15: st.info(f"🟡 **Medium Risk**: {vol_increase_pct:.1f}% local volume growth is ambitious.", icon="⚡")
                                else: st.success(f"🟢 **Low Risk**: {vol_increase_pct:.1f}% local volume shift is structurally achievable.", icon="✅")
                            
                            else:
                                st.info(f"⚙️ **Operational Shift**: {adjustment_variable} changed by {local_pct_change:+.1f}% in this region.", icon="ℹ️")

st.markdown("---")

# ==========================================
# 7. EXECUTIVE INTELLIGENCE & STRATEGIC INSIGHTS
# ==========================================
st.subheader("Executive Dashboard - Business Performance & Strategic Insights")

try:
    # Calculate comprehensive financial metrics
    prod_revs = filtered_df.groupby('Product')['Total Revenue (€)'].sum()
    top_prod = prod_revs.idxmax()
    top_prod_pct = (prod_revs.max() / total_revenue) * 100
    
    prod_margins = filtered_df.groupby('Product').apply(lambda x: x['Gross Profit (€)'].sum() / x['Total Revenue (€)'].sum() * 100 if x['Total Revenue (€)'].sum()>0 else 0)
    best_margin_prod = prod_margins.idxmax()
    worst_margin_prod = prod_margins.idxmin()
    best_margin_val = prod_margins.max()
    worst_margin_val = prod_margins.min()
    
    # Cost analysis
    total_mat_spend = filtered_df['Total Material Cost (€)'].sum()
    total_labor_spend = filtered_df['Total Labor Cost (€)'].sum()
    mat_pct = (total_mat_spend / total_prod_spend) * 100 if total_prod_spend > 0 else 0
    lab_pct = 100 - mat_pct
    
    # Volume and inventory metrics
    total_prod_units = filtered_df['Production Units'].sum()
    latest_month = [m for m in months if m in selected_months][-1]
    trapped_capital = filtered_df[filtered_df['Month'] == latest_month]['Ending Inv Value (€)'].sum()
    
    # Risk and sensitivity analysis
    cogs_spike_impact = (total_mat_spend * 0.10)
    margin_erosion = (cogs_spike_impact / total_revenue) * 100
    
    # EBIT and profitability ratios
    opex_total = total_revenue * (st.session_state.opex_rate / 100)
    ebit_total = total_profit - opex_total
    ebit_margin_pct = (ebit_total / total_revenue * 100) if total_revenue > 0 else 0
    roa_proxy = (ebit_total / total_prod_spend * 100) if total_prod_spend > 0 else 0
    
    # Product and country analysis
    prod_by_country = filtered_df.groupby(['Product', 'Country'])['Total Revenue (€)'].sum().reset_index()
    prod_by_country['Revenue Pct'] = (prod_by_country['Total Revenue (€)'] / total_revenue * 100)
    
    st.markdown("""
    <div class="report-box">
        <h3>Comprehensive Financial Overview & Performance Analysis</h3>
        <p>Strategic insights for C-suite decision-making based on current business model and market positioning.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Financial Metrics
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric("Total Revenue", f"{sym}{(total_revenue*rate):,.0f}", f"Gross margin: {gross_margin:.1f}%")
    with kpi_col2:
        st.metric("Operating Profit (EBIT)", f"{sym}{(ebit_total*rate):,.0f}", f"EBIT margin: {ebit_margin_pct:.1f}%")
    with kpi_col3:
        st.metric("Manufacturing Spend", f"{sym}{(total_prod_spend*rate):,.0f}", f"ROA: {roa_proxy:.1f}%")
    with kpi_col4:
        st.metric("Working Capital (Inventory)", f"{sym}{(trapped_capital*rate):,.0f}", f"Capital intensity")
    
    st.markdown("---")
    
    # Section 1: Revenue Concentration & Mix Analysis
    with st.expander("**Section 1: Revenue Concentration & Product Mix**", expanded=False):
        col_rev1, col_rev2 = st.columns([1, 1])
        
        with col_rev1:
            st.markdown(f"""
            **Revenue Anchors:**
            - **Primary Driver:** {top_prod} generates **{top_prod_pct:.1f}%** of total revenue
            - **Revenue Concentration Risk:** {'🟢 Low Risk (well diversified)' if top_prod_pct < 40 else '🟡 Medium Risk' if top_prod_pct < 50 else '🔴 High Risk (over-concentrated)'}
            
            **Recommendation:**
            - Monitor {top_prod} demand closely as it's critical to overall business stability
            - Invest in growth of secondary products to reduce concentration risk
            """)
        
        with col_rev2:
            # Revenue by product pie chart
            prod_rev_data = filtered_df.groupby('Product')['Total Revenue (€)'].sum() * rate
            fig_pie = px.pie(
                values=prod_rev_data.values,
                names=prod_rev_data.index,
                title="Revenue Mix by Product",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, width='stretch')
    
    # Section 2: Profitability Spectrum
    with st.expander("**Section 2: Profitability Spectrum & Pricing Power**", expanded=False):
        col_prof1, col_prof2 = st.columns([1, 1])
        
        with col_prof1:
            st.markdown(f"""
            **Margin Leaders & Laggards:**
            - **Highest Margin:** {best_margin_prod} at **{best_margin_val:.1f}%** gross margin
              - Indicates strong pricing power and/or lean manufacturing
              - Opportunity: Use as flagship for brand positioning
            
            - **Lowest Margin:** {worst_margin_prod} at **{worst_margin_val:.1f}%** gross margin
              - Margin spread: **{best_margin_val - worst_margin_val:.1f}%** between best and worst
              - Vulnerability: Highly exposed to cost inflation and pricing pressure
            
            **Strategic Actions:**
            1. For {best_margin_prod}: Premium positioning, selective distribution
            2. For {worst_margin_prod}: Cost reduction initiatives, volume growth strategy
            """)
        
        with col_prof2:
            # Margin comparison chart
            margin_data = pd.DataFrame({
                'Product': prod_margins.index,
                'Gross Margin %': prod_margins.values
            }).sort_values('Gross Margin %', ascending=True)
            
            fig_margin = px.bar(
                margin_data,
                x='Gross Margin %',
                y='Product',
                orientation='h',
                color='Gross Margin %',
                color_continuous_scale='RdYlGn',
                title="Gross Margin by Product",
                labels={'Gross Margin %': 'Margin (%)'}
            )
            fig_margin.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_margin, width='stretch')
    
    # Section 3: Cost Structure & Supply Chain
    with st.expander("**Section 3: Cost Structure & Supply Chain Efficiency**", expanded=False):
        col_cost1, col_cost2 = st.columns([1, 1])
        
        with col_cost1:
            st.markdown(f"""
            **Manufacturing Cost Breakdown:**
            - **Materials (COGS):** {mat_pct:.1f}% → {sym}{(total_mat_spend*rate):,.0f}
              - Largest cost lever for optimization
            - **Direct Labor:** {lab_pct:.1f}% → {sym}{(total_labor_spend*rate):,.0f}
              - Fixed component; scale to reduce per-unit cost
            
            **Supply Chain Risk Assessment:**
            - 10% material cost spike = **{sym}{(cogs_spike_impact*rate):,.0f}** profit erosion
            - Margin impact: **{margin_erosion:.1f}%** margin compression
            
            **Risk Mitigation Strategies:**
            1. Supplier diversification across 3+ vendors
            2. Long-term fixed-price contracts for {worst_margin_prod}
            3. Value engineering: Design cost optimization
            4. Vertical integration assessment for high-volume components
            """)
        
        with col_cost2:
            # Cost structure pie
            cost_breakdown = pd.DataFrame({
                'Category': ['Materials', 'Labor', 'Overhead'],
                'Amount': [total_mat_spend, total_labor_spend, total_prod_spend - total_mat_spend - total_labor_spend]
            })
            cost_breakdown = cost_breakdown[cost_breakdown['Amount'] > 0]
            fig_cost_pie = px.pie(
                cost_breakdown,
                values='Amount',
                names='Category',
                title="Manufacturing Cost Breakdown",
                color_discrete_map={'Materials': '#8e8e93', 'Labor': '#ff9f0a', 'Overhead': '#0071e3'}
            )
            fig_cost_pie.update_layout(height=300)
            st.plotly_chart(fig_cost_pie, width='stretch')
    
    # Section 4: Working Capital & Liquidity
    with st.expander("**Section 4: Working Capital Management & Liquidity**", expanded=False):
        col_wc1, col_wc2 = st.columns([1, 1])
        
        with col_wc1:
            inventory_days = (trapped_capital / total_prod_spend * 30) if total_prod_spend > 0 else 0
            inventory_turnover = (total_prod_spend / trapped_capital) if trapped_capital > 0 else 0
            
            st.markdown(f"""
            **Inventory Position (End of {latest_month}):**
            - **Trapped Capital:** {sym}{(trapped_capital*rate):,.0f}
            - **Days Inventory Outstanding:** ~{inventory_days:.0f} days
            - **Inventory Turnover Ratio:** {inventory_turnover:.2f}x per period
            
            **Working Capital Health:**
            - Inventory represents {(trapped_capital/total_prod_spend*100):.1f}% of total production spend
            - Buffer inventory ensures service levels but ties up cash
            
            **Optimization Opportunities:**
            1. **Inventory Reduction:** Each 10% reduction → {sym}{(trapped_capital*rate*0.1):,.0f} cash freed
            2. **Demand Forecasting:** Reduce safety stock through better prediction
            3. **Supply Chain Agility:** Faster replenishment = lower buffer levels
            4. **Just-in-Time (JIT):** Evaluate for high-volume, stable-demand products
            """)
        
        with col_wc2:
            # Working capital trend
            wc_by_month = filtered_df.groupby('Month')[['Ending Inv Value (€)', 'Production Spend (€)']].sum().reset_index()
            wc_by_month['Month'] = pd.Categorical(wc_by_month['Month'], categories=months, ordered=True)
            wc_by_month = wc_by_month.sort_values('Month')
            wc_by_month = wc_by_month[wc_by_month['Month'].isin(selected_months)]
            
            fig_wc = px.area(
                wc_by_month,
                x='Month',
                y=['Ending Inv Value (€)', 'Production Spend (€)'],
                labels={'value': f'Value ({sym})', 'variable': 'Metric'},
                title="Working Capital Trend",
                color_discrete_map={'Ending Inv Value (€)': '#0071e3', 'Production Spend (€)': '#8e8e93'}
            )
            fig_wc.update_layout(height=300, hovermode='x unified')
            st.plotly_chart(fig_wc, width='stretch')
    
    # Section 5: Operating Leverage & Profitability
    with st.expander("**Section 5: Operating Leverage & EBIT Analysis**", expanded=False):
        col_ebit1, col_ebit2 = st.columns([1, 1])
        
        with col_ebit1:
            opex_pct_revenue = (opex_total / total_revenue * 100) if total_revenue > 0 else 0
            
            st.markdown(f"""
            **Profitability Cascade:**
            1. **Gross Revenue:** {sym}{(total_revenue*rate):,.0f}
            2. **Less: COGS:** -{sym}{(total_prod_spend*rate):,.0f}
            3. **= Gross Profit:** {sym}{(total_profit*rate):,.0f} ({gross_margin:.1f}% margin)
            4. **Less: OPEX (SG&A+R&D):** -{sym}{(opex_total*rate):,.0f} ({opex_pct_revenue:.1f}% of revenue)
            5. **= Operating Profit (EBIT):** {sym}{(ebit_total*rate):,.0f} ({ebit_margin_pct:.1f}% margin)
            
            **Operating Efficiency Metrics:**
            - OPEX Efficiency: {opex_pct_revenue:.1f}% of revenue (target: <15%)
            - EBIT/Gross Profit: {(ebit_total/total_profit*100):.1f}% (operating leverage indicator)
            - Manufacturing ROI: {roa_proxy:.1f}% (EBIT ÷ Production Spend)
            
            **Key Leverage Points:**
            - Every 1% gross margin improvement = {sym}{(total_revenue/100*rate):,.0f} profit gain
            - Every 1% OPEX reduction = {sym}{(opex_total/100*rate):,.0f} profit gain
            """)
        
        with col_ebit2:
            # Create cleanly formatted text labels for the chart bars & hover
            text_labels = [
                f"{sym}{(total_revenue*rate)/1000000:,.1f}M",
                f"-{sym}{(total_prod_spend*rate)/1000000:,.1f}M",
                f"{sym}{(total_profit*rate)/1000000:,.1f}M",
                f"-{sym}{(opex_total*rate)/1000000:,.1f}M",
                f"{sym}{(ebit_total*rate)/1000000:,.1f}M"
            ]

            # Waterfall chart for profitability
            fig_waterfall = go.Figure(data=[go.Waterfall(
                name="Profitability",
                orientation="v",
                measure=["relative", "relative", "total", "relative", "total"], # THE FIX: Tells Plotly which columns are sums!
                x=['Revenue', 'COGS', 'Gross Profit', 'OPEX', 'EBIT'],
                textposition="outside",
                text=text_labels,
                y=[total_revenue*rate, -total_prod_spend*rate, total_profit*rate, -opex_total*rate, ebit_total*rate],
                connector={"line": {"color": "rgba(0, 113, 227, 0.5)"}},
                decreasing={"marker": {"color": "#ff453a"}},
                increasing={"marker": {"color": "#32d74b"}},
                totals={"marker": {"color": "#0071e3"}},
                hovertemplate="<b>%{x}</b><br>Value: %{text}<extra></extra>" # THE FIX: Cleans up the hover tooltip
            )])
            
            fig_waterfall.update_layout(
                height=300, 
                title="Profitability Waterfall", 
                margin=dict(b=0),
                yaxis=dict(showticklabels=False) # Hide the messy y-axis numbers since we have labels directly on the bars
            )
            st.plotly_chart(fig_waterfall, width='stretch')
    
    st.markdown("---")
    
    # Executive Summary Box
    st.markdown("""
    <div class="report-box">
        <h4>Executive Summary & Strategic Priorities</h4>
        <ol>
            <li><b>Revenue Growth:</b> Focus on diversifying away from {0} concentration; develop secondary products</li>
            <li><b>Margin Defense:</b> Protect {1} gross margin through cost management and supply chain optimization</li>
            <li><b>Cost Management:</b> Target 10% reduction in material costs through supplier negotiation and design optimization</li>
            <li><b>Working Capital:</b> Reduce inventory by 15% to free {2} in cash while maintaining service levels</li>
            <li><b>EBIT Growth:</b> Drive operating profit growth through volume scaling and operational efficiency</li>
        </ol>
    </div>
    """.format(top_prod, best_margin_prod, f"{sym}{(trapped_capital*rate*0.15):,.0f}"), unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"Error generating executive dashboard: {str(e)}")
    st.write("*(Please select more data to generate comprehensive insights)*")

st.markdown("---")

# ==========================================
# 8. FINANCIAL PERFORMANCE & OPERATIONAL ANALYTICS
# ==========================================
st.subheader("Financial Analytics & Operational Dashboards")

tab_v1, tab_v2, tab_v3, tab_v4, tab_v5, tab_v6, tab_v7 = st.tabs([
    "Demand-Supply", "Revenue Analysis", "Cost Structure", 
    "Unit Economics", "Financial Statements", "Scenario Comparison",
    "Smart Query Engine" 
])

with tab_v1:
    st.markdown("### Demand-Supply Reconciliation Analysis")
    st.caption("Monitor inventory alignment between sales forecast and production capacity")
    sp_df = filtered_df.groupby('Product')[['Sales Units', 'Production Units']].sum().reset_index()
    fig_sp = go.Figure(data=[
        go.Bar(name='Sales Forecast', x=sp_df['Product'], y=sp_df['Sales Units'], marker_color='#0071e3'),
        go.Bar(name='Production Capacity', x=sp_df['Product'], y=sp_df['Production Units'], marker_color='#8e8e93')
    ])
    fig_sp.update_layout(barmode='group', yaxis_title="Volume (Units)", title="<b>Sales vs. Production Volume Alignment</b>")
    st.plotly_chart(fig_sp, width='stretch')

with tab_v2:
    st.markdown("### Revenue Performance & Market Trends")
    st.caption("Track top-line growth by product line and geographic market")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        rev_df = filtered_df.groupby(['Product', 'Country'])['Total Revenue (€)'].sum().reset_index()
        rev_df['Converted Revenue'] = rev_df['Total Revenue (€)'] * rate
        fig_rev = px.bar(rev_df, x="Product", y="Converted Revenue", color="Country", barmode="group", text_auto='.2s', color_discrete_sequence=['#0071e3', '#333336'])
        fig_rev.update_layout(xaxis_title="Product", yaxis_title=f"Revenue ({sym})", title="<b>Revenue by Product & Territory</b>")
        st.plotly_chart(fig_rev, width='stretch')
    with chart_col2:
        trend_df = filtered_df.groupby(['Month', 'Product'])['Sales Units'].sum().reset_index()
        trend_df['Month'] = pd.Categorical(trend_df['Month'], categories=months, ordered=True)
        trend_df = trend_df.sort_values('Month')
        fig_trend = px.line(trend_df, x="Month", y="Sales Units", color="Product", markers=True, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_trend.update_layout(title="<b>Volume Trend Analysis</b>", yaxis_title="Units Sold")
        st.plotly_chart(fig_trend, width='stretch')

with tab_v3:
    st.markdown("### Cost of Goods Sold (COGS) Composition")
    st.caption("Analyze material and labor cost drivers across product portfolio")
    cost_df = filtered_df.groupby('Product')[['Total Material Cost (€)', 'Total Labor Cost (€)']].sum().reset_index()
    fig_cost = go.Figure(data=[
        go.Bar(name='Material Costs', x=cost_df['Product'], y=cost_df['Total Material Cost (€)'] * rate, marker_color='#8e8e93'),
        go.Bar(name='Direct Labor', x=cost_df['Product'], y=cost_df['Total Labor Cost (€)'] * rate, marker_color='#ff9f0a')
    ])
    fig_cost.update_layout(barmode='stack', yaxis_title=f"COGS ({sym})", title="<b>Cost Structure by Product</b>")
    st.plotly_chart(fig_cost, width='stretch')

with tab_v4:
    st.markdown("### Unit Economics & Pricing Strategy")
    st.caption("Evaluate per-unit profitability and pricing competitiveness (bubble size = margin %)")
    unit_df = filtered_df[['Product', 'Country', 'Total Unit Cost (€)', 'Selling Price (€)', 'Unit Gross Margin %']].drop_duplicates()
    unit_df['Converted Price'] = unit_df['Selling Price (€)'] * rate
    unit_df['Converted Cost'] = unit_df['Total Unit Cost (€)'] * rate
    fig_scatter = px.scatter(
        unit_df, x="Converted Cost", y="Converted Price", color="Product", symbol="Country",
        size="Unit Gross Margin %", hover_data=['Unit Gross Margin %'], text="Product",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(xaxis_title=f"Unit Cost ({sym})", yaxis_title=f"Selling Price ({sym})", title="<b>Unit Economics Positioning</b>")
    st.plotly_chart(fig_scatter, width='stretch')

with tab_v5:
    st.markdown("## Consolidated Pro-Forma Financial Statements")
    st.markdown("""
    **What you're seeing:** A complete month-by-month financial model including:
    - **Volume Metrics:** Sales forecast and production planning
    - **Income Statement:** Revenue, COGS, gross profit, operating expenses, and EBIT
    - **Working Capital:** Manufacturing cash flow and inventory investment
    """)
    
    mb_df = filtered_df.groupby('Month', as_index=False).agg({
        'Sales Units': 'sum', 'Production Units': 'sum', 'Total Revenue (€)': 'sum', 'Total Cost (€)': 'sum', 
        'Gross Profit (€)': 'sum', 'Production Spend (€)': 'sum', 'Ending Inv Value (€)': 'sum'
    })
    mb_df['OPEX (€)'] = mb_df['Total Revenue (€)'] * (st.session_state.opex_rate / 100)
    mb_df['EBIT (€)'] = mb_df['Gross Profit (€)'] - mb_df['OPEX (€)']
    mb_df['Gross Margin %'] = (mb_df['Gross Profit (€)'] / mb_df['Total Revenue (€)'] * 100).round(2)
    mb_df['EBIT Margin %'] = (mb_df['EBIT (€)'] / mb_df['Total Revenue (€)'] * 100).round(2)
    mb_df['Month'] = pd.Categorical(mb_df['Month'], categories=months, ordered=True)
    mb_df = mb_df.sort_values('Month')
    
    # Section Headers for better readability
    metrics = [
        "━━ DEMAND & CAPACITY PLANNING ━━",
        "   Sales Forecast (Units)", 
        "   Production Volume (Units)",
        "   Production Variance (Units)",
        "",
        "━━ REVENUE & COST OF SALES ━━", 
        f"   Gross Revenue ({sym})", 
        f"   Cost of Goods Sold ({sym})",
        f"   Gross Profit ({sym})", 
        "   Gross Margin (%)",
        "",
        "━━ OPERATING PROFITABILITY ━━",
        f"   Operating Expenses - OPEX ({sym})",
        f"   Operating Profit - EBIT ({sym})", 
        "   EBIT Margin (%)",
        "",
        "━━ WORKING CAPITAL & LIQUIDITY ━━",
        f"   Production Cash Outflow ({sym})",
        f"   Inventory Investment ({sym})",
        f"   Inventory Turnover (Days)",
    ]
    
    # Build data for each month
    mb_data = {}
    for m in months:
        if m in selected_months:
            m_data = mb_df[mb_df['Month'] == m].iloc[0] if not mb_df[mb_df['Month'] == m].empty else None
            if m_data is not None:
                prod_var = m_data['Production Units'] - m_data['Sales Units']
                inv_turnover = (m_data['Ending Inv Value (€)'] / m_data['Total Cost (€)'] * 30) if m_data['Total Cost (€)'] > 0 else 0
                mb_data[m] = [
                    "",
                    f"{m_data['Sales Units']:,.0f}", 
                    f"{m_data['Production Units']:,.0f}",
                    f"{prod_var:+,.0f}",
                    "",
                    "", 
                    f"{sym}{(m_data['Total Revenue (€)']*rate):,.0f}", 
                    f"{sym}{(m_data['Total Cost (€)']*rate):,.0f}",
                    f"{sym}{(m_data['Gross Profit (€)']*rate):,.0f}", 
                    f"{m_data['Gross Margin %']:.1f}%",
                    "",
                    "",
                    f"{sym}{(m_data['OPEX (€)']*rate):,.0f}",
                    f"{sym}{(m_data['EBIT (€)']*rate):,.0f}", 
                    f"{m_data['EBIT Margin %']:.1f}%",
                    "",
                    "",
                    f"{sym}{(m_data['Production Spend (€)']*rate):,.0f}",
                    f"{sym}{(m_data['Ending Inv Value (€)']*rate):,.0f}",
                    f"{inv_turnover:.0f}",
                ]
    
    # Consolidated totals
    total_rev_mb = mb_df['Total Revenue (€)'].sum()
    total_units = mb_df['Sales Units'].sum()
    total_prod_units = mb_df['Production Units'].sum()
    total_prod_var = total_prod_units - total_units
    avg_inv_turnover = (mb_df['Ending Inv Value (€)'].sum() / mb_df['Total Cost (€)'].sum() * 30) if mb_df['Total Cost (€)'].sum() > 0 else 0
    
    mb_data["CONSOLIDATED TOTAL"] = [
        "",
        f"{total_units:,.0f}", 
        f"{total_prod_units:,.0f}",
        f"{total_prod_var:+,.0f}",
        "",
        "", 
        f"{sym}{(total_rev_mb*rate):,.0f}", 
        f"{sym}{(mb_df['Total Cost (€)'].sum()*rate):,.0f}",
        f"{sym}{(mb_df['Gross Profit (€)'].sum()*rate):,.0f}", 
        f"{(mb_df['Gross Profit (€)'].sum() / total_rev_mb * 100):.1f}%",
        "",
        "",
        f"{sym}{(mb_df['OPEX (€)'].sum()*rate):,.0f}",
        f"{sym}{(mb_df['EBIT (€)'].sum()*rate):,.0f}", 
        f"{(mb_df['EBIT (€)'].sum() / total_rev_mb * 100):.1f}%",
        "",
        "",
        f"{sym}{(mb_df['Production Spend (€)'].sum()*rate):,.0f}",
        f"{sym}{(mb_df['Ending Inv Value (€)'].sum()*rate):,.0f}",
        f"{avg_inv_turnover:.0f}",
    ]
    
    master_budget_df = pd.DataFrame(mb_data, index=metrics)
    cols = ["Metric"] + list(master_budget_df.columns)
    cell_values = [master_budget_df.index] + [master_budget_df[c] for c in master_budget_df.columns]
    
    # Color scheme with improved contrast
    row_header_color = "#1a1a1c"
    row_data_color = "#0d1117"
    line_color = "#30363d"
    header_font_color = "#ffffff"
    data_font_color = "#e6edf3"  # Lighter gray for better readability
    
    # Intelligent row coloring
    row_colors = []
    for idx in master_budget_df.index:
        if "━━" in idx:
            row_colors.append("#0d3b66")  # Darker blue for section headers
        elif "EBIT" in idx or "Gross Profit" in idx or "Gross Margin" in idx:
            row_colors.append("#1f6feb")  # Blue for important metrics
        elif "CONSOLIDATED" in idx:
            row_colors.append("#238636")  # Green for totals
        elif idx.strip() == "":
            row_colors.append(row_data_color)
        else:
            row_colors.append(row_data_color)
            
    fig_mb = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{c}</b>" for c in cols], 
            fill_color=row_header_color, 
            line_color=line_color, 
            font=dict(color=header_font_color, size=13, family="Arial"), 
            align='left', 
            height=35
        ),
        cells=dict(
            values=cell_values, 
            fill_color=[row_colors]*len(cols), 
            line_color=line_color, 
            align=['left'] + ['right']*(len(cols)-1), 
            font=dict(color=data_font_color, size=11),
            height=28
        )
    )])
    fig_mb.update_layout(
        height=700, 
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_mb, width='stretch')
    
    # Key insights from the budget
    st.markdown("### Financial Health Indicators")
    col_insight1, col_insight2, col_insight3, col_insight4 = st.columns(4)
    
    avg_gross_margin = (mb_df['Gross Profit (€)'].sum() / total_rev_mb * 100) if total_rev_mb > 0 else 0
    avg_ebit_margin = (mb_df['EBIT (€)'].sum() / total_rev_mb * 100) if total_rev_mb > 0 else 0
    total_opex = mb_df['OPEX (€)'].sum() * rate
    total_ebit = mb_df['EBIT (€)'].sum() * rate
    
    with col_insight1:
        st.metric("Period Avg Gross Margin", f"{avg_gross_margin:.1f}%", "Production efficiency")
    with col_insight2:
        st.metric("Period Avg EBIT Margin", f"{avg_ebit_margin:.1f}%", "Operating leverage")
    with col_insight3:
        st.metric("Total OPEX", f"{sym}{total_opex:,.0f}", "SG&A + R&D spend")
    with col_insight4:
        st.metric("Operating Profit (EBIT)", f"{sym}{total_ebit:,.0f}", f"Net operating earnings")

# REFINED: UNIFIED IMPACT REPORT & MULTI-SCENARIO TRACKER
# REFINED: UNIFIED IMPACT REPORT & MULTI-SCENARIO TRACKER (WITH CHARTS)
with tab_v6:
    st.markdown("### Scenario Comparison & Performance Tracking")
    st.markdown("Compare all saved scenarios at once. Track strategic performance metrics across different business models and market conditions.")

    scenarios_to_compare = st.session_state.scenarios.copy()
    scenarios_to_compare["Current (Unsaved) State"] = {
        'df': df, 'opex_rate': st.session_state.opex_rate, 'labor_rate': st.session_state.labor_rate,
        'inputs': {'prices': st.session_state.df_prices, 'sales_it': st.session_state.df_sales_it, 'sales_sw': st.session_state.df_sales_sw, 'materials': st.session_state.df_materials}
    }
    
    kpi_labels = ["Total Units Sold", f"Gross Revenue ({sym})", f"COGS ({sym})", f"Gross Profit ({sym})", "Gross Margin (%)", "OPEX %", f"EBIT ({sym})", "EBIT Margin (%)", f"Mfg Spend ({sym})"]
    comp_data = {}
    
    # NEW: A list to hold raw numbers for our charts
    numeric_chart_data = [] 
    
    for s_name, s_data in scenarios_to_compare.items():
        s_df = s_data['df']
        f_s_df = s_df[(s_df['Country'].isin(selected_countries)) & (s_df['Product'].isin(selected_products)) & (s_df['Month'].isin(selected_months))]
        if not f_s_df.empty:
            s_units = f_s_df['Sales Units'].sum()
            s_rev = f_s_df['Total Revenue (€)'].sum() * rate
            s_cogs = f_s_df['Total Cost (€)'].sum() * rate
            s_gp = f_s_df['Gross Profit (€)'].sum() * rate
            s_gpm = (s_gp / s_rev * 100) if s_rev > 0 else 0
            s_opex_rate = s_data['opex_rate']
            s_opex_cost = s_rev * (s_opex_rate / 100)
            s_ebit = s_gp - s_opex_cost
            s_ebit_m = (s_ebit / s_rev * 100) if s_rev > 0 else 0
            s_spend = f_s_df['Production Spend (€)'].sum() * rate
            
            # Formatted strings for the Data Table
            comp_data[s_name] = [
                f"{s_units:,.0f}", f"{s_rev/1000000:,.1f}M", f"{s_cogs/1000000:,.1f}M", f"{s_gp/1000000:,.1f}M", f"{s_gpm:.1f}%",
                f"{s_opex_rate:.1f}%", f"{s_ebit/1000000:,.1f}M", f"{s_ebit_m:.1f}%", f"{s_spend/1000000:,.1f}M"
            ]
            
            # Raw numbers for the Plotly Charts
            numeric_chart_data.append({
                'Scenario': s_name,
                f'Revenue ({sym})': s_rev,
                f'Gross Profit ({sym})': s_gp,
                f'EBIT ({sym})': s_ebit,
                f'Mfg Spend ({sym})': s_spend,
                'Gross Margin %': s_gpm,
                'EBIT Margin %': s_ebit_m
            })
            
    comp_df = pd.DataFrame(comp_data, index=kpi_labels).reset_index()
    comp_df.rename(columns={'index': 'KPI Metric'}, inplace=True)
    num_chart_df = pd.DataFrame(numeric_chart_data)
    
    # --- VISUAL COMPARISON CHARTS ---
    st.markdown("#### Scenario Visual Comparison")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Chart 1: Financial scale comparison (Revenue vs Profit vs Spend)
        fig_scale = go.Figure(data=[
            go.Bar(name='Revenue', x=num_chart_df['Scenario'], y=num_chart_df[f'Revenue ({sym})'], marker_color='#0071e3'),
            go.Bar(name='EBIT', x=num_chart_df['Scenario'], y=num_chart_df[f'EBIT ({sym})'], marker_color='#32d74b'),
            go.Bar(name='Mfg Spend', x=num_chart_df['Scenario'], y=num_chart_df[f'Mfg Spend ({sym})'], marker_color='#ff453a')
        ])
        fig_scale.update_layout(
            barmode='group', 
            title="<b>Financial Scale by Scenario</b>",
            yaxis_title=f"Value ({sym})",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_scale, width='stretch') # Native theme applied automatically!
        
    with chart_col2:
        # Chart 2: Margin Efficiency (Scatter plot of margins)
        fig_margin = go.Figure()
        fig_margin.add_trace(go.Scatter(
            x=num_chart_df['Scenario'], y=num_chart_df['Gross Margin %'], 
            mode='lines+markers+text', name='Gross Margin %',
            text=num_chart_df['Gross Margin %'].apply(lambda x: f"{x:.1f}%"),
            textposition="top center", marker=dict(size=10, color='#0071e3')
        ))
        fig_margin.add_trace(go.Scatter(
            x=num_chart_df['Scenario'], y=num_chart_df['EBIT Margin %'], 
            mode='lines+markers+text', name='EBIT Margin %',
            text=num_chart_df['EBIT Margin %'].apply(lambda x: f"{x:.1f}%"),
            textposition="bottom center", marker=dict(size=10, color='#32d74b')
        ))
        fig_margin.update_layout(
            title="<b>Efficiency & Margin Profile</b>",
            yaxis_title="Margin (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_margin, width='stretch') # Native theme applied automatically!

    # --- DATA TABLE & AUDIT ---
    st.markdown("#### The Global KPI Matrix")
    st.dataframe(comp_df, hide_index=True, width='stretch')

    st.markdown("#### Holistic Variance Report (vs Base Case)")
    
    # [The rest of your deep audit logic remains exactly the same below this line]
    base_inputs = st.session_state.scenarios['Base Case']
    base_ebit_val = float(comp_data['Base Case'][6].replace('M','').replace(',',''))
    b_rev_v = float(comp_data['Base Case'][1].replace('M','').replace(',','')) * 1000000
    b_gpm_v = float(comp_data['Base Case'][4].replace('%',''))
    b_spend_v = float(comp_data['Base Case'][8].replace('M','').replace(',','')) * 1000000
    
    for s_name, s_data in scenarios_to_compare.items():
        if s_name == 'Base Case': continue
        
        changes = []
        if base_inputs['opex_rate'] != s_data['opex_rate']:
            changes.append(f"Global OPEX adjusted from {base_inputs['opex_rate']}% to {s_data['opex_rate']}%")
        if base_inputs['labor_rate'] != s_data['labor_rate']:
            changes.append(f"Global Labor Rate modified from {sym}{base_inputs['labor_rate']} to {sym}{s_data['labor_rate']}")
            
        bp = base_inputs['inputs']['prices']
        cp = s_data['inputs']['prices']
        for i, row in bp.iterrows():
            prod = row['Product']
            for col in ['Italy Price (€)', 'Sweden Price (€)']:
                old_v, new_v = row[col], cp.loc[i, col]
                if old_v != new_v:
                    pct = ((new_v - old_v)/old_v)*100 if old_v else 0
                    changes.append(f"{prod} {col.replace(' (€)', '')} changed from {sym}{old_v*rate:,.0f} to {sym}{new_v*rate:,.0f} (<span class='badge-hl'>{pct:+.1f}%</span>)")

        for c_prefix in ['_it', '_sw']:
            b_vol = base_inputs['inputs'][f'sales{c_prefix}'].drop('Product', axis=1).sum(axis=1)
            c_vol = s_data['inputs'][f'sales{c_prefix}'].drop('Product', axis=1).sum(axis=1)
            for i, p_name in enumerate(products):
                old_v, new_v = b_vol[i], c_vol[i]
                if old_v != new_v:
                    c_name = "Italy" if c_prefix == "_it" else "Sweden"
                    pct = ((new_v - old_v)/old_v)*100 if old_v else 0
                    changes.append(f"{p_name} Volume in {c_name} changed from {old_v:,.0f} to {new_v:,.0f} units (<span class='badge-hl'>{pct:+.1f}%</span>)")

        bm = base_inputs['inputs']['materials']
        cm = s_data['inputs']['materials']
        for i, row in bm.iterrows():
            prod = row['Product']
            old_mat = row[mat_cols].sum()
            new_mat = cm.loc[i, mat_cols].sum()
            if old_mat != new_mat:
                pct = ((new_mat - old_mat)/old_mat)*100 if old_mat else 0
                changes.append(f"{prod} Material Cost changed from {sym}{old_mat*rate:,.1f} to {sym}{new_mat*rate:,.1f} (<span class='badge-hl'>{pct:+.1f}%</span>)")

        s_ebit_val = float(comp_data[s_name][6].replace('M','').replace(',',''))
        s_rev_v = float(comp_data[s_name][1].replace('M','').replace(',','')) * 1000000
        s_gpm_v = float(comp_data[s_name][4].replace('%',''))
        s_spend_v = float(comp_data[s_name][8].replace('M','').replace(',','')) * 1000000
        
        ebit_delta = s_ebit_val - base_ebit_val
        rev_delta = s_rev_v - b_rev_v
        spend_delta = s_spend_v - b_spend_v
        
        # Determine styling class
        rev_class = "val-pos" if rev_delta > 0 else "val-neg" if rev_delta < 0 else "val-neu"
        ebit_class = "val-pos" if ebit_delta > 0 else "val-neg" if ebit_delta < 0 else "val-neu"
        spend_class = "val-pos" if spend_delta < 0 else "val-neg" if spend_delta > 0 else "val-neu" # Spend lower = good

        with st.expander(f"Deep Audit: {s_name}", expanded=True):
            if not changes: st.write("No structural assumption changes detected versus the Base Case.")
            else:
                st.markdown(f"**Assumption Edits Logged:**")
                for c in changes: st.markdown(f"- {c}", unsafe_allow_html=True)
                
                st.markdown(f"""
                <table class='impact-table'>
                    <tr>
                        <th>Strategic Metric</th>
                        <th>Base Case</th>
                        <th>{s_name}</th>
                        <th>Absolute Impact</th>
                    </tr>
                    <tr>
                        <td>Gross Revenue</td>
                        <td>{sym}{b_rev_v/1000000:,.1f}M</td>
                        <td>{sym}{s_rev_v/1000000:,.1f}M</td>
                        <td class='{rev_class}'>{sym}{rev_delta/1000000:+.1f}M</td>
                    </tr>
                    <tr>
                        <td>Gross Margin</td>
                        <td>{b_gpm_v:.1f}%</td>
                        <td>{s_gpm_v:.1f}%</td>
                        <td class='{"val-pos" if s_gpm_v > b_gpm_v else "val-neg" if s_gpm_v < b_gpm_v else "val-neu"}'>{s_gpm_v - b_gpm_v:+.1f}%</td>
                    </tr>
                    <tr>
                        <td>Operating Profit (EBIT)</td>
                        <td>{sym}{base_ebit_val:,.1f}M</td>
                        <td>{sym}{s_ebit_val:,.1f}M</td>
                        <td class='{ebit_class}'>{sym}{ebit_delta:+.1f}M</td>
                    </tr>
                    <tr>
                        <td>Mfg Cash Trapped / Spend</td>
                        <td>{sym}{b_spend_v/1000000:,.1f}M</td>
                        <td>{sym}{s_spend_v/1000000:,.1f}M</td>
                        <td class='{spend_class}'>{sym}{spend_delta/1000000:+.1f}M</td>
                    </tr>
                </table>
                """, unsafe_allow_html=True)


# ==========================================
# NATURAL LANGUAGE QUERY ENGINE (NLQ)
# ==========================================
with tab_v7:
    st.markdown("### Natural Language Query Engine")
    st.caption("Build a sentence below to instantly query the database. Select multiple options in any field!")
    
    # Define standard options
    all_metrics = ["Gross Revenue", "Gross Profit", "Sales Units", "Production Spend", "Total COGS", "Ending Inventory Value", "Gross Margin %", "Avg Selling Price"]
    prod_opts = products
    country_opts = ["Italy", "Sweden"]
    month_opts = months
    scenario_list = list(st.session_state.scenarios.keys())

    # Helper function to compute metrics accurately (handling margins properly)
    def compute_metric(temp_df, m_name):
        if temp_df.empty: return 0
        if m_name == "Gross Revenue": return temp_df['Total Revenue (€)'].sum() * rate
        elif m_name == "Gross Profit": return temp_df['Gross Profit (€)'].sum() * rate
        elif m_name == "Sales Units": return temp_df['Sales Units'].sum()
        elif m_name == "Production Spend": return temp_df['Production Spend (€)'].sum() * rate
        elif m_name == "Total COGS": return temp_df['Total Cost (€)'].sum() * rate
        elif m_name == "Ending Inventory Value": return temp_df['Ending Inv Value (€)'].sum() * rate
        elif m_name == "Avg Selling Price": return temp_df['Selling Price (€)'].mean() * rate
        elif m_name == "Gross Margin %":
            rev = temp_df['Total Revenue (€)'].sum()
            prof = temp_df['Gross Profit (€)'].sum()
            return (prof / rev * 100) if rev > 0 else 0
            
    def format_nlq_val(val, m_name):
        if "%" in m_name: return f"{val:.1f}%"
        elif "Units" in m_name: return f"{val:,.0f}"
        else: return f"{sym}{val:,.0f}"

    
    st.markdown("<div class='nlq-container'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown("<div class='nlq-label'>I want to...</div>", unsafe_allow_html=True)
        # 🌟 REPLACED: "Find the highest/lowest" is now "Rank"
        action = st.selectbox("Action", ["Calculate", "Compare", "Compare scenarios", "Rank", "Analyze the trend of"], label_visibility="collapsed")
    
    with c2:
        # 🌟 REFINED: All actions now simply ask for the metrics
        st.markdown("<div class='nlq-label'>the metrics...</div>", unsafe_allow_html=True)
        metric = st.multiselect("Metric", all_metrics, default=["Gross Revenue", "Gross Profit"], label_visibility="collapsed")
            
    with c3:
        if action == "Calculate" or action == "Analyze the trend of":
            st.markdown("<div class='nlq-label'>for products...</div>", unsafe_allow_html=True)
            q_prod = st.multiselect("Prod", prod_opts, default=prod_opts, label_visibility="collapsed")
        elif action == "Compare":
            st.markdown("<div class='nlq-label'>split by...</div>", unsafe_allow_html=True)
            split_dim = st.selectbox("Dim", ["Products", "Countries", "Months"], label_visibility="collapsed")
        elif action == "Compare scenarios":
            st.markdown("<div class='nlq-label'>between scenario...</div>", unsafe_allow_html=True)
            scen_a = st.selectbox("Scenario A", scenario_list, index=0, label_visibility="collapsed")
        elif action == "Rank":
            st.markdown("<div class='nlq-label'>across...</div>", unsafe_allow_html=True)
            rank_dim = st.selectbox("Rank Dim", ["Products", "Months"], label_visibility="collapsed")

    with c4:
        if action == "Calculate":
            st.markdown("<div class='nlq-label'>in countries...</div>", unsafe_allow_html=True)
            q_country = st.multiselect("Country", country_opts, default=country_opts, label_visibility="collapsed")
        elif action == "Compare":
            st.markdown("<div class='nlq-label'>select items...</div>", unsafe_allow_html=True)
            if split_dim == "Products": items = st.multiselect("Items", products, default=products[:2], label_visibility="collapsed")
            elif split_dim == "Countries": items = st.multiselect("Items", ["Italy", "Sweden"], default=["Italy", "Sweden"], label_visibility="collapsed")
            elif split_dim == "Months": items = st.multiselect("Items", months, default=months[:3], label_visibility="collapsed")
        elif action == "Compare scenarios":
            st.markdown("<div class='nlq-label'>and scenario...</div>", unsafe_allow_html=True)
            default_idx = 1 if len(scenario_list) > 1 else 0
            scen_b = st.selectbox("Scenario B", scenario_list, index=default_idx, label_visibility="collapsed")
        elif action == "Rank":
            st.markdown("<div class='nlq-label'>&nbsp;</div>", unsafe_allow_html=True) # Spacer
        elif action == "Analyze the trend of":
            st.markdown("<div class='nlq-label'>in countries...</div>", unsafe_allow_html=True)
            q_country = st.multiselect("Country", country_opts, default=country_opts, label_visibility="collapsed")
            
    st.markdown("</div>", unsafe_allow_html=True)

    # Lingering filters based on selected action
    if action == "Calculate":
        q_month = st.multiselect("during timeframe...", month_opts, default=month_opts)
        
    elif action == "Compare":
        c5, c6 = st.columns(2)
        with c5: q_country = st.multiselect("Filtered by Country...", country_opts, default=country_opts) if split_dim != "Countries" else country_opts
        with c6: q_month = st.multiselect("Filtered by Timeframe...", month_opts, default=month_opts) if split_dim != "Months" else month_opts
        q_prod = st.multiselect("Filtered by Product...", prod_opts, default=prod_opts) if split_dim != "Products" else prod_opts
        
    elif action == "Compare scenarios":
        c5, c6, c7 = st.columns(3)
        with c5: q_country = st.multiselect("Filtered by Country...", country_opts, default=country_opts)
        with c6: q_month = st.multiselect("Filtered by Timeframe...", month_opts, default=month_opts)
        with c7: q_prod = st.multiselect("Filtered by Product...", prod_opts, default=prod_opts)
        
    elif action == "Rank":
        c5, c6, c7 = st.columns(3)
        with c5:
            st.markdown("<div class='nlq-label'>specifically from candidates...</div>", unsafe_allow_html=True)
            if rank_dim == "Products":
                rank_items = st.multiselect("Candidates", prod_opts, default=prod_opts, label_visibility="collapsed")
            else:
                rank_items = st.multiselect("Candidates", month_opts, default=month_opts, label_visibility="collapsed")
        with c6:
            st.markdown("<div class='nlq-label'>filtered by country...</div>", unsafe_allow_html=True)
            q_country = st.multiselect("Filtered by Country...", country_opts, default=country_opts, label_visibility="collapsed")
        with c7:
            if rank_dim == "Products":
                st.markdown("<div class='nlq-label'>filtered by timeframe...</div>", unsafe_allow_html=True)
                q_month = st.multiselect("Filtered by Timeframe...", month_opts, default=month_opts, label_visibility="collapsed")
            else:
                st.markdown("<div class='nlq-label'>filtered by product...</div>", unsafe_allow_html=True)
                q_prod = st.multiselect("Filtered by Product...", prod_opts, default=prod_opts, label_visibility="collapsed")

    st.markdown("---")
    
    # ================= ENGINE EXECUTION =================
    if st.button("Generate Insight", type="primary", width = 'stretch'):
        
        # Clean filtering function using Pandas .isin() directly
        def get_filtered_data(target_df, p_list, c_list, m_list):
            return target_df[
                target_df['Product'].isin(p_list) & 
                target_df['Country'].isin(c_list) & 
                target_df['Month'].isin(m_list)
            ]

        # Edge case handler
        if not metric: st.warning("Please select at least one metric.")
        
        # ----------------------------------------------------
        # PATH 1: CALCULATE
        # ----------------------------------------------------
        elif action == "Calculate":
            target_df = get_filtered_data(filtered_df, q_prod, q_country, q_month)
            
            st.success("**Calculated Results**")
            
            cols_per_row = 4
            for i in range(0, len(metric), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, m in enumerate(metric[i:i+cols_per_row]):
                    val = compute_metric(target_df, m)
                    cols[j].metric(m, format_nlq_val(val, m))

        # ----------------------------------------------------
        # PATH 2: COMPARE (WITH DELTA ENGINE)
        # ----------------------------------------------------
        elif action == "Compare":
            if not items: st.warning("Please select at least one item to compare.")
            else:
                results = []
                for item in items:
                    p = [item] if split_dim == "Products" else q_prod
                    c = [item] if split_dim == "Countries" else q_country
                    m = [item] if split_dim == "Months" else q_month
                    
                    target_df = get_filtered_data(filtered_df, p, c, m)
                    row_data = {'Item': item}
                    for m_name in metric:
                        row_data[m_name] = compute_metric(target_df, m_name)
                    results.append(row_data)
                
                res_df = pd.DataFrame(results)
                
                melted_df = res_df.melt(id_vars='Item', value_vars=metric, var_name='Metric', value_name='Value')
                melted_df['Formatted'] = melted_df.apply(lambda x: format_nlq_val(x['Value'], x['Metric']), axis=1)
                
                col_chart, col_data = st.columns([2, 1])
                with col_chart:
                    fig = px.bar(melted_df, x='Item', y='Value', color='Metric', barmode='group', 
                                 text='Formatted', title=f"Comparison across {split_dim}",
                                 hover_data={'Formatted': True, 'Value': False})
                    
                    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{data.name}: %{customdata[0]}<extra></extra>")
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, width = 'stretch')
                    
                with col_data:
                    display_df = res_df.copy()
                    for m_name in metric:
                        display_df[m_name] = display_df[m_name].apply(lambda x: format_nlq_val(x, m_name))
                    st.dataframe(display_df, hide_index=True, width = 'stretch')
                
                # --- VARIANCE & DELTA ENGINE ---
                st.markdown("---")
                
                if len(items) == 2:
                    st.markdown("#### 🔍 Variance & Delta Analysis")
                    var_cols = st.columns(len(metric))
                    for i, m_name in enumerate(metric):
                        val_a = res_df.loc[res_df['Item'] == items[0], m_name].values[0]
                        val_b = res_df.loc[res_df['Item'] == items[1], m_name].values[0]
                        diff = val_a - val_b
                        pct = (diff / abs(val_b) * 100) if val_b != 0 else 0
                        
                        delta_str = f"{diff:+.1f} pts vs {items[1]}" if "%" in m_name else f"{pct:+.1f}% vs {items[1]}"
                        var_cols[i].metric(f"{m_name} Delta ({items[0]} vs {items[1]})", format_nlq_val(diff, m_name), delta_str)
                        
                elif len(items) > 2:
                    st.markdown("#### Variance Analysis (Max vs Min Spread)")
                    var_cols = st.columns(len(metric))
                    for i, m_name in enumerate(metric):
                        max_idx = res_df[m_name].idxmax()
                        min_idx = res_df[m_name].idxmin()
                        val_max = res_df.loc[max_idx, m_name]
                        val_min = res_df.loc[min_idx, m_name]
                        item_max = res_df.loc[max_idx, 'Item']
                        item_min = res_df.loc[min_idx, 'Item']
                        
                        diff = val_max - val_min
                        pct = (diff / abs(val_min) * 100) if val_min != 0 else 0
                        
                        delta_str = f"Spread: {diff:+.1f} pts" if "%" in m_name else f"Spread: {pct:+.1f}%"
                        var_cols[i].metric(f"{m_name} Spread ({item_max} vs {item_min})", format_nlq_val(diff, m_name), delta_str)

        # ----------------------------------------------------
        # PATH 3: COMPARE SCENARIOS
        # ----------------------------------------------------
        elif action == "Compare scenarios":
            if scen_a == scen_b:
                st.warning("Please select two different scenarios to compare.")
            else:
                df_a = st.session_state.scenarios[scen_a]['df']
                df_b = st.session_state.scenarios[scen_b]['df']
                
                filt_a = get_filtered_data(df_a, q_prod, q_country, q_month)
                filt_b = get_filtered_data(df_b, q_prod, q_country, q_month)
                
                results = []
                row_a = {'Scenario': scen_a}
                row_b = {'Scenario': scen_b}
                
                for m_name in metric:
                    row_a[m_name] = compute_metric(filt_a, m_name)
                    row_b[m_name] = compute_metric(filt_b, m_name)
                    
                results.append(row_a)
                results.append(row_b)
                res_df = pd.DataFrame(results)
                
                melted_df = res_df.melt(id_vars='Scenario', value_vars=metric, var_name='Metric', value_name='Value')
                melted_df['Formatted'] = melted_df.apply(lambda x: format_nlq_val(x['Value'], x['Metric']), axis=1)
                
                col_chart, col_data = st.columns([2, 1])
                with col_chart:
                    fig = px.bar(melted_df, x='Metric', y='Value', color='Scenario', barmode='group', 
                                 text='Formatted', title=f"Head-to-Head: {scen_a} vs {scen_b}",
                                 hover_data={'Formatted': True, 'Value': False})
                    
                    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{data.name}: %{customdata[0]}<extra></extra>")
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, width = 'stretch')
                    
                with col_data:
                    display_df = res_df.copy()
                    for m_name in metric:
                        display_df[m_name] = display_df[m_name].apply(lambda x: format_nlq_val(x, m_name))
                    st.dataframe(display_df, hide_index=True, width = 'stretch')
                
                st.markdown("---")
                st.markdown("#### Scenario Delta Analysis")
                var_cols = st.columns(len(metric))
                for i, m_name in enumerate(metric):
                    val_a = row_a[m_name]
                    val_b = row_b[m_name]
                    diff = val_a - val_b
                    pct = (diff / abs(val_b) * 100) if val_b != 0 else 0
                    
                    delta_str = f"{diff:+.1f} pts vs {scen_b}" if "%" in m_name else f"{pct:+.1f}% vs {scen_b}"
                    var_cols[i].metric(f"{m_name} Impact ({scen_a} vs {scen_b})", format_nlq_val(diff, m_name), delta_str)

# ----------------------------------------------------
        # 🌟 PATH 4: RANK (NEW LEADERBOARD ENGINE)
        # ----------------------------------------------------
        elif action == "Rank":
            if not rank_items: 
                st.warning("Please select at least one candidate to rank.")
            else:
                st.success(" **Ranking Leaderboards:**")
                
                # We use 2 columns per row to give the HTML leaderboards plenty of room to stretch
                cols_per_row = 2
                for i in range(0, len(metric), cols_per_row):
                    cols = st.columns(cols_per_row)
                    
                    for j, m_name in enumerate(metric[i:i+cols_per_row]):
                        results = []
                        for item in rank_items:
                            p = [item] if rank_dim == "Products" else q_prod
                            m = [item] if rank_dim == "Months" else q_month
                            target_df = get_filtered_data(filtered_df, p, q_country, m)
                            val = compute_metric(target_df, m_name)
                            results.append({'Item': item, 'Value': val})
                        
                        # Sort values descending (Highest = Rank #1)
                        res_df = pd.DataFrame(results).sort_values('Value', ascending=False).reset_index(drop=True)
                        
                        # FIX: We construct the string line-by-line without leading spaces 
                        # so Streamlit doesn't mistake it for a markdown code block!
                        html_str = ""
                        html_str += f"<div style='background-color: #1a1a1c; padding: 20px; border-radius: 12px; border-top: 4px solid #0071e3; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);'>"
                        html_str += f"<h4 style='color: #e6edf3; margin-top: 0; margin-bottom: 15px; font-weight: 600; font-family: \"Helvetica Neue\", sans-serif;'>{m_name} Leaderboard</h4>"
                        html_str += f"<div style='display: flex; flex-direction: column; gap: 8px;'>"
                        
                        if not res_df.empty:
                            for rank, row in res_df.iterrows():
                                item_name = row['Item']
                                val = row['Value']
                                val_str = format_nlq_val(val, m_name)
                                
                                # Assign Medals/Colors to the top 3
                                badge_color = "#32d74b" if rank == 0 else "#0071e3" if rank == 1 else "#ff9f0a" if rank == 2 else "#8e8e93"
                                rank_badge = f"<span style='background-color: {badge_color}; color: white; padding: 3px 9px; border-radius: 12px; font-size: 0.85rem; font-weight: bold; margin-right: 12px;'>#{rank+1}</span>"
                                
                                gap_html = ""
                                # Starting from Rank #2, calculate the gap compared to the rank directly above it
                                if rank > 0:
                                    prev_val = res_df.loc[rank-1, 'Value']
                                    diff = val - prev_val
                                    pct = (diff / abs(prev_val) * 100) if prev_val != 0 else 0
                                    
                                    # Format the absolute difference based on the metric type
                                    if "%" in m_name: diff_display = f"{abs(diff):.1f} pts"
                                    elif "Units" in m_name: diff_display = f"{abs(diff):,.0f}"
                                    else: diff_display = f"{sym}{abs(diff):,.0f}"

                                    color = "#ff453a" if diff < 0 else "#32d74b" if diff > 0 else "#8e8e93"
                                    arrow = "▼" if diff < 0 else "▲" if diff > 0 else "-"
                                    
                                    # Subscript styling for the percentage next to the absolute gap
                                    gap_html = f"<div style='font-size: 0.85rem; color: {color}; margin-top: 2px; text-align: right; font-weight: 500;'>{arrow} {diff_display} <sub style='font-size: 0.75rem; opacity: 0.8; margin-left: 2px;'>({pct:+.1f}% vs #{rank})</sub></div>"

                                # Construct the individual row
                                html_str += f"<div style='display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background-color: #242426; border-radius: 8px;'>"
                                html_str += f"<div style='font-size: 1.05rem; font-weight: 500; color: #e6edf3; display: flex; align-items: center;'>{rank_badge} {item_name}</div>"
                                html_str += f"<div style='text-align: right;'><div style='font-size: 1.15rem; font-weight: bold; color: white;'>{val_str}</div>{gap_html}</div>"
                                html_str += f"</div>"
                                
                        html_str += "</div></div>"
                        
                        # Render the custom HTML securely
                        with cols[j]:
                            st.markdown(html_str, unsafe_allow_html=True)

        # ----------------------------------------------------
        # PATH 5: TREND
        # ----------------------------------------------------
        elif action == "Analyze the trend of":
            results = []
            for m in months:
                target_df = get_filtered_data(filtered_df, q_prod, q_country, [m])
                row_data = {'Month': m}
                for m_name in metric:
                    row_data[m_name] = compute_metric(target_df, m_name)
                results.append(row_data)
                
            res_df = pd.DataFrame(results)
            res_df['Month'] = pd.Categorical(res_df['Month'], categories=months, ordered=True)
            
            melted_df = res_df.melt(id_vars='Month', value_vars=metric, var_name='Metric', value_name='Value')
            melted_df['Formatted'] = melted_df.apply(lambda x: format_nlq_val(x['Value'], x['Metric']), axis=1)
            
            fig = px.line(melted_df.sort_values('Month'), x='Month', y='Value', color='Metric', markers=True, 
                          title=f"Trend Analysis for selected metrics", hover_data={'Formatted': True, 'Value': False})
            
            fig.update_traces(hovertemplate="<b>%{x}</b><br>%{data.name}: %{customdata[0]}<extra></extra>")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, width = 'stretch')

st.markdown("---")                

# ============================================================================
# SECTION 9: OUTPUT DATA TABLE & DATA EXPORT
# ============================================================================
# Export the filtered financial data in a clean, formatted table for reporting.
# All values are converted to the user's selected currency for easy reference.
# Unit columns are formatted with thousand separators for readability.
st.subheader("Filtered Results Extract")
display_df = filtered_df.copy()

format_cols = ['Selling Price (€)', 'Total Unit Cost (€)', 'Total Revenue (€)', 
               'Total Cost (€)', 'Production Spend (€)', 'Gross Profit (€)', 'Ending Inv Value (€)']

for col in format_cols: 
    new_col_name = col.replace("€", sym.strip())
    display_df[new_col_name] = display_df[col].apply(lambda x: f"{sym}{(x * rate):,.2f}")
    if new_col_name != col: display_df = display_df.drop(columns=[col])

unit_cols = ['Sales Units', 'Production Units', 'Beginning Inventory', 'Ending Inventory']
for col in unit_cols: display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
display_df['Unit Gross Margin %'] = display_df['Unit Gross Margin %'].apply(lambda x: f"{x:.1f}%")

display_df = display_df.drop(columns=['Unit Material Cost (€)', 'Unit Labor Cost (€)', 'Total Material Cost (€)', 'Total Labor Cost (€)'])

st.dataframe(display_df, width='stretch', hide_index=True)