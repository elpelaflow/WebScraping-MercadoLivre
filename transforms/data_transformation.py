import os
import sqlite3
from datetime import datetime, timezone

import pandas as pd

from config_utils import load_search_query


def read_data(path_to_data: str = "") -> pd.DataFrame:
    if not path_to_data:
        json_files = sorted(file for file in os.listdir("data") if file.endswith(".json"))
        if not json_files:
            return pd.DataFrame()
        path_to_data = os.path.join("data", json_files[-1])

    try:
        return pd.read_json(path_to_data)
    except ValueError:
        print("Error while loading data")
        return pd.DataFrame()


def add_columns(df: pd.DataFrame) -> pd.DataFrame:
    search_query = load_search_query()
    scraped_at = datetime.now(timezone.utc).isoformat()

    df["_source"] = f"https://listado.mercadolibre.com.ar/{search_query}"
    df["_search_query"] = search_query
    df["_scraped_at"] = scraped_at
    df["scrap_date"] = scraped_at

    return df


def fill_nulls(df: pd.DataFrame) -> pd.DataFrame:
    if "price" in df.columns:
        df["price"] = df["price"].fillna("0")
    if "reviews_rating_number" in df.columns:
        df["reviews_rating_number"] = df["reviews_rating_number"].fillna("0")
    if "reviews_amount" in df.columns:
        df["reviews_amount"] = df["reviews_amount"].fillna("(0)")
    if "is_ad" in df.columns:
        df["is_ad"] = df["is_ad"].fillna(0)

    return df


def standardize_strings(df: pd.DataFrame) -> pd.DataFrame:
    if "price" in df.columns:
        df["price"] = df["price"].astype(str).str.replace(".", "", regex=False)
    if "reviews_amount" in df.columns:
        df["reviews_amount"] = df["reviews_amount"].astype(str).str.strip("()")

    return df


def normalize_is_ad(df: pd.DataFrame) -> pd.DataFrame:
    if "is_ad" in df.columns:
        df["is_ad"] = (
            df["is_ad"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes", "si", "sí"])
            .astype(int)
        )

    return df


def price_to_float(df: pd.DataFrame) -> pd.DataFrame:
    if "price" in df.columns:
        df["price"] = pd.to_numeric(
            df["price"].astype(str).str.replace(",", ".", regex=False), errors="coerce"
        )

    return df


def save_to_sqlite3(df: pd.DataFrame) -> None:
    with sqlite3.connect("data/database.db") as connection:
        df.to_sql("mercadolivre_items", connection, if_exists="replace", index=False)


def transform_data(path_to_data: str = "") -> None:
    if not path_to_data:
        path_to_data = "../data/data.json"

    df = read_data(path_to_data)
    if df.empty:
        return

    if "ml_item_id" in df.columns:
        df = df.drop_duplicates(subset=["ml_item_id"])
    else:
        df = df.drop_duplicates()

    df = add_columns(df)
    df = fill_nulls(df)
    df = normalize_is_ad(df)
    df = standardize_strings(df)
    df = price_to_float(df)

    save_to_sqlite3(df)


if __name__ == "__main__":
    transform_data("../data/data.json")
