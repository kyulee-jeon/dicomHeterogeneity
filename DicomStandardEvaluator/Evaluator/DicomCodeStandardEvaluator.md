DicomCodeStandardEvaluator
==========================

이 클래스는 DICOM 메타데이터가 DICOM 표준 정의에 얼마나 부합하는지를 평가하고,
기관 및 제조사 간 메타데이터 사용의 이질성을 정량화하기 위한 분석 도구입니다.

주요 기능
--------
1. analyze_rates:
    - 그룹별(Tag 기준)로 DICOM 메타데이터의 존재율, 값 존재율, 표준화율, 값 다양성을 분석

2. analyze_rates_with_stats:
    - 위 분석 결과를 바탕으로 평균, 표준편차, 변동계수(CV), 범위 등의 통계량 생성

입력 데이터
-----------
- df_metadata: 실제 DICOM 메타데이터 (필수 컬럼: IOD, File ID, Tag, Value, VR, etc.)
- df_standard: DICOM 표준 태그 정의 테이블 (필수 컬럼: IOD, Tag, Attribute Name, Type, Type_Group, Standard Terms 등)

핵심 개념 정의
--------------
- Tag Existence Rate: 특정 Tag가 존재하는 파일 비율
- Value Existence Rate: Tag가 존재하는 파일 중 Value가 존재하는 비율
- Value Standardization Rate: Value 중 표준값(Enumerated/Defined Terms)과 일치하는 비율 (VR == CS일 때만 계산)
- Value Diversity: 고유 Value 개수

사용 예시
---------
evaluator = DicomCodeStandardEvaluator(df_metadata, df_standard)
rates_df, stats_df = evaluator.analyze_rates_with_stats(group_cols=['IOD', 'Manufacturer'])

개발자
------
- 작성자: Kyulee Jeon 외
- 업데이트: 2025년 7월
