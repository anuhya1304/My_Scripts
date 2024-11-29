# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 13:51:59 2023

@author: AshokKumarSathasivam
"""
import pandas as pd
import chardet

## ====TimeStamp column possible values to identify starting Row====##
ts_columns = ["Timestamp", "DateTime", "Date/Time", "Date", "datetime"]
preferred = [',', '\t', ';',  ':']
dele = ','

## ========Read data from file================##


def readdata(file):
    data_type = 'Satellite'
    dele = ','
    header_lineno = 0
    data_dict = {}
    for index, line in enumerate(file):
        line = line.decode("utf-8").strip()
        if ':' in line:
            key, value = line.split(':', 1)
            if key in ['Site name', 'Latitude', 'Longitude', 'Elevation', 'Time zone']:
                # Strip any whitespace
                data_dict[key.strip()] = value.strip().replace(',', '')
        if any(x in line for x in ['Windographer']):
            data_type = 'Measured'
        # for index, line in enumerate(f):
        if any(x in line for x in ts_columns):
            datecol = ' '.join(
                [x for x in ts_columns if x in str(line.strip())]).replace(',', '')
            header_lineno = index
            if any(x in line for x in preferred):
                dele = ' '.join(
                    [x for x in preferred if x in str(line.strip())])

    file_content = file.read(1024)
    result = chardet.detect(file_content)
    file.seek(0)

    data = pd.read_csv(file, sep=dele, header=0, skiprows=header_lineno, low_memory=False,
                       encoding=result['encoding'], parse_dates=[datecol], dayfirst=True)

    if datecol in ("Date", "Time"):
        datecol = "Timestamp"
        data[datecol] = pd.to_datetime(data['Date'].astype(
            str) + ' ' + data['Time'].astype(str))
    if datecol != "Timestamp":
        data["Timestamp"] = data[datecol]
        datecol = "Timestamp"

    data[datecol] = pd.to_datetime(data[datecol])
    data['date'] = pd.to_datetime(data[datecol]).dt.date
    data['day'] = (pd.to_datetime(data[datecol]).dt.day).astype('int')
    data['hour'] = pd.to_datetime(data[datecol]).dt.hour
    data['month'] = pd.to_datetime(data[datecol]).dt.month
    data[datecol] = pd.to_datetime(data[datecol], format='%d-%m-%Y %H:%M')
    data = data.set_index('Timestamp')
    return data, data_type, data_dict
# data,datecol = readdata('./MM1_05_Oct_2021_Validated-Exported.txt')
