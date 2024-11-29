import duckdb
from databaseupload import Upload
import os
from openpyxl import load_workbook
from utilsfol.All_rmse_calc import AllRMSECalc
from utilsfol.All_mbe_calc import AllMBECalc
# from utilsfol.All_correlation_calc import CorrelationCalcAll
import plotly.graph_objects as go
from utils import DataHandler, ColumnMapping
from ReadData import readdata

from utilsfol.correlation_cal_db import CorrelationCalcAll
from utilsfol.apply_adaption_db import AdaptionMain

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import warnings

from datetime import datetime


warnings.filterwarnings("ignore")


st.set_page_config(
    page_title="Solar Site Adaption",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)


@st.cache_data
def cached_load_data(uploaded_file):

    df, data_type, data_dict = readdata(uploaded_file)

    columnmapping = ColumnMapping(df)
    col_mapped_dict = columnmapping.column_flag_mapping()

    datahandler = DataHandler(df, col_mapped_dict)
    if data_type == 'Measured':
        df = datahandler.df_format()
        df = datahandler.interpolate_data()
        df_1hr = datahandler.resample_data()
    if data_type == 'Satellite':
        df_1hr = datahandler.resample_sat_data()

    return df, data_type, data_dict, col_mapped_dict, df_1hr


def initialize_database(conn):

    conn.execute('''
        CREATE TABLE IF NOT EXISTS source_data (
            Timestamp DATETIME,
            hour INTEGER,
            day	INTEGER,
            month INTEGER,
            year INTEGER,
            date Date,
            datasetid	VARCHAR,
            variable	VARCHAR,
            value FLOAT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS resample_data (
            Timestamp DATETIME,
            hour INTEGER,
            day	INTEGER,
            month INTEGER,
            year INTEGER,
            date Date,
            datasetid	VARCHAR,
            variable	VARCHAR,
            value FLOAT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS GHI_bins (
            Timestamp DATETIME,
            hour INTEGER,
            day	INTEGER,
            month INTEGER,
            year INTEGER,
            date Date,
            datasetid	VARCHAR,
            variable	VARCHAR,
            value FLOAT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS output_data (
            Timestamp   DATETIME,
            datasetid	VARCHAR,
            variable	VARCHAR,
            value       FLOAT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS correlation_data (
            type            VARCHAR,
            groupby	        VARCHAR,
            Correlation	     FLOAT,
            Correlation_Per  FLOAT
        )
    ''')


if "db_init" not in st.session_state:
    st.session_state.db_init = False

if not st.session_state.db_init:
    st.session_state.db_init = True
    conn = duckdb.connect(database=':memory:')
    st.session_state.conn = conn
    initialize_database(conn)


def cached_fileupload_database(conn, df, df_1hr, data_type, filename):
    upload = Upload(conn, df, df_1hr, data_type, filename)
    upload.source_data()
    upload.upload_resample_data()


