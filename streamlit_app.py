import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from data_loader import load_xml, load_xml_redemption

st.set_page_config(layout="wide", page_title='Danish Bonds Data')

# Load custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Helper functions
@st.cache_data
def load_files():
    return load_xml(), load_xml_redemption()

@st.cache_data
def calculate_percentage(df, selected_isins):
    percentage_dfs = []
    for isin in selected_isins:
        filtered_df = df[(df['isin'] == isin) & (df['laan_gruppe'] != 'C')].copy()
        total_restgaeld_obl = filtered_df['restgaeld_obl'].sum()
        total_restgaeld_kontant = filtered_df['restgaeld_obl_kontant'].sum()
        filtered_df['percentage'] = (filtered_df['restgaeld_obl'] / total_restgaeld_obl) * 100
        filtered_df['percentage_obl_kontant'] = (filtered_df['restgaeld_obl_kontant'] / total_restgaeld_kontant) * 100
        filtered_df['isin'] = isin
        percentage_dfs.append(filtered_df)
    return pd.concat(percentage_dfs)

@st.cache_data
def compute_avg_loan_size(df, selected_isins):
    loan_size_dfs = []
    for isin in selected_isins:
        filtered_df = df[df['isin'] == isin].copy()
        filtered_df['Avg_obl_loan'] = filtered_df['restgaeld_obl'] / filtered_df['antal_obl_laan']
        filtered_df['Avg_cash_loan'] = filtered_df['restgaeld_obl_kontant'] / filtered_df['antal_kontant_laan']
        filtered_df['isin'] = isin
        loan_size_dfs.append(filtered_df)
    return pd.concat(loan_size_dfs)

@st.cache_data
def calculate_restgaeld_shares(df, isin):
    filtered_df = df[df['isin'] == isin].copy()
    total_restgaeld_obl = filtered_df['restgaeld_obl'].sum()
    total_restgaeld_obl_kontant = filtered_df['restgaeld_obl_kontant'].sum()
    total_restgaeld = total_restgaeld_obl + total_restgaeld_obl_kontant
    share_restgaeld_obl = total_restgaeld_obl / total_restgaeld if total_restgaeld != 0 else 0
    share_restgaeld_obl_kontant = total_restgaeld_obl_kontant / total_restgaeld if total_restgaeld != 0 else 0
    return share_restgaeld_obl, share_restgaeld_obl_kontant

@st.cache_data
def calculate_loan_shares(df, isin):
    filtered_df = df[(df['isin'] == isin) & df['laan_gruppe'].isin(['A', 'B'])].copy()
    total_loans_A = filtered_df[filtered_df['laan_gruppe'] == 'A'][['restgaeld_obl', 'restgaeld_obl_kontant']].sum().sum()
    total_loans_B = filtered_df[filtered_df['laan_gruppe'] == 'B'][['restgaeld_obl', 'restgaeld_obl_kontant']].sum().sum()
    total_loans = total_loans_A + total_loans_B
    share_A = total_loans_A / total_loans if total_loans != 0 else 0
    share_B = total_loans_B / total_loans if total_loans != 0 else 0
    return share_A, share_B

@st.cache_data
def calculate_interval_distribution(df, selected_isins):
    interval_dfs = []
    for isin in selected_isins:
        filtered_df = df[df['isin'] == isin].copy()
        interval_data = filtered_df.groupby('restgaeldinterval').agg(
            total_restgaeld_obl=('restgaeld_obl', 'sum'),
            total_restgaeld_obl_kontant=('restgaeld_obl_kontant', 'sum')
        ).reset_index()
        interval_data['total_restgaeld'] = interval_data['total_restgaeld_obl'] + interval_data['total_restgaeld_obl_kontant']
        total_restgaeld = interval_data['total_restgaeld'].sum()
        interval_data['percentage'] = (interval_data['total_restgaeld'] / total_restgaeld) * 100 if total_restgaeld != 0 else 0
        interval_data['isin'] = isin
        interval_dfs.append(interval_data)
    all_intervals_df = pd.concat(interval_dfs)
    pivoted_intervals_df = all_intervals_df.pivot(index='isin', columns='restgaeldinterval', values='percentage').fillna(0)
    pivoted_intervals_df['total'] = all_intervals_df.groupby('isin')['total_restgaeld'].sum()
    return pivoted_intervals_df

