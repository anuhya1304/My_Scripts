import pandas as pd
import pyodbc
import threading


# File path 
file_path=""


#database connection details
driver = ""
SQL_server = ""
SQL_database = ""
SQL_password = ""
port = ""
SQL_user = ""


# Read Excel file
df = pd.read_excel(file_path)


# Database connection string
conn1 = f'DRIVER={driver};SERVER={SQL_server};PORT={port};DATABASE={SQL_database};UID={SQL_user};PWD={SQL_password}'

# Function to execute SQL operations
def execute_sql(df, conn1, sTableName, mapping_dict):
    conn = pyodbc.connect(conn1)
    cursor = conn.cursor()
    
    # Rename DataFrame columns
    df_renamed = df.rename(columns=mapping_dict)
    
    # Prepare SQL insert statement
    sql_columns = list(mapping_dict.values())
    sql_clmns_str = ', '.join(sql_columns)
    placeholder = ', '.join(['?'] * len(sql_columns))
    insert_statement = f"SET NOCOUNT ON;INSERT INTO {sTableName} ({sql_clmns_str}) VALUES ({placeholder})"
    
    # Loop through DataFrame rows and execute insert statement
    for index, row in df_renamed.iterrows():
        values = tuple(row[sql_columns])
        cursor.execute(insert_statement, values)
    
    # Commit the transaction
    conn.commit()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

# Fetch column mapping from SQL table
def get_column_mapping(conn1, sql_query):
    conn = pyodbc.connect(conn1)
    table2_df = pd.read_sql_query(sql_query, conn)
    mapping_dict = table2_df.set_index('input_columns')['db_columns'].to_dict()
    conn.close()
    return mapping_dict

# Table and query details
sTableName = "table_1"
table2 = 'Table_2'
sql_query = 'SELECT * FROM table_2'

# Get the column mapping dictionary
mapping_dict = get_column_mapping(conn1, sql_query)

# Create and start a thread for SQL execution
sql_thread = threading.Thread(target=execute_sql, args=(df, conn1, sTableName, mapping_dict))
sql_thread.start()

# Optional: Wait for the thread to finish
sql_thread.join()
