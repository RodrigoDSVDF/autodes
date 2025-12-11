import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Nexus | Auto-Desenvolvimento",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Profissional (Glassmorphism & Clean UI) ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Base */
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        
        /* Cor de fundo */
        .stApp { background-color: #0E1117; }

        /* Metric Cards */
        .metric-card {
            background: rgba(38, 39, 48, 0.6);
            border: 1px solid rgba(250, 250, 250, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            text-align: left;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: #4F8BF9;
            transform: translateY(-2px);
        }
        .metric-label {
            color: #9CA3AF;
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 5px;
        }
        .metric-value {
            color: #FFFFFF;
            font-size: 1.8rem;
            font-weight: 700;
        }
        .metric-delta {
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 8px;
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(255,255,255,0.05);
        }

        /* Botões */
        div.stButton > button {
            background-color: #4F8BF9;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            height: 3em;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Componentes Visuais ---
def metric_card(label, value, subtext=None, color="var(--text-color)"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta" style="color: {color}; border-left: 3px solid {color};">{subtext if subtext else '&nbsp;'}</div>
    </div>
    """, unsafe_allow_html=True)

# --- CONEXÃO GOOGLE SHEETS ---
SHEET_NAME = "AutoDesenvolvimento_DB" 

def get_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client

@st.cache_data(ttl=60)
def load_data():
    cols = ["Data", "Estudo_min", "Organizacao", "Treino_min", "Bem_estar", 
            "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario", "Observacoes"]
    
    try:
        client = get_connection()
        sheet = client.open(SHEET_NAME).sheet1 
        data = sheet.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=cols)
            
        df = pd.DataFrame(data)
        
        # Ajuste de compatibilidade para nomes de colunas antigos
        if "Estudo_h" in df.columns:
            df.rename(columns={"Estudo_h": "Estudo_min"}, inplace=True)

        # Limpeza e Tipagem
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
        
        numeric_cols = ["Estudo_min", "Organizacao", "Treino_min", "Bem_estar", 
                        "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario"]
        
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        df = df.sort_values(by="Data")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=cols)

def save_entry_google(data_dict):
    try:
        client = get_connection()
        sheet = client.open(SHEET_NAME).sheet1
        
        nota_org = 10 if data_dict["Organizacao"] == 1 else 0
        
        # Cálculo simplificado do score (0 a 100)
        soma_fatores = (data_dict["Bem_estar"] + data_dict["Nutricao"] + 
                        data_dict["Motivacao"] + data_dict["Relacoes"] + nota_org)
        
        score_auto = soma_fatores * 2
        score_auto = min(score_auto, 100)
        
        row = [
            str(data_dict["Data"]),
            data_dict["Estudo_min"], 
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
        st.error(f"Erro ao salvar: {e}")
        return False

# --- Aplicação Principal ---
def main():
    apply_custom_styles()
    
    with st.sidebar:
        st.title("⚙️ Filtros")
        periodo = st.selectbox("📅 Período", ["Últimos 7 dias", "Últimos 30 dias", "Todo o período"])
        st.caption("Nexus Tracker v2.2")

    st.markdown("## 🚀 Painel de Evolução")

    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    df_full = st.session_state.df

    if not df_full.empty:
        if periodo == "Últimos 7 dias":
            cutoff = date.today() - timedelta(days=7)
            df = df_full[df_full['Data'] > cutoff]
        elif periodo == "Últimos 30 dias":
            cutoff = date.today() - timedelta(days=30)
            df = df_full[df_full['Data'] > cutoff]
        else:
            df = df_full
    else:
        df = df_full

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Novo Registro", "📂 Dados"])

    # --- ABA 1: DASHBOARD ---
    with tab1:
        if not df.empty and len(df) > 0:
            last = df.iloc[-1]
            
            # Score Delta
            delta_html = "&nbsp;"
            delta_color = "#9CA3AF"
            if len(df) > 1:
                prev = df.iloc[-2]
                diff = last['Score_diario'] - prev['Score_diario']
                color_metric = "#00CC96" if diff >= 0 else "#EF553B"
                symbol = "+" if diff >= 0 else ""
                delta_html = f"{symbol}{diff:.0f} pts"
                delta_color = color_metric

            # KPIs
            total_estudo_min = df['Estudo_min'].sum()
            horas_estudo = total_estudo_min / 60
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: metric_card("Score Hoje", f"{last['Score_diario']:.0f}", delta_html, delta_color)
            with c2: metric_card("Total Estudo", f"{horas_estudo:.1f}h", f"{total_estudo_min} min totais", "#4F8BF9")
            with c3: metric_card("Treino Físico", f"{df['Treino_min'].sum()} min", "Acumulado Período", "#FFA500")
            with c4: metric_card("Média Sono", f"{df['Sono_h'].mean():.1f}h", "Qualidade do descanso", "#AB63FA")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Gráficos
            col_radar, col_line = st.columns([0.5, 0.5])
            
            with col_radar:
                st.markdown("##### 🕸️ Radar de Equilíbrio")
                st.caption("A escala de estudo considera o total de minutos do dia (1440 min).")
                
                # Definir colunas para o Radar (Incluindo TREINO e ESTUDO)
                radar_cols = ['Estudo_min', 'Treino_min', 'Sono_h', 'Nutricao', 'Motivacao', 'Relacoes', 'Bem_estar']
                vals_radar = last[radar_cols].copy()
                
                # --- Lógica de Escala (Normalização 0-10) ---
                
                # 1. Estudo: Escala baseada no dia inteiro (1440 min = nota 10)
                # Ex: 4h de estudo (240 min) -> (240/1440)*10 = 1.66
                vals_radar['Estudo_min'] = (vals_radar['Estudo_min'] / 1440) * 10
                
                # 2. Treino: Escala onde 2 horas (120 min) = nota 10 (para equilíbrio visual)
                vals_radar['Treino_min'] = min((vals_radar['Treino_min'] / 120) * 10, 10)
                
                # 3. Sono: Escala onde 10 horas = nota 10.
                vals_radar['Sono_h'] = min(vals_radar['Sono_h'], 10)
                
                # Plotagem
                r_vals = vals_radar.values.tolist()
                r_vals.append(r_vals[0]) # Fechar o ciclo
                
                theta_vals = ['Estudo (Dia)', 'Treino', 'Sono', 'Nutrição', 'Motivação', 'Relações', 'Bem-estar']
                theta_vals.append(theta_vals[0])
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals, theta=theta_vals, fill='toself', name='Hoje',
                    line_color='#4F8BF9', fillcolor='rgba(79, 139, 249, 0.3)'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 10], showticklabels=False, linecolor='rgba(255,255,255,0.1)'),
                        angularaxis=dict(tickfont=dict(size=11, color='#9CA3AF'))
                    ),
                    margin=dict(t=30, b=30, l=40, r=40),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    dragmode=False
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_line:
                st.markdown("##### 📈 Evolução de Produtividade")
                
                fig_combo = go.Figure()
                
                # Barra de Estudo
                fig_combo.add_trace(go.Bar(
                    x=df['Data'], y=df['Estudo_min'], name="Estudo (min)",
                    marker_color='rgba(79, 139, 249, 0.4)', yaxis='y'
                ))
                
                # Linha de Treino (para comparar esforço físico x mental)
                fig_combo.add_trace(go.Scatter(
                    x=df['Data'], y=df['Treino_min'], name="Treino (min)",
                    mode='lines', line=dict(color='#FFA500', width=2, dash='dot'),
                    yaxis='y'
                ))
                
                fig_combo.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(title="Minutos", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    legend=dict(orientation="h", y=1.1, x=0),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig_combo, use_container_width=True)

        else:
            st.info("👈 Nenhum dado encontrado. Inicie seus registros!")

    # --- ABA 2: REGISTRO ---
    with tab2:
        col_center, _ = st.columns([0.6, 0.4]) 
        with col_center:
            st.markdown("#### 📝 Registro Diário")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                
                with c1:
                    st.info("🎯 Métricas Objetivas")
                    data_input = st.date_input("Data", date.today())
                    estudo_min = st.number_input("⏱️ Estudo (minutos brutos)", min_value=0, max_value=1440, value=60, step=10)
                    treino_min = st.number_input("🏋️ Treino (minutos)", 0, 300, 45, step=5)
                    sono_h = st.number_input("💤 Sono (horas)", 0.0, 24.0, 7.0, 0.5)
                
                with c2:
                    st.success("🧠 Métricas Subjetivas (1-10)")
                    bem_estar = st.slider("Bem-estar Geral", 1, 10, 7)
                    nutricao = st.slider("Qualidade da Nutrição", 1, 10, 7)
                    motivacao = st.slider("Nível de Motivação", 1, 10, 7)
                    relacoes = st.slider("Relacionamentos", 1, 10, 7)
                    st.write("")
                    organizacao = st.toggle("✅ Cumpri a organização?", value=True)
                
                st.markdown("---")
                observacoes = st.text_area("Diário de Bordo", placeholder="Insights do dia...")
                
                submitted = st.form_submit_button("💾 Salvar Registro")
                
                if submitted:
                    entry = {
                        "Data": data_input, "Estudo_min": estudo_min, 
                        "Organizacao": 1 if organizacao else 0,
                        "Treino_min": treino_min, "Bem_estar": bem_estar, 
                        "Sono_h": sono_h, "Nutricao": nutricao, 
                        "Motivacao": motivacao, "Relacoes": relacoes,
                        "Observacoes": observacoes
                    }
                    with st.spinner("Processando..."):
                        if save_entry_google(entry):
                            st.cache_data.clear()
                            st.session_state.df = load_data() 
                            st.toast("Registro salvo!", icon="✅")

    # --- ABA 3: DADOS ---
    with tab3:
        st.markdown("### 🗄️ Base de Dados")
        st.dataframe(
            df_full.sort_values(by="Data", ascending=False), 
            use_container_width=True
        )
        csv = df_full.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV", csv, "nexus_backup.csv", "text/csv")

if __name__ == "__main__":
    main()