def cached_adaption(conn, measured_file, satellite_file):
    reg_result_adap1_dict = {}
    reg_result_adap2_dict = {}
    adap_col_list = ['GHI', 'DNI', 'Temp']

    upload = Upload(conn)
    upload.output_data_creation()

    for adap_col in adap_col_list:
        common_df = conn.sql(
            f"select * from resample_data a, resample_data b Where a.Timestamp = b.Timestamp and a.datasetid = '{measured_file}' and b.datasetid = '{satellite_file}' and a.value>0 and b.value>0 and lower(a.variable) like lower('{adap_col}%') and lower(b.variable) like lower('{adap_col}%') ").df()

        common_df1 = conn.sql(f"""select Timestamp,datasetid,variable,value from resample_data a Where a.datasetid = '{measured_file}' and a.value>0 and value is not null and lower(a.variable) like lower('{adap_col}%')
                              UNION
                                  select Timestamp,datasetid,variable,value from resample_data b Where b.datasetid = '{satellite_file}'  and b.value>0 and value is not null  and  lower(b.variable) like lower('{adap_col}%') """).df()

        # st.write(conn.execute("SELECT * FROM output_data").df())
        measured_adap_cols = list(common_df['variable'].unique())
        satellite_adap_cols = list(common_df['variable_1'].unique())

        adap_datasetid = measured_file+'_'+satellite_file

        for cols in measured_adap_cols:
            measured_adap_col = cols
            satellite_adap_col = satellite_adap_cols[0]

            temp_df = common_df1.pivot(index=['Timestamp'], columns=[
                                       'variable'], values='value')
            temp_df = temp_df.dropna()

            m_pivot_query = f""" WITH pivot_alias AS (
                        PIVOT resample_data
                        ON variable
                        USING first(value))
                        Select Timestamp,"{cols}" from pivot_alias Where datasetid = '{measured_file}' and "{cols}" is not null order by Timestamp
                    """
            s_pivot_query = f""" WITH pivot_alias AS (
                        PIVOT resample_data
                        ON variable
                        USING first(value))
                        Select Timestamp,"{satellite_adap_col}" from pivot_alias Where datasetid = '{satellite_file}' and "{satellite_adap_col}" is not null order by Timestamp
                    """
            tmp_measured_data = conn.sql(m_pivot_query).df()
            tmp_satellite_data = conn.sql(s_pivot_query).df()

            tmp_satellite_data.set_index('Timestamp', inplace=True)
            tmp_measured_data.set_index('Timestamp', inplace=True)

            # Apply adaptation methods
            adaptionmain = AdaptionMain(
                tmp_satellite_data, tmp_measured_data, temp_df, measured_adap_col, satellite_adap_col, adap_col)

            reg_result_adap1, satellit_df_adap1 = adaptionmain.applyadaption_met1()
            reg_result_adap2, satellit_df_adap2 = adaptionmain.applyadaption_met2()

            satellit_df_adap1.reset_index(inplace=True)
            satellit_df_adap2.reset_index(inplace=True)

            adap1_db_query = f"""
                        Insert into output_data
                        Select Timestamp, '{satellite_file}', '{adap_col}'||'_Adapted_1', {adap_col.lower()}_adapted_1
                        from satellit_df_adap1
                        """
            conn.sql(adap1_db_query)

            adap2_db_query = f"""
                        Insert into output_data
                        Select Timestamp,' {satellite_file}', '{adap_col}'||'_Adapted_2', {adap_col.lower()}_adapted_2
                        from satellit_df_adap2
                        """
            conn.sql(adap2_db_query)

            reg_result_adap1_dict[adap_col] = satellit_df_adap1
            reg_result_adap2_dict[adap_col] = satellit_df_adap2
    # st.write('the output data is:')
    # st.write(conn.execute("SELECT * FROM output_data").df())

    return common_df, reg_result_adap1_dict, reg_result_adap2_dict


def cached_correlation(conn, measured_file, satellite_file):
    correlation_results_dict = {}
    adap_col_list = ['GHI', 'DNI', 'Temp']

    for adap_col in adap_col_list:
        # Fetch data directly from output_data
        common_df_2 = conn.sql(f"""
            SELECT *
            FROM output_data
            WHERE LOWER(variable) LIKE LOWER('{adap_col}%')
        """).df()
        st.write('The fetched common_df is:', common_df_2)

        if not common_df_2.empty:
            # Pivot the data for correlation calculation
            pivot_df = common_df_2.pivot_table(
                index='Timestamp',
                columns=['variable'],
                values='value'
            )
            pivot_df = pivot_df.dropna()  # Drop rows with missing values

            # Define mea_cols as a dictionary
            mea_cols = {
                'GHI': 'GHI',
                'DNI': 'DNI',
                'Temp': 'Temp'
            }

            # Calculate correlations
            correlation_calculator = CorrelationCalcAll(
                pivot_df, mea_cols  # Pass mea_cols as a dictionary
            )
            overall_corr, hourly_corr, monthly_corr = correlation_calculator.cal_corr([
                f'{adap_col}', f'{adap_col}_Adapted_1', f'{adap_col}_Adapted_2'
            ])

            correlation_results_dict[adap_col] = {
                'Overall': overall_corr,
                'Hourly': hourly_corr,
                'Monthly': monthly_corr
            }

    # Compile results into a DataFrame
    data = []
    for variable, results in correlation_results_dict.items():
        for metric, value in results.items():
            data.append(
                {"Variable": variable, "Metric": metric, "Value": value})
    df = pd.DataFrame(data)

    # Save to the database
    conn.execute(
        "CREATE TABLE IF NOT EXISTS correlationtable AS SELECT * FROM df")
    st.write("Correlation Table Data:")
    st.write(conn.execute("SELECT * FROM correlationtable").df())

    return correlation_results_dict


