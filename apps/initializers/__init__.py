import os
import sqlite3
from fastapi.applications import FastAPI
from apps.config import logger


def setup_initializers(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        db_path = './model_integration.db'
        sql_file_path = './init.sql'

        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            box_count = conn.execute('SELECT COUNT(*) FROM box').fetchone()[0]
            accounts_count = conn.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]
            if box_count == 0 or accounts_count == 0:
                with open(sql_file_path, 'r') as file:
                    sql_script = file.read()
                    conn.executescript(sql_script)
                logger.info("Database initialized successfully.")
            conn.close()
            logger.info("table already exists. Skipping initialization.")
        else:
            logger.info("Database not exists.")
