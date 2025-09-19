"""Streamlit dashboard for Mercado Libre scraping results."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from config_utils import load_search_query
from services.domain_discovery import fetch_domain_discovery

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

    if "price" in df.columns and df["price"].notna().any():
        min_available = float(df["price"].min())
        max_available = float(df["price"].max())
    else:
        min_available = 0.0
        max_available = 0.0

    search_term = ""
    min_price = min_available
    max_price = max_available

    with st.sidebar:
        st.header("Filtros")
        with st.sidebar.expander("🧰 Filtros", expanded=True):
            # Si ya tenés tabs para Básicos/Avanzados, mantenelos y solo agrega la de Domain Discovery.
            try:
                tab_basicos, tab_avanzados, tab_dd = st.tabs(["Básicos", "Avanzados", "Domain Discovery"])
            except Exception:
                # Fallback si no existen otras tabs
                tab_dd, = st.tabs(["Domain Discovery"])

            with tab_dd:
                q = load_search_query()  # misma búsqueda que definiste en search_ui
                st.caption(f"Búsqueda actual: **{q}**")

                dd_limit = st.slider("Límite del llamado", 1, 20, 5, key="dd_limit")
                site = st.selectbox("Site", ["MLA"], index=0, help="Dejalo en MLA salvo que necesites otro")

                @st.cache_data(show_spinner=False, ttl=60*60)
                def _cached_domain_discovery(query: str, limit: int, site_code: str):
                    return fetch_domain_discovery(query=query, limit=limit, site=site_code)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Refrescar"):
                        _cached_domain_discovery.clear()

                raw = _cached_domain_discovery(q, dd_limit, site)

                st.markdown("**Respuesta (JSON crudo):**")
                st.json(raw, expanded=False)

                # Vista rápida (si se puede)
                if isinstance(raw, list) and len(raw) > 0:
                    import pandas as pd
                    df_dd = pd.DataFrame(raw)
                    keep = [c for c in ["domain_id", "domain_name", "category_id", "category_name", "relevance"] if c in df_dd.columns]
                    if keep:
                        st.markdown("**Vista rápida (tabla):**")
                        st.dataframe(df_dd[keep], use_container_width=True, hide_index=True)

                # URL de ejemplo para copiar/pegar
                import urllib.parse
                url_example = "https://api.mercadolibre.com/sites/{}/domain_discovery/search?q={}&limit={}".format(
                    site, urllib.parse.quote_plus(q or ""), dd_limit
                )
                st.code(f"GET {url_example}", language="bash")

                # (Opcional) Filtrar dataset principal por categoría sugerida si df existe en este scope:
                try:
                    if isinstance(raw, list) and len(raw) > 0 and "category_id" in df.columns:
                        sugeridas = pd.DataFrame(raw)
                        if "category_id" in sugeridas.columns:
                            opciones = (
                                (sugeridas["category_name"].fillna("") + " (" + sugeridas["category_id"] + ")")
                                if "category_name" in sugeridas.columns
                                else sugeridas["category_id"]
                            ).dropna().drop_duplicates().tolist()
                            choice = st.selectbox("Filtrar dataset por categoría sugerida", ["(ninguna)"] + opciones)
                            if choice != "(ninguna)":
                                cat_elegida = choice.split("(")[-1].rstrip(")")
                                df = df[df["category_id"] == cat_elegida]
                    elif isinstance(raw, list) and len(raw) > 0 and "category_id" not in (df.columns if 'df' in locals() else []):
                        st.warning("Tu dataset no incluye 'category_id'. Extraelo en el spider y guardalo para poder filtrar por categoría.")
                except Exception:
                    pass

            if "tab_basicos" in locals():
                with tab_basicos:
                    search_term = st.text_input("Buscar en todos los campos:")
                    min_price = st.number_input("Precio mínimo", value=min_available, step=100.0)
                    max_price = st.number_input("Precio máximo", value=max_available, step=100.0)
            else:
                search_term = st.text_input("Buscar en todos los campos:")
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