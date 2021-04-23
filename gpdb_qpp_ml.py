import gpdb_q_helper as gqh
import pandas as pd

def main():
# Load the data from Quandl
    df_pd = gqh.get_quandl_df('LPPM/PALL')
    df_pt = gqh.get_quandl_df('LPPM/PLAT')

    df_pd.columns = ['Pd_USD_AM', 'Pd_EUR_AM', 'Pd_GBP_AM', 'Pd_USD_PM', 'Pd_EUR_PM', 'Pd_GBP_PM']
    df_pt.columns = ['Pt_USD_AM', 'Pt_EUR_AM', 'Pt_GBP_AM', 'Pt_USD_PM', 'Pt_EUR_PM', 'Pt_GBP_PM']

    # join Pd & Pt dataframes on date and return a single flattened dataframe
    df_pd_pt = pd.merge(left=df_pd, right=df_pt,
                        left_index=True, right_index=True)


    # remove the index so index field can be explicitly referenced in insert cursor
    df_pd_pt = gqh.reformat_df(df_pd_pt, True)

    # insert data into Greenplum
    gqh.load_gpdb_table(df_pd_pt)

if __name__ == "__main__":
    main()
