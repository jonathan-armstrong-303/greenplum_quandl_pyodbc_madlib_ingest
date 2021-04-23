import quandl
import pyodbc
import pandas as pd

# Quandl will supply you with an API key upon registering.
quandl.ApiConfig.api_key = 'YOUR_QUANDL_KEY_HERE'

cnxn = pyodbc.connect('DRIVER={/opt/Progress/DataDirect/Connect64_for_ODBC_71/lib/ddgplm27.so};'
'LogonID=gpadmin;'
'Password=gpadmin;'
'Database=development;'
'HostName=192.168.0.200;'
'PortNumber=5432;'
'AutoCommit=True')

def get_quandl_df(quandl_dataset):
    output_df = quandl.get(quandl_dataset, returns="pandas", parse_dates=['Date'])

    return output_df

# write the DF to flat file if desired
def write_quandl_df(input_df, output_filename):
    input_df.to_csv(output_filename, encoding='utf-8', index=False)

# display some of the most common Pandas DF metrics on a DF
def desc_quandl_df(input_df):

    print ("HEAD OF", input_df)
    print (input_df.head())

    print ("INDEX OF", input_df)
    print (input_df.index)

    print ("COLUMNS OF",input_df, "BEFORE reset_index")
    print (input_df.columns)

    print ("INFO OF", input_df)
    print (input_df.info())

    print ("DESCRIBE OF", input_df)
    print (input_df.describe())


# performs some common cleanup/"munging" type tasks if desired:
def reformat_df(input_df, remove_index=True):
    # removes indices if desired so columns can be referenced in cursor inserted
    # into database table.
    # If desired, we can re-add an index again if we want to do a Pandas DataFrame
    # operation after we perform the insert.
    if remove_index is True:
        input_df.reset_index(inplace=True)
    elif remove_index is False:
        input_df = input_df.reset_index()

    #strip whitespace from column names and replace with underscores
    input_df.columns = [x.strip().replace(' ', '_') for x in input_df.columns]

    #get rid of those irritating NaN Pandas dataframe values
    input_df = input_df.fillna(0)
    return input_df

# load the dataframe into Greenplum
def load_gpdb_table(input_df, input_table='pd_pt_prices'):
    cursor = cnxn.cursor()
    # truncate table before every load.
    cursor.execute(f'TRUNCATE TABLE {input_table}')

    # Insert Dataframe into Greenplum DB:
    for index, row in input_df.iterrows():
        cursor.execute("INSERT INTO pd_pt_prices(closing_date, \
                        pd_usd_am, pd_usd_pm, \
                        pd_eur_am, pd_eur_pm, \
                        pd_gbp_am, pd_gbp_pm, \
                        pt_usd_am, pt_usd_pm, \
                        pt_eur_am, pt_eur_pm, \
                        pt_gbp_am, pt_gbp_pm ) \
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", \
                        row.Date, \
                        row.Pd_USD_AM, row.Pd_USD_PM, \
                        row.Pd_EUR_AM, row.Pd_EUR_PM, \
                        row.Pd_GBP_AM, row.Pd_GBP_PM, \
                        row.Pt_USD_AM, row.Pt_USD_PM, \
                        row.Pt_EUR_AM, row.Pt_EUR_PM, \
                        row.Pt_GBP_AM, row.Pt_GBP_PM)
    cnxn.commit()
    cursor.close()
