Danish Bonds Analysis App
Overview
This Streamlit app provides comprehensive analysis and visualization of Danish bond data. It allows users to explore various metrics such as debtor distribution, average loan size, and share of obligations (obl) and cash loans across selected ISINs. Furthermore, the app highlights the top 20 ISINs with the highest percentage in '+50m' loan size, offering insights into larger financial movements within the Danish bond market.

Features
Data Loading: Automated loading and parsing of XML data files containing bond information.
Interactive Analysis: Users can select specific ISINs for detailed analysis.
Visualization: Utilizes Plotly for dynamic charting to represent debtor distribution and loan sizes.
Top 20 ISINs Analysis: Special focus on the top 20 ISINs exceeding 50 million in loan size.
Setup
Requirements
Python 3.6+
Streamlit
Pandas
Plotly
XML.etree.ElementTree
Installation
Clone this repository to your local machine.
Install the required Python packages:
bash
Copy code
pip install streamlit pandas plotly
Ensure your data files (dlr.xml, jyk.xml, nda.xml, nyk.xml, rd.xml) are placed within a ./Data directory at the root of the project.
Running the App
Navigate to the project directory in your terminal and run:

bash
Copy code
streamlit run app.py
Replace app.py with the path to the script if your file has a different name.

Usage
Upon launching, the app will present a sidebar for ISIN selection and two main analysis pages:

Full Table: Displays detailed analysis for the selected ISINs, including debtor distribution percentages, average loan sizes, and merged dataframes showcasing a combination of metrics.
List Large Loans: Highlights the top 20 (or 50, based on your preference) ISINs with the largest loans, focusing on those exceeding 50 million.
Use the radio buttons to navigate between the analysis pages.

