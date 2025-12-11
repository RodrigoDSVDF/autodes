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
        
        /* Cor de fundo para dar destaque aos cards */
        .stApp {
            background-color: #0E1117;
        }

        /* Metric Cards com efeito Glassmorphism */
        .metric-card {
            background: rgba(38, 39, 48, 0.6);
            border: 1px solid rgba(250, 250, 250, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            text-align: left;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            border-color: #4F8BF9;
            box-shadow: 0 4px 20px rgba(79, 139, 249, 0.15);
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

        /* Customização dos Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        
        /* Botões */
        div.stButton > button {
            background-color: #4F8BF9;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s;
        }
        div.stButton > button:hover {
            background-color: #3b6Nc9;
            box-shadow: 0 2px 10px rgba(79, 139, 249, 0.4);
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
    cols = ["Data", "Estudo_h", "Organizacao", "Treino_min", "Bem_estar", 
            "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario", "Observacoes"]
    
    try:
        client = get_connection()
        sheet = client.open(SHEET_NAME).sheet1 
        data = sheet.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=cols)
            
        df = pd.DataFrame(data)
        
        # Limpeza e Tipagem
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
        
        numeric_cols = ["Estudo_h", "Organizacao", "Treino_min", "Bem_estar", 
                        "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario"]
        
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        # Ordenar por data para gráficos corretos
        df = df.sort_values(by="Data")
        
        return df
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return pd.DataFrame(columns=cols)

def save_entry_google(data_dict):
    try:
        client = get_connection()
        sheet = client.open(SHEET_NAME).sheet1
        
        # Cálculo do Score (Algoritmo ajustado)
        nota_org = 10 if data_dict["Organizacao"] == 1 else 0
        
        # O estudo tem peso alto? Se sim, podemos incluir no score
        # Fórmula: (Bem_estar + Nutricao + Motivacao + Relacoes + Org + (Estudo/2 limitado a 5)) / 55 * 100
        # Simplificado atual:
        soma_fatores = (data_dict["Bem_estar"] + data_dict["Nutricao"] + 
                        data_dict["Motivacao"] + data_dict["Relacoes"] + nota_org)
        
        # Bonus por estudo e treino (opcional, mantendo lógica simples por enquanto * 2)
        score_auto = soma_fatores * 2
        score_auto = min(score_auto, 100)
        
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
        st.error(f"Erro ao salvar: {e}")
        return False

# --- Aplicação Principal ---
def main():
    apply_custom_styles()
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Controles")
        st.markdown("---")
        periodo = st.selectbox("📅 Período de Análise", ["Últimos 7 dias", "Últimos 30 dias", "Todo o período"])
        st.markdown("---")
        st.caption("Auto-Desenvolvimento Pro v2.0")

    st.markdown("""
        <h2 style='margin-bottom: 20px;'>
            Painel de Performance <span style='color: #4F8BF9; font-size: 0.8em;'>Cloud</span>
        </h2>
    """, unsafe_allow_html=True)

    # Load Data
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    df_full = st.session_state.df

    # Filtragem de Data
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

    tab1, tab2, tab3 = st.tabs(["📊 Analytics & Radar", "📝 Novo Registro", "📂 Database"])

    # --- ABA 1: DASHBOARD ---
    with tab1:
        if not df.empty and len(df) > 0:
            last = df.iloc[-1]
            
            # Cálculo de Delta
            delta_html = "&nbsp;"
            delta_color = "#9CA3AF"
            
            if len(df) > 1:
                prev = df.iloc[-2]
                diff = last['Score_diario'] - prev['Score_diario']
                color_metric = "#00CC96" if diff >= 0 else "#EF553B"
                symbol = "+" if diff >= 0 else ""
                delta_html = f"{symbol}{diff:.0f} pts vs ontem"
                delta_color = color_metric

            # Linha de KPIs
            c1, c2, c3, c4 = st.columns(4)
            with c1: metric_card("Daily Score", f"{last['Score_diario']:.0f}", delta_html, delta_color)
            with c2: metric_card("Foco Total (Estudo)", f"{df['Estudo_h'].sum():.1f}h", "Acumulado no período", "#4F8BF9")
            with c3: metric_card("Consistência Treino", f"{df[df['Treino_min'] > 0].shape[0]} dias", "Dias ativos", "#FFA500")
            with c4: metric_card("Média Sono", f"{df['Sono_h'].mean():.1f}h", "Qualidade do descanso", "#AB63FA")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Layout Charts
            col_radar, col_line = st.columns([0.4, 0.6])
            
            with col_radar:
                st.markdown("##### 🕸️ Radar de Equilíbrio")
                # Prepara dados para o Radar
                # Incluindo ESTUDO e Normalizando visualmente horas para escala próxima de 10
                radar_cols = ['Estudo_h', 'Sono_h', 'Nutricao', 'Motivacao', 'Relacoes', 'Bem_estar']
                vals_radar = last[radar_cols].copy()
                
                # Ajuste visual: Se estudo > 10, vira 10 no gráfico para não estourar (mas o valor real é preservado nos dados)
                vals_radar['Estudo_h'] = min(vals_radar['Estudo_h'], 12) 
                vals_radar['Sono_h'] = min(vals_radar['Sono_h'], 12)
                
                # Fechar o ciclo do radar
                r_vals = vals_radar.values.tolist()
                r_vals.append(r_vals[0])
                theta_vals = radar_cols
                theta_vals.append(theta_vals[0])
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals,
                    theta=theta_vals,
                    fill='toself',
                    name='Hoje',
                    line_color='#4F8BF9',
                    fillcolor='rgba(79, 139, 249, 0.3)'
                ))
                
                # Adicionar média do período para comparação
                if len(df) > 1:
                    mean_vals = df[radar_cols].mean().tolist()
                    mean_vals.append(mean_vals[0])
                    fig_radar.add_trace(go.Scatterpolar(
                        r=mean_vals,
                        theta=theta_vals,
                        name='Média Período',
                        line_color='#FFFFFF',
                        opacity=0.4,
                        line_dash='dot'
                    ))

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 10], showticklabels=False, linecolor='rgba(255,255,255,0.1)'),
                        angularaxis=dict(tickfont=dict(size=11, color='#9CA3AF'))
                    ),
                    margin=dict(t=30, b=30, l=30, r=30),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", y=-0.1),
                    dragmode=False
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_line:
                st.markdown("##### 📈 Evolução de Performance")
                fig_line = px.area(df, x="Data", y="Score_diario", markers=True)
                fig_line.update_traces(line_color='#00CC96', fillcolor='rgba(0, 204, 150, 0.1)')
                
                # Adicionar linha de Estudo no eixo secundário ou junto? Vamos colocar Estudo como barra atrás
                fig_combo = go.Figure()
                fig_combo.add_trace(go.Bar(
                    x=df['Data'], y=df['Estudo_h'], name="Estudo (h)",
                    marker_color='rgba(79, 139, 249, 0.3)'
                ))
                fig_combo.add_trace(go.Scatter(
                    x=df['Data'], y=df['Score_diario'], name="Score Dia",
                    mode='lines+markers', line=dict(color='#00CC96', width=3)
                ))
                
                fig_combo.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    legend=dict(orientation="h", y=1.1, x=0),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig_combo, use_container_width=True)

        else:
            st.info("👈 Nenhum dado encontrado no período selecionado ou banco de dados vazio.")

    # --- ABA 2: REGISTRO ---
    with tab2:
        col_center, _ = st.columns([0.6, 0.4]) 
        with col_center:
            st.markdown("#### 📝 Registro Diário")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                
                with c1:
                    st.caption("Produtividade & Físico")
                    data_input = st.date_input("Data", date.today())
                    estudo_h = st.number_input("Horas de Estudo", 0.0, 24.0, 1.0, 0.5)
                    treino_min = st.number_input("Treino (min)", 0, 300, 45, 15)
                    sono_h = st.number_input("Sono (h)", 0.0, 24.0, 7.0, 0.5)
                
                with c2:
                    st.caption("Subjetivo (1-10)")
                    bem_estar = st.slider("Bem-estar Geral", 1, 10, 7)
                    nutricao = st.slider("Qualidade da Nutrição", 1, 10, 7)
                    motivacao = st.slider("Nível de Motivação", 1, 10, 7)
                    relacoes = st.slider("Relacionamentos", 1, 10, 7)
                    st.write("")
                    organizacao = st.toggle("✅ Cumpri o planejado?", value=True)
                
                st.markdown("---")
                observacoes = st.text_area("Diário de Bordo", placeholder="Insights, vitórias ou aprendizados do dia...")
                
                submitted = st.form_submit_button("Salvar Registro")
                
                if submitted:
                    entry = {
                        "Data": data_input, "Estudo_h": estudo_h, 
                        "Organizacao": 1 if organizacao else 0,
                        "Treino_min": treino_min, "Bem_estar": bem_estar, 
                        "Sono_h": sono_h, "Nutricao": nutricao, 
                        "Motivacao": motivacao, "Relacoes": relacoes,
                        "Observacoes": observacoes
                    }
                    with st.spinner("Sincronizando..."):
                        if save_entry_google(entry):
                            st.cache_data.clear()
                            st.session_state.df = load_data() 
                            st.toast("Dados salvos com sucesso!", icon="🚀")
                            # Pequeno hack para atualizar a página suavemente se necessário
                            # st.rerun()

    # --- ABA 3: DADOS ---
    with tab3:
        st.markdown("### 🗄️ Banco de Dados")
        st.dataframe(
            df_full.sort_values(by="Data", ascending=False), 
            use_container_width=True,
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Score_diario": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100)
            }
        )
        
        csv = df_full.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar CSV", csv, "backup_autodesenvolvimento.csv", "text/csv")

if __name__ == "__main__":
    main()
