import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Auto-Desenvolvimento Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Otimizado e Responsivo ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-weight: 700; }
        
        /* Card Customizado (Adaptável ao Tema Dark/Light) */
        .metric-card {
            background-color: var(--secondary-background-color);
            border: 1px solid var(--secondary-background-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s ease;
        }
        .metric-card:hover { transform: translateY(-2px); border-color: #4F8BF9; }
        .metric-label { opacity: 0.7; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
        .metric-value { color: var(--primary-color); font-size: 2rem; font-weight: 700; margin: 8px 0; }
        .metric-delta { font-size: 0.8rem; font-weight: 600; }

        /* Botões refinados */
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
            height: 3em;
            transition: all 0.3s ease;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Componentes Visuais ---
def metric_card(label, value, subtext=None, color="var(--text-color)"):
    """Componente HTML puro para evitar limitações do st.metric"""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta" style="color: {color};">{subtext if subtext else '&nbsp;'}</div>
    </div>
    """, unsafe_allow_html=True)

# --- CONEXÃO GOOGLE SHEETS E GERENCIAMENTO DE DADOS ---
SHEET_NAME = "AutoDesenvolvimento_DB" # Nome da planilha no Drive

def get_connection():
    """Conecta ao Google Sheets usando st.secrets"""
    # Escopo de permissões (leitura e escrita)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Carrega credenciais do bloco [gcp_service_account] nos secrets
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client

@st.cache_data(ttl=60) # Cache para não ler o Sheets em cada interação rápida
def load_data():
    """Lê os dados da planilha e retorna um DataFrame limpo"""
    cols = ["Data", "Estudo_h", "Organizacao", "Treino_min", "Bem_estar", 
            "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario", "Observacoes"]
    
    try:
        client = get_connection()
        # Assume que os dados estão na primeira aba (Sheet1)
        sheet = client.open(SHEET_NAME).sheet1 
        data = sheet.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=cols)
            
        df = pd.DataFrame(data)
        
        # Conversão e limpeza de tipos
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
        numeric_cols = ["Estudo_h", "Organizacao", "Treino_min", "Bem_estar", 
                        "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        return df
    except Exception as e:
        # Erro de conexão/permissão. AVISO VISÍVEL!
        st.error(f"Erro de Conexão com Google Sheets. Verifique: 1. Permissão do Editor; 2. Nome da Planilha. Erro: {e}")
        return pd.DataFrame(columns=cols)

def save_entry_google(data_dict):
    """Salva uma nova linha no Google Sheets"""
    try:
        client = get_connection()
        sheet = client.open(SHEET_NAME).sheet1
        
        # Cálculo do Score (back-end)
        nota_org = 10 if data_dict["Organizacao"] == 1 else 5
        score_auto = (data_dict["Bem_estar"] + data_dict["Nutricao"] + 
                      data_dict["Motivacao"] + data_dict["Relacoes"] + nota_org) * 2
        score_auto = min(score_auto, 100)
        
        # Prepara a linha (lista de valores na ordem correta das colunas)
        row = [
            str(data_dict["Data"]),
            data_dict["Estudo_h"],
            data_dict["Organizacao"],
            data_dict["Treino_min"],
            data_dict["Bem_estar"],
            data_dict["Sono_h"],
            data_dict["Nutricao"],
            data_dict["Motivacao"],
            data_dict["Relacoes"],
            score_auto,
            data_dict["Observacoes"]
        ]
        
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no Sheets: {e}")
        return False

# --- Aplicação Principal ---
def main():
    apply_custom_styles()
    
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 30px;'>
            🚀 Painel <span style='color: #4F8BF9;'>Cloud</span>
        </h1>
    """, unsafe_allow_html=True)

    # Carregamento de Dados na Session State
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    df = st.session_state.df

    tab1, tab2, tab3 = st.tabs(["📝 Registro Diário", "📊 Analytics & Insights", "📂 Gerenciar Dados"])

    # --- ABA 1: REGISTRO ---
    with tab1:
        col_center, _ = st.columns([0.8, 0.2]) 
        with col_center:
            st.markdown("#### Preencha os dados de hoje")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                
                with c1:
                    st.info("📌 Métricas Físicas")
                    data_input = st.date_input("Data", date.today())
                    estudo_h = st.number_input("Horas de Estudo", 0.0, 24.0, 1.0, 0.5)
                    treino_min = st.number_input("Treino (min)", 0, 300, 45, 15)
                    sono_h = st.number_input("Sono (h)", 0.0, 24.0, 7.0, 0.5)
                
                with c2:
                    st.success("🧠 Métricas Subjetivas (1-10)")
                    bem_estar = st.slider("Bem-estar Geral", 1, 10, 7)
                    nutricao = st.slider("Qualidade da Nutrição", 1, 10, 7)
                    motivacao = st.slider("Nível de Motivação", 1, 10, 7)
                    relacoes = st.slider("Qualidade das Relações", 1, 10, 7)
                    organizacao = st.toggle("Cumpri minha organização?", value=True)
                
                st.markdown("---")
                observacoes = st.text_area("Diário de Bordo / Observações", placeholder="O que aprendi hoje? O que posso melhorar?")
                
                submitted = st.form_submit_button("💾 Salvar na Nuvem")
                
                if submitted:
                    entry = {
                        "Data": data_input, "Estudo_h": estudo_h, 
                        "Organizacao": 1 if organizacao else 0,
                        "Treino_min": treino_min, "Bem_estar": bem_estar, 
                        "Sono_h": sono_h, "Nutricao": nutricao, 
                        "Motivacao": motivacao, "Relacoes": relacoes,
                        "Observacoes": observacoes
                    }
                    with st.spinner("Enviando para o Google Sheets..."):
                        if save_entry_google(entry):
                            st.cache_data.clear() # Limpa cache para ler os novos dados
                            st.session_state.df = load_data() 
                            st.toast("Registro salvo na nuvem com sucesso!", icon="✅")
                            st.rerun()

    # --- ABA 2: DASHBOARD ---
    with tab2:
        if not df.empty and len(df) > 0:
            last = df.iloc[-1]
            delta_html = "&nbsp;"
            delta_color = "var(--text-color)"
            
            if len(df) > 1:
                prev = df.iloc[-2]
                diff = last['Score_diario'] - prev['Score_diario']
                color_metric = "#00CC96" if diff >= 0 else "#EF553B"
                symbol = "▲" if diff >= 0 else "▼"
                delta_html = f"{symbol} {abs(diff):.0f} pts"
                delta_color = color_metric

            k1, k2, k3, k4 = st.columns(4)
            with k1: metric_card("Score do Dia", f"{last['Score_diario']:.0f}", delta_html, delta_color)
            with k2: metric_card("Total Estudo", f"{df['Estudo_h'].sum():.1f}h", "Horas Acumuladas")
            with k3: metric_card("Média Sono", f"{df['Sono_h'].mean():.1f}h", "Últimos 7 dias" if len(df)>7 else "Geral")
            with k4: metric_card("Frequência", f"{len(df)}", "Dias Registrados")

            st.markdown("---")
            
            g1, g2 = st.columns([0.6, 0.4])
            with g1:
                st.subheader("📈 Evolução Temporal")
                fig_line = px.line(df, x="Data", y=["Score_diario", "Bem_estar"], markers=True, color_discrete_sequence=["#4F8BF9", "#00CC96"])
                fig_line.update_layout(hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_line, use_container_width=True)
            with g2:
                st.subheader("🕸️ Radar de Equilíbrio")
                categories = ['Nutricao', 'Motivacao', 'Relacoes', 'Bem_estar', 'Sono_h']
                vals_radar = last[categories].copy()
                vals_radar['Sono_h'] = min(vals_radar['Sono_h'], 10)
                r_vals = vals_radar.values.tolist() + [vals_radar.values[0]]
                theta_vals = categories + [categories[0]]
                fig_radar = go.Figure(data=go.Scatterpolar(r=r_vals, theta=theta_vals, fill='toself', line_color='#4F8BF9'))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_radar, use_container_width=True)
            
            with st.expander("🔍 Análise Detalhada: O que impacta seu dia?"):
                try:
                    fig_scat = px.scatter(
                        df, x="Estudo_h", y="Score_diario", 
                        size="Bem_estar", color="Motivacao",
                        color_continuous_scale="Viridis",
                        title="Correlação: Estudo vs Score (Tamanho = Bem-estar)"
                    )
                    fig_scat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_scat, use_container_width=True)
                except:
                    st.warning("Dados insuficientes para correlação.")

        else:
            st.info("👈 Comece registrando seu primeiro dia na aba 'Registro Diário'.")

    # --- ABA 3: DADOS ---
    with tab3:
        st.markdown("### 📂 Visualizar Dados (Google Sheets)")
        st.info("Para editar dados ou garantir o backup, acesse sua planilha diretamente no Google Drive. A edição nesta tela não é salva de volta no Sheets.")
        st.dataframe(df, use_container_width=True)
        
        # Download (Apenas para backup manual)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Backup CSV Atual", csv, "meus_dados_cloud_backup.csv", "text/csv")

if __name__ == "__main__":
    main()
