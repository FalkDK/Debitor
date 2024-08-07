import requests
import os
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

def get_news(free_text='', from_date=None, to_date=None, market='', company='', category=''):
    url = "https://api.news.eu.nasdaq.com/news/query.action"
    
    params = {
        'type': 'json',
        'showAttachments': 'true',
        'showCnsSpecific': 'true',
        'showCompany': 'true',
        'countResults': 'false',
        'displayLanguage': 'en',
        'freeText': free_text,
        'market': market,
        'company': company,
        'cnscategory': category,
        'fromDate': int(from_date.timestamp() * 1000) if from_date else '',
        'toDate': int(to_date.timestamp() * 1000) if to_date else '',
        'limit': '20',
        'start': '0'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error: {}".format(response.status_code))
        return None

def download_xml(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded XML: {save_path}")

def load_xml():
    data_folder = "./Data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    mapping = {
    "Jyske Realkredit A/S": "Data on debtor",
    "Nordea Kredit Realkreditaktieselskab": "debtor",
    "Nykredit Realkredit A/S": "Debtor distribution",
    "DLR Kredit A/S": "Debitormassens sammensætning",
    "Realkredit Danmark A/S": 'Breakdown of debtors',
}

    mapping_short = {
        "Jyske Realkredit A/S": "Jyske",
        "Nordea Kredit Realkreditaktieselskab": "Nordea",
        "Nykredit Realkredit A/S": "Nykredit",
        "DLR Kredit A/S": "DLR",
        "Realkredit Danmark A/S": 'RD',
    }

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    file_paths = {}

    for key, value in mapping.items():
        news = get_news(
            free_text=value,
            from_date=start_date,
            to_date=end_date,
            company=key,
            market="Main Market, Copenhagen"
        )

        if news and 'results' in news and 'item' in news['results'] and news['results']['item']:
            if 'Realkredit Danmark A/S' not in key:
                attachment_url = news['results']['item'][0]['attachment'][0]['attachmentUrl']
            else:
                attachment_url = news['results']['item'][0]['attachment'][1]['attachmentUrl']
            published_date = str(pd.to_datetime(news['results']['item'][0]['published']).strftime('%Y-%m-%d'))
            file_name = f"{published_date}_{mapping_short[key]}.xml"
            save_path = os.path.join(data_folder, file_name)
            download_xml(attachment_url, save_path)
            file_paths[key] = save_path

    all_data = []

    for company, file_path in file_paths.items():
        try:
            print(f"Parsing XML: {file_path}")
            tree = ET.parse(file_path)
            root = tree.getroot()

            for debitormasse in root.findall('debitormasse'):
                record = {}
                record['isin'] = debitormasse.findtext('isin')
                record['laan_gruppe'] = debitormasse.findtext('laan_gruppe')
                restgaeldinterval = debitormasse.findtext('restgaeldinterval')
                record['restgaeldinterval'] = int(restgaeldinterval) if restgaeldinterval is not None else None
                D = debitormasse.find('D')
                if D is not None:
                    for child in D:
                        record[child.tag] = float(child.text) if child.text is not None else None
                all_data.append(record)
        except Exception as e:
            print(f"Error loading file {file_path}: {str(e)}")

    return pd.DataFrame(all_data)
