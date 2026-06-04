import pandas as pd
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path

SYNTHETIC_FRAUD_SAMPLES = 100
SYNTHETIC_LEGIT_SAMPLES = 250
RANDOM_STATE = 42
MAX_REAL_TRAINING_ROWS = 120000
FRAUD_OVERSAMPLE_ROWS = 20000
TREE_COUNT = 50


def generate_synthetic_fraud_features(df, sample_size=SYNTHETIC_FRAUD_SAMPLES):
    features = ['amt', 'hour', 'age', 'city_pop']
    fraud_pool = df[df['is_fraud'] == 1][features]
    base_pool = fraud_pool if not fraud_pool.empty else df[features]

    synthetic = (
        base_pool.sample(n=sample_size, replace=True, random_state=RANDOM_STATE)
        .reset_index(drop=True)
        .copy()
    )

    rng = np.random.default_rng(RANDOM_STATE)
    synthetic['amt'] = np.clip(
        synthetic['amt'] * rng.uniform(3.0, 9.0, size=sample_size),
        1500,
        500000,
    )
    synthetic['hour'] = rng.choice([0, 1, 2, 3, 4, 5, 22, 23], size=sample_size)
    synthetic['age'] = np.clip(
        synthetic['age'] + rng.integers(-5, 6, size=sample_size),
        18,
        90,
    )
    synthetic['city_pop'] = np.clip(
        (synthetic['city_pop'] * rng.uniform(0.2, 0.8, size=sample_size)).astype(int),
        50,
        None,
    )

    synthetic['is_fraud'] = 1
    return synthetic


def generate_synthetic_legit_features(df, sample_size=SYNTHETIC_LEGIT_SAMPLES):
    features = ['amt', 'hour', 'age', 'city_pop']
    legit_pool = df[df['is_fraud'] == 0][features]
    if legit_pool.empty:
        legit_pool = df[features]

    synthetic = (
        legit_pool.sample(n=sample_size, replace=True, random_state=RANDOM_STATE + 1)
        .reset_index(drop=True)
        .copy()
    )

    rng = np.random.default_rng(RANDOM_STATE + 1)
    moderate_high_count = int(sample_size * 0.7)
    night_count = sample_size - moderate_high_count
    amount_col = synthetic.columns.get_loc('amt')
    hour_col = synthetic.columns.get_loc('hour')
    hour_dtype = synthetic['hour'].dtype

    # Many legitimate edge cases: moderately high amounts during day/evening.
    synthetic.iloc[:moderate_high_count, amount_col] = np.clip(
        synthetic.iloc[:moderate_high_count, amount_col]
        * rng.uniform(3.0, 8.0, size=moderate_high_count),
        600,
        6000,
    )
    moderate_hours = rng.choice(
        [9, 10, 11, 12, 13, 14, 15, 18, 19, 20, 21],
        size=moderate_high_count,
    ).astype(hour_dtype, copy=False)
    synthetic.iloc[:moderate_high_count, hour_col] = moderate_hours

    # Some legitimate night transactions too, but at milder amounts.
    if night_count > 0:
        start = moderate_high_count
        synthetic.iloc[start:, amount_col] = np.clip(
            synthetic.iloc[start:, amount_col] * rng.uniform(1.5, 4.0, size=night_count),
            150,
            2500,
        )
        night_hours = rng.choice([22, 23, 0, 1], size=night_count).astype(
            hour_dtype,
            copy=False,
        )
        synthetic.iloc[start:, hour_col] = night_hours

    synthetic['age'] = np.clip(
        synthetic['age'] + rng.integers(-8, 9, size=sample_size),
        18,
        90,
    )
    synthetic['city_pop'] = np.clip(
        (synthetic['city_pop'] * rng.uniform(0.7, 1.3, size=sample_size)).astype(int),
        50,
        None,
    )

    synthetic['is_fraud'] = 0
    return synthetic

