import pandas as pd
import time


class Upload():
    def __init__(self, conn, df=None, resample_df=None, data_type=None, filename=None):
        self.conn = conn
        self.df = df
        self.resample_df = resample_df
        self.data_type = data_type
        self.filename = filename

    def source_data(self):
        self.df.reset_index(inplace=True)
        self.df['datasetid'] = self.filename
        start_time = time.time()
        self.df['hour'] = self.df['Timestamp'].dt.hour
        self.df['day'] = self.df['Timestamp'].dt.day
        self.df['month'] = self.df['Timestamp'].dt.month
        self.df['year'] = self.df['Timestamp'].dt.year
        self.df['Date'] = self.df['Timestamp'].dt.date

        for col in list(self.df.columns):
            if col == "date":
                self.df = self.df.drop(['date'], axis=1)
            if col == "datetime":
                self.df = self.df.drop(['datetime'], axis=1)

        data_unpivot = pd.melt(self.df, id_vars=[
                               'Timestamp', 'hour', 'day', 'month', 'year', 'Date', 'datasetid'], value_vars=list(self.df.columns))
        print('Time Difference unpivot ' + str(time.time() - start_time))
        start_time = time.time()
        data_unpivot['req_col'] = 0
        data_unpivot.loc[data_unpivot['variable'].str.lower(
        ).str.startswith('ghi'), 'req_col'] = 1
        data_unpivot.loc[data_unpivot['variable'].str.lower(
        ).str.startswith('dni'), 'req_col'] = 1
        data_unpivot.loc[data_unpivot['variable'].str.lower(
        ).str.startswith('temp'), 'req_col'] = 1
        self.conn.sql("Insert into source_data(Timestamp,hour,day,month,year,date,datasetid,variable,value)  SELECT Timestamp,hour,day,month,year,date,datasetid,variable,value FROM data_unpivot where req_col = 1 and variable not like '%flags%'")
        print('Time Difference upload ' + str(time.time() - start_time))

    def upload_resample_data(self):
        self.resample_df.reset_index(inplace=True)
        self.resample_df['datasetid'] = self.filename

        for col in list(self.resample_df.columns):
            if col == "date":
                self.resample_df = self.resample_df.drop(['date'], axis=1)
            if col == "datetime":
                self.resample_df = self.resample_df.drop(['datetime'], axis=1)

        self.resample_df['hour'] = self.resample_df['Timestamp'].dt.hour
        self.resample_df['day'] = self.resample_df['Timestamp'].dt.day
        self.resample_df['month'] = self.resample_df['Timestamp'].dt.month
        self.resample_df['year'] = self.resample_df['Timestamp'].dt.year
        self.resample_df['date'] = self.resample_df['Timestamp'].dt.date

        data_unpivot = pd.melt(self.resample_df, id_vars=[
                               'Timestamp', 'hour', 'day', 'month', 'year', 'date', 'datasetid'], value_vars=list(self.resample_df.columns))
        data_unpivot['req_col'] = 0
        data_unpivot.loc[data_unpivot['variable'].str.lower(
        ).str.startswith('ghi'), 'req_col'] = 1
        data_unpivot.loc[data_unpivot['variable'].str.lower(
        ).str.startswith('dni'), 'req_col'] = 1
        data_unpivot.loc[data_unpivot['variable'].str.lower(
        ).str.startswith('temp'), 'req_col'] = 1

        self.conn.sql("Insert into resample_data(Timestamp,hour,day,month,year,date,datasetid,variable,value)  SELECT Timestamp,hour,day,month,year,date,datasetid,variable,value FROM data_unpivot where req_col = 1 and variable not like '%flags%'")

    def output_data_creation(self):
        output_db_query = """
                        Delete from output_data;
                        Insert into output_data
                        Select Timestamp, datasetid, variable, value
                        from resample_data
                        """
        self.conn.sql(output_db_query)
