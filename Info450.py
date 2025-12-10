# fema_dashboard.py
# Run with: streamlit run fema_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="FEMA Disaster Relief Dashboard", layout="wide")

@st.cache_data
def load_data():
    url = "https://storage.googleapis.com/info_450/IndividualAssistanceHousingRegistrantsLargeDisasters%20(1).csv"
    
    df = pd.read_csv(url, low_memory=False)
    
    # Sample for performance
    if len(df) > 50000:
        df = df.sample(n=50000, random_state=42)
    
    # Clean data
    df['repairAmount'] = pd.to_numeric(df['repairAmount'], errors='coerce')
    df['tsaEligible'] = pd.to_numeric(df['tsaEligible'], errors='coerce')
    df['waterLevel'] = pd.to_numeric(df['waterLevel'], errors='coerce')
    df['grossIncome'] = pd.to_numeric(df['grossIncome'], errors='coerce')
    
    df = df[df['tsaEligible'].isin([0, 1])]
    
    df['repairAmount'] = df['repairAmount'].fillna(0)
    df['waterLevel'] = df['waterLevel'].fillna(0)
    df['grossIncome'] = df['grossIncome'].fillna(0)
    
    return df

try:
    df = load_data()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading data: {e}")
    data_loaded = False

# Header
st.title("FEMA Disaster Relief Dashboard")
st.markdown("Analysis of FEMA disaster relief data")

if data_loaded:
    # Sidebar
    st.sidebar.header("Filters")
    
    if 'damagedStateAbbreviation' in df.columns:
        states = ['All'] + sorted(df['damagedStateAbbreviation'].dropna().unique().tolist())
        selected_state = st.sidebar.selectbox("Select State", states)
        
        if selected_state != 'All':
            df_filtered = df[df['damagedStateAbbreviation'] == selected_state]
        else:
            df_filtered = df
    else:
        df_filtered = df
    
    tsa_filter = st.sidebar.radio(
        "TSA Eligibility",
        ['All', 'Eligible (1)', 'Not Eligible (0)']
    )
    
    if tsa_filter == 'Eligible (1)':
        df_filtered = df_filtered[df_filtered['tsaEligible'] == 1]
    elif tsa_filter == 'Not Eligible (0)':
        df_filtered = df_filtered[df_filtered['tsaEligible'] == 0]
    
    # Metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{len(df_filtered):,}")
    
    with col2:
        avg_repair = df_filtered['repairAmount'].mean()
        st.metric("Avg Repair Amount", f"${avg_repair:,.2f}")
    
    with col3:
        tsa_rate = df_filtered['tsaEligible'].mean() * 100
        st.metric("TSA Eligibility Rate", f"{tsa_rate:.1f}%")
    
    with col4:
        total_repairs = df_filtered['repairAmount'].sum()
        st.metric("Total Repair Costs", f"${total_repairs:,.0f}")
    
    st.markdown("---")
    
    # Data preview
    with st.expander("View Data Sample"):
        st.dataframe(df_filtered.head(100), use_container_width=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Repair Amount Distribution",
        "By Residence Type",
        "TSA Analysis",
        "Income Analysis"
    ])
    
    # Tab 1
    with tab1:
        st.subheader("Distribution of Repair Amounts")
        
        fig_hist = px.histogram(
            df_filtered,
            x="repairAmount",
            nbins=50,
            title="Repair Amount Distribution",
            labels={"repairAmount": "Repair Amount (USD)"}
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Median", f"${df_filtered['repairAmount'].median():,.2f}")
        with col2:
            st.metric("Mean", f"${df_filtered['repairAmount'].mean():,.2f}")
        with col3:
            st.metric("Std Dev", f"${df_filtered['repairAmount'].std():,.2f}")
    
    # Tab 2
    with tab2:
        if 'residenceType' in df_filtered.columns:
            st.subheader("Repair Amount by Residence Type")
            
            fig_box_res = px.box(
                df_filtered,
                x="residenceType",
                y="repairAmount",
                title="Repair Amount Distribution by Residence Type",
                labels={"residenceType": "Residence Type", "repairAmount": "Repair Amount (USD)"}
            )
            st.plotly_chart(fig_box_res, use_container_width=True)
            
            avg_by_res = df_filtered.groupby('residenceType')['repairAmount'].mean().sort_values(ascending=False)
            
            st.markdown("**Average Repair Amount by Residence Type:**")
            st.bar_chart(avg_by_res)
        else:
            st.info("Residence type data not available")
    
    # Tab 3
    with tab3:
        st.subheader("TSA Eligibility Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_box_tsa = px.box(
                df_filtered,
                x="tsaEligible",
                y="repairAmount",
                title="Repair Amount by TSA Eligibility",
                labels={"tsaEligible": "TSA Eligible", "repairAmount": "Repair Amount (USD)"}
            )
            fig_box_tsa.update_xaxes(ticktext=["Not Eligible", "Eligible"], tickvals=[0, 1])
            st.plotly_chart(fig_box_tsa, use_container_width=True)
        
        with col2:
            tsa_counts = df_filtered['tsaEligible'].value_counts()
            fig_pie = px.pie(
                values=tsa_counts.values,
                names=['Not Eligible' if x == 0 else 'Eligible' for x in tsa_counts.index],
                title="TSA Eligibility Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("**Comparison Statistics:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**TSA Eligible:**")
            eligible = df_filtered[df_filtered['tsaEligible'] == 1]['repairAmount']
            st.write(f"- Count: {len(eligible):,}")
            st.write(f"- Mean: ${eligible.mean():,.2f}")
            st.write(f"- Median: ${eligible.median():,.2f}")
        
        with col2:
            st.markdown("**Not TSA Eligible:**")
            not_eligible = df_filtered[df_filtered['tsaEligible'] == 0]['repairAmount']
            st.write(f"- Count: {len(not_eligible):,}")
            st.write(f"- Mean: ${not_eligible.mean():,.2f}")
            st.write(f"- Median: ${not_eligible.median():,.2f}")
    
    # Tab 4
    with tab4:
        st.subheader("TSA Eligibility by Income Level")
        
        income_analysis = df_filtered.groupby('grossIncome').agg({
            'tsaEligible': ['mean', 'count']
        }).reset_index()
        income_analysis.columns = ['grossIncome', 'tsaRate', 'count']
        income_analysis = income_analysis[income_analysis['count'] >= 10]
        income_analysis = income_analysis.sort_values('tsaRate', ascending=False)
        
        if len(income_analysis) > 0:
            fig_income = px.bar(
                income_analysis,
                x="grossIncome",
                y="tsaRate",
                title="TSA Eligibility Rate by Gross Income Category",
                labels={"grossIncome": "Gross Income", "tsaRate": "TSA Eligibility Rate"}
            )
            fig_income.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_income, use_container_width=True)
        else:
            st.info("Insufficient data for income analysis")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **Key Insights:**
    - Explore repair amount distributions across different residence types and TSA eligibility
    - Dashboard shows how FEMA disaster relief funds are distributed
    - Use sidebar filters to focus on specific states or eligibility groups
    """)
    
else:
    st.error("Unable to load data")