# Create tabs
datasettab, adaptiontab = st.tabs(
    ["📝 Dataset", '📊 AdaptionTab'])


timezone_path = './static/time_zone.csv'

timezone_df = pd.read_csv(timezone_path, encoding='ISO-8859-1')
unique_timezones = timezone_df['UTC'].unique()


# Content for Tab 1
with datasettab:

    # Upload multiple files
    uploaded_files = st.file_uploader(
        "Add Datasets", type=['csv', 'txt', 'xlsx'], accept_multiple_files=True)

    files_dict = {}
    data_dicts_list = []
    db_upload = []
    all_files = []

    satellite_file = None
    measured_file = None

    if 'db_upload' not in st.session_state:
        st.session_state.db_upload = []
    if 'adap_comp' not in st.session_state:
        st.session_state.adap_comp = False
    if 'mbe_cal' not in st.session_state:
        st.session_state.mbe_cal = False
    # Save the uploaded files in session state
    if uploaded_files is not None:
        st.session_state.uploaded_files = uploaded_files

    if st.session_state.uploaded_files is not None:

        cols = st.columns(1 if len(uploaded_files) ==
                          0 else len(uploaded_files))

        for idx, file in enumerate(uploaded_files):
            filename = file.name.split('.')[0]
            all_files.append(filename)

        for idx, file in enumerate(uploaded_files):
            data_dict1 = {}
            filename = file.name.split('.')[0]

            df, data_type, data_dict, col_mapped_dict_tmp, df_1hr = cached_load_data(
                file)

            if data_type == "Satellite":
                df_1hr = df.copy()
            else:
                col_mapped_dict = col_mapped_dict_tmp
            files_dict[filename] = {
                'df': df, 'data_type': data_type, 'resampled_data': df_1hr}
            data_dict1['File Name'] = filename
            data_dict1['Data Type'] = data_type
            data_dict1.update(data_dict)
            data_dict1['Data Starts Date'] = df.index.min()
            data_dict1['Data Ends Date'] = df.index.max()

            data_dict_df = pd.DataFrame(
                list(data_dict1.items()), columns=['Key', 'Value'])

            files_dict[filename]['data_dict_df'] = data_dict_df

            with cols[idx]:
                st.markdown(
                    f"<h1 style='font-size: 25px;'>{filename}</h1>",
                    unsafe_allow_html=True
                )
                # st.write(data_dict_df)
                st.dataframe(data_dict_df, hide_index=True,
                             use_container_width=True)
                selected_timezone = st.selectbox(
                    f"Please Select the required Time Zone for {filename}",
                    options=unique_timezones
                )

            conn = st.session_state.conn

            measured_cnt = 0
            satellite_cnt = 0

            for keys, values in files_dict.items():
                if values['data_type'] == 'Satellite':
                    satellite_cnt = satellite_cnt+1
                    satellite_file = [
                        filename for filename, value in files_dict.items() if value['data_type'] == 'Satellite'][0]

                if values['data_type'] == 'Measured':
                    measured_cnt = measured_cnt+1
                    measured_file = [
                        filename for filename, value in files_dict.items() if value['data_type'] == 'Measured'][0]

            if filename not in st.session_state.db_upload:
                print('Uploadinnggg.....')
                db_upload = st.session_state.db_upload
                db_upload.append(filename)
                st.session_state.db_upload = db_upload
                a = cached_fileupload_database(
                    conn, df, df_1hr, data_type, filename)

                if satellite_cnt == 1 and measured_cnt == 1:
                    # cached_adaption()
                    print('Applying Adaption')

            # For Debugging Adaption
            st.session_state.adap_comp = False
            st.session_state.mbe_cal = False

            # Get the Measured and Satellite data types
            if satellite_file and measured_file and not st.session_state.adap_comp:
                a, reg_result_adap1, reg_result_adap2 = cached_adaption(
                    conn, measured_file, satellite_file)

                st.session_state.reg_result_adap1 = reg_result_adap1
                st.session_state.reg_result_adap2 = reg_result_adap2

                st.session_state.adap_comp = True

                st.write(conn.sql(
                    f"Select * from output_data where lower(variable) like '%adap%'").df())

            if satellite_file and measured_file and not st.session_state.mbe_cal:
                correlation_results_dict = cached_correlation(
                    conn, measured_file, satellite_file)

                # Store results in session state
                st.session_state.correlation_results_df = correlation_results_dict

                st.session_state.mbe_cal = True
                #  insert_correlation_results(conn, correlation_results_dict)

            if not all_files == st.session_state.db_upload:
                for dbfile in st.session_state.db_upload:
                    if dbfile not in all_files:
                        print('Removing----'+dbfile)
                        st.session_state.db_upload.remove(dbfile)
                        st.session_state.adap_comp = False
                        st.session_state.download_df = False
                        conn.sql(
                            f"delete from source_data where datasetid = '{dbfile}'")
                        conn.sql(
                            f"delete from resample_data where datasetid = '{dbfile}'")

            # st.write(conn.sql("Select count(*),datasetid from source_data group by datasetid").df())
            # st.write(conn.sql("Select count(*),datasetid from resample_data group by datasetid").df())
        st.session_state.files_dict = files_dict

    else:
        st.write("Please Upload the file.")


