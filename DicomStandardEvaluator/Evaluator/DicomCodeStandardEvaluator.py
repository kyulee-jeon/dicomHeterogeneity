import pandas as pd
import numpy as np
import ast
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

class DicomCodeStandardEvaluator:
    def __init__(self, df_metadata, df_standard):
        """
        DICOM 메타데이터와 DICOM 표준 정의 테이블을 받아 초기화
        :param df_metadata: 실제 DICOM 메타데이터
        :param df_standard: DICOM 표준 정의 테이블
        """
        self.df_standard = df_standard
        if 'VR' not in df_metadata.columns:
            df_metadata = df_metadata.merge(
                df_standard[['Tag', 'VR']].drop_duplicates(),
                on='Tag', how='left'
            )
        self.df_metadata = df_metadata

    def _calculate_value_scores(self, tag_data, valid_values):
        """
        Value 표준화 점수 계산
        :param tag_data: 특정 Tag에 대해 Value가 존재하는 행들의 DataFrame
        :param valid_values: 표준 용어 리스트
        :return: 총 점수 합
        """
        value_score_sum = 0.0
        for _, row_t in tag_data.iterrows():
            val_str = str(row_t['Value']) if pd.notna(row_t['Value']) else ""
            val_str = val_str.strip()
            try:
                parsed_list = ast.literal_eval(val_str)
                if not isinstance(parsed_list, list):
                    parsed_list = [parsed_list]
            except (ValueError, SyntaxError):
                parsed_list = [] if val_str == "" else [val_str]

            if len(parsed_list) == 0:
                score_file = 0
            elif len(parsed_list) == 1:
                score_file = 1 if parsed_list[0] in valid_values else 0
            else:
                standard_count = sum((p in valid_values) for p in parsed_list)
                if standard_count == len(parsed_list):
                    score_file = 1
                elif standard_count > 0:
                    score_file = 0.5
                else:
                    score_file = 0

            value_score_sum += score_file
        return value_score_sum

    def _extract_valid_values(self, standard_terms):
        """
        표준 정의에서 유효한 Value 목록 추출
        :param standard_terms: 'Enumerated Values' 또는 'Defined Terms'가 포함된 dict 또는 문자열
        :return: 유효한 값들의 집합
        """
        valid_values = set()
        if isinstance(standard_terms, dict):
            for key in ['Enumerated Values', 'Defined Terms']:
                values = standard_terms.get(key, [])
                if isinstance(values, list):
                    valid_values.update(values)
        else:
            try:
                parsed = ast.literal_eval(standard_terms)
                if isinstance(parsed, dict):
                    for key in ['Enumerated Values', 'Defined Terms']:
                        values = parsed.get(key, [])
                        if isinstance(values, list):
                            valid_values.update(values)
            except:
                pass
        return valid_values

    def _analyze_rates_for_one_group(self, df, group_id):
        """
        하나의 그룹에 대해 DICOM 태그 사용 분석 수행
        :param df: 분석 대상 그룹 데이터
        :param group_id: 그룹 정보 dict (예: {'IOD': 'CT Image IOD', 'Manufacturer': 'GE'})
        :return: 분석 결과 DataFrame
        """
        iod = group_id['IOD']
        iod_standard = self.df_standard[self.df_standard['IOD'] == iod]
        total_files = df['file_global'].nunique()
        if total_files == 0:
            return pd.DataFrame()

        empty_value_mask = (
            df["Value"].isna() |
            (df["Value"].str.strip() == "") |
            (df["Value"].str.strip() == "[]") |
            (df["Value"].str.isspace()) |
            (df["Value"].str.len() == 0)
        )

        rows = []
        for _, std_row in iod_standard.iterrows():
            tag_val = std_row['Tag']
            mask_tag = (df['Tag'] == tag_val)
            file_count_tag = df[mask_tag]['file_global'].nunique()
            tag_existence_rate = file_count_tag / total_files

            mask_nonempty = mask_tag & (~empty_value_mask)
            file_count_nonempty = df[mask_nonempty]['file_global'].nunique()
            value_existence_rate = (
                file_count_nonempty / file_count_tag if file_count_tag > 0 else 0
            )

            file_count_cs = 0
            value_standardization_rate = np.nan
            if file_count_nonempty > 0:
                mask_cs = mask_nonempty & (df['VR'] == 'CS')
                file_count_cs = df[mask_cs]['file_global'].nunique()
                if file_count_cs > 0:
                    standard_terms = std_row.get('Standard Terms', None)
                    valid_values = self._extract_valid_values(standard_terms)
                    tag_data = df[mask_nonempty].drop_duplicates(subset=["file_global"])
                    value_score_sum = self._calculate_value_scores(tag_data, valid_values)
                    value_standardization_rate = value_score_sum / file_count_nonempty

            unique_values = df[mask_nonempty]['Value'].dropna().unique()
            value_diversity = len(unique_values)

            row_dict = {
                'Tag': tag_val,
                'Attribute Name': std_row['Attribute Name'],
                'total_files': total_files,
                'files_with_tag': file_count_tag,
                'files_with_value': file_count_nonempty,
                'files_with_cs_vr': file_count_cs,
                'tag_existence_rate': tag_existence_rate,
                'value_existence_rate': value_existence_rate,
                'value_standardization_rate': value_standardization_rate,
                'value_diversity': value_diversity
            }
            row_dict.update(group_id)
            rows.append(row_dict)

        return pd.DataFrame(rows)

    def analyze_rates(self, group_cols):
        """
        그룹 단위로 전체 DICOM 태그 분석 수행
        :param group_cols: 그룹화할 컬럼명 리스트
        :return: 모든 그룹의 분석 결과
        """
        grouped = self.df_metadata.groupby(group_cols)
        results = []
        for group_keys, group_df in grouped:
            group_id = dict(zip(group_cols, group_keys))
            one_result = self._analyze_rates_for_one_group(group_df, group_id)
            results.append(one_result)
        return pd.concat(results, ignore_index=True)

    def analyze_rates_with_stats(self, group_cols=['IOD', 'study_global']):
        """
        그룹별 태그 분석 결과로부터 통계량 (Mean, Std, CV, Range 등) 계산
        :param group_cols: 그룹화할 컬럼 리스트
        :return: (개별 결과, 통계 요약 결과)
        """
        rates_df = self.analyze_rates(group_cols=group_cols)
        metric_cols = ['tag_existence_rate', 'value_existence_rate', 'value_standardization_rate', 'value_diversity']

        stats_list = []
        for (iod, tag), group in rates_df.groupby(['IOD', 'Tag']):
            for metric in metric_cols:
                metric_values = group[metric].dropna()
                metric_stats = {
                    'IOD': iod,
                    'Tag': tag,
                    'Attribute Name': group['Attribute Name'].iloc[0],
                    'Metric': metric,
                    'Mean': metric_values.mean(),
                    'Std': metric_values.std(),
                    'CV(%)': (metric_values.std() / metric_values.mean() * 100) if metric_values.mean() != 0 else np.nan,
                    'Min': metric_values.min(),
                    'Max': metric_values.max(),
                    'Range': metric_values.max() - metric_values.min(),
                    'n_groups': len(group)
                }
                stats_list.append(metric_stats)
        return rates_df, pd.DataFrame(stats_list)



