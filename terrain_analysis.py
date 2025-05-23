# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 12:25:42 2025

@author: SaiAnuhyaKurra
"""

from osgeo import gdal
import rasterio
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import matplotlib.ticker as mticker
import sqlalchemy
import urllib

driver = ""
server = ""
database = ""
password = ""
port    = ""
uid     = ""

params = 'DRIVER='+driver + ';SERVER='+server + ';PORT=1433;DATABASE=' + database + ';UID=' + uid + ';PWD=' + password
db_params = urllib.parse.quote_plus(params)
engine = sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect={}".format(db_params),fast_executemany=True)

def get_area_index(project_id,bin_width= 1):
    sql_query =  "  "##select statement
    sql_df  = pd.read_sql(sql_query, engine)
    
    sql_df['bin_group'] = ((sql_df['bin_id']-1)//bin_width)*bin_width
    agg_df = sql_df.groupby(['project_code','bin_group']).agg({
    'frequency': 'sum',
    'pctbin': 'sum'
    }).reset_index()
    agg_df["pctcumm"] = agg_df.groupby('project_code')["pctbin"].cumsum()
    agg_df["pctinvcumm"] = (100 - agg_df["pctcumm"]).round(3)
    agg_df['bin_end'] = agg_df['bin_group'] + 5
    agg_df = agg_df.rename(columns={'bin_group': 'bin_start'})
    
    project_summ = agg_df.groupby(['project_code']).agg({'pctinvcumm':lambda x: (x * 0.05).sum()}).reset_index()
    project_summ = project_summ.rename(columns={'pctinvcumm': 'area'})
    area_min = project_summ['area'].min()
    area_max = project_summ['area'].max()
    project_summ['area_index'] = 1+ (project_summ['area'] - area_min) * 9 / (area_max - area_min)
    area_index = project_summ[project_summ['project_code']==project_id]['area_index'].values[0]
    return area_index

def process_tiff(slope_tiff_path, project_id ):
    with rasterio.open(slope_tiff_path) as dataset:
        bins = np.arange(0, 101, 1)
        bin_labels = np.arange(1, 101, 1)
        bin_counts = np.zeros(len(bin_labels), dtype=np.int64)
        total_pixels = 0

        for ji, window in dataset.block_windows(1):
            tiff_data = dataset.read(1, window=window)
            valid_mask = tiff_data != -9999
            tiff_data = tiff_data[valid_mask]
            total_pixels += len(tiff_data)
            digitized = np.digitize(tiff_data, bins, right=False) - 1
            digitized = np.clip(digitized, 0, len(bin_labels) - 1)
            for i in range(len(bin_labels)):
                bin_counts[i] += np.sum(digitized == i)

    new_df = pd.DataFrame({
        "project_code": project_id,
        "bin_id": bin_labels,
        "frequency": bin_counts
    })

    percentage_df = new_df.copy()
    percentage_df["pctbin"] = (bin_counts / total_pixels) * 100

    cumulative_df = percentage_df.copy()
    cumulative_df["pctcumm"] = cumulative_df["pctbin"].cumsum()

    inverse_cumulative_df = cumulative_df.copy()
    inverse_cumulative_df["pctinvcumm"] = (100 - cumulative_df["pctcumm"]).round(3)
    
    
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(
                sqlalchemy.text("DELETE FROM {table_name} WHERE project_code = :project_id"),
                {"project_id": project_id}
                )
        
    inverse_cumulative_df.to_sql('slope_summary', engine, index=False, if_exists="append", schema="dbo", method='multi')
    
    
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(
                sqlalchemy.text("DELETE FROM {table_name}")
                )
            conn.execute(
                sqlalchemy.text(""" Insert into slope_calc_summary
                                (	bin_id			,	 minpctbin			,	minpctcumm			,	 minpctinvcumm		,
                                	maxpctbin		,	 maxpctcumm			,	 maxpctinvcumm		,	 avgpctbin			,
                                	avgpctcumm		,	 avgpctinvcumm		)
                                    Select bin_id, min(pctbin), min(pctinvcumm), min(pctinvcumm), 
                                            max(pctbin), max(pctinvcumm), max(pctinvcumm), 
                                            Avg(pctbin), Avg(pctinvcumm), Avg(pctinvcumm) 
                                    From slope_summary 
                                    group by  bin_id  """
                                )
                        )
    

# Example usage
if __name__ == "__main__":
    
    sql_query_project =  " Select * from project"
    project_details  = pd.read_sql(sql_query_project, engine)
    print(project_details)
    
    project = "PR001"
    
    slope_tiff_path  =r"D:\REA\Murchison\Data\Slope\Murchison_SlopePercent.tif"
    
    bin_width = 5
    process_tiff(slope_tiff_path, project)
    area_index = get_area_index(project, bin_width)
