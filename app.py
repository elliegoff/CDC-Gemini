"""
CDC Natality Dashboard (Single-File Application)
Target Audience: Undergraduate Business Analytics Students
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# =============================================================================
# 1. PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="CDC Natality Dashboard",
    page_icon="👶",
    layout="wide"
)

# =============================================================================
# 2. CONSTANTS & MAPPINGS
# =============================================================================
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

STATE_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

COLOR_PALETTE = {
    "Male": "#1f77b4",     # Soft Blue
    "Female": "#e377c2",   # Muted Pink
    "Primary": "#2b5c8f",   # Navy Blue
    "Heatmap": "Viridis",
    "Choropleth": "Blues"
}

# =============================================================================
# 3. DATA LOADING & VALIDATION
# =============================================================================
@st.cache_data
def load_and_validate_data(relative_path: str = "Provisional_Natality_2025_CDC1.csv") -> pd.DataFrame:
    """Loads dataset, performs integrity checks, and adds geographic mappings."""
    base_dir = Path(__file__).resolve().parent
    possible_paths = [
        base_dir / relative_path,
        base_dir / "data" / relative_path,
        Path(relative_path)
    ]
    
    file_path = None
    for path in possible_paths:
        if path.is_file():
            file_path = path
            break
            
    if file_path is None:
        st.error(f"Data file '{relative_path}' could not be located in directory paths.")
        st.stop()
        
    df = pd.read_csv(file_path)
    
    expected_cols = {'state_of_residence', 'month', 'month_code', 'year_code', 'sex_of_infant', 'births'}
    if not expected_cols.issubset(set(df.columns)):
        missing = expected_cols - set(df.columns)
        st.error(f"Dataset integrity check failed. Missing columns: {missing}")
        st.stop()
        
    if (df['births'] < 0).any():
        st.warning("Validation Warning: Dataset contains negative birth counts.")
        
    if not df['month_code'].between(1, 12).all():
        st.warning("Validation Warning: Month codes outside expected range 1-12 found.")
        
    df['month'] = pd.Categorical(df['month'], categories=MONTH_ORDER, ordered=True)
    df['state_abbr'] = df['state_of_residence'].map(STATE_TO_ABBR)
    
    return df

# =============================================================================
# 4. SHARED UI COMPONENTS (HEADER, SIDEBAR & KPIS)
# =============================================================================
def render_header():
    st.title("👶 CDC Provisional Natality Dashboard (2025)")
    st.markdown("""
    **Target Audience:** Undergraduate Business Analytics Students  
    *Explore geographic, monthly, and sex-based variations in birth counts across the United States.*
    """)
    
    st.info("""
    **Data Attribution & Methodology Notes:**
    - **Source:** CDC National Center for Health Statistics (NCHS) Provisional Natality Data.
    - **Provisional Notice:** Figures are provisional and subject to updates.
    - **Important Metric Distinction:** All figures reflect raw **birth counts**, NOT population-adjusted **birth rates**.
    """)
    st.markdown("---")

def render_sidebar(df: pd.DataFrame):
    st.sidebar.header("Filter Controls")
    
    all_states = sorted(df['state_of_residence'].unique().tolist())
    all_months = [m for m in MONTH_ORDER if m in df['month'].unique()]
    
    if "selected_states" not in st.session_state:
        st.session_state.selected_states = all_states
    if "selected_months" not in st.session_state:
        st.session_state.selected_months = all_months
    if "selected_sex" not in st.session_state:
        st.session_state.selected_sex = "All"

    col1, col2 = st.sidebar.columns(2)
    if col1.button("Select All"):
        st.session_state.selected_states = all_states
        st.session_state.selected_months = all_months
        st.session_state.selected_sex = "All"
        st.rerun()
        
    if col2.button("Reset Filters"):
        st.session_state.selected_states = all_states
        st.session_state.selected_months = all_months
        st.session_state.selected_sex = "All"
        st.rerun()

    selected_states = st.sidebar.multiselect(
        "Select State(s):",
        options=all_states,
        default=st.session_state.selected_states
    )
    
    selected_months = st.sidebar.multiselect(
        "Select Month(s):",
        options=all_months,
        default=st.session_state.selected_months
    )
    
    sex_options = ["All", "Female", "Male"]
    selected_sex = st.sidebar.radio(
        "Select Infant Sex:",
        options=sex_options,
        index=sex_options.index(st.session_state.selected_sex)
    )

    st.session_state.selected_states = selected_states
    st.session_state.selected_months = selected_months
    st.session_state.selected_sex = selected_sex

    filtered_df = df.copy()
    if selected_states:
        filtered_df = filtered_df[filtered_df['state_of_residence'].isin(selected_states)]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if selected_months:
        filtered_df = filtered_df[filtered_df['month'].isin(selected_months)]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if selected_sex != "All":
        filtered_df = filtered_df[filtered_df['sex_of_infant'] == selected_sex]

    with st.sidebar.expander("📌 Active Filters Summary", expanded=False):
        st.write(f"**States Selected:** {len(selected_states)} of {len(all_states)}")
        st.write(f"**Months Selected:** {len(selected_months)} of {len(all_months)}")
        st.write(f"**Sex Selected:** {selected_sex}")

    return filtered_df

def render_kpis(filtered_df: pd.DataFrame):
    st.subheader("Key Indicator Metrics")
    
    if filtered_df.empty:
        st.warning("⚠️ No observations match your current filter selections.")
        return

    total_births = filtered_df['births'].sum()
    num_states = filtered_df['state_of_residence'].nunique()
    num_months = filtered_df['month'].nunique()
    
    avg_births_per_month = total_births / num_months if num_months > 0 else 0
    
    top_geo = filtered_df.groupby('state_of_residence')['births'].sum().idxmax() if not filtered_df.empty else "N/A"
    top_geo_val = filtered_df.groupby('state_of_residence')['births'].sum().max() if not filtered_df.empty else 0
    
    top_month = filtered_df.groupby('month')['births'].sum().idxmax() if not filtered_df.empty else "N/A"
    top_month_val = filtered_df.groupby('month')['births'].sum().max() if not filtered_df.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Births", f"{total_births:,}")
    col2.metric("Geographies", f"{num_states:,}")
    col3.metric("Avg Births / Month", f"{int(avg_births_per_month):,}")
    col4.metric("Top Geography", f"{top_geo}", f"{top_geo_val:,} births")
    col5.metric("Top Month", f"{top_month}", f"{top_month_val:,} births")
    
    st.markdown("---")

# =============================================================================
# 5. DASHBOARD TAB VIEWS
# =============================================================================
def render_tab_overview(df: pd.DataFrame):
    st.header("Executive Overview")
    
    if df.empty:
        st.warning("No data available for the current filter selection.")
        return

    col1, col2 = st.columns([2, 1])
    
    with col1:
        monthly_agg = df.groupby('month', as_index=False)['births'].sum()
        fig_trend = px.line(
            monthly_agg,
            x='month',
            y='births',
            markers=True,
            title="Monthly Total Birth Trend",
            labels={'month': 'Month', 'births': 'Total Births'}
        )
        fig_trend.update_layout(yaxis=dict(rangemode='tozero'))
        fig_trend.update_traces(hovertemplate="Month: %{x}<br>Births: %{y:,}")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        sex_agg = df.groupby('sex_of_infant', as_index=False)['births'].sum()
        fig_sex = px.pie(
            sex_agg,
            names='sex_of_infant',
            values='births',
            title="Infant Sex Distribution",
            color='sex_of_infant',
            color_discrete_map=COLOR_PALETTE,
            hole=0.4
        )
        fig_sex.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_sex, use_container_width=True)

def render_tab_geographic(df: pd.DataFrame):
    st.header("Geographic Analysis")
    
    if df.empty:
        st.warning("No data available for the current filter selection.")
        return

    state_agg = df.groupby(['state_of_residence', 'state_abbr'], as_index=False)['births'].sum()
    
    st.subheader("US State Births Map")
    fig_map = px.choropleth(
        state_agg,
        locations='state_abbr',
        locationmode="USA-states",
        color='births',
        scope="usa",
        color_continuous_scale=COLOR_PALETTE["Choropleth"],
        labels={'births': 'Total Births', 'state_abbr': 'State'},
        title="Birth Counts by State of Residence"
    )
    fig_map.update_traces(hovertemplate="State: %{location}<br>Births: %{z:,}")
    st.plotly_chart(fig_map, use_container_width=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("State Birth Rankings")
        sorted_states = state_agg.sort_values(by='births', ascending=True)
        fig_rank = px.bar(
            sorted_states,
            x='births',
            y='state_of_residence',
            orientation='h',
            title="State Ranking by Total Selected Births",
            labels={'births': 'Total Births', 'state_of_residence': 'State'}
        )
        fig_rank.update_layout(xaxis=dict(rangemode='tozero'), height=max(400, len(sorted_states) * 18))
        fig_rank.update_traces(hovertemplate="State: %{y}<br>Births: %{x:,}")
        st.plotly_chart(fig_rank, use_container_width=True)

    with col2:
        st.subheader("Top & Bottom Comparison")
        n_top = min(5, len(state_agg))
        if n_top > 0:
            top_n = state_agg.nlargest(n_top, 'births').assign(Category='Top')
            bottom_n = state_agg.nsmallest(n_top, 'births').assign(Category='Bottom')
            top_bottom = pd.concat([top_n, bottom_n]).drop_duplicates()

            fig_tb = px.bar(
                top_bottom,
                x='state_abbr',
                y='births',
                color='Category',
                title=f"Top {n_top} vs Bottom {n_top} Geographies",
                labels={'births': 'Total Births', 'state_abbr': 'State'}
            )
            fig_tb.update_layout(yaxis=dict(rangemode='tozero'))
            fig_tb.update_traces(hovertemplate="State: %{x}<br>Births: %{y:,}")
            st.plotly_chart(fig_tb, use_container_width=True)

def render_tab_monthly_sex(df: pd.DataFrame):
    st.header("Monthly & Sex Analysis")
    
    if df.empty:
        st.warning("No data available for the current filter selection.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Birth Trend by Sex")
        monthly_sex = df.groupby(['month', 'sex_of_infant'], as_index=False)['births'].sum()
        fig_ms = px.line(
            monthly_sex,
            x='month',
            y='births',
            color='sex_of_infant',
            markers=True,
            title="Monthly Birth Trends Segmented by Sex",
            color_discrete_map=COLOR_PALETTE,
            labels={'month': 'Month', 'births': 'Birth Count', 'sex_of_infant': 'Sex'}
        )
        fig_ms.update_layout(yaxis=dict(rangemode='tozero'))
        fig_ms.update_traces(hovertemplate="Month: %{x}<br>Sex: %{fullData.name}<br>Births: %{y:,}")
        st.plotly_chart(fig_ms, use_container_width=True)

    with col2:
        st.subheader("Sex Comparison Aggregate")
        sex_totals = df.groupby('sex_of_infant', as_index=False)['births'].sum()
        fig_sex_bar = px.bar(
            sex_totals,
            x='sex_of_infant',
            y='births',
            color='sex_of_infant',
            color_discrete_map=COLOR_PALETTE,
            title="Total Birth Count by Infant Sex",
            labels={'sex_of_infant': 'Sex', 'births': 'Total Births'}
        )
        fig_sex_bar.update_layout(yaxis=dict(rangemode='tozero'))
        fig_sex_bar.update_traces(hovertemplate="Sex: %{x}<br>Total Births: %{y:,}")
        st.plotly_chart(fig_sex_bar, use_container_width=True)

    st.subheader("State-by-Month Birth Heatmap")
    heatmap_pivot = df.pivot_table(
        index='state_of_residence',
        columns='month',
        values='births',
        aggfunc='sum',
        observed=False
    ).fillna(0)

    fig_heat = px.imshow(
        heatmap_pivot,
        labels=dict(x="Month", y="State", color="Birth Count"),
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        color_continuous_scale=COLOR_PALETTE["Heatmap"],
        title="State-by-Month Birth Distribution Heatmap",
        aspect="auto"
    )
    fig_heat.update_traces(hovertemplate="State: %{y}<br>Month: %{x}<br>Births: %{z:,}")
    st.plotly_chart(fig_heat, use_container_width=True)

def render_tab_table(df: pd.DataFrame):
    st.header("Filtered Data Table & Export")
    
    if df.empty:
        st.warning("No observations available matching your current filter selection.")
        return

    st.write(f"Displaying **{len(df):,}** records matching current filter selection.")
    
    st.dataframe(
        df[['state_of_residence', 'month', 'year_code', 'sex_of_infant', 'births']],
        use_container_width=True,
        hide_index=True
    )

    csv_data = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name="cdc_filtered_natality_data_2025.csv",
        mime="text/csv"
    )

def render_tab_about():
    st.header("About the Dataset & Metadata")
    
    st.markdown("""
    ### Data Source & Context
    This application utilizes provisional birth data published by the **Centers for Disease Control and Prevention (CDC) National Center for Health Statistics (NCHS)**.

    #### Key Data Characteristics:
    - **Provisional Status:** These records represent provisional counts that are subject to updates before final annual release files are published.
    - **Counts vs. Rates:** Values represent absolute **birth counts** within given demographic and geographic criteria. They do **not** represent population-adjusted birth rates (e.g., births per 1,000 residents).
    
    #### Data Dictionary:
    | Field Name | Description | Example |
    | :--- | :--- | :--- |
    | `state_of_residence` | Full state/territory name of mother's residence | *California* |
    | `month` | Calendar month of birth | *January* |
    | `month_code` | Numeric month representation (1-12) | *1* |
    | `year_code` | Calendar year of birth | *2025* |
    | `sex_of_infant` | Infant sex assigned at birth | *Female / Male* |
    | `births` | Total recorded live births | *2,402* |

    #### Analytics Learning Focus:
    Designed specifically for undergraduate business analytics coursework to practice interactive exploratory data analysis (EDA), data visualization best practices, and categorical aggregation techniques.
    """)

# =============================================================================
# 6. MAIN CONTROLLER
# =============================================================================
def main():
    raw_df = load_and_validate_data()
    render_header()
    filtered_df = render_sidebar(raw_df)
    render_kpis(filtered_df)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🗺️ Geographic Analysis",
        "📈 Monthly & Sex Analysis",
        "📋 Data Table & Download",
        "ℹ️ About the Data"
    ])
    
    with tab1:
        render_tab_overview(filtered_df)
        
    with tab2:
        render_tab_geographic(filtered_df)
        
    with tab3:
        render_tab_monthly_sex(filtered_df)
        
    with tab4:
        render_tab_table(filtered_df)
        
    with tab5:
        render_tab_about()

if __name__ == "__main__":
    main()
