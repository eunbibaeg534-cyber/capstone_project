"""
응급실 오픈API 데이터 전처리 스크립트
- 서울시 API: openapi.seoul.go.kr (TvEmgcHospitalInfo)
- 경기도 API: openapi.gg.go.kr (EmgncyMedcareInstStus)
→ ERD hospital 테이블에 맞게 전처리 후 CSV 저장
"""
 
import hashlib
import re
import requests
import pandas as pd
import time
import logging
from datetime import datetime
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
# ============================================================
# 🔑 인증키 설정 (여기에 발급받은 키 입력)
# ============================================================
SEOUL_API_KEY = "774365634f63686f3836664b4e516e"   # 서울 열린데이터광장 인증키
GYEONGGI_API_KEY = "705d04e40e8d4082beb521d23a3d0f69"  # 경기도 공공데이터 인증키
# 1. 서울시 응급실 API 호출
# ============================================================
def fetch_seoul_hospitals(api_key: str, batch_size: int = 1000) -> list[dict]:
    """
    서울시 TvEmgcHospitalInfo API 전체 페이징 호출
    - 한 번에 최대 1000건 요청 가능
    """
    base_url = "http://openapi.seoul.go.kr:8088"
    service = "TvEmgcHospitalInfo"
    all_rows = []
    start = 1
 
    # 총 건수 먼저 파악 (1건만 호출)
    url = f"{base_url}/{api_key}/json/{service}/1/1/"
    resp = requests.get(url, timeout=10).json()
    total = int(resp[service]["list_total_count"])
    log.info(f"[서울] 총 데이터 건수: {total}")
 
    while start <= total:
        end = min(start + batch_size - 1, total)
        url = f"{base_url}/{api_key}/json/{service}/{start}/{end}/"
        resp = requests.get(url, timeout=10).json()
 
        result_code = resp[service]["RESULT"]["CODE"]
        if result_code != "INFO-000":
            log.error(f"[서울] API 오류: {resp[service]['RESULT']}")
            break
 
        rows = resp[service]["row"]
        all_rows.extend(rows)
        log.info(f"[서울] {start}~{end} 수집 완료 ({len(all_rows)}/{total})")
        start = end + 1
        time.sleep(0.3)  # 서버 부하 방지
 
    return all_rows
# 2. 경기도 응급의료기관 API 호출
# ============================================================
def fetch_gyeonggi_hospitals(api_key: str, page_size: int = 1000) -> list[dict]:
    """
    경기도 EmgncyMedcareInstStus API 전체 페이징 호출
    - pIndex(페이지번호) / pSize(페이지당 건수) 방식
    """
    base_url = "https://openapi.gg.go.kr/EmgncyMedcareInstStus"
    all_rows = []
    page = 1
 
    while True:
        params = {
            "Key": api_key,
            "Type": "json",
            "pIndex": page,
            "pSize": page_size,
        }
        resp = requests.get(base_url, params=params, timeout=10).json()
 
        # 응답 구조: {"EmgncyMedcareInstStus": [{"head": ...}, {"row": [...]}]}
        data = resp.get("EmgncyMedcareInstStus", [])
        if not data:
            log.error("[경기] 응답 없음")
            break
 
        head = data[0]["head"]
        result_code = head[1]["RESULT"]["CODE"]
        if result_code not in ("INFO-000",):
            log.warning(f"[경기] 더 이상 데이터 없음 또는 오류: {head[1]['RESULT']}")
            break
 
        total = int(head[0]["list_total_count"])
        rows = data[1].get("row", [])
        all_rows.extend(rows)
        log.info(f"[경기] 페이지 {page} 수집 완료 ({len(all_rows)}/{total})")
 
        if len(all_rows) >= total:
            break
        page += 1
        time.sleep(0.3)
 
    return all_rows
