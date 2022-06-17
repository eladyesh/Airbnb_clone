# importing the required modules
import sqlite3
from random import *
import time
import pandas as pd
from tkinter import messagebox
from xlsxwriter.workbook import Workbook

"""

DataBase Helper

in these functions, the name and the keys in the functions,
will always be type string

all the id keys (except room id) are primary and autoincremented and type integer

"""


def create_new_table(name, keys):
    """
    functions creates a new table for the database
    :param name: name of data base
    :param keys: the keys of the database
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    primary = f"{keys[0]} INTEGER PRIMARY KEY AUTOINCREMENT ,"
    finish = f"{','.join(key + ' text' for key in keys[1:])}"
    cur.execute(f'''CREATE TABLE IF NOT EXISTS {name}(
                    {primary + finish}
                    )
                ''')
    con.commit()
    con.close()


def delete(name):
    """
    function deletes the table from the database
    :param name: name of the database (as string)
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    cur.execute(f"DROP TABLE {name};")
    con.commit()


def order_by_parameter(name, parameter, order_by_parameter):
    """
    functions returns the information ordered by a certain parameter from database
    :param name: name of database
    :param parameter: the keys
    :param order_by_parameter: the key to order by
    :return: rows that are ordered by that parameter (as list)
    """
    select = ""
    for i in parameter:
        select += f"{i},"
    select = select[:-1]

    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    data = cur.execute(f'''SELECT {select} from {name} ORDER BY {order_by_parameter};''').fetchall()
    con.commit()
    return data


def insert_to_record(keys):
    """
    functions inserts to 'record' table the given keys
    :param keys: the keys to insert
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    cur.execute("INSERT INTO record VALUES (:user_id, :email, :name, :country, :password, "
                ":is_admin)", {
                    'user_id': keys[0],
                    'email': keys[1],
                    'name': keys[2],
                    'country': keys[3],
                    'password': keys[4],
                    'is_admin': 'False'
                })
    con.commit()


def check_if_user_exists(user_id):
    """
    function checks if user exists by the id
    :param user_id: the users id (as int)
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    usernamecheck = cur.execute("SELECT rowid FROM record WHERE user_id = ?",
                                (user_id,)).fetchall()

    if len(usernamecheck) != 0:
        return True


def update(data_base, update_key, update_value, where_key, where_value):
    """
    function updated the database at a specific row
    :param data_base: database name
    :param update_key: the key to update
    :param update_value: the value to update
    :param where_key: where a certain key
    :param where_value: equals to a certain value
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    cur.execute(f"UPDATE {data_base} set {update_key} = '{update_value}' where {where_key} = '{where_value}'")
    con.commit()


def insert_to_offers(keys):
    """
    function inserts certain keys into 'offer' table
    :param keys: the keys to insert
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    cur.execute(
        f"INSERT INTO offers VALUES (:offer_id, :user_id, :room_id, :price_per_day, :images, "
        f":time_available, "
        f":conditions, "
        f":room_name, "
        f":location)", {
            'offer_id': keys[0],
            'user_id': keys[1],
            'room_id': keys[2],
            'price_per_day': keys[3],
            'images': keys[4],
            'time_available': keys[5],
            'conditions': keys[6],
            'room_name': keys[7],
            'location': keys[8],
        })
    con.commit()


def fetch_all(name):
    """
    function gets all the information from a database
    :param name: database name
    :return: data on database
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    data = cur.execute(f"SELECT * FROM {name}").fetchall()
    return data


def fetch_by_location(name, key):
    """
    function gets all the information about a row from a certain table by the location (the 'offers' table)
    :param name:
    :param key:
    :return: row data from the database
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    data = cur.execute(f"SELECT * FROM {name} WHERE location = ?", (key,)).fetchall()
    return data


def fetch_by_parameter(name, parameter):
    """
    function gets
    :param name: database name
    :param parameter: parameter to search by
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    data = cur.execute(f"SELECT {parameter} FROM {name}").fetchall()
    return data


def fetch_row_by_parameter(name, parameter, key):
    """
    :param name: database name
    :param parameter: parameter to search by
    :param key: the value being searched for
    :return:
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    data = cur.execute(f"SELECT * FROM {name} WHERE {parameter} = ?",
                       (key,)).fetchall()
    return data


def insert_to_rating(keys):
    """
    function inserts to table 'ratings' certain keys
    :param keys: the keys to insert
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    cur.execute(f"INSERT INTO ratings VALUES (:purchase_id, :offer_id, :user_email, "
                f":scale_rating, :review, :is_anonymous)", {
                    'purchase_id': keys[0],
                    'offer_id': keys[1],
                    'user_email': keys[2],
                    'scale_rating': keys[3],
                    'review': keys[4],
                    'is_anonymous': keys[5]
                })
    con.commit()


def check_if_exists(name, parameter, key):
    """
    function checks is a row exists by a certain parameter
    :param name: database name
    :param parameter: the key to search by
    :param key: the value needed to be searched for
    :return: True if exists
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    check = cur.execute(f"SELECT rowid FROM record WHERE {parameter} = ?",
                        (key,)).fetchall()

    if len(check) != 0:
        return True


def search(name, keys, search):
    """
    function searches
    :param name: database name
    :param keys: the keys to search for
    :param search: the value to search by
    :return: data from database matching to search query
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    query = f"SELECT * FROM {name} WHERE "
    for i in keys:
        query += f"{i} LIKE '%{search}%' OR "
    query = query[:-3]
    data = cur.execute(query).fetchall()
    con.commit()
    return data


def insert_to_purchases(keys):
    """
    functions inserts certain keys into the 'purchases' table
    :param keys: the keys to insert
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    cur.execute(f"INSERT INTO purchases VALUES (:purchase_id, :offer_id, :duration, "
                f":user_email, :credit_number, :is_registered)", {
                    'purchase_id': keys[0],
                    'offer_id': keys[1],
                    'duration': keys[2],
                    'user_email': keys[3],
                    'credit_number': keys[4],
                    'is_registered': keys[5]
                })
    con.commit()


def check_if_admin(user_email):
    """
    function check's if the user is admin by user email
    :param user_email: the user's email
    :return: 1 or 0 if the user is admin or not (as bool)
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    is_admin = fetch_row_by_parameter("record", "email", user_email)[0][-1]
    return bool(1 if is_admin == "True" else 0)


def drop_column(name, column):
    """
    function deletes a certain column in table
    :param name: database name
    :param column: the column to drop
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    con.execute(f"ALTER TABLE {name} DROP COLUMN {column};")
    con.commit()


def remove_row_by_parameter(name, parameter, key):
    """
    function removes row by a certain parameter
    :param name: database name
    :param parameter: the parameter to search by
    :param key: the value being searched for
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    con.execute(f"DELETE FROM {name} WHERE {parameter} = ?", (key,))
    con.commit()


def export_to_csv(name):
    """
    function exports the table from database to a .csv file
    :param name: database name
    :return: None
    """
    con = sqlite3.connect('data_base/user_data.db')
    cur = con.cursor()
    db_df = pd.read_sql_query(f"SELECT * FROM {name}", con)
    db_df.to_csv(f'{name}_table.csv', index=False)


if __name__ == "__main__":
    pass