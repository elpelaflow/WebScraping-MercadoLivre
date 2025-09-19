"""Streamlit dashboard for Mercado Libre scraping results."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("data/database.db")
JSON_FALLBACK_PATH = Path("data/data.json")


def load_from_sqlite(db_path: Path) -> pd.DataFrame:
    """Load data from SQLite database, returning an empty DataFrame on failure."""
    if not db_path.exists():
        return pd.DataFrame()

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(db_path)
        return pd.read_sql_query("SELECT * FROM mercadolivre_items", connection)
    except Exception as exc:  # pragma: no cover - surface error to UI
        st.warning(f"No se pudo leer la base de datos SQLite: {exc}")
        return pd.DataFrame()
    finally:
        if connection is not None:
            connection.close()


def load_from_json(json_path: Path) -> pd.DataFrame:
    """Load data from JSON file, returning an empty DataFrame on failure."""
    if not json_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_json(json_path)
    except ValueError as exc:  # pragma: no cover - surface error to UI
        st.error(f"No se pudo leer el archivo JSON: {exc}")
        return pd.DataFrame()


def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize price column if it exists and is textual."""
    if df.empty or "price" not in df.columns:
        return df

    if not pd.api.types.is_numeric_dtype(df["price"]):
        df = df.copy()
        df["price"] = (
            df["price"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        )
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

    return df


def filter_by_search_term(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    if not search_term:
        return df

    contains_mask = df.astype(str).apply(lambda col: col.str.contains(search_term, case=False, na=False))
    return df[contains_mask.any(axis=1)]


def apply_price_filters(df: pd.DataFrame, min_price: float, max_price: float) -> pd.DataFrame:
    if df.empty or "price" not in df.columns:
        return df

    price_series = df["price"].fillna(0)
    return df[(price_series >= min_price) & (price_series <= max_price)]


def render_dashboard(df: pd.DataFrame) -> None:
    st.set_page_config(page_title="Mercado Libre Dashboard", layout="wide")

    st.title("📊 Mercado Libre – Dashboard")

    if df.empty:
        st.info(
            "No hay datos para mostrar en este momento. Genera una nueva búsqueda desde la aplicación o "
            "verifica las fuentes de datos disponibles."
        )
        return

    with st.sidebar:
        st.header("Filtros")
        search_term = st.text_input("Buscar en todos los campos:")
        if "price" in df.columns and df["price"].notna().any():
            min_available = float(df["price"].min())
            max_available = float(df["price"].max())
        else:
            min_available = 0.0
            max_available = 0.0
        min_price = st.number_input("Precio mínimo", value=min_available, step=100.0)
        max_price = st.number_input("Precio máximo", value=max_available, step=100.0)

    total_items = df.shape[0]
    col1, col2 = st.columns(2)
    col1.metric("Total de ítems", total_items)
    if "price" in df.columns and df["price"].notna().any():
        col2.metric("Precio promedio (ARS)", f"{df['price'].mean():,.2f}")
    else:
        col2.metric("Precio promedio (ARS)", "—")

    filtered_df = filter_by_search_term(df, search_term)
    filtered_df = apply_price_filters(filtered_df, min_price, max_price)

    st.markdown("### Resultados")
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)


def main() -> None:
    data_frame = load_from_sqlite(DB_PATH)
    fallback_used = False
    if data_frame.empty:
        fallback_used = True
        data_frame = load_from_json(JSON_FALLBACK_PATH)

    if fallback_used and data_frame.empty:
        st.warning(
            "No fue posible obtener datos desde la base SQLite ni desde el archivo JSON de respaldo."
        )

    normalized_df = normalize_prices(data_frame)
    render_dashboard(normalized_df)


if __name__ == "__main__":
    main()