import mysql.connector
import pandas as pd

def server_connect(config):
    cnxn = mysql.connector.connect(**config)
    return cnxn.cursor(), cnxn

def server_process_kill(cursor = None):
    if cursor is not None:
        cursor.execute("SHOW PROCESSLIST")
        result = cursor.fetchall()
        for process in result:
            if process[4] == 'Sleep':
                cursor.execute("KILL {}".format(process[0]))

#컬럼 받기
def server_get_column(cursor = None, table = ''):
    if cursor is not None:
        cursor.execute("SHOW FULL COLUMNS FROM {};".format(table))
        column_result = cursor.fetchall()
        print(column_result)
        print(list(map(lambda x: x[0], column_result)))

#dataframe으로 받기
def server_get_df(cursor = None, table = ''):
    cursor.execute("SHOW FULL COLUMNS FROM {};".format(table))
    column_result = cursor.fetchall()
    cursor.execute("SELECT * FROM {}".format(table))
    result = cursor.fetchall()
    df = pd.DataFrame(result, columns=list(map(lambda x: x[0], column_result)))
    return df
