# Danish Bonds Analysis App

## Overview
This Streamlit app provides comprehensive analysis and visualization of Danish bond data. It allows users to explore various metrics such as debtor distribution, average loan size, and share of obligations (obl) and cash loans across selected ISINs. Furthermore, the app highlights the top 50 ISINs with the highest percentage in '+50m' loan size, offering insights into larger financial movements within the Danish bond market.

## Features
- **Data Loading**: Automated loading and parsing of XML data files containing bond information.
- **Interactive Analysis**: Users can select specific ISINs for detailed analysis.
- **Visualization**: Utilizes Plotly for dynamic charting to represent debtor distribution and loan sizes.
- **Top 50 ISINs Analysis**: Special focus on the top 50 ISINs exceeding 50 million in loan size.

## Setup

### Requirements
- Python 3.6+
- Streamlit
- Pandas
- Plotly
- XML.etree.ElementTree

### Installation
1. Clone this repository to your local machine.
2. Install the required Python packages:
   ```bash
     pip install streamlit pandas plotly

## Running the App
Navigate to the project directory in your terminal and execute the following command:
```bash
streamlit run streamlit_app.py
```
## Usage
After launching the app, you'll encounter the main interface, which includes:

- **ISIN Selection Sidebar**: Use the multiselect dropdown to choose one or more ISINs you wish to analyze.

- **Page Navigation**: Utilize the `st.radio` buttons to toggle between different analysis views:
    - **Full Table**: This view presents a comprehensive analysis for the chosen ISINs, detailing debtor distribution percentages, average loan sizes, and a merged DataFrame that combines various metrics for a quick overview.
    - **List Large Loans**: Specifically focuses on identifying the top 50 ISINs with the largest loans, particularly those exceeding 50 million. This section aims to highlight significant financial movements within the Danish bond market.

Choose the appropriate radio button to navigate between the analysis pages. The visualizations and tables will update based on the selected ISINs and the analysis page you are viewing.

