import streamlit as st
import pandas as pd
from datetime import date

from documenti import COLONNE_PRIMA_NOTA, df_to_excel_bytes


def pagina_prima_nota():
    st.subheader("Prima nota (alimentata automaticamente dalle ricevute)")

    if "prima_nota" not in st.session_state:
        st.session_state.prima_nota = pd.DataFrame(columns=COLONNE_PRIMA_NOTA)

    df = st.session_state.prima_nota.copy()

    if df.empty:
        st.info(
            "La prima nota è vuota. "
            "Si compila automaticamente quando emetti le ricevute."
        )
        return

    # Preparazione dati
    df["Data_dt"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    min_date = df["Data_dt"].min()
    max_date = df["Data_dt"].max()
    if pd.isna(min_date):
        min_date = pd.to_datetime(date.today().replace(month=1, day=1))
    if pd.isna(max_date):
        max_date = pd.to_datetime(date.today())

    st.markdown("### Filtri")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    # Periodo
    with col_f1:
        periodo = st.date_input(
            "Periodo (dal - al)",
            (min_date.date(), max_date.date()),
        )
        if isinstance(periodo, tuple) and len(periodo) == 2:
            data_da, data_a = periodo
        else:
            data_da, data_a = min_date.date(), max_date.date()

    # Tipologia importo
    with col_f2:
        tipi = sorted(
            [t for t in df["TipoVoce"].dropna().unique().tolist() if t != ""]
        )
        tipo_scelto = st.selectbox(
            "Tipologia importo",
            ["Tutte"] + tipi,
        )

    # Metodo di pagamento
    with col_f3:
        metodi = sorted(
            [m for m in df["MetodoPagamento"].dropna().unique().tolist() if m != ""]
        )
        metodo_scelto = st.selectbox(
            "Metodo di pagamento",
            ["Tutti"] + metodi,
        )

    # Centro di costo
    with col_f4:
        centri = sorted(
            [c for c in df["CentroCosto"].dropna().unique().tolist() if c != ""]
        )
        centro_scelto = st.selectbox(
            "Attività / Centro di costo",
            ["Tutti"] + centri,
        )

    # Applicazione filtri
    mask = (df["Data_dt"].dt.date >= data_da) & (df["Data_dt"].dt.date <= data_a)
    if tipo_scelto != "Tutte":
        mask &= df["TipoVoce"] == tipo_scelto
    if metodo_scelto != "Tutti":
        mask &= df["MetodoPagamento"] == metodo_scelto
    if centro_scelto != "Tutti":
        mask &= df["CentroCosto"] == centro_scelto

    df_filtrato = df.loc[mask].copy()

    if "Data_dt" in df_filtrato.columns:
        df_filtrato = df_filtrato.drop(columns=["Data_dt"])

    st.markdown("### Elenco movimenti filtrati")
    st.dataframe(df_filtrato)

    # Export Excel filtrato
    excel_bytes = df_to_excel_bytes(df_filtrato, sheet_name="PrimaNota")
    st.download_button(
        label="⬇️ Esporta prima nota (filtrata) in Excel",
        data=excel_bytes,
        file_name="prima_nota_asd_ssd_filtrata.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Riepilogo
    st.markdown("### Riepilogo (sui dati filtrati)")

    totale_entrate = df_filtrato["Entrata"].sum() if not df_filtrato.empty else 0.0
    totale_uscite = df_filtrato["Uscita"].sum() if not df_filtrato.empty else 0.0
    saldo = totale_entrate - totale_uscite

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Entrate totali",
        f"€ {totale_entrate:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
    col2.metric(
        "Uscite totali",
        f"€ {totale_uscite:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
    col3.metric(
        "Saldo",
        f"€ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
