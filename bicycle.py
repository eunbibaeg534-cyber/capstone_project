#자전거
import pandas as pd

# 1. CSV 불러오기
df = pd.read_csv("12_24_bicycle.csv", encoding="cp949")

# 2. 필요한 컬럼만 선택
df = df[[
    "시도시군구명",
    "지점명",
    "사고건수",
    "사망자수",
    "중상자수",
    "위도",
    "경도"
]]

# 3. 서울 + 경기만 필터링
df = df[df["시도시군구명"].str.contains("서울|경기", na=False)].copy()

# 4. 컬럼명 DB 기준으로 변경
df = df.rename(columns={
    "시도시군구명": "region_name",
    "지점명": "spot_name",
    "위도": "latitude",
    "경도": "longitude",
    "사고건수": "accident_count",
    "중상자수": "serious_injury",
    "사망자수": "death"
})

# 5. region_name 뒤 숫자 제거
df["region_name"] = df["region_name"].astype(str).str.replace(r"\d+$", "", regex=True)

# 6. 숫자형 변환
num_cols = ["latitude", "longitude", "accident_count", "serious_injury", "death"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# 7. 좌표 없는 행 제거
df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]

# 8. 정수형 변환
df["accident_count"] = df["accident_count"].astype(int)
df["serious_injury"] = df["serious_injury"].astype(int)
df["death"] = df["death"].astype(int)

# 9. 추가 컬럼
df["schoolzone"] = 0
df["accident_type"] = "자전거"
df["grid_id"] = 3   # 임시값, 나중에 격자 매핑할 때 수정

# 10. 최종 컬럼 순서
df = df[[
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

# 11. 저장
df.to_csv("bicycle_processed.csv", index=False, encoding="cp949")

print("자전거 전처리 완료")
print(df.head())
print("총 행 개수:", len(df))
print(df.columns)


#보행어린이
import pandas as pd

# 1. CSV 불러오기
df = pd.read_csv("12_24_child.csv", encoding="cp949")

# 2. 필요한 컬럼만 선택
df = df[[
    "시도시군구명",
    "지점명",
    "사고건수",
    "사망자수",
    "중상자수",
    "위도",
    "경도"
]]

# 3. 서울 + 경기만 필터링
df = df[df["시도시군구명"].str.contains("서울|경기", na=False)].copy()

# 4. 컬럼명 DB 기준으로 변경
df = df.rename(columns={
    "시도시군구명": "region_name",
    "지점명": "spot_name",
    "위도": "latitude",
    "경도": "longitude",
    "사고건수": "accident_count",
    "중상자수": "serious_injury",
    "사망자수": "death"
})

# 5. region_name 뒤 숫자 제거
df["region_name"] = df["region_name"].astype(str).str.replace(r"\d+$", "", regex=True)

# 6. 숫자형 변환
num_cols = ["latitude", "longitude", "accident_count", "serious_injury", "death"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# 7. 좌표 없는 행 제거
df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]

# 8. 정수형 변환
df["accident_count"] = df["accident_count"].astype(int)
df["serious_injury"] = df["serious_injury"].astype(int)
df["death"] = df["death"].astype(int)

# 9. 추가 컬럼
df["schoolzone"] = 0
df["accident_type"] = "보행어린이"
df["grid_id"] = 3   # 임시값, 나중에 격자 매핑 때 수정

# 10. 최종 컬럼 순서
df = df[[
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

# 11. 저장
df.to_csv("child_pedestrian_processed.csv", index=False, encoding="cp949")

print("보행어린이 전처리 완료")
print(df.head())
print("총 행 개수:", len(df))
print(df.columns)

#보행노인
import pandas as pd

df = pd.read_csv("12_24_oldman.csv", encoding="cp949")

df = df[[
    "시도시군구명",
    "지점명",
    "사고건수",
    "사망자수",
    "중상자수",
    "위도",
    "경도"
]]

df = df[df["시도시군구명"].str.contains("서울|경기", na=False)].copy()

df = df.rename(columns={
    "시도시군구명": "region_name",
    "지점명": "spot_name",
    "위도": "latitude",
    "경도": "longitude",
    "사고건수": "accident_count",
    "중상자수": "serious_injury",
    "사망자수": "death"
})

df["region_name"] = df["region_name"].astype(str).str.replace(r"\d+$", "", regex=True)

num_cols = ["latitude", "longitude", "accident_count", "serious_injury", "death"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]

df["accident_count"] = df["accident_count"].astype(int)
df["serious_injury"] = df["serious_injury"].astype(int)
df["death"] = df["death"].astype(int)

df["schoolzone"] = 0
df["accident_type"] = "보행노인"
df["grid_id"] = 3  # 임시값

df_oldman = df[[
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


df_oldman.to_csv("oldman_processed.csv", index=False, encoding="cp949")
print("보행노인 전처리 완료")
print(df_oldman.head())
print("총 행 개수:", len(df_oldman))
print(df_oldman.columns)


#이륜차
import pandas as pd

df = pd.read_csv("17_24_motorcycle.csv", encoding="cp949")

df = df[[
    "시도시군구명",
    "지점명",
    "사고건수",
    "사망자수",
    "중상자수",
    "위도",
    "경도"
]]

df = df[df["시도시군구명"].str.contains("서울|경기", na=False)].copy()

df = df.rename(columns={
    "시도시군구명": "region_name",
    "지점명": "spot_name",
    "위도": "latitude",
    "경도": "longitude",
    "사고건수": "accident_count",
    "중상자수": "serious_injury",
    "사망자수": "death"
})

df["region_name"] = df["region_name"].astype(str).str.replace(r"\d+$", "", regex=True)

num_cols = ["latitude", "longitude", "accident_count", "serious_injury", "death"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]

df["accident_count"] = df["accident_count"].astype(int)
df["serious_injury"] = df["serious_injury"].astype(int)
df["death"] = df["death"].astype(int)

df["schoolzone"] = 0
df["accident_type"] = "이륜차"
df["grid_id"] = 3  # 임시값

df_motorcycle = df[[
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


df_motorcycle.to_csv("motorcycle_processed.csv", index=False, encoding="cp949")
print("이륜차 전처리 완료")
print(df_motorcycle.head())
print("총 행 개수:", len(df_motorcycle))
print(df_motorcycle.columns)