# 3. 서울 데이터 → hospital 테이블 매핑
# ============================================================
def transform_seoul(rows: list[dict]) -> pd.DataFrame:
    """
    API 출력 필드 → ERD hospital 테이블 컬럼 매핑
 
    API 필드           →  hospital 컬럼
    ─────────────────────────────────────
    HPID               →  hospital_id (문자열 그대로 사용)
    DUTYNAME           →  hospital_name
    DUTYADDR           →  address
    WGS84LAT           →  latitude
    WGS84LON           →  longitude
    DUTYERYN (1=운영)  →  emergency_room_yn (BOOLEAN)
    DUTYTIME1S~8S/C    →  operating_hours (가공하여 요약 문자열)
    -                  →  hospital_status (기본값 '운영중')
    DUTYTEL1           →  phone
    """
    df = pd.DataFrame(rows)
    log.info(f"[서울] 원본 컬럼: {df.columns.tolist()}")
 
    # 운영시간 요약: 월~일 시작~종료 정보를 하나의 문자열로
    def summarize_hours(row):
        days = ["월", "화", "수", "목", "금", "토", "일", "공휴일"]
        parts = []
        for i, day in enumerate(days, start=1):
            s = str(row.get(f"DUTYTIME{i}S", "")).strip()
            c = str(row.get(f"DUTYTIME{i}C", "")).strip()
            if s and c and s != "nan" and c != "nan":
                parts.append(f"{day} {s[:2]}:{s[2:]}~{c[:2]}:{c[2:]}")
        return " | ".join(parts) if parts else None
 
    df["operating_hours"] = df.apply(summarize_hours, axis=1)
 
    out = pd.DataFrame({
        "hospital_id":       "S_" + df["HPID"].astype(str),  # prefix로 경기(GG_)와 충돌 방지
        "hospital_name":     df["DUTYNAME"].astype(str),
        "address":           df.get("DUTYADDR", pd.Series(dtype=str)).astype(str),
        "latitude":          pd.to_numeric(df["WGS84LAT"], errors="coerce"),
        "longitude":         pd.to_numeric(df["WGS84LON"], errors="coerce"),
        "emergency_room_yn": df["DUTYERYN"].astype(str).str.strip() == "1",
        "operating_hours":   df["operating_hours"],
        "hospital_status":   "운영중",  # 서울 API는 상태 필드 없음 → 기본값
        "phone":             df.get("DUTYTEL1", pd.Series(dtype=str)).where(df.get("DUTYTEL1", pd.Series(dtype=str)).notna(), None),
        "region":            "서울",   # 출처 구분용 (DB INSERT 시 활용)
    })
 
    return out
# 4. 경기도 데이터 → hospital 테이블 매핑
# ============================================================
def transform_gyeonggi(rows: list[dict]) -> pd.DataFrame:
    """
    API 출력 필드           →  hospital 컬럼
    ────────────────────────────────────────────
    SIGUN_CD + HOSPTL_CENTER_NM (조합) → hospital_id
    HOSPTL_CENTER_NM               →  hospital_name
    REFINE_ROADNM_ADDR             →  address
    REFINE_WGS84_LAT               →  latitude
    REFINE_WGS84_LOGT              →  longitude
    EMGNCY_SPORT_CENTER_YN (Y/N)   →  emergency_room_yn
    -                              →  operating_hours (없음 → None)
    -                              →  hospital_status (기본값 '운영중')
    REPRSNT_TELNO                  →  phone
    """
    df = pd.DataFrame(rows)
    log.info(f"[경기] 원본 컬럼: {df.columns.tolist()}")
 
    # 병원명 + 주소 조합으로 안정적인 해시 ID 생성 (순서 바뀌어도 동일 ID 보장)
    def make_id(name, addr):
        key = (str(name) + str(addr)).encode("utf-8")
        return "GG_" + hashlib.md5(key).hexdigest()[:12]  # GG_(3) + 12 = 15자, VARCHAR(20) 안전
 
    df["hospital_id"] = df.apply(
        lambda x: make_id(x["HOSPTL_CENTER_NM"], x["REFINE_ROADNM_ADDR"]), axis=1
    )
 
    out = pd.DataFrame({
        "hospital_id":       df["hospital_id"],
        "hospital_name":     df["HOSPTL_CENTER_NM"].astype(str),
        "address":           df.get("REFINE_ROADNM_ADDR", pd.Series(dtype=str)).astype(str),
        "latitude":          pd.to_numeric(df["REFINE_WGS84_LAT"], errors="coerce"),
        "longitude":         pd.to_numeric(df["REFINE_WGS84_LOGT"], errors="coerce"),
        "emergency_room_yn": df["EMGNCY_SPORT_CENTER_YN"].astype(str).str.strip().str.upper() == "Y",
        "operating_hours":   None,   # 경기 API에 진료시간 없음
        "hospital_status":   "운영중",
        "phone":             df.get("REPRSNT_TELNO", pd.Series(dtype=str)).where(df.get("REPRSNT_TELNO", pd.Series(dtype=str)).notna(), None),
        "region":            "경기",
    })
 
    return out
