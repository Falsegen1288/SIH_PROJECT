"""
Phase 2 (Updated with Section A0 Issue 3 Fix):
Preprocessing and Feature Engineering Pipeline for Global Multi-Commodity Price Forecasting.

Implements:
- Section A0: Gap-size-adaptive imputation:
    * real: raw market trades
    * interpolated_short_gap (<= 7 days): log-linear interpolation
    * carried_seasonal_gap (8 - 90 days): flat forward-fill
    * structural_edge (pre-inception / post-exit): rectangular grid alignment only
- Section A0: Unified Training Mask (is_training_sample):
    * Origin day t has fill_type == 'real'
    * Lookback window t-60 does not overlap pre-inception structural_edge (t >= first_real_trade + 60 days)
    * Target lookahead t+15 does not exceed last_real_trade (t <= last_real_trade - 15 days)
- B1: Lags (1, 2, 3, 7, 14, 30, 60)
- B2: Rolling statistics (7, 14, 30, 60) and stochastic position envelopes
- B3: Return volatility (ARCH-aware rolling std of dlog(P))
- B4: Scale-invariant log-spread (log(Max/Min)) and spread dynamics
- B4b: Staleness tracking (days_since_last_real_trade)
- B5: Cross-sectional market return (M_t = median_c(dlog(P))) and idiosyncratic excess return
- B6 (Revised): Multi-horizon targets:
    * target_7d: Auxiliary task
    * target_15d: Primary forecasting task
    (target_1d dropped due to destination-side fill degeneracy)
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional


def filter_qualifying_commodities(
    df: pd.DataFrame,
    min_span_days: int = 730,
    min_rows: int = 500
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filters commodities that satisfy minimum history requirements for reliable deep learning.
    Standardizes unit casing (e.g. KG -> Kg).
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Unit'] = df['Unit'].replace({'KG': 'Kg'})
    
    spans = df.groupby('Commodity')['Date'].agg(['min', 'max', 'count'])
    spans['span_days'] = (spans['max'] - spans['min']).dt.days + 1
    
    qualifying = spans[
        (spans['span_days'] >= min_span_days) & 
        (spans['count'] >= min_rows)
    ].index.tolist()
    
    filtered_df = df[df['Commodity'].isin(qualifying)].copy()
    return filtered_df, sorted(qualifying)


def create_adaptive_calendar_grid_per_commodity(
    df: pd.DataFrame,
    global_start_date: Optional[pd.Timestamp] = None,
    global_end_date: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """
    Constructs a uniform global daily calendar grid per commodity with Section A0 gap-adaptive imputation:
    - 'real': raw market trade record
    - 'interpolated_short_gap' (<= 7 days): log-linear price interpolation
    - 'carried_seasonal_gap' (8 - 90 days): flat forward fill
    - 'structural_edge': pre-inception / post-exit boundary padding
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.drop(columns=['SN'], errors='ignore')
    
    if global_start_date is None:
        global_start_date = df['Date'].min()
    if global_end_date is None:
        global_end_date = df['Date'].max()
        
    full_calendar = pd.date_range(start=global_start_date, end=global_end_date, freq='D', name='Date')
    
    grid_records = []
    
    for comm, raw_group in df.groupby('Commodity'):
        raw_group = raw_group.sort_values('Date').drop_duplicates(subset=['Date'])
        unit = raw_group['Unit'].iloc[0]
        
        first_real_date = raw_group['Date'].min()
        last_real_date = raw_group['Date'].max()
        
        # Reindex to full global calendar
        g = raw_group.set_index('Date').reindex(full_calendar)
        g['Commodity'] = comm
        g['Unit'] = unit
        
        is_real = ~g['Average'].isna()
        g['is_real_trade'] = is_real.astype(int)
        
        # Classify each day's fill_type
        dates = g.index
        fill_types = np.empty(len(dates), dtype=object)
        
        # Identify boundaries
        pre_mask = dates < first_real_date
        post_mask = dates > last_real_date
        real_mask = is_real.values
        
        fill_types[pre_mask] = 'structural_edge'
        fill_types[post_mask] = 'structural_edge'
        fill_types[real_mask] = 'real'
        
        # In-between gap dates
        gap_indices = np.where((~pre_mask) & (~post_mask) & (~real_mask))[0]
        real_indices = np.where(real_mask)[0]
        
        for idx in gap_indices:
            prev_real_idx = real_indices[real_indices < idx][-1]
            next_real_idx = real_indices[real_indices > idx][0]
            gap_length = (dates[next_real_idx] - dates[prev_real_idx]).days - 1
            
            if gap_length <= 7:
                fill_types[idx] = 'interpolated_short_gap'
            else:
                fill_types[idx] = 'carried_seasonal_gap'
                
        g['fill_type'] = fill_types
        
        # Apply Price Imputation according to fill_type
        # 1. Log-linear interpolation for short gaps
        log_avg = np.log(raw_group.set_index('Date')['Average']).reindex(full_calendar)
        log_min = np.log(np.maximum(raw_group.set_index('Date')['Minimum'], 1.0)).reindex(full_calendar)
        log_max = np.log(np.maximum(raw_group.set_index('Date')['Maximum'], 1.0)).reindex(full_calendar)
        
        log_avg_interp = np.exp(log_avg.interpolate(method='time'))
        log_min_interp = np.exp(log_min.interpolate(method='time'))
        log_max_interp = np.exp(log_max.interpolate(method='time'))
        
        # 2. Forward fill for seasonal gaps and post-exit edges
        avg_ffill = g['Average'].ffill()
        min_ffill = g['Minimum'].ffill()
        max_ffill = g['Maximum'].ffill()
        
        # Backfill for pre-inception edge
        avg_bfill = avg_ffill.bfill()
        min_bfill = min_ffill.bfill()
        max_bfill = max_ffill.bfill()
        
        final_avg = np.where(
            g['fill_type'] == 'interpolated_short_gap',
            log_avg_interp,
            avg_bfill
        )
        final_min = np.where(
            g['fill_type'] == 'interpolated_short_gap',
            log_min_interp,
            min_bfill
        )
        final_max = np.where(
            g['fill_type'] == 'interpolated_short_gap',
            log_max_interp,
            max_bfill
        )
        
        g['Average'] = final_avg
        g['Minimum'] = final_min
        g['Maximum'] = final_max
        
        # Staleness indicator: days_since_last_real_trade (B4b)
        staleness = np.zeros(len(dates), dtype=np.float32)
        count = 0
        for i in range(len(dates)):
            if g['is_real_trade'].iloc[i] == 1:
                count = 0
            else:
                count += 1
            staleness[i] = count
        g['days_since_last_real_trade'] = staleness
        
        # Unified Training Mask (Section A0 Option C)
        valid_origin = (g['fill_type'] == 'real')
        valid_lookback = (dates >= (first_real_date + pd.Timedelta(days=60)))
        valid_lookahead = (dates <= (last_real_date - pd.Timedelta(days=15)))
        
        g['is_training_sample'] = (valid_origin & valid_lookback & valid_lookahead).astype(int)
        g['first_real_date'] = first_real_date
        g['last_real_date'] = last_real_date
        
        grid_records.append(g.reset_index())
        
    return pd.concat(grid_records, ignore_index=True)


