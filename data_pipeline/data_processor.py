import logging
import pandas as pd

logger = logging.getLogger(__name__)


def remove_duplicates(df):
    """Remove duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()
    logger.debug(f"remove_duplicates: {before} → {len(df)} rows ({before - len(df)} removed)")
    return df


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis not in ("rows", "columns"):
        logger.error(f"Unsupported axis: {axis}")
        raise ValueError(f"Unsupported axis: {axis}")

    if axis == "rows":
        before = len(df)
        df = df.dropna()
        logger.debug(f"handle_missing: {before} → {len(df)} rows")
    else:
        before = df.shape[1]
        df = df.dropna(axis=1)
        logger.debug(f"handle_missing: {before} → {df.shape[1]} columns")

    return df


def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    if method not in ("iqr", "zscore"):
        logger.error(f"Unsupported outlier method: {method}")
        raise ValueError(f"Unsupported outlier method: {method}")

    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column not found: {col}")
            continue

        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Column is not numeric: {col}")
            continue

        before = len(df)

        if method == "iqr":
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            df = df[(df[col] >= lower) & (df[col] <= upper)]
            logger.debug(
                f"{col}: method=iqr, threshold={threshold}, "
                f"lower={lower}, upper={upper}, removed={before - len(df)}"
            )
        else:
            mean = df[col].mean()
            std = df[col].std()
            z_scores = (df[col] - mean) / std
            df = df[z_scores.abs() <= threshold]
            logger.debug(
                f"{col}: method=zscore, threshold={threshold}, "
                f"removed={before - len(df)}"
            )

    return df


def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    settings = config["processing"]

    if settings.get("remove_duplicates"):
        df = remove_duplicates(df)

    missing = settings.get("missing", {})
    if missing.get("enabled"):
        df = handle_missing(df, missing["axis"])

    outliers = settings.get("outliers", {})
    if outliers.get("enabled"):
        df = remove_outliers(
            df,
            outliers["columns"],
            outliers["method"],
            outliers["threshold"],
        )

    return df


def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    rows_before = df_before.shape[0]
    rows_after = df_after.shape[0]
    columns_before = df_before.shape[1]
    columns_after = df_after.shape[1]

    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "columns_before": columns_before,
        "columns_after": columns_after,
        "columns_removed": columns_before - columns_after,
    }