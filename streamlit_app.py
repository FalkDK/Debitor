import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.express as px
import os

# Function to load data from XML files
@st.cache_data
def load_data():
    data_folder = "./Data"
    file_paths = ['dlr.xml', 'jyk.xml', 'nda.xml', 'nyk.xml', 'rd.xml']
    all_data = []

    for file_name in file_paths:
        file_path = os.path.join(data_folder, file_name)
        print("Trying to load:", file_path)
        if not os.path.exists(file_path):
            print("File does not exist:", file_path)
            continue
        tree = ET.parse(file_path)
        root = tree.getroot()

        for debitormasse in root.findall('debitormasse'):
            record = {}
            record['isin'] = str(debitormasse.find('isin').text if debitormasse.find('isin') is not None else None)
            record['laan_gruppe'] = str(debitormasse.find('laan_gruppe').text if debitormasse.find('laan_gruppe') is not None else None)
            record['restgaeldinterval'] = int(debitormasse.find('restgaeldinterval').text if debitormasse.find('restgaeldinterval') is not None else None)
            D = debitormasse.find('D')
            if D is not None:
                for child in D:
                    record[child.tag] = float(child.text)
            all_data.append(record)

    return pd.DataFrame(all_data)

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


# Function to compute average loan size
def compute_avg_loan_size(df, selected_isins):
    loan_size_dfs = []
    for isin in selected_isins:
        filtered_df = df[df['isin'] == isin].copy()
        filtered_df['Avg_obl_loan'] = filtered_df['restgaeld_obl'] / filtered_df['antal_obl_laan']
        filtered_df['Avg_cash_loan'] = filtered_df['restgaeld_obl_kontant'] / filtered_df['antal_kontant_laan']
        filtered_df['isin'] = isin
        loan_size_dfs.append(filtered_df)
    return pd.concat(loan_size_dfs)

# Function to compute loan_size per laan gruppe
def calculate_avg_loan_size_per_laan_gruppe(df, selected_isins):
    loan_size_dfs = []
    for isin in selected_isins:
        # Filter out laan_gruppe C and the specified isin
        df_filtered = df[(df['laan_gruppe'] != 'C') & (df['isin'] == isin)].copy()

        # Aggregate the data
        aggregated_data = df_filtered.groupby(['laan_gruppe', 'restgaeldinterval']).agg(
            total_restgaeld_obl=('restgaeld_obl', 'sum'),
            total_restgaeld_obl_kontant=('restgaeld_obl_kontant', 'sum'),
            total_antal_obl_laan=('antal_obl_laan', 'sum'),
            total_antal_kontant_laan=('antal_kontant_laan', 'sum')
        ).reset_index()

        # Calculate the total loan amounts and total loan counts
        aggregated_data['total_loan_amount'] = aggregated_data['total_restgaeld_obl'] + aggregated_data['total_restgaeld_obl_kontant']
        aggregated_data['total_loan_count'] = aggregated_data['total_antal_obl_laan'] + aggregated_data['total_antal_kontant_laan']
        
        # Calculate the average loan size for each type and overall
        aggregated_data['avg_loan_size'] = aggregated_data['total_loan_amount'] / aggregated_data['total_loan_count']
        aggregated_data['avg_obl_loan_size'] = aggregated_data['total_restgaeld_obl'] / aggregated_data['total_antal_obl_laan']
        aggregated_data['avg_kontant_loan_size'] = aggregated_data['total_restgaeld_obl_kontant'] / aggregated_data['total_antal_kontant_laan']

        # Replace infinite values with NaN
        aggregated_data.replace([float('inf'), -float('inf')], pd.NA, inplace=True)

        # Add ISIN column for identification
        aggregated_data['isin'] = isin

        # Append to list
        loan_size_dfs.append(aggregated_data)

    # Concatenate all dataframes into one
    return pd.concat(loan_size_dfs)

# Function to compute share of obl and cash loans
def calculate_restgaeld_shares(df, isin):
    # Filter the DataFrame by ISIN
    filtered_df = df[df['isin'] == isin].copy()
    
    # Calculate the total sum of restgaeld_obl and restgaeld_obl_kontant
    total_restgaeld_obl = filtered_df['restgaeld_obl'].sum()
    total_restgaeld_obl_kontant = filtered_df['restgaeld_obl_kontant'].sum()
    
    # Calculate the total of both restgaeld_obl and restgaeld_obl_kontant
    total_restgaeld = total_restgaeld_obl + total_restgaeld_obl_kontant
    
    # Calculate the share of restgaeld_obl and restgaeld_obl_kontant
    share_restgaeld_obl = total_restgaeld_obl / total_restgaeld if total_restgaeld != 0 else 0
    share_restgaeld_obl_kontant = total_restgaeld_obl_kontant / total_restgaeld if total_restgaeld != 0 else 0
    
    return share_restgaeld_obl, share_restgaeld_obl_kontant

