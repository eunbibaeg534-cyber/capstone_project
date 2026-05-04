import requests
import pandas as pd

API_KEY = "e9481933ed7d903e2a6f2113330dd6687c4e7074bd0e424d880700e07c73983a"

url = "http://apis.data.go.kr/B552061/schoolzoneChild/getRestSchoolzoneChild"

params = {
    "serviceKey": API_KEY,
    "searchYearCd": "2024",
    "siDo": "",
    "guGun": "",
    "type": "json",
    "numOfRows": "100",
    "pageNo": "1"
}

response = requests.get(url, params=params)
data = response.json()

items = data["items"]["item"]
df = pd.DataFrame(items)

# 서울/경기만 필터링
df = df[df["sido_sgg_nm"].str.contains("서울|경기", na=False)].copy()

# 필요한 컬럼 선택
df = df[[
    "sido_sgg_nm",
    "spot_nm",
    "la_crd",
    "lo_crd",
    "occrrnc_cnt",
    "se_dnv_cnt",
    "dth_dnv_cnt"
]]

# DB 컬럼명으로 변경
df = df.rename(columns={
    "sido_sgg_nm": "region_name",
    "spot_nm": "spot_name",
    "la_crd": "latitude",
    "lo_crd": "longitude",
    "occrrnc_cnt": "accident_count",
    "se_dnv_cnt": "serious_injury",
    "dth_dnv_cnt": "death"
})

# region_name 뒤 숫자 제거
df["region_name"] = df["region_name"].astype(str).str.replace(r"\d+$", "", regex=True)

# 숫자형 변환
num_cols = ["latitude", "longitude", "accident_count", "serious_injury", "death"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# 좌표 없는 행 제거
df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]

# 정수형 변환
df["accident_count"] = df["accident_count"].astype(int)
df["serious_injury"] = df["serious_injury"].astype(int)
df["death"] = df["death"].astype(int)

# 추가 컬럼
df["schoolzone"] = 1
df["accident_type"] = "스쿨존"
df["grid_id"] = 3   # 임시값, 나중에 격자 매핑 때 수정

# 최종 컬럼 순서
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

df.to_csv("schoolzone_processed.csv", index=False, encoding="cp949")

print("스쿨존 전처리 완료")
print(df.head())
print("최종 개수:", len(df))
print(df.columns)


