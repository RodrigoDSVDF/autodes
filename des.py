import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta
import os
import json
from io import BytesIO

# Tentar importar módulos do Google Sheets (opcional)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    st.warning("Módulos do Google Sheets não disponíveis. Usando armazenamento local.")

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Nexus | Auto-Desenvolvimento",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Profissional Aprimorado ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Base */
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        
        /* Cor de fundo */
        .stApp { 
            background: linear-gradient(135deg, #0E1117 0%, #1a1d25 100%);
            min-height: 100vh;
        }

        /* Metric Cards */
        .metric-card {
            background: rgba(38, 39, 48, 0.7);
            border: 1px solid rgba(250, 250, 250, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            text-align: left;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        .metric-card:hover {
            border-color: #4F8BF9;
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(79, 139, 249, 0.2);
        }
        .metric-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
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
            background: linear-gradient(135deg, #4F8BF9 0%, #3B82F6 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            height: 3em;
            width: 100%;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(79, 139, 249, 0.4);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(38, 39, 48, 0.5);
            padding: 8px;
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px !important;
            padding: 10px 20px !important;
        }
        
        /* Animações */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .metric-card, .plotly-graph-div {
            animation: fadeIn 0.5s ease-out;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Componentes Visuais ---
def metric_card(label, value, subtext=None, color="#FFFFFF", gradient=False):
    gradient_class = "metric-gradient" if gradient else ""
    st.markdown(f"""
    <div class="metric-card {gradient_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta" style="color: {color}; border-left: 3px solid {color};">{subtext if subtext else '&nbsp;'}</div>
    </div>
    """, unsafe_allow_html=True)

# --- SISTEMA DE ARMAZENAMENTO (Google Sheets ou Local) ---
SHEET_NAME = "AutoDesenvolvimento_DB"
LOCAL_DATA_FILE = "data_nexus.json"

# Verificar se existe arquivo de credenciais
def google_sheets_available():
    """Verifica se as credenciais do Google Sheets estão disponíveis"""
    if not GOOGLE_SHEETS_AVAILABLE:
        return False
    
    try:
        # Verificar se existe secrets.toml
        if 'gcp_service_account' in st.secrets:
            return True
    except:
        pass
    
    # Verificar se existe arquivo JSON de credenciais
    if os.path.exists("credentials.json"):
        return True
    
    return False

# --- CONEXÃO GOOGLE SHEETS (se disponível) ---
def get_connection():
    """Tenta conectar ao Google Sheets"""
    if not GOOGLE_SHEETS_AVAILABLE:
        raise ImportError("Módulos do Google Sheets não disponíveis")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Primeiro tenta usar secrets.toml
        if 'gcp_service_account' in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        # Se não, tenta arquivo JSON
        elif os.path.exists("credentials.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        else:
            raise FileNotFoundError("Nenhuma credencial encontrada")
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro na conexão Google Sheets: {e}")
        raise

# --- ARMAZENAMENTO LOCAL (fallback) ---
def load_local_data():
    """Carrega dados do arquivo local"""
    cols = ["Data", "Estudo_min", "Organizacao", "Treino_min", "Bem_estar", 
            "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario", "Observacoes"]
    
    try:
        if os.path.exists(LOCAL_DATA_FILE):
            df = pd.read_json(LOCAL_DATA_FILE, orient='records')
            
            # Garantir que todas as colunas existam
            for col in cols:
                if col not in df.columns:
                    df[col] = 0 if col != 'Observacoes' else ''
            
            df['Data'] = pd.to_datetime(df['Data']).dt.date
            return df.sort_values(by="Data")
        else:
            return pd.DataFrame(columns=cols)
    except Exception as e:
        st.error(f"Erro ao carregar dados locais: {e}")
        return pd.DataFrame(columns=cols)

def save_local_data(df):
    """Salva dados no arquivo local"""
    try:
        df.to_json(LOCAL_DATA_FILE, orient='records')
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados locais: {e}")
        return False

def add_local_entry(data_dict):
    """Adiciona um novo registro ao arquivo local"""
    try:
        # Calcular score
        nota_org = 10 if data_dict["Organizacao"] == 1 else 0
        soma_fatores = (data_dict["Bem_estar"] + data_dict["Nutricao"] + 
                        data_dict["Motivacao"] + data_dict["Relacoes"] + nota_org)
        score_auto = min(soma_fatores * 2, 100)
        
        # Criar novo registro
        new_entry = {
            "Data": str(data_dict["Data"]),
            "Estudo_min": data_dict["Estudo_min"],
            "Organizacao": data_dict["Organizacao"],
            "Treino_min": data_dict["Treino_min"],
            "Bem_estar": data_dict["Bem_estar"],
            "Sono_h": data_dict["Sono_h"],
            "Nutricao": data_dict["Nutricao"],
            "Motivacao": data_dict["Motivacao"],
            "Relacoes": data_dict["Relacoes"],
            "Score_diario": score_auto,
            "Observacoes": data_dict["Observacoes"]
        }
        
        # Carregar dados existentes
        df = load_local_data()
        new_df = pd.DataFrame([new_entry])
        df = pd.concat([df, new_df], ignore_index=True)
        
        # Salvar
        return save_local_data(df)
    except Exception as e:
        st.error(f"Erro ao adicionar registro local: {e}")
        return False

# --- Função principal de carregamento de dados ---
@st.cache_data(ttl=60)
def load_data():
    """Carrega dados do Google Sheets (se disponível) ou localmente"""
    
    # Verificar se Google Sheets está disponível
    if google_sheets_available():
        try:
            cols = ["Data", "Estudo_min", "Organizacao", "Treino_min", "Bem_estar", 
                    "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario", "Observacoes"]
            
            client = get_connection()
            sheet = client.open(SHEET_NAME).sheet1 
            data = sheet.get_all_records()
            
            if not data:
                return pd.DataFrame(columns=cols)
                
            df = pd.DataFrame(data)
            
            # Ajuste de compatibilidade
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
            st.success("✅ Conectado ao Google Sheets")
            return df
        except Exception as e:
            st.warning(f"⚠️ Google Sheets não disponível: {e}. Usando armazenamento local.")
            return load_local_data()
    else:
        st.info("📁 Usando armazenamento local (Google Sheets não configurado)")
        return load_local_data()

def save_entry(data_dict):
    """Salva entrada no Google Sheets (se disponível) ou localmente"""
    if google_sheets_available():
        try:
            # Tentar salvar no Google Sheets
            client = get_connection()
            sheet = client.open(SHEET_NAME).sheet1
            
            nota_org = 10 if data_dict["Organizacao"] == 1 else 0
            soma_fatores = (data_dict["Bem_estar"] + data_dict["Nutricao"] + 
                            data_dict["Motivacao"] + data_dict["Relacoes"] + nota_org)
            score_auto = min(soma_fatores * 2, 100)
            
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
            st.success("✅ Salvo no Google Sheets")
            return True
        except Exception as e:
            st.warning(f"⚠️ Erro ao salvar no Google Sheets: {e}. Salvando localmente.")
            return add_local_entry(data_dict)
    else:
        # Salvar localmente
        return add_local_entry(data_dict)

# --- Funções de Análise Avançada ---
def calcular_metricas_avancadas(df):
    """Calcula métricas avançadas"""
    if len(df) == 0:
        return df, None
    
    df_analise = df.copy()
    
    # Série temporal de 7 dias
    df_analise['Media_Movel_7'] = df_analise['Score_diario'].rolling(7, min_periods=1).mean()
    
    # Identificar padrões
    df_analise['Tendencia_Score'] = df_analise['Score_diario'].diff()
    df_analise['Dia_Semana'] = pd.to_datetime(df_analise['Data']).dt.day_name('pt_BR')
    
    # Correlações
    metricas_correlacao = ['Estudo_min', 'Sono_h', 'Treino_min', 'Bem_estar', 
                          'Nutricao', 'Motivacao', 'Relacoes', 'Score_diario']
    
    cols_existentes = [col for col in metricas_correlacao if col in df_analise.columns]
    if len(cols_existentes) > 1:
        matriz_correlacao = df_analise[cols_existentes].corr()
    else:
        matriz_correlacao = None
    
    return df_analise, matriz_correlacao

def calcular_pontos_recompensa(df):
    """Sistema de gamificação"""
    pontos = 0
    conquistas = []
    
    if len(df) >= 7:
        ultimos_7 = df.tail(7)
        dias_consecutivos = (ultimos_7['Score_diario'] >= 70).sum()
        
        if dias_consecutivos >= 7:
            pontos += 100
            conquistas.append("🏆 7 dias consecutivos com score ≥70")
    
    total_estudo = df['Estudo_min'].sum()
    if total_estudo > 10000:
        pontos += 50
        conquistas.append("📚 +10000 minutos de estudo")
    
    return pontos, conquistas

def previsao_tendencia(df):
    """Previsão simples"""
    if len(df) >= 5:
        ultimos_scores = df['Score_diario'].tail(5).values
        x = np.arange(len(ultimos_scores))
        try:
            z = np.polyfit(x, ultimos_scores, 1)
            tendencia = z[0]
            
            if tendencia > 2:
                return "📈 Tendência positiva forte", "#00CC96"
            elif tendencia > 0.5:
                return "↗️ Tendência positiva leve", "#7FDBFF"
            elif tendencia < -2:
                return "📉 Tendência negativa forte", "#EF553B"
            elif tendencia < -0.5:
                return "↘️ Tendência negativa leve", "#FFA500"
            else:
                return "➡️ Tendência estável", "#9CA3AF"
        except:
            return "⏳ Coletando dados...", "#9CA3AF"
    return "⏳ Coletando dados...", "#9CA3AF"

# --- Aplicação Principal ---
def main():
    apply_custom_styles()
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Configurações")
        
        periodo = st.selectbox(
            "📅 Período",
            ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todo o período"]
        )
        
        # Verificar conexão
        if google_sheets_available():
            st.success("✅ Conectado ao Google Sheets")
        else:
            st.info("📁 Usando armazenamento local")
        
        # Gamificação
        if 'df' not in st.session_state:
            st.session_state.df = load_data()
        
        pontos, conquistas = calcular_pontos_recompensa(st.session_state.df)
        st.metric("🏆 Pontos", pontos)
        
        if conquistas:
            with st.expander("Conquistas"):
                for c in conquistas:
                    st.success(c)
        
        st.markdown("---")
        st.caption(f"📊 {len(st.session_state.df)} registros")
        st.caption("Nexus Tracker v3.0")

    # Header
    st.markdown("# 🚀 Painel de Evolução Pessoal")
    
    # Carregar dados
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    
    df_full = st.session_state.df
    
    # Filtrar por período
    if not df_full.empty:
        hoje = date.today()
        if periodo == "Últimos 7 dias":
            cutoff = hoje - timedelta(days=7)
            df = df_full[df_full['Data'] > cutoff]
        elif periodo == "Últimos 30 dias":
            cutoff = hoje - timedelta(days=30)
            df = df_full[df_full['Data'] > cutoff]
        elif periodo == "Últimos 90 dias":
            cutoff = hoje - timedelta(days=90)
            df = df_full[df_full['Data'] > cutoff]
        else:
            df = df_full
    else:
        df = df_full
    
    # Calcular métricas avançadas
    df_analise, matriz_correlacao = calcular_metricas_avancadas(df)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Novo Registro", "📈 Relatórios"])

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
            with c1: 
                metric_card("Score Hoje", f"{last['Score_diario']:.0f}", delta_html, delta_color, gradient=True)
            with c2: 
                metric_card("Total Estudo", f"{horas_estudo:.1f}h", f"{total_estudo_min} min", "#4F8BF9")
            with c3: 
                metric_card("Treino Físico", f"{df['Treino_min'].sum()} min", "Acumulado", "#FFA500")
            with c4: 
                metric_card("Média Sono", f"{df['Sono_h'].mean():.1f}h", "Qualidade", "#AB63FA")

            # Gráficos
            col_radar, col_line = st.columns([0.5, 0.5])
            
            with col_radar:
                st.markdown("##### 🕸️ Radar de Equilíbrio")
                
                radar_cols = ['Estudo_min', 'Treino_min', 'Sono_h', 'Nutricao', 'Motivacao', 'Relacoes', 'Bem_estar']
                vals_radar = last[radar_cols].copy()
                
                # Normalização
                vals_radar['Estudo_min'] = (vals_radar['Estudo_min'] / 1440) * 10
                vals_radar['Treino_min'] = min((vals_radar['Treino_min'] / 120) * 10, 10)
                vals_radar['Sono_h'] = min(vals_radar['Sono_h'], 10)
                
                r_vals = vals_radar.values.tolist()
                r_vals.append(r_vals[0])
                
                theta_vals = ['Estudo', 'Treino', 'Sono', 'Nutrição', 'Motivação', 'Relações', 'Bem-estar']
                theta_vals.append(theta_vals[0])
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals, theta=theta_vals, fill='toself', name='Hoje',
                    line_color='#4F8BF9', fillcolor='rgba(79, 139, 249, 0.3)'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 10], showticklabels=False, 
                                      linecolor='rgba(255,255,255,0.1)'),
                        angularaxis=dict(tickfont=dict(size=11, color='#9CA3AF'))
                    ),
                    margin=dict(t=30, b=30, l=40, r=40),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    dragmode=False
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_line:
                st.markdown("##### 📈 Evolução: Estudo vs Score")
                
                fig_combo = go.Figure()
                fig_combo.add_trace(go.Bar(
                    x=df['Data'], y=df['Estudo_min'], name="Estudo (min)",
                    marker_color='rgba(79, 139, 249, 0.4)', yaxis='y'
                ))
                fig_combo.add_trace(go.Scatter(
                    x=df['Data'], y=df['Score_diario'], name="Score do Dia",
                    mode='lines+markers', 
                    line=dict(color='#FFA500', width=3),
                    yaxis='y2'
                ))
                
                fig_combo.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(title="Minutos de Estudo", showgrid=True, 
                             gridcolor='rgba(255,255,255,0.05)'),
                    yaxis2=dict(title="Score (0-100)", overlaying='y', side='right', 
                               showgrid=False, range=[0, 110]),
                    legend=dict(orientation="h", y=1.1, x=0),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig_combo, use_container_width=True)
            
            # Tendência
            tendencia, cor = previsao_tendencia(df)
            st.markdown(f"**📊 Tendência**: <span style='color:{cor}'>{tendencia}</span>", 
                       unsafe_allow_html=True)
            
        else:
            st.info("👈 Nenhum dado encontrado. Adicione seu primeiro registro!")

    # --- ABA 2: REGISTRO ---
    with tab2:
        st.markdown("#### 📝 Registro Diário")
        
        with st.form("entry_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            
            with c1:
                st.info("🎯 Métricas Objetivas")
                data_input = st.date_input("Data", date.today())
                estudo_min = st.number_input("⏱️ Estudo (minutos)", 0, 1440, 60, step=10)
                treino_min = st.number_input("🏋️ Treino (minutos)", 0, 300, 45, step=5)
                sono_h = st.number_input("💤 Sono (horas)", 0.0, 24.0, 7.0, 0.5)
            
            with c2:
                st.success("🧠 Métricas Subjetivas (1-10)")
                bem_estar = st.slider("Bem-estar Geral", 1, 10, 7)
                nutricao = st.slider("Qualidade da Nutrição", 1, 10, 7)
                motivacao = st.slider("Nível de Motivação", 1, 10, 7)
                relacoes = st.slider("Relacionamentos", 1, 10, 7)
                organizacao = st.toggle("✅ Cumpri a organização?", value=True)
            
            observacoes = st.text_area("📖 Diário de Bordo", 
                                     placeholder="Insights do dia...",
                                     height=100)
            
            submitted = st.form_submit_button("💾 Salvar Registro", type="primary")
            
            if submitted:
                entry = {
                    "Data": data_input, "Estudo_min": estudo_min, 
                    "Organizacao": 1 if organizacao else 0,
                    "Treino_min": treino_min, "Bem_estar": bem_estar, 
                    "Sono_h": sono_h, "Nutricao": nutricao, 
                    "Motivacao": motivacao, "Relacoes": relacoes,
                    "Observacoes": observacoes
                }
                
                with st.spinner("Salvando..."):
                    if save_entry(entry):
                        st.cache_data.clear()
                        st.session_state.df = load_data()
                        st.toast("✅ Registro salvo!", icon="✅")
                        st.rerun()

    # --- ABA 3: RELATÓRIOS ---
    with tab3:
        st.markdown("### 📈 Relatórios")
        
        if len(df_full) > 0:
            # Dados completos
            st.markdown("#### 📊 Dados Completos")
            st.dataframe(
                df_full.sort_values(by="Data", ascending=False),
                use_container_width=True,
                height=300
            )
            
            # Botões de exportação
            col_csv, col_json = st.columns(2)
            
            with col_csv:
                csv = df_full.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Baixar CSV",
                    csv,
                    "nexus_dados.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col_json:
                json_data = df_full.to_json(orient='records', indent=2)
                st.download_button(
                    "📊 Baixar JSON",
                    json_data,
                    "nexus_dados.json",
                    "application/json",
                    use_container_width=True
                )
            
            # Estatísticas
            st.markdown("#### 📈 Estatísticas")
            
            if len(df) > 0:
                col_stats1, col_stats2 = st.columns(2)
                
                with col_stats1:
                    st.metric("Média Score", f"{df['Score_diario'].mean():.1f}")
                    st.metric("Média Estudo", f"{df['Estudo_min'].mean()/60:.1f}h")
                    st.metric("Média Sono", f"{df['Sono_h'].mean():.1f}h")
                
                with col_stats2:
                    st.metric("Melhor Score", f"{df['Score_diario'].max():.0f}")
                    st.metric("Total Estudo", f"{df['Estudo_min'].sum()/60:.1f}h")
                    st.metric("Dias Org.", f"{df['Organizacao'].sum()}")
            
            # Configuração Google Sheets
            st.markdown("---")
            st.markdown("#### ⚙️ Configuração do Google Sheets")
            
            with st.expander("Como configurar Google Sheets"):
                st.markdown("""
                1. **Crie um projeto no Google Cloud Console**
                2. **Ative as APIs**: Google Sheets e Google Drive
                3. **Crie uma Service Account**
                4. **Baixe o JSON de credenciais**
                5. **Crie o arquivo `.streamlit/secrets.toml`**:
                
                ```toml
                [gcp_service_account]
                type = "service_account"
                project_id = "seu-project-id"
                private_key_id = "sua-chave-privada"
                private_key = "-----BEGIN PRIVATE KEY-----\\nsua-chave\\n-----END PRIVATE KEY-----\\n"
                client_email = "seu-email@projeto.iam.gserviceaccount.com"
                client_id = "seu-client-id"
                auth_uri = "https://accounts.google.com/o/oauth2/auth"
                token_uri = "https://oauth2.googleapis.com/token"
                auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
                client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/seu-email%40projeto.iam.gserviceaccount.com"
                universe_domain = "googleapis.com"
                ```
                
                6. **Compartilhe a planilha** com o email da service account
                """)
                
                # Botão para testar conexão
                if st.button("🔗 Testar Conexão Google Sheets"):
                    if google_sheets_available():
                        try:
                            test_df = load_data()
                            st.success(f"✅ Conectado! {len(test_df)} registros carregados")
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
                    else:
                        st.warning("⚠️ Google Sheets não configurado")
        
        else:
            st.info("Adicione registros para ver relatórios")

if __name__ == "__main__":
    main()
