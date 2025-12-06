import streamlit as st
import pandas as pd


def pagina_dashboard():
    st.subheader("Dashboard statistica")

    # Controllo dati
    if "prima_nota" not in st.session_state or st.session_state.prima_nota.empty:
        st.info("La prima nota è vuota. Genera prima qualche ricevuta.")
        return

    df = st.session_state.prima_nota.copy()

    # Converto data in datetime e creo campo AnnoMese
    df["Data_dt"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    df["AnnoMese"] = df["Data_dt"].dt.to_period("M").astype(str)

    # ==========================
    # ENTRATE PER MESE
    # ==========================
    st.markdown("### Entrate per mese")

    entrate_mese = (
        df.groupby("AnnoMese")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("AnnoMese")
    )

    if entrate_mese.empty:
        st.info("Nessuna entrata registrata per mese.")
    else:
        st.line_chart(
            data=entrate_mese,
            x="AnnoMese",
            y="Entrata",
        )

    # ==========================
    # ENTRATE PER TIPOLOGIA
    # ==========================
    st.markdown("### Entrate per tipologia importo")

    entrate_tipo = (
        df.groupby("TipoVoce")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("Entrata", ascending=False)
    )

    if entrate_tipo.empty:
        st.info("Nessuna entrata per tipologia.")
    else:
        st.bar_chart(
            data=entrate_tipo,
            x="TipoVoce",
            y="Entrata",
        )

    # ==========================
    # ENTRATE PER CENTRO DI COSTO
    # ==========================
    st.markdown("### Entrate per attività / centro di costo")

    entrate_centro = (
        df.groupby("CentroCosto")["Entrata"]
        .sum()
        .reset_index()
        .sort_values("Entrata", ascending=False)
    )

    if entrate_centro.empty:
        st.info("Nessuna entrata per attività / centro di costo.")
    else:
        st.bar_chart(
            data=entrate_centro,
            x="CentroCosto",
            y="Entrata",
        )