with adaptiontab:

    adap_datasettab, adap_graphtab, down_csvtab = st.tabs(
        ["📝 Adaption", "📈 Graph", "💾 CSV Download"])
    if st.session_state.adap_comp:
        with adap_graphtab:
            if st.session_state.adap_comp:
                variables = conn.sql("SELECT DISTINCT variable FROM output_data").df()[
                    "variable"].tolist()

                if "var" not in st.session_state:
                    st.session_state.var = variables

                # selected_columns = st.multiselect("Select variables to plot", options=variables)
                selected_columns = st.multiselect(
                    "What are your favorite colors",
                    st.session_state.var, st.session_state.var[0],
                )

                # Query DuckDB to get data for the selected variable
                if selected_columns:

                    # selected_columns_str = "'" + "', '".join(selected_columns) + "'"

                    # query = f"""
                    #     SELECT Timestamp, variable, value
                    #     FROM output_data
                    #     WHERE variable IN ({selected_columns_str})
                    #     ORDER BY Timestamp
                    # """
                    # data = conn.sql(query).df()

                    fig_adap2 = go.Figure()
                    for idx, varr in enumerate(selected_columns):
                        query = f"""
                        SELECT Timestamp, variable, value 
                        FROM output_data 
                        WHERE variable IN ('{varr}')
                        ORDER BY Timestamp
                        """
                        variable_data = conn.sql(query).df()
                        # variable_data = data[data["variable"] == varr]
                        fig_adap2.add_trace(go.Scatter(
                            x=variable_data['Timestamp'],
                            # Replace with your DNI column name
                            # y=resampled_measured_data[mea_ghi_col]
                            y=variable_data['value'],
                            mode='lines',
                            name=varr))
                    # fig = px.line(data,x='Timestamp', y='value', color="variable", title=f"Comparison Graph")

                    st.plotly_chart(fig_adap2)
    else:
        st.write(
            "Please Upload Both Satellite Data and Measured Data for Site Adaption")
    if st.session_state.adap_comp:
        with down_csvtab:

            # down_pivot_query = f""" WITH pivot_alias AS (
            #             PIVOT output_data
            #             ON variable
            #             USING first(value))
            #             Select * from pivot_alias order by Timestamp
            #         """
            # download_df = conn.sql(down_pivot_query).df()
            # Fetch unique variable names
            variables = conn.execute(
                "SELECT DISTINCT variable FROM output_data order by variable").fetchdf()["variable"].tolist()

            if "download_df" not in st.session_state:
                st.session_state.download_df = False
            st.session_state.download_df = False
            if not st.session_state.download_df:
                # Build dynamic pivot query
                pivot_query = f"""
                SELECT Timestamp,
                    {', '.join([f"MAX(CASE WHEN variable = '{var}' THEN Value END) AS '{var}'" for var in variables])}
                FROM output_data
                GROUP BY Timestamp
                ORDER BY Timestamp
                """
                download_df = conn.sql(pivot_query).df()
                st.session_state.download_df = True
                print(st.session_state.download_df)

            if st.session_state.download_df:
                # csv = download_df.to_csv()
                # st.download_button(
                #     label="Download Adapted Data",
                #     data=csv,
                #     file_name="Adapted_Meteo_Data.csv",
                #     mime="text/csv",
                # )
                # Save file to specified path on the server

                if st.button("Save to Server"):
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        default_path = os.path.join(os.path.expanduser(
                            "~"), "Downloads", f"Site_Adapted_Data_{timestamp}.csv")

                        # Check if a path was selected
                        if default_path:
                            # Save the DataFrame to the selected file path
                            download_df.to_csv(default_path, index=False)
                            st.success(
                                f"File successfully saved to {default_path}")
                        else:
                            st.warning("Download was canceled.")

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
    else:
        st.write(
            "Please Upload Both Satellite Data and Measured Data for Site Adaption")


