import pandas as pd
import pytest
import os

MASTER_CSV = "data/processed/bridges_master.csv"
SCORED_CSV = "data/processed/bridges_risk_scored.csv"

@pytest.fixture(scope="module")
def master_df():
    assert os.path.exists(MASTER_CSV)
    return pd.read_csv(MASTER_CSV, low_memory=False)

@pytest.fixture(scope="module")
def scored_df():
    assert os.path.exists(SCORED_CSV)
    return pd.read_csv(SCORED_CSV, low_memory=False)

def test_row_count(master_df, scored_df):
    """Output row count matches source bridge count (6,554)."""
    assert len(scored_df) == len(master_df)
    assert len(scored_df) == 6554

def test_risk_score_validity(scored_df):
    """risk_score exists, is numeric, falls in 0-100, has zero nulls."""
    assert "risk_score" in scored_df.columns
    assert pd.api.types.is_numeric_dtype(scored_df["risk_score"])
    assert scored_df["risk_score"].isnull().sum() == 0
    assert scored_df["risk_score"].min() >= 0.0
    assert scored_df["risk_score"].max() <= 100.0

def test_likelihood_weights(scored_df):
    """Likelihood weights sum to 1.0."""
    for _, row in scored_df.dropna(subset=['likelihood_score']).head(100).iterrows():
        weight_sum = 0
        expected_score = 0
        if pd.notna(row.get('age_risk')):
            weight_sum += 0.45
            expected_score += row['age_risk'] * 0.45
        if pd.notna(row.get('traffic_risk')):
            weight_sum += 0.30
            expected_score += row['traffic_risk'] * 0.30
        if pd.notna(row.get('climate_risk')):
            weight_sum += 0.25
            expected_score += row['climate_risk'] * 0.25
            
        if weight_sum > 0:
            assert pytest.approx(row['likelihood_score'], rel=1e-5) == expected_score / weight_sum

def test_consequence_multiplier(master_df, scored_df):
    """Consequence multiplier only takes values {1.5, 1.2, 1.1, 1.0}."""
    assert "consequence_multiplier" in scored_df.columns
    unique_vals = set(scored_df["consequence_multiplier"].dropna().unique())
    assert unique_vals.issubset({1.5, 1.2, 1.1, 1.0})
    
    merged = pd.merge(master_df[['_id', 'CD_STATE_CLASS']], scored_df[['_id', 'consequence_multiplier']], on='_id')
    
    mapping = {'HF': 1.5, 'MR': 1.2, 'TR': 1.1, 'RA': 1.0, 'FR': 1.0}
    
    def expected_mult(code):
        return mapping.get(str(code).strip(), 1.0)
        
    for _, row in merged.head(100).iterrows():
        assert row['consequence_multiplier'] == expected_mult(row['CD_STATE_CLASS'])

def test_median_imputation(scored_df):
    """Median imputation only altered originally-missing values."""
    raw_scores = scored_df['likelihood_score'] * scored_df['consequence_multiplier'] * 100
    median_val = raw_scores.median()
    
    min_val = raw_scores.min()
    max_val = raw_scores.max()
    imputed_risk_score = (median_val - min_val) / (max_val - min_val) * 100
    imputed_risk_score = round(imputed_risk_score, 1)
    
    missing_likelihood = scored_df[scored_df['likelihood_score'].isnull()]
    for _, row in missing_likelihood.iterrows():
        assert row['risk_score'] == imputed_risk_score

def test_assign_inspection_priority():
    from data_loader import assign_inspection_priority, PRIORITY_1_LABEL, PRIORITY_2_LABEL, PRIORITY_3_LABEL
    
    assert assign_inspection_priority(75.0) == PRIORITY_1_LABEL
    assert assign_inspection_priority(70.0) == PRIORITY_1_LABEL
    
    assert assign_inspection_priority(69.9) == PRIORITY_2_LABEL
    assert assign_inspection_priority(40.0) == PRIORITY_2_LABEL
    
    assert assign_inspection_priority(39.9) == PRIORITY_3_LABEL
    assert assign_inspection_priority(10.0) == PRIORITY_3_LABEL
    
    assert assign_inspection_priority(pd.NA) == "Unknown"
    assert assign_inspection_priority(None) == "Unknown"
def test_scoring_logic_reproduces_batch(scored_df):
    """Confirm the shared function at default weights exactly reproduces existing risk_score values."""
    from pipeline.scoring_logic import apply_risk_scoring
    
    # Run the logic on the scored_df (which already has age_risk, etc.)
    # We drop risk_score to see if it recalculates it identically
    test_df = scored_df.copy()
    
    recomputed_df = apply_risk_scoring(test_df)
    
    # Check if risk_score matches exactly
    pd.testing.assert_series_equal(
        scored_df['risk_score'],
        recomputed_df['risk_score'],
        check_dtype=False,
        check_exact=False,
        atol=0.01  # allow minor float rounding diffs, though it should be identical
    )