@st.cache_data
def gather_loan_shares(df, selected_isins):
    shares_data = []
    for isin in selected_isins:
        share_a, share_b = calculate_loan_shares(df, isin)
        share_obl, share_kontant = calculate_restgaeld_shares(df, isin)
        shares_data.append({
            'isin': isin, 
            'Private': share_a*100, 
            'Commercial': share_b*100, 
            'Obl (%)': share_obl*100, 
            'Cash (%)': share_kontant*100
        })
    shares_df = pd.DataFrame(shares_data)
    return shares_df.set_index('isin')

@st.cache_data
def calculate_avg_loan_size_per_laan_gruppe(df, selected_isins):
    loan_size_dfs = []
    for isin in selected_isins:
        df_filtered = df[(df['laan_gruppe'] != 'C') & (df['isin'] == isin)].copy()
        aggregated_data = df_filtered.groupby(['laan_gruppe', 'restgaeldinterval']).agg(
            total_restgaeld_obl=('restgaeld_obl', 'sum'),
            total_restgaeld_obl_kontant=('restgaeld_obl_kontant', 'sum'),
            total_antal_obl_laan=('antal_obl_laan', 'sum'),
            total_antal_kontant_laan=('antal_kontant_laan', 'sum')
        ).reset_index()
        aggregated_data['total_loan_amount'] = aggregated_data['total_restgaeld_obl'] + aggregated_data['total_restgaeld_obl_kontant']
        aggregated_data['total_loan_count'] = aggregated_data['total_antal_obl_laan'] + aggregated_data['total_antal_kontant_laan']
        aggregated_data['avg_loan_size'] = aggregated_data['total_loan_amount'] / aggregated_data['total_loan_count']
        aggregated_data['avg_obl_loan_size'] = aggregated_data['total_restgaeld_obl'] / aggregated_data['total_antal_obl_laan']
        aggregated_data['avg_kontant_loan_size'] = aggregated_data['total_restgaeld_obl_kontant'] / aggregated_data['total_antal_kontant_laan']
        aggregated_data.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
        aggregated_data['isin'] = isin
        loan_size_dfs.append(aggregated_data)
    return pd.concat(loan_size_dfs)

@st.cache_data
def calculate_afdrag_percentage(df):
    """
    Calculates the percentage and cumulative percentage of 'afdrag_belob' for each ISIN relative to the total 'afdrag_belob' for that ISIN.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing columns 'isin', 'afdrag_belob', and 'terminsdato'.

    Returns:
    pd.DataFrame: The DataFrame with additional 'afdrag_percentage' and 'cumulative_percentage' columns.
    """
    # Step 1: Calculate the total afdrag_belob for each ISIN
    total_afdrag_per_isin = df.groupby('isin')['afdrag_belob'].sum().reset_index()
    total_afdrag_per_isin.rename(columns={'afdrag_belob': 'total_afdrag_belob'}, inplace=True)

    # Step 2: Merge this total back into the original DataFrame
    df = pd.merge(df, total_afdrag_per_isin, on='isin')

    # Step 3: Calculate the percentage
    df['afdrag_percentage'] = (df['afdrag_belob'] / df['total_afdrag_belob']) * 100

    # Step 4: Sort the DataFrame by ISIN and date to ensure proper cumulative calculation
    df.sort_values(by=['isin', 'terminsdato'], inplace=True)

    # Step 5: Calculate the cumulative percentage for each ISIN
    df['cumulative_percentage'] = df.groupby('isin')['afdrag_percentage'].cumsum()

    return df


