#!/usr/bin/env python
import settings
import mysql.connector

def db_connect():
    return mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
            )

def load_from_db():
        mydb = db_connect()

        mycursor = mydb.cursor()

        mycursor.execute("SELECT * FROM creator_channels")

        for row in mycursor.fetchall():
            creator_channels[row[0]] = row[1]

            mycursor.execute("SELECT id, guild_id FROM users, user_guilds WHERE id = user_id")

        for row in mycursor.fetchall():
            if row[0] in users.keys():
                users[row[0]].append(row[1])
            else:
                users[row[0]] = [ row[1] ]

        mycursor.close()
        mydb.disconnect()

