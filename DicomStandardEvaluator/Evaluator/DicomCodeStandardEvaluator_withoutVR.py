import pandas as pd
import numpy as np

class DicomCodeStandardEvaluator_withoutVR:
    def __init__(self, df_metadata, df_standard):
        # Initialize the standard and metadata dataframes
        self.df_standard = df_standard
        self.df_metadata = df_metadata

    def _analyze_rates_for_one_group(self, df, group_id):
        # Analyze the rates for one group
        iod = group_id['IOD']
        iod_standard = self.df_standard[self.df_standard['IOD'] == iod]
        total_files = df['file_id'].nunique()
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
            file_count_tag = df[mask_tag]['file_id'].nunique()
            tag_existence_rate = file_count_tag / total_files

            mask_nonempty = mask_tag & (~empty_value_mask)
            file_count_nonempty = df[mask_nonempty]['file_id'].nunique()
            value_existence_rate = (
                file_count_nonempty / file_count_tag if file_count_tag > 0 else 0
            )

            row_dict = {
                'Tag': tag_val,
                'Attribute Name': std_row['Attribute Name'],
                'total_files': total_files,
                'files_with_tag': file_count_tag,
                'files_with_value': file_count_nonempty,
                'tag_existence_rate': tag_existence_rate,
            'value_existence_rate': value_existence_rate
            }
            row_dict.update(group_id)
            rows.append(row_dict)

        return pd.DataFrame(rows)

    def analyze_rates(self, group_cols):
        # Analyze the rates for all groups
        grouped = self.df_metadata.groupby(group_cols)
        results = []
        for group_keys, group_df in grouped:
            group_id = dict(zip(group_cols, group_keys))
            one_result = self._analyze_rates_for_one_group(group_df, group_id)
            results.append(one_result)
        return pd.concat(results, ignore_index=True)

    def analyze_rates_with_stats(self, group_cols=['IOD', 'study_id']):
        # Calculate the statistics for the rates
        rates_df = self.analyze_rates(group_cols=group_cols)
        metric_cols = ['tag_existence_rate', 'value_existence_rate']

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