# Main function
def main():
    
    with st.sidebar:
        selected = option_menu(
            "Main Menu",
            ["Home", "Debtor Distribution", "Large Loans", "Cashflow"],
            icons=['house', 'graph-up', 'list-ol', 'bar-chart'],
            menu_icon="cast",
            default_index=1,
        )
    
    with st.spinner('Loading data...'):
        if 'data_loaded' not in st.session_state:
            st.session_state.df, st.session_state.df_r = load_files()
            st.session_state.data_loaded = True
        
        df = st.session_state.df
        df_r = st.session_state.df_r
    
    if selected == "Home":
        display_home()
    elif selected == "Debtor Distribution":
        display_debitor_analysis(df)
    elif selected == "Large Loans":
        display_large_loans(df)
    elif selected == "Cashflow":
        display_redemption(df_r)

# Display functions
def display_home():
    st.title("Danish Bonds Data")
    st.write("Welcome to the Danish Bonds Data dashboard.")
    st.write("Use the sidebar to navigate through different datasets.")
    st.info("This dashboard provides insights into Danish bonds, including debtor distribution and large loans analysis.")

def display_debitor_analysis(df):
    st.title("Debtor Distribution")
    isin_options = df['isin'].unique()
    default_isins = ['DK0009540981', 'DK0009409922', 'DK0006359286', 'DK0004626918', 'DK0002058346', 'DK0009541013', 'DK0009409419', 'DK0006359369', 'DK0004627056', 'DK0002058429']
    default_isins = [isin for isin in default_isins if isin in isin_options]
    selected_isins = st.multiselect("Select ISINs:", options=isin_options, default=default_isins)
    
    if not selected_isins:
        st.warning("Please select at least one ISIN to view analysis.")
        return
    
    interval_distribution_df = calculate_interval_distribution(df, selected_isins)
    interval_distribution_df.columns = ["0-200k", '200k-500k', '500k-1m', '1-3m', '3-10m', '10-50m', '+50m', 'total']
    loan_shares_df = gather_loan_shares(df, selected_isins)
    merged_df = interval_distribution_df.merge(loan_shares_df, left_index=True, right_index=True)
    merged_df.columns = merged_df.columns.map(str)
    
    tab1, tab2, tab3 = st.tabs(["Distribution", "Loan Sizes", "Summary"])
    
    with tab1:
        display_distribution(df, selected_isins)
    
    with tab2:
        display_loan_sizes(df, selected_isins)
    
    with tab3:
        display_summary(merged_df)

