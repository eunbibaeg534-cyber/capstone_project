#사고유형api(보행자,보행어린이,보행노인,이륜차,자전거)
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pymysql
from pymysql.cursors import DictCursor

app = FastAPI()

# 프론트 연결 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="eunbi0114!!!@",  # 너 비번
        database="capstone_project",
        charset="utf8mb4",
        cursorclass=DictCursor
    )

@app.get("/api/accidents")
def get_accidents(accident_type: str | None = Query(default=None)):
    conn = get_conn()
    cursor = conn.cursor()

    if accident_type:
        sql = """
        SELECT latitude, longitude, accident_count,
               serious_injury, death, schoolzone,
               accident_type, region_name, spot_name
        FROM accident
        WHERE accident_type = %s
        """
        cursor.execute(sql, (accident_type,))
    else:
        sql = """
        SELECT latitude, longitude, accident_count,
               serious_injury, death, schoolzone,
               accident_type, region_name, spot_name
        FROM accident
        """
        cursor.execute(sql)

    result = cursor.fetchall()
    conn.close()
    return result




#격자api
@app.get("/api/risk-grid")
def get_risk_grid():
    conn = get_conn()
    cursor = conn.cursor()

    sql = """
    SELECT grid_id,
           center_latitude,
           center_longitude,
           risk_score,
           risk_level
    FROM risk_grid
    """

    cursor.execute(sql)
    result = cursor.fetchall()
    conn.close()

    return result