def compute_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes cross-sectional market return (B5):
    M_t = median_c(dlog(Average_{t, c})) across active qualifying commodities.
    Adds Idiosyncratic Excess Return: ExcessReturn_{t, c} = dlog(Average_{t, c}) - M_t.
    """
    df = df.copy()
    df = df.sort_values(['Commodity', 'Date'])
    
    df['log_Average'] = np.log1p(df['Average'])
    df['dlog_Average'] = df.groupby('Commodity')['log_Average'].diff().fillna(0.0)
    
    # Compute market median only over real/active commodities on each date
    market_median_ret = df[df['fill_type'] != 'structural_edge'].groupby('Date')['dlog_Average'].median().rename('market_dlog_median')
    
    df = df.merge(market_median_ret, on='Date', how='left')
    df['market_dlog_median'] = df['market_dlog_median'].fillna(0.0)
    df['excess_return'] = df['dlog_Average'] - df['market_dlog_median']
    
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates the complete suite of justified indicators (B1 - B6).
    Multi-horizon targets are target_7d (auxiliary) and target_15d (primary).
    """
    df = df.copy()
    df = df.sort_values(['Commodity', 'Date'])
    
    df['log_Minimum'] = np.log1p(df['Minimum'])
    df['log_Maximum'] = np.log1p(df['Maximum'])
    
    # B4. Scale-invariant LogSpread: log(Maximum / Minimum)
    safe_min = np.maximum(df['Minimum'], 1.0)
    safe_max = np.maximum(df['Maximum'], safe_min)
    df['log_spread'] = np.log(safe_max / safe_min)
    
    engineered_groups = []
    lag_list = [1, 2, 3, 7, 14, 30, 60]
    window_list = [7, 14, 30, 60]
    
    for comm, group in df.groupby('Commodity'):
        g = group.sort_values('Date').copy()
        
        # B1. Lag Features
        for lag in lag_list:
            g[f'dlog_lag_{lag}'] = g['dlog_Average'].shift(lag)
            g[f'log_price_ratio_lag_{lag}'] = g['log_Average'] - g['log_Average'].shift(lag)
            g[f'excess_return_lag_{lag}'] = g['excess_return'].shift(lag)
            g[f'log_spread_lag_{lag}'] = g['log_spread'].shift(lag)
            g[f'market_dlog_lag_{lag}'] = g['market_dlog_median'].shift(lag)
            
        # B2. Rolling Statistics
        for w in window_list:
            roll_log_p = g['log_Average'].rolling(window=w, min_periods=w)
            roll_raw_p = g['Average'].rolling(window=w, min_periods=w)
            
            g[f'rolling_mean_{w}'] = roll_log_p.mean()
            g[f'rolling_std_{w}'] = roll_log_p.std()
            g[f'price_to_rolling_mean_{w}'] = g['log_Average'] - g[f'rolling_mean_{w}']
            
            roll_min = roll_raw_p.min()
            roll_max = roll_raw_p.max()
            g[f'stochastic_pos_{w}'] = (g['Average'] - roll_min) / (roll_max - roll_min + 1e-5)
            g[f'stochastic_pos_{w}'] = g[f'stochastic_pos_{w}'].clip(0.0, 1.0)
            
        # B3. Volatility-Aware Indicators (ARCH / Return Volatility)
        g['return_volatility_14d'] = g['dlog_Average'].rolling(window=14, min_periods=14).std()
        g['return_volatility_30d'] = g['dlog_Average'].rolling(window=30, min_periods=30).std()
        g['return_volatility_60d'] = g['dlog_Average'].rolling(window=60, min_periods=60).std()
        
        # B4. Spread dynamics
        g['log_spread_diff_7d'] = g['log_spread'] - g['log_spread'].shift(7)
        g['log_spread_diff_30d'] = g['log_spread'] - g['log_spread'].shift(30)
        
        # B6 (Revised). Multi-Horizon Targets: target_7d (auxiliary) and target_15d (primary)
        for h in [7, 15]:
            g[f'target_{h}d'] = g['log_Average'].shift(-h) - g['log_Average']
            g[f'target_raw_{h}d'] = g['Average'].shift(-h)
            
        engineered_groups.append(g)
        
    res_df = pd.concat(engineered_groups, ignore_index=True)
    
    # B4. Cyclical Calendar Encodings
    dates = pd.to_datetime(res_df['Date'])
    day_of_year = dates.dt.dayofyear
    day_of_week = dates.dt.dayofweek
    month = dates.dt.month
    
    res_df['sin_day_of_year'] = np.sin(2.0 * np.pi * day_of_year / 365.25).astype(np.float32)
    res_df['cos_day_of_year'] = np.cos(2.0 * np.pi * day_of_year / 365.25).astype(np.float32)
    res_df['sin_day_of_week'] = np.sin(2.0 * np.pi * day_of_week / 7.0).astype(np.float32)
    res_df['cos_day_of_week'] = np.cos(2.0 * np.pi * day_of_week / 7.0).astype(np.float32)
    res_df['day_of_week'] = day_of_week.astype(int)
    res_df['month'] = month.astype(int)
    
    # Entity ID Encodings
    comm_categories = sorted(res_df['Commodity'].unique())
    comm_to_id = {c: i for i, c in enumerate(comm_categories)}
    res_df['commodity_id'] = res_df['Commodity'].map(comm_to_id).astype(int)
    
    unit_categories = sorted(res_df['Unit'].unique())
    unit_to_id = {u: i for i, u in enumerate(unit_categories)}
    res_df['unit_id'] = res_df['Unit'].map(unit_to_id).astype(int)
    
    # Fill boundary NaNs for structural edges
    feature_cols = [
        c for c in res_df.columns 
        if c not in ['Commodity', 'Unit', 'Date', 'fill_type', 'is_training_sample', 
                     'first_real_date', 'last_real_date',
                     'target_7d', 'target_15d', 
                     'target_raw_7d', 'target_raw_15d']
    ]
    res_df[feature_cols] = res_df.groupby('Commodity')[feature_cols].bfill().ffill().fillna(0.0)
    
    return res_df