def display_distribution(df, selected_isins):
    st.header("Debtor Distribution")
    
    with st.spinner('Calculating distribution...'):
        percentage_df = calculate_percentage(df, selected_isins)
    
    fig_obl = px.bar(percentage_df, x='restgaeldinterval', y='percentage', color='isin', barmode='group',
                     title='Percentage Distribution of Obl',
                     labels={'restgaeldinterval': 'Loan Interval', 'percentage': 'Percentage'},
                     hover_data=['isin', 'laan_gruppe'])
    st.plotly_chart(fig_obl, use_container_width=True)
    
    fig_cash = px.bar(percentage_df, x='restgaeldinterval', y='percentage_obl_kontant', color='isin', barmode='group',
                      title='Percentage Distribution of Cash Loans',
                      labels={'restgaeldinterval': 'Loan Interval', 'percentage_obl_kontant': 'Percentage'},
                      hover_data=['isin', 'laan_gruppe'])
    st.plotly_chart(fig_cash, use_container_width=True)

    selected_isin = st.selectbox("Breakdown of selected ISIN:", selected_isins, key='debtor')

    if selected_isin:
        percentage_df = calculate_percentage(df, [selected_isin])
        pivoted_df = percentage_df.pivot_table(index=['isin', 'restgaeldinterval'], columns='laan_gruppe', values='percentage', aggfunc='sum', margins=True, margins_name="Total")
        pivoted_df_kontant = percentage_df.pivot_table(index=['isin', 'restgaeldinterval'], columns='laan_gruppe', values='percentage_obl_kontant', aggfunc='sum', margins=True, margins_name="Total")

        rest_obl = df[(df['isin'] == selected_isin)]['restgaeld_obl'].sum()
        rest_kontant = df[(df['isin'] == selected_isin)]['restgaeld_obl_kontant'].sum()
        share_obl, share_kontant = calculate_restgaeld_shares(df, selected_isin)
        share_a, share_b = calculate_loan_shares(df, selected_isin)
        
        st.markdown(f"""
        <div class='info-box'>
        <strong>ISIN:</strong> {selected_isin} | 
        <strong>Private Share:</strong> {round(share_a, 3)} | 
        <strong>Commercial Share:</strong> {round(share_b, 3)}
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
        <div class='info-box'>
        <strong>Obl:</strong> {rest_obl:,} | 
        <strong>Share:</strong> {round(share_obl, 3)}
        </div>
        """, unsafe_allow_html=True)
            p_df = pivoted_df.loc[selected_isin].fillna(0)
            p_df.columns.name = 'LoanInterval'
            p_df.index.name = None
            st.markdown(p_df.to_html(classes='styled-table'), unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
        <div class='info-box'>
        <strong>Cash:</strong> {rest_kontant:,} | 
        <strong>Share:</strong> {round(share_kontant, 3)} 
        </div>
        """, unsafe_allow_html=True)
            p_df = pivoted_df_kontant.loc[selected_isin].fillna(0)
            p_df.columns.name = 'LoanInterval'
            p_df.index.name = None
            st.markdown(p_df.to_html(classes='styled-table'), unsafe_allow_html=True)

def display_loan_sizes(df, selected_isins):
    st.header("Average Loan Sizes")
    
    with st.spinner('Calculating average loan sizes...'):
        loan_size_df_combined = compute_avg_loan_size(df, selected_isins)
    
    fig_loan_size = px.bar(loan_size_df_combined.melt(id_vars=['isin', 'restgaeldinterval'], value_vars=['Avg_obl_loan', 'Avg_cash_loan']), 
                           x='restgaeldinterval', y='value', color='isin', facet_col='variable', barmode='group',
                           title='Average Loan Sizes Across Restgæld Interval for Obl and Cash loans',
                           labels={'restgaeldinterval': 'Restgæld Interval', 'value': 'Average Loan Size'},
                           hover_data=['isin'])
    st.plotly_chart(fig_loan_size, use_container_width=True)
    
    loan_size_df_gruppe_combined = calculate_avg_loan_size_per_laan_gruppe(df, selected_isins)
    fig_loan_size = px.bar(
        loan_size_df_gruppe_combined.melt(id_vars=['isin', 'restgaeldinterval', 'laan_gruppe'], value_vars=['avg_loan_size']),
        x='restgaeldinterval',
        y='value',
        color='isin',
        facet_col='laan_gruppe',
        barmode='group',
        title='Average Loan Sizes Across Restgaeldinterval for Privat and Other Loans'
    )

    st.plotly_chart(fig_loan_size, use_container_width=True)
    
    subset_isin = st.selectbox("Breakdown of selected ISIN:", selected_isins, key='LoanSize')
    
    if subset_isin:
        st.markdown(f"""
<div class='info-box'>
<strong>ISIN:</strong> {subset_isin}
</div>
""", unsafe_allow_html=True)
        loan_size_df = compute_avg_loan_size(df, [subset_isin])
        df_l = loan_size_df.pivot_table(index='restgaeldinterval', columns='laan_gruppe', values=['Avg_obl_loan', 'Avg_cash_loan'], aggfunc='mean').fillna(0)
        df_l = df_l.map(lambda x: f"{x:,.0f}")
        df_l.index.name = None
        df_l.columns.name = None
        st.markdown(df_l.to_html(classes='styled-table'), unsafe_allow_html=True)

def display_summary(merged_df):
    st.header("Summary Statistics")
    
    st.dataframe(merged_df.style.format({
        '0-200k': '{:.2f}%',
        '200k-500k': '{:.2f}%',
        '500k-1m': '{:.2f}%',
        '1-3m': '{:.2f}%',
        '3-10m': '{:.2f}%',
        '10-50m': '{:.2f}%',
        '+50m': '{:.2f}%',
        'Private': '{:.2f}%',
        'Commercial': '{:.2f}%',
        'Obl (%)': '{:.2f}%',
        'Cash (%)': '{:.2f}%'
    }), use_container_width=True)
    
    csv = merged_df.to_csv()
    st.download_button(
        label="Download summary as CSV",
        data=csv,
        file_name='bond_summary.csv',
        mime='text/csv',
    )

def display_large_loans(df):
    st.title("Large Loans Analysis")
    
    with st.spinner('Analyzing large loans...'):
        isin_options = df['isin'].unique()
        total_int_distribution = calculate_interval_distribution(df, isin_options)
        total_int_distribution.columns = ["0-200k", '200k-500k', '500k-1m', '1-3m', '3-10m', '10-50m', '+50m', 'total']
        
        # Combine '10-50m' and '+50m' into a single threshold column
        total_int_distribution['Over 10m'] = total_int_distribution['10-50m'] + total_int_distribution['+50m']
        
        # Sort by the new combined column and select the top 50
        top_50_isins = total_int_distribution.sort_values('Over 10m', ascending=False).head(50)
        
        st.subheader("Top 50 ISINs with the Highest Combined Percentage in 'Over 10m'")
        st.dataframe(top_50_isins, use_container_width=True)
        
        # Custom colorscale for the stacked bar chart
        custom_colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']
        
        # Stacked Bar Chart: Loan Distribution Across Buckets by ISIN
        fig_stacked = px.bar(
            top_50_isins.reset_index(),
            x='isin',
            y=["0-200k", "200k-500k", "500k-1m", "1-3m", "3-10m", "10-50m", "+50m"],
            title='Loan Distribution Across Buckets by ISIN',
            labels={'value': 'Percentage of Loans', 'isin': 'ISIN'},
            hover_data={'total': True},
            barmode='stack',
            color_discrete_sequence=custom_colors
        )
        fig_stacked.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_stacked, use_container_width=True)
        
        # Bar Chart: Combined Percentage of Loans Over 10m by ISIN
        fig_combined = px.bar(
            top_50_isins.reset_index(),
            x='isin',
            y='Over 10m',
            title='Combined Percentage of Loans Over 10m by ISIN',
            labels={'isin': 'ISIN', 'Over 10m': 'Combined Percentage of Loans Over 10m'},
            hover_data=['isin']
        )
        fig_combined.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_combined, use_container_width=True)


def display_redemption(df):
    st.header("Cash Flows")
    new_df = calculate_afdrag_percentage(df)
    selected_isins = st.multiselect("Select ISINs:", options=new_df['isin'].unique(), default=['DK0006357660', 'DK0009542094', 'DK0002058189', 'DK0002058262'])

    if selected_isins:
        filtered_df = new_df[new_df['isin'].isin(selected_isins)]
        st.download_button(
            label="Download Selected ISINs as CSV",
            data=filtered_df.to_csv(),
            file_name='redemption.csv',
            mime='text/csv')

        pivoted_df = filtered_df.pivot(index='terminsdato', columns='isin', values='afdrag_percentage').fillna('')      
        pivoted_df.columns.name = "Date/ISIN"
        pivoted_df.index.name = None
        st.markdown(pivoted_df.to_html(classes='styled-table'), unsafe_allow_html=True)
        
        
        # Step 3: Plot the data with date on x-axis
        fig = px.line(
            filtered_df,
            x='terminsdato',  # Assuming 'terminsdato' is the date column
            y='cumulative_percentage',
            color='isin',
            title='Cash Flow Over Time by ISIN<br><sup>Cumulative Percentage of Redemptions LogY scale</sup>',
            labels={'terminsdato': 'Date', 'cumulative_percentage': 'Cumulative Percentage (%) '},
            markers=True,  # Add markers for each data point, 
            log_y=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one ISIN to view the data.")
    
if __name__ == "__main__":
    main()
