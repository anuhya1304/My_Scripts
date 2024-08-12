import pandas as pd
import pyodbc
import threading
import os

# File path 
dest_folder = r'' #please add the path 
file_path = ""
files=os.listdir(file_path)

# Database connection details
driver = ""
SQL_server = ""
SQL_database = ""
SQL_password = ""
port = ""
SQL_user = ""


conn_str = f'DRIVER={driver};SERVER={SQL_server};PORT={port};DATABASE={SQL_database};UID={SQL_user};PWD={SQL_password}'

# Function to execute SQL operations with threading
def execute_sql(df_unpivot_list1, sTableName, sql_clmns_str, placeholder):
    try:
        conn = pyodbc.connect(conn_str, autocommit=False, Timeout=3600)
        cursor = conn.cursor()
        cursor.fast_executemany = True
        
        insert_statement = f"SET NOCOUNT ON;INSERT INTO {sTableName} ({sql_clmns_str}) VALUES ({placeholder})"
        cursor.executemany(insert_statement, df_unpivot_list1)  # Insert data
        conn.commit()  # Commit the transaction
        print(f"Thread {threading.current_thread().name}: Inserted {len(df_unpivot_list1)} rows into {sTableName}")
    except Exception as e:
        print(f"Thread {threading.current_thread().name}: Error executing SQL: {e}")
    finally:
        cursor.close()
        conn.close()

def process_batches(batches, sTableName, sql_clmns_str, placeholder):
    threads = []
    for batch in batches:
        thread = threading.Thread(target=execute_sql, args=(batch, sTableName, sql_clmns_str, placeholder))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

# Iterate over each file in the directory
for file in files:
    files_path = os.path.join(file_path, file) 
    df = pd.read_excel(files_path)
    
    # src_path = os.path.join(filepath,f)
    # des_path = os.path.join(dest_folder,f)  
    # os.rename(src_path,des_path)

    # Fetch column mapping from SQL table
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    sTableName = ''
    sql_query = 'SELECT * FROM {table_name}'
    table2_df = pd.read_sql_query(sql_query, conn)
    mapping_dict = table2_df.set_index('input_columns')['db_columns'].to_dict()

    # Rename DataFrame columns
    df_renamed = df.rename(columns=mapping_dict)

    # Prepare SQL insert statement
    sql_columns = list(mapping_dict.values())
    sql_clmns_str = ', '.join(sql_columns)
    placeholder = ', '.join(['?'] * len(sql_columns))

    # Unique combinations of Project_code and Version_no(an sample column data chane accordingly to the data you have)
    version_number = df_renamed['Project_code'].unique()
    Project_code = df_renamed['Version_no'].unique()

    batch_size = 1000  # Adjust the batch size based on your performance needs
    num_threads = 4  # Number of threads to use

    for pro, version in zip(Project_code, version_number):
        Projectcode = pro
        version_number = version
        
        query = f"SELECT TOP 1 * FROM {table_name} WHERE Project_code = '{Projectcode}' AND Version_no = '{version_number}'"
        cursor.execute(query)
        existing_data = cursor.fetchall()
        
        if len(existing_data) != 0:
            cursor.execute(f"DELETE FROM {table_name} WHERE Project_code = '{Projectcode}' AND Version_no = '{version_number}'")
            conn.commit()
            print(f"Deleted existing data for Project_code = {Projectcode} and Version_no = {version_number}")

        df_unpivot_lt = df_renamed.values.tolist()
        
        # Split the data into batches
        batches = [df_unpivot_lt[i:i + batch_size] for i in range(0, len(df_unpivot_lt), batch_size)]
        
        # Process the batches in parallel using threads
        for i in range(0, len(batches), num_threads):
            process_batches(batches[i:i + num_threads], sTableName, sql_clmns_str, placeholder)
            
    src_path = files_path
    des_path = os.path.join(dest_folder, file)
    os.rename(src_path, des_path)
    print(f"Moved file {file} to {dest_folder}")

    cursor.close()
    conn.close()