# 5. 통합 정제 (공통 클렌징)
# ============================================================
def clean_combined(df: pd.DataFrame) -> pd.DataFrame:
    """
    공통 정제 처리
    - 좌표 이상값 제거 (한반도 범위 밖)
    - 중복 hospital_id 제거
    - phone 정규화 (숫자/하이픈만 유지)
    - NaN → None
    """
    before = len(df)
 
    # 좌표 범위 필터 (대한민국: lat 33~38.6, lon 124.6~132)
    df = df[
        df["latitude"].between(33.0, 38.6) &
        df["longitude"].between(124.6, 132.0)
    ].copy()
    log.info(f"좌표 이상값 제거: {before - len(df)}건 제외")
 
    # 중복 제거
    df = df.drop_duplicates(subset=["hospital_id"])
 
    # 전화번호 정제 (숫자와 하이픈만)
    df["phone"] = df["phone"].apply(
        lambda x: re.sub(r"[^\d\-]", "", str(x)) if pd.notna(x) else None
    )
 
    # 빈 문자열 → None
    for col in ["address", "operating_hours", "phone"]:
        df[col] = df[col].replace({"": None, "nan": None, "None": None})
 
    # 타입 보정 — astype(bool) 직접 사용 시 NaN → True 오변환 위험
    df["emergency_room_yn"] = df["emergency_room_yn"].fillna(False).astype(int)
 
    df = df.reset_index(drop=True)
 
    # operating_hours 결측 여부 표시
    # 현재는 "결측값인가?" 의미 (True = 데이터 없음)
    # 추후 실제 보정값을 채웠을 때 "보정된 값인가?"로 의미 전환 필요
    df["operating_hours_imputed"] = df["operating_hours"].isna().astype(int)
 
    log.info(f"최종 컬럼: {list(df.columns)}")
    log.info(f"최종 정제 완료: {len(df)}건 | operating_hours 없음: {df['operating_hours_imputed'].sum()}건")
    return df

# 6. 메인 실행
# ============================================================
def main():
    log.info("===== 응급실 데이터 수집 및 전처리 시작 =====")
 
    dfs = []
 
    # 서울
    try:
        seoul_raw = fetch_seoul_hospitals(SEOUL_API_KEY)
        seoul_df = transform_seoul(seoul_raw)
        dfs.append(seoul_df)
        log.info(f"[서울] 변환 완료: {len(seoul_df)}건")
    except Exception as e:
        log.error(f"[서울] 수집 실패: {e}")
 
    # 경기
    try:
        gg_raw = fetch_gyeonggi_hospitals(GYEONGGI_API_KEY)
        gg_df = transform_gyeonggi(gg_raw)
        dfs.append(gg_df)
        log.info(f"[경기] 변환 완료: {len(gg_df)}건")
    except Exception as e:
        log.error(f"[경기] 수집 실패: {e}")
 
    if not dfs:
        log.error("수집된 데이터 없음. 종료.")
        return
 
    # 통합 및 정제
    combined = pd.concat(dfs, ignore_index=True)
    cleaned = clean_combined(combined)
 
    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"hospital_preprocessed_{timestamp}.csv"

    cleaned = cleaned.loc[:, ~cleaned.columns.duplicated()]
    
    cleaned.to_csv(out_path, index=False, encoding="cp949")
    log.info(f"저장 완료: {out_path}")
 
    # 컬럼 순서를 ERD 기준으로 맞춰 출력
    print("\n[샘플 미리보기]")
    print(cleaned[[
        "hospital_id", "hospital_name", "address",
        "latitude", "longitude", "emergency_room_yn",
        "operating_hours", "hospital_status", "phone", "region"
    ]].head(5).to_string(index=False))
 
    return cleaned
 
 
if __name__ == "__main__":
    main()