def train_fraud_model():
    # Load fraudTrain.csv
    csv_path = Path(__file__).parent.parent.parent / 'fraudTrain.csv'
    df = pd.read_csv(csv_path)
    
    # Preprocess
    df['trans_date_trans_time'] = pd.to_datetime(df['trans_date_trans_time'])
    df['hour'] = df['trans_date_trans_time'].dt.hour
    df['dob'] = pd.to_datetime(df['dob'])
    df['age'] = (pd.Timestamp.now() - df['dob']).dt.days // 365
    
    # Features: amt, hour, age, city_pop
    features = ['amt', 'hour', 'age', 'city_pop']
    if len(df) > MAX_REAL_TRAINING_ROWS:
        fraud_rows = df[df['is_fraud'] == 1]
        non_fraud_rows = df[df['is_fraud'] == 0]

        fraud_sample_size = min(len(fraud_rows), FRAUD_OVERSAMPLE_ROWS)
        non_fraud_sample_size = max(MAX_REAL_TRAINING_ROWS - fraud_sample_size, 0)

        sampled_parts = []
        if fraud_sample_size:
            sampled_parts.append(
                fraud_rows.sample(
                    n=fraud_sample_size,
                    replace=False,
                    random_state=RANDOM_STATE,
                )
            )
        if non_fraud_sample_size:
            sampled_parts.append(
                non_fraud_rows.sample(
                    n=min(len(non_fraud_rows), non_fraud_sample_size),
                    replace=False,
                    random_state=RANDOM_STATE,
                )
            )
        df = pd.concat(sampled_parts, ignore_index=True).sample(
            frac=1,
            random_state=RANDOM_STATE,
        ).reset_index(drop=True)

    synthetic_fraud = generate_synthetic_fraud_features(df)
    synthetic_legit = generate_synthetic_legit_features(df)

    training_df = pd.concat(
        [df[features + ['is_fraud']], synthetic_fraud, synthetic_legit],
        ignore_index=True,
    )

    X = training_df[features]
    y = training_df['is_fraud']
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=TREE_COUNT,
        random_state=RANDOM_STATE,
        class_weight='balanced_subsample',
        min_samples_leaf=2,
        n_jobs=1,
    )
    model.fit(X, y)
    
    # Save model
    project_root = Path(__file__).parent.parent.parent
    backend_root = Path(__file__).parent.parent
    joblib.dump(model, project_root / 'fraud_model.pkl')
    joblib.dump(model, backend_root / 'fraud_model.pkl')
    print(
        f"Fraud model trained with {len(df)} real rows and "
        f"{len(synthetic_fraud)} synthetic fraud rows plus "
        f"{len(synthetic_legit)} synthetic legit rows."
    )

def train_creditcard_model():
    # Load creditcard.csv
    csv_path = Path(__file__).parent.parent.parent / 'creditcard.csv'
    df = pd.read_csv(csv_path)
    
    # Features: all except Class
    X = df.drop('Class', axis=1)
    y = df['Class']
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=TREE_COUNT,
        random_state=RANDOM_STATE,
        class_weight='balanced_subsample',
        min_samples_leaf=2,
        n_jobs=1,
    )
    model.fit(X, y)
    
    # Save model
    project_root = Path(__file__).parent.parent.parent
    backend_root = Path(__file__).parent.parent
    joblib.dump(model, project_root / 'creditcard_model.pkl')
    joblib.dump(model, backend_root / 'creditcard_model.pkl')
    print("Creditcard model trained and saved.")

def train_models(force_retrain=False):
    project_root = Path(__file__).parent.parent.parent
    fraud_model_path = project_root / 'fraud_model.pkl'
    creditcard_model_path = project_root / 'creditcard_model.pkl'
    
    if force_retrain or not fraud_model_path.exists():
        train_fraud_model()
    else:
        print("Fraud model already exists.")
    
    if force_retrain or not creditcard_model_path.exists():
        train_creditcard_model()
    else:
        print("Creditcard model already exists.")

if __name__ == "__main__":
    train_models(force_retrain=True)
