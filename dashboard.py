import streamlit as st
import pandas as pd


def pagina_dashboard():
    st.subheader("Dashboard statistica")

    if "prima_nota" not in st.session_state or st.session_state.prima_nota.empty:
        st.info("La prima nota è vuota. Genera prima qualche ricevuta.")
        return

    df = st.session_state.prima_nota.copy()
    df["Data_dt"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    df["AnnoMese"] = df["Data_dt"].dt.to_period("M").astype(str)

    # Entrate per mese
    st.markdown("### Entrate per mese")
    entrate_mese = (
        df.groupby("AnnoMese")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("AnnoMese")
    )
    st.line_chart(
        data=entrate_mese,
        x="AnnoMese",
        y="Entrata",
    )

    # Entrate per tipologia
    st.markdown("### Entrate per tipologia importo")
    entrate_tipo = (
        df.groupby("TipoVoce")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("Entrata", ascending=False)
    )
    st.bar_chart(
        data=entrate_tipo,
        x="TipoVoce",
        y="Entrata",
    )

    # Entrate per centro di costo
    st.markdown("### Entrate per attività / centro di costo")
    entrate_centro = (
        df.groupby("CentroCosto")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("Entrata", ascending=False)
    )
    st.bar_chart(
        data=entrate_centro,
        x="CentroCosto",
        y="Entrata",
    )
onsulting – Emesse gestite dall'app; ricezione e invio via Openapi SdI.")