# Function to compute share of private and corporate loan share
def calculate_loan_shares(df, isin):
    # Step 1: Filter the DataFrame by ISIN and laan_gruppe
    filtered_df = df[(df['isin'] == isin) & df['laan_gruppe'].isin(['A', 'B'])].copy()
    
    # Step 2: Calculate the total sum of loans in each laan_gruppe across restgaeld_obl and restgaeld_obl_kontant
    total_loans_A = filtered_df[filtered_df['laan_gruppe'] == 'A'][['restgaeld_obl', 'restgaeld_obl_kontant']].sum().sum()
    total_loans_B = filtered_df[filtered_df['laan_gruppe'] == 'B'][['restgaeld_obl', 'restgaeld_obl_kontant']].sum().sum()
    
    # Step 3: Calculate the share of loans in each laan_gruppe over the total sum of loans in both groups
    total_loans = total_loans_A + total_loans_B
    share_A = total_loans_A / total_loans if total_loans != 0 else 0
    share_B = total_loans_B / total_loans if total_loans != 0 else 0
    
    return share_A, share_B

    # Function to compute percentage distribution per restgaeldinterval for each ISIN
def calculate_interval_distribution(df, selected_isins):
    interval_dfs = []
    for isin in selected_isins:
        # Filter the DataFrame by ISIN
        filtered_df = df[df['isin'] == isin].copy()

        # Calculate the total sum of restgaeld_obl and restgaeld_obl_kontant for each restgaeldinterval
        interval_data = filtered_df.groupby('restgaeldinterval').agg(
            total_restgaeld_obl=('restgaeld_obl', 'sum'),
            total_restgaeld_obl_kontant=('restgaeld_obl_kontant', 'sum')
        ).reset_index()

        # Calculate the total of both restgaeld_obl and restgaeld_obl_kontant
        interval_data['total_restgaeld'] = interval_data['total_restgaeld_obl'] + interval_data['total_restgaeld_obl_kontant']

        # Calculate the percentage distribution of restgaeldinterval
        total_restgaeld = interval_data['total_restgaeld'].sum()
        interval_data['percentage'] = (interval_data['total_restgaeld'] / total_restgaeld) * 100 if total_restgaeld != 0 else 0

        # Add ISIN column for identification
        interval_data['isin'] = isin

        # Append to list
        interval_dfs.append(interval_data)

    # Concatenate all dataframes into one and pivot
    all_intervals_df = pd.concat(interval_dfs)
    pivoted_intervals_df = all_intervals_df.pivot(index='isin', columns='restgaeldinterval', values='percentage').fillna(0)
    return pivoted_intervals_df

## Updated function to gather shares of 'A', 'B', 'obl', and 'cash' (kontant) loan groups for each ISIN
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


# Main Streamlit app
st.set_page_config(layout="centered", page_title='Callables')  # wide/centered
st.title("Debitor Distribution")


# Load data
df = load_data()

# default isin
default_isins = ['DK0009540981', 'DK0009409922', 'DK0006359286', 'DK0004626918', 'DK0002058346']
isin_options = df['isin'].unique()

# Ensure all default ISINs are in the options
default_isins = [isin for isin in default_isins if isin in isin_options]
selected_isins = st.multiselect("Select ISINs:", options=isin_options, default=default_isins)

# sidebar
with st.sidebar:
    st.button('Debitor')
    st.button('Cash Flow')

# Checkbox to show/hide raw data
show_raw_data = st.checkbox('Show Raw Data')
show_debitor_table = st.checkbox('Show Tables')

# Show raw data
if show_raw_data:
    st.subheader('Raw Data')
    if selected_isins:
        for isin in selected_isins:
            st.write(f"ISIN: {isin}")
            st.table(df[(df['isin'] == isin)].sort_values(by=['laan_gruppe', 'restgaeldinterval']))
    else:
        st.write("Please select at least one ISIN.")

