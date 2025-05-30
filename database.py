import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host="108.167.132.58",  # IP do seu banco HostGator
        user="noust785_nousmeiadmin",
        password="N@usM31#",
        database="noust785_nousmei_app"
    )
