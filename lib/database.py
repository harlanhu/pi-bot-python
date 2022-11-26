import pymysql

conn = pymysql.connect(host='192.168.31.161', port=3306, user='root', password='lb82ndLF', db='pi-bot')


def execute_sql(sql):
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
        conn.commit()
    except Exception as e:
        conn.rollback()