# Show debtor distribution as percentages
if selected_isins:
    st.subheader('Debitor Distribution (%)', divider='red')
    percentage_df = calculate_percentage(df, selected_isins)
    pivoted_df = percentage_df.pivot_table(index=['isin', 'restgaeldinterval'], columns='laan_gruppe', values='percentage', aggfunc='sum', margins=True, margins_name="Total")
    pivoted_df_kontant = percentage_df.pivot_table(index=['isin', 'restgaeldinterval'], columns='laan_gruppe', values='percentage_obl_kontant', aggfunc='sum', margins=True, margins_name="Total")

    for isin in selected_isins:
        rest_obl = df[(df['isin'] == isin)]['restgaeld_obl'].sum()
        rest_kontant = df[(df['isin'] == isin)]['restgaeld_obl_kontant'].sum()
        share_obl, share_kontant = calculate_restgaeld_shares(df, isin)
        share_a, share_b = calculate_loan_shares(df, isin)
        st.write(f"**ISIN:** {isin} | **Private Share:** {round(share_a, 3)} | **Commercial Share:** {round(share_b,3)}")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'**Obl:** {rest_obl:,} | **Share:** {round(share_obl, 3)}')
            st.table(pivoted_df.loc[isin].fillna(0))  # Using fillna(0) to replace NaN values with 0 for better presentation
        with col2:
            st.write(f'**Cash:** {rest_kontant:,} | **Share:** {round(share_kontant, 3)} ')
            st.table(pivoted_df_kontant.loc[isin].fillna(0))  # Using fillna(0) to replace NaN values with 0 for better presentation

    # Plotting the combined bar chart for debtor distribution
    st.subheader('Debitor Distribution (%)', divider='red')
    fig = px.bar(percentage_df, x='restgaeldinterval', y='percentage', color='isin', barmode='group', title='Percentage Distribution of Restgaeld_obl Across Restgaeldinterval')
    st.plotly_chart(fig)
    fig = px.bar(percentage_df, x='restgaeldinterval', y='percentage_obl_kontant', color='isin', barmode='group', title='Percentage Distribution of Restgaeld_obl_kontant')
    st.plotly_chart(fig)
    
# Show average loan size
if selected_isins:
    st.subheader('Avg Loan Size', divider='red')
    show_full = st.checkbox('Full Breakdown')
    for isin in selected_isins:
        st.write(f"ISIN: {isin}")
        loan_size_df = compute_avg_loan_size(df, [isin])
        loan_size_df_gruppe = calculate_avg_loan_size_per_laan_gruppe(df, [isin])
        if not show_full:
            st.table(loan_size_df_gruppe.pivot(index='restgaeldinterval', columns='laan_gruppe', values='avg_loan_size').fillna(0))
        else:
            st.table(loan_size_df.pivot_table(index='restgaeldinterval', columns='laan_gruppe', values=['Avg_obl_loan', 'Avg_cash_loan'], aggfunc='mean').fillna(0))

    # Plotting the combined bar chart for average loan sizes
    st.subheader('Avg Loan Size - Combined Bar Chart', divider='red')
    loan_size_df_combined = compute_avg_loan_size(df, selected_isins)
    fig_loan_size = px.bar(loan_size_df_combined.melt(id_vars=['isin', 'restgaeldinterval'], value_vars=['Avg_obl_loan', 'Avg_cash_loan']), 
                            x='restgaeldinterval', y='value', color='isin', facet_col='variable', barmode='group',
                            title='Average Loan Sizes Across Restgaeldinterval for Obl and Cash loans')
    
    st.plotly_chart(fig_loan_size)
    
    # Plotting across interval per gruppe
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

    st.plotly_chart(fig_loan_size)

# Calculate interval distribution and store in a variable
interval_distribution_df = calculate_interval_distribution(df, selected_isins)
interval_distribution_df.columns = ["0-200k", '200k-500k', '500k-1m', '1-3m', '3-10m', '10-50m', '+50m']

# Calculate shares and store in a variable
loan_shares_df = gather_loan_shares(df, selected_isins)

# Merge the two DataFrames side by side
merged_df = interval_distribution_df.merge(loan_shares_df, left_index=True, right_index=True)
merged_df.columns = merged_df.columns.map(str)

# Display the merged DataFrame using Streamlit
if selected_isins:
    st.subheader('Interval Distribution, A/B Shares, and Obl/Cash Shares per ISIN')
    st.dataframe(merged_df)

else:
    st.write("Please select at least one ISIN.")
    
total_int_distribution = calculate_interval_distribution(df, isin_options)
total_int_distribution.columns = ["0-200k", '200k-500k', '500k-1m', '1-3m', '3-10m', '10-50m', '+50m']

# Calculate shares and store in a variable
total_loan_shares_df = gather_loan_shares(df, isin_options)

total_merged_df = total_int_distribution.merge(total_loan_shares_df, left_index=True, right_index=True)
total_merged_df.columns = total_merged_df.columns.map(str)

top_20_isins_for_50m = total_merged_df.sort_values('+50m', ascending=False).head(20)

st.subheader('Top 20 ISIN sorted loans above 50mio')
st.dataframe(top_20_isins_for_50m)
