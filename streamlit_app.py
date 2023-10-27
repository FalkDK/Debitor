import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import plotly.express as px
import os

# Function to load data from XML files
@st.cache_data
def load_data():
    data_folder = "Data"
    file_paths = ['dlr.xml', 'jyk.xml', 'nda.xml', 'nyk.xml', 'rd.xml']
    all_data = []

    for file_name in file_paths:
        file_path = os.path.join(data_folder, file_name)
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

# Main Streamlit app
st.set_page_config(layout="centered", page_title='Callables')  # wide/centered
st.title("Debitor Distribution")

# Load data
df = load_data()

# Sidebar for ISIN selection
default_isins = ['DK0009540981', 'DK0009409922', 'DK0006359286', 'DK0004626918', 'DK0002058346'] 
selected_isins = st.multiselect("Select ISINs:", options=df['isin'].unique(), default=default_isins)

# sidebar
with st.sidebar:
    st.write('Debitor')

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
        st.write(f"ISIN: {isin}")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'restgaeld_obl: {rest_obl:,}')
            st.table(pivoted_df.loc[isin].fillna(0))  # Using fillna(0) to replace NaN values with 0 for better presentation
        with col2:
            st.write(f'restgaeld_obl_kontant')
            st.table(pivoted_df_kontant.loc[isin].fillna(0))  # Using fillna(0) to replace NaN values with 0 for better presentation

    # Plotting the combined bar chart for debtor distribution
    st.subheader('Debitor Distribution (%) - Combined Bar Chart', divider='red')
    fig = px.bar(percentage_df, x='restgaeldinterval', y='percentage', color='isin', barmode='group', title='Percentage Distribution of restgaeld_obl across restgaeldinterval')
    st.plotly_chart(fig)
    fig = px.bar(percentage_df, x='restgaeldinterval', y='percentage_obl_kontant', color='isin', barmode='group', title='Percentage Distribution of restgaeld_obl_kontant')
    st.plotly_chart(fig)
    
# Show average loan size
if selected_isins:
    st.subheader('Avg Loan Size', divider='red')
    for isin in selected_isins:
        st.write(f"ISIN: {isin}")
        loan_size_df = compute_avg_loan_size(df, [isin])
        st.table(loan_size_df.pivot_table(index='restgaeldinterval', columns='laan_gruppe', values=['Avg_obl_loan', 'Avg_cash_loan'], aggfunc='mean'))

    # Plotting the combined bar chart for average loan sizes
    st.subheader('Avg Loan Size - Combined Bar Chart', divider='red')
    loan_size_df_combined = compute_avg_loan_size(df, selected_isins)
    print(loan_size_df_combined.head())
    fig_loan_size = px.bar(loan_size_df_combined.melt(id_vars=['isin', 'restgaeldinterval'], value_vars=['Avg_obl_loan', 'Avg_cash_loan']), 
                            x='restgaeldinterval', y='value', color='isin', facet_col='variable', barmode='group',
                            title='Average Loan Sizes across restgaeldinterval')
    
    st.plotly_chart(fig_loan_size)
else:
    st.write("Please select at least one ISIN.")