def build_full_processed_dataset(
    raw_csv_path: str = 'data/kalimati_tarkari_dataset.csv',
    min_span_days: int = 730,
    min_rows: int = 500
) -> Tuple[pd.DataFrame, Dict]:
    """
    End-to-end execution of Phase 2 pipeline.
    """
    raw_df = pd.read_csv(raw_csv_path)
    
    filtered_df, qualifying_comms = filter_qualifying_commodities(
        raw_df, min_span_days=min_span_days, min_rows=min_rows
    )
    grid_df = create_adaptive_calendar_grid_per_commodity(filtered_df)
    market_df = compute_market_features(grid_df)
    engineered_df = engineer_features(market_df)
    
    feature_cols = [
        col for col in engineered_df.columns 
        if col not in [
            'Commodity', 'Unit', 'Date', 'fill_type', 'is_training_sample',
            'first_real_date', 'last_real_date',
            'target_7d', 'target_15d', 
            'target_raw_7d', 'target_raw_15d'
        ]
    ]
    
    training_rows = (engineered_df['is_training_sample'] == 1).sum()
    
    meta = {
        'total_grid_rows': len(engineered_df),
        'training_mask_rows': int(training_rows),
        'num_commodities': len(qualifying_comms),
        'qualifying_commodities': qualifying_comms,
        'feature_columns': feature_cols,
        'target_columns': ['target_7d', 'target_15d'],
        'date_range': (str(engineered_df['Date'].min().date()), str(engineered_df['Date'].max().date())),
        'fill_type_breakdown': engineered_df['fill_type'].value_counts().to_dict(),
        'training_target_15d_nulls': int(engineered_df[engineered_df['is_training_sample'] == 1]['target_15d'].isna().sum())
    }
    
    return engineered_df, meta
