
import pandas as pd
import numpy as np
import pymysql

# =========================
# 1. 전처리된 CSV 파일 불러오기
# =========================

files = [
    "seoul_gyeonggi_accident_processed.csv",   # 보행자
    "schoolzone_processed.csv",                # 스쿨존
    "child_pedestrian_processed.csv",          # 보행어린이
    "oldman_processed.csv",                    # 보행노인
    "bicycle_processed.csv",                   # 자전거
    "motorcycle_processed.csv"                 # 이륜차
]

df_list = []

for file in files:
    temp = pd.read_csv(file, encoding="cp949")
    df_list.append(temp)

df_all = pd.concat(df_list, ignore_index=True)

print("전체 사고 데이터 개수:", len(df_all))
print(df_all.columns)

# =========================
# 2. 필요한 컬럼만 정리
# =========================

required_cols = [
    "latitude",
    "longitude",
    "accident_count",
    "serious_injury",
    "death",
    "schoolzone",
    "grid_id",
    "accident_type",
    "region_name",
    "spot_name"
]

df_all = df_all[required_cols]

# =========================
# 3. 숫자형 변환
# =========================

num_cols = [
    "latitude",
    "longitude",
    "accident_count",
    "serious_injury",
    "death",
    "schoolzone"
]

for col in num_cols:
    df_all[col] = pd.to_numeric(df_all[col], errors="coerce").fillna(0)

df_all = df_all[(df_all["latitude"] != 0) & (df_all["longitude"] != 0)]

df_all["accident_count"] = df_all["accident_count"].astype(int)
df_all["serious_injury"] = df_all["serious_injury"].astype(int)
df_all["death"] = df_all["death"].astype(int)
df_all["schoolzone"] = df_all["schoolzone"].astype(int)

# =========================
# 4. 기존 임시 grid_id 제거
# =========================

df_all = df_all.drop(columns=["grid_id"])

# =========================
# 5. 500m 격자 grid_id 생성
# =========================

lat_base = df_all["latitude"].min()
lon_base = df_all["longitude"].min()

mean_lat = df_all["latitude"].mean()

lat_meter = 111320
lon_meter = 111320 * np.cos(np.radians(mean_lat))

df_all["x_meter"] = (df_all["longitude"] - lon_base) * lon_meter
df_all["y_meter"] = (df_all["latitude"] - lat_base) * lat_meter

df_all["grid_x"] = (df_all["x_meter"] // 500).astype(int)
df_all["grid_y"] = (df_all["y_meter"] // 500).astype(int)

df_all["grid_key"] = df_all["grid_x"].astype(str) + "_" + df_all["grid_y"].astype(str)

df_all["grid_id"] = pd.factorize(df_all["grid_key"])[0] + 1

# =========================
# 6. risk_grid 테이블용 데이터 생성
# 위험도 계산 X, 위험등급 X
# =========================

risk_grid = df_all.groupby("grid_id").agg(
    center_latitude=("latitude", "mean"),
    center_longitude=("longitude", "mean")
).reset_index()

print("생성된 격자 개수:", len(risk_grid))

# =========================
# 7. DB에 넣기 전 컬럼 정리
# =========================

df_all_insert = df_all[[
    "latitude",
    "longitude",
    "accident_count",
    "serious_injury",
    "death",
    "schoolzone",
    "grid_id",
    "accident_type",
    "region_name",
    "spot_name"
]]

# 확인용 CSV 저장
df_all_insert.to_csv("all_accident_with_grid.csv", index=False, encoding="cp949")
risk_grid.to_csv("risk_grid_processed.csv", index=False, encoding="cp949")

print("CSV 저장 완료")

# =========================
# 8. MySQL INSERT
# =========================

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="eunbi0114!!!@",
    database="capstone_project",
    charset="utf8mb4"
)

cursor = conn.cursor()

# FK 때문에 accident 먼저 삭제
cursor.execute("DELETE FROM accident")
cursor.execute("DELETE FROM risk_grid")

# =========================
# 9. risk_grid 먼저 INSERT
# =========================

sql_grid = """
INSERT INTO risk_grid
(grid_id, center_latitude, center_longitude)
VALUES (%s, %s, %s)
"""

for _, row in risk_grid.iterrows():
    cursor.execute(sql_grid, (
        int(row["grid_id"]),
        float(row["center_latitude"]),
        float(row["center_longitude"])
    ))

# =========================
# 10. accident INSERT
# =========================

sql_accident = """
INSERT INTO accident
(latitude, longitude, accident_count, serious_injury, death,
 schoolzone, grid_id, accident_type, region_name, spot_name)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df_all_insert.iterrows():
    cursor.execute(sql_accident, (
        float(row["latitude"]),
        float(row["longitude"]),
        int(row["accident_count"]),
        int(row["serious_injury"]),
        int(row["death"]),
        int(row["schoolzone"]),
        int(row["grid_id"]),
        str(row["accident_type"]),
        str(row["region_name"]),
        str(row["spot_name"])
    ))

conn.commit()
conn.close()

print("DB 삽입 완료")
print("사고 데이터 수:", len(df_all_insert))
print("격자 데이터 수:", len(risk_grid))
