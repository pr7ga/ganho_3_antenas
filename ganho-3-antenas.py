import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt

st.title("Cálculo de Ganho Absoluto - Método das Três Antenas")

st.markdown("""
Este aplicativo calcula o **ganho absoluto** das antenas por meio do **método das três antenas**,
utilizando os arquivos S2P medidos para cada par de antenas.

**Instruções:**
1. Carregue os três arquivos S2P correspondentes às medições:
   - Antena 1 ↔ Antena 2  
   - Antena 1 ↔ Antena 3  
   - Antena 2 ↔ Antena 3  
2. Informe a frequência (em MHz) para cálculo.
3. O aplicativo calculará o ganho absoluto de cada antena considerando as perdas por reflexão.
""")

# === Uploads ===
file_12 = st.file_uploader("Carregue o arquivo S2P da medição ANT1 ↔ ANT2", type=["s2p"])
file_13 = st.file_uploader("Carregue o arquivo S2P da medição ANT1 ↔ ANT3", type=["s2p"])
file_23 = st.file_uploader("Carregue o arquivo S2P da medição ANT2 ↔ ANT3", type=["s2p"])

freq_input = st.number_input("Frequência de interesse (MHz):", min_value=0.0, step=0.1)

# === Função para ler arquivos S2P ===
def read_s2p(file):
    if file is None:
        return None
    content = file.getvalue().decode(errors='ignore').splitlines()
    data_lines = [line for line in content if not line.startswith('!') and not line.startswith('#') and line.strip() != '']
    df = pd.read_csv(io.StringIO("\n".join(data_lines)),
                     delim_whitespace=True,
                     header=None,
                     names=["Freq", "S11_mag", "S11_phase", "S21_mag", "S21_phase",
                            "S12_mag", "S12_phase", "S22_mag", "S22_phase"])
    return df

# === Função de correção por reflexão ===
def corrected_S21(S21_dB, S11_dB, S22_dB):
    # converte para magnitude linear
    gamma_in = 10**(S11_dB / 20)
    gamma_out = 10**(S22_dB / 20)
    corr = 10 * np.log10((1 - gamma_in**2) * (1 - gamma_out**2))
    return S21_dB + corr

if file_12 and file_13 and file_23:
    df12 = read_s2p(file_12)
    df13 = read_s2p(file_13)
    df23 = read_s2p(file_23)

    if df12 is not None and df13 is not None and df23 is not None:
        # Ajuste de unidade de frequência
        for df in [df12, df13, df23]:
            if df["Freq"].mean() > 1e6:
                df["Freq_MHz"] = df["Freq"] / 1e6
            else:
                df["Freq_MHz"] = df["Freq"]

        # Interpolação dos valores na frequência desejada
        f = freq_input
        if f > 0:
            S21_12 = np.interp(f, df12["Freq_MHz"], df12["S21_mag"])
            S11_12 = np.interp(f, df12["Freq_MHz"], df12["S11_mag"])
            S22_12 = np.interp(f, df12["Freq_MHz"], df12["S22_mag"])

            S21_13 = np.interp(f, df13["Freq_MHz"], df13["S21_mag"])
            S11_13 = np.interp(f, df13["Freq_MHz"], df13["S11_mag"])
            S22_13 = np.interp(f, df13["Freq_MHz"], df13["S22_mag"])

            S21_23 = np.interp(f, df23["Freq_MHz"], df23["S21_mag"])
            S11_23 = np.interp(f, df23["Freq_MHz"], df23["S11_mag"])
            S22_23 = np.interp(f, df23["Freq_MHz"], df23["S22_mag"])

            # Correção de S21 por reflexão
            S21_12_corr = corrected_S21(S21_12, S11_12, S22_12)
            S21_13_corr = corrected_S21(S21_13, S11_13, S22_13)
            S21_23_corr = corrected_S21(S21_23, S11_23, S22_23)

            # === Cálculo dos ganhos individuais ===
            G1 = (S21_12_corr + S21_13_corr - S21_23_corr) / 2
            G2 = (S21_12_corr + S21_23_corr - S21_13_corr) / 2
            G3 = (S21_13_corr + S21_23_corr - S21_12_corr) / 2

            st.markdown("### 📈 Resultados do Cálculo")
            st.write(f"**Frequência:** {f:.2f} MHz")
            st.write(f"**S21(1-2):** {S21_12_corr:.2f} dB")
            st.write(f"**S21(1-3):** {S21_13_corr:.2f} dB")
            st.write(f"**S21(2-3):** {S21_23_corr:.2f} dB")

            st.latex(r"""
            \begin{aligned}
            G_1 &= \frac{S_{21,12} + S_{21,13} - S_{21,23}}{2} \\
            G_2 &= \frac{S_{21,12} + S_{21,23} - S_{21,13}}{2} \\
            G_3 &= \frac{S_{21,13} + S_{21,23} - S_{21,12}}{2}
            \end{aligned}
            """)

            st.success(f"**Ganho da Antena 1 (AUT): {G1:.2f} dBi**")
            st.info(f"**Ganho da Antena 2:** {G2:.2f} dBi")
            st.info(f"**Ganho da Antena 3:** {G3:.2f} dBi")

            # === Gráfico ilustrativo ===
            fig, ax = plt.subplots()
            labels = ['Antena 1', 'Antena 2', 'Antena 3']
            gains = [G1, G2, G3]
            ax.bar(labels, gains, color='skyblue')
            ax.set_ylabel("Ganho (dBi)")
            ax.set_title(f"Ganho absoluto das antenas a {f:.1f} MHz")
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)
        else:
            st.warning("Insira uma frequência de interesse para o cálculo.")