# %%
# def cached_correlation(conn, measured_file, satellite_file):
#     # Initialize dictionaries to store correlation results for each adaptation type
#     correlation_results = []
#     adap_col_list = ['GHI', 'DNI', 'Temp']

#     upload = Upload(conn)
#     upload.correlation_data_creation()

#     for adap_col in adap_col_list:
#         # Retrieve data for measured and satellite files with the current adaptation column
#         common_df = conn.sql(
#             f"select * from resample_data a, resample_data b Where a.Timestamp = b.Timestamp "
#             f"and a.datasetid = '{measured_file}' and b.datasetid = '{satellite_file}' "
#             f"and a.value>0 and b.value>0 and lower(a.variable) like lower('{adap_col}%') "
#             f"and lower(b.variable) like lower('{adap_col}%')"
#         ).df()
#         temp_common_df = common_df
#         # Apply correlation calculations for Overall, Hourly, and Monthly
#         correlation_calc = CorrelationCalcAll(
#             temp_common_df, mea_ghi_col='GHI', mea_dni_col='DNI', mea_temp_col='Temp')

#         # Overall correlation
#         overall_corr = correlation_calc.cal_corr([adap_col])
#         correlation_results.append({
#             'type': 'Overall',
#             'groupby': 'None',
#             'Correlation': overall_corr[0],
#             'correlation_per': adap_col
#         })

#         # Hourly correlation
#         hourly_corr = correlation_calc.calculate_hourly_correlations([
#                                                                      adap_col])
#         for idx, row in hourly_corr.iterrows():
#             correlation_results.append({
#                 'type': 'Hourly',
#                 'groupby': row['Hour'],
#                 'Correlation': row[f'Correlation_{adap_col}'],
#                 'correlation_per': adap_col
#             })

#         # Monthly correlation
#         monthly_corr = correlation_calc.calculate_monthly_correlations([
#                                                                        adap_col])
#         for idx, row in monthly_corr.iterrows():
#             correlation_results.append({
#                 'type': 'Monthly',
#                 'groupby': row['Month'],
#                 'Correlation': row[f'Correlation_{adap_col}'],
#                 'correlation_per': adap_col
#             })

#     # Convert correlation results to a DataFrame
#     correlation_results_df = pd.DataFrame(correlation_results)

#     # Store the results in the database
#     for _, row in correlation_results_df.iterrows():
#         insert_query = f"""
#         INSERT INTO correlation_data
#         (type, groupby, correlation, correlation_per)
#         VALUES ('{row['type']}', '{row['groupby']}', {row['Correlation']}, '{row['correlation_per']}')
#         """
#         conn.sql(insert_query)
#     st.write('the Correlation df is:')
#     st.write(conn.execute("SELECT * FROM correlation_data").df())

#     return correlation_results_df
