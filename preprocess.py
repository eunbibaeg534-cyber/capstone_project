import pandas as pd
import pymysql

# 1. CSV 파일 불러오기
df = pd.read_csv("19_24_pedstrians.csv", encoding="cp949")

# 2. 필요한 컬럼 선택
df = df[['지점코드', '시도시군구명', '지점명', '사고건수', '사망자수', '중상자수', '위도', '경도']]

# 3. 서울 + 경기 필터링
df = df[df['시도시군구명'].str.contains('서울|경기', na=False)]

# 4. 결측치 처리
df = df.fillna(0)

# 5. 숫자형 변환
num_cols = ['사고건수', '사망자수', '중상자수', '위도', '경도']
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# 6. 좌표 없는 행 제거
df = df[(df['위도'] != 0) & (df['경도'] != 0)]

# 7. 정수형 변환
df['사고건수'] = df['사고건수'].astype(int)
df['사망자수'] = df['사망자수'].astype(int)
df['중상자수'] = df['중상자수'].astype(int)

# 8. SQL 컬럼명으로 변경
df_db = df.rename(columns={
    '지점코드': 'spot_code',
    '시도시군구명': 'region_name',
    '지점명': 'spot_name',
    '위도': 'latitude',
    '경도': 'longitude',
    '사고건수': 'accident_count',
    '중상자수': 'serious_injury',
    '사망자수': 'death'
})

# 9. region_name 뒤 숫자 제거
df_db['region_name'] = df_db['region_name'].astype(str).str.replace(r'\d+$', '', regex=True)

# 10. 추가 컬럼 생성
df_db['schoolzone'] = 0
df_db['accident_type'] = '보행자'
df_db['grid_id'] = 3   # 임시값. 나중에 격자 매핑하면 수정해야 함

# 11. 최종 컬럼 순서
df_db = df_db[[
    'latitude',
    'longitude',
    'accident_count',
    'serious_injury',
    'death',
    'schoolzone',
    'grid_id',
    'accident_type',
    'region_name',
    'spot_name'
]]

# 12. 전처리 결과 저장
df_db.to_csv("seoul_gyeonggi_accident_processed.csv", index=False, encoding="cp949")

print("전처리 완료")
print(df_db.head())
print("총 행 개수:", len(df_db))
print(df_db.columns)

# 13. MySQL 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='eunbi0114!!!@',
    database='capstone_project',
    charset='utf8mb4'
)

cursor = conn.cursor()

# 14. SQL 삽입
sql = """
INSERT INTO accident 
(latitude, longitude, accident_count, serious_injury, death, schoolzone, grid_id, accident_type, region_name, spot_name)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df_db.iterrows():
    cursor.execute(sql, (
        row['latitude'],
        row['longitude'],
        row['accident_count'],
        row['serious_injury'],
        row['death'],
        row['schoolzone'],
        row['grid_id'],
        row['accident_type'],
        row['region_name'],
        row['spot_name']
    ))

conn.commit()
conn.close()

print("데이터 삽입 완료")
