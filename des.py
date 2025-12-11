import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(
    page_title="Nexus | Alta Performance",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Profissional (Glassmorphism & XP Bar) ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Base & Background */
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { 
            background: linear-gradient(135deg, #0E1117 0%, #161920 100%);
        }

        /* Cards Metric Glassmorphism */
        .metric-card {
            background: rgba(38, 39, 48, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 24px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            border-color: #4F8BF9;
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        
        /* Tipografia dos Cards */
        .metric-label {
            color: #9CA3AF;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        .metric-value {
            color: #FFFFFF;
            font-size: 2rem;
            font-weight: 700;
        }
        .metric-delta {
            font-size: 0.85rem;
            font-weight: 500;
            margin-top: 8px;
            display: inline-flex;
            align-items: center;
            padding: 4px 8px;
            border-radius: 6px;
            background: rgba(255,255,255,0.05);
        }

        /* Botões Estilizados */
        div.stButton > button {
            background: linear-gradient(90deg, #4F8BF9 0%, #3B82F6 100%);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            opacity: 0.9;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        /* Tabs Customizadas */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(255,255,255,0.02);
            padding: 8px;
            border-radius: 12px;
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px !important;
            border: none !important;
            color: #9CA3AF;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(79, 139, 249, 0.1) !important;
            color: #4F8BF9 !important;
            font-weight: 600;
        }
        
        /* XP Bar Container */
        .xp-container {
            background-color: rgba(255,255,255,0.05);
            border-radius: 10px;
            height: 8px;
            width: 100%;
            margin-top: 5px;
            overflow: hidden;
        }
        .xp-fill {
            height: 100%;
            border-radius: 10px;
            background: linear-gradient(90deg, #4F8BF9, #00CC96);
            transition: width 1s ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Componente Visual: Card de Métrica ---
def metric_card(label, value, subtext=None, color="#FFFFFF"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta" style="color: {color}; border-left: 2px solid {color};">
            {subtext if subtext else '&nbsp;'}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Conexão Google Sheets ---
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
        
        # Normalização de Nomes de Coluna (Compatibilidade)
        if "Estudo_h" in df.columns:
            df.rename(columns={"Estudo_h": "Estudo_min"}, inplace=True)

        # Tipagem e Limpeza
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
        numeric_cols = ["Estudo_min", "Organizacao", "Treino_min", "Bem_estar", 
                        "Sono_h", "Nutricao", "Motivacao", "Relacoes", "Score_diario"]
        
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        return df.sort_values(by="Data")
    except Exception as e:
        st.error(f"Erro de conexão com Database: {e}")
        return pd.DataFrame(columns=cols)

def save_entry_google(data_dict):
    try:
        client = get_connection()
        sheet = client.open(SHEET_NAME).sheet1
        
        nota_org = 10 if data_dict["Organizacao"] == 1 else 0
        
        # Algoritmo de Score (0-100)
        soma_fatores = (data_dict["Bem_estar"] + data_dict["Nutricao"] + 
                        data_dict["Motivacao"] + data_dict["Relacoes"] + nota_org)
        score_auto = min(soma_fatores * 2, 100)
        
        row = [
            str(data_dict["Data"]), data_dict["Estudo_min"], data_dict["Organizacao"],
            data_dict["Treino_min"], data_dict["Bem_estar"], data_dict["Sono_h"],
            data_dict["Nutricao"], data_dict["Motivacao"], data_dict["Relacoes"],
            score_auto, data_dict["Observacoes"]
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- Lógica Avançada (Gamificação e HTML) ---

def calcular_xp_nivel(df):
    """Calcula XP e Nível baseado em consistência e volume"""
    if df.empty: return 0, 1, 0, []
    
    xp = 0
    conquistas = []
    
    # XP por volume
    xp += int(df['Estudo_min'].sum() / 30)  # 1 XP a cada 30min estudo
    xp += int(df['Treino_min'].sum() / 30)  # 1 XP a cada 30min treino
    xp += int(df['Score_diario'].sum() / 10) # XP pelo score acumulado
    
    # Conquistas (Badges)
    if len(df) >= 7:
        if (df['Score_diario'].tail(7) > 70).all():
            xp += 100
            conquistas.append("🔥 Streak Semanal (+70 score)")
    
    if df['Estudo_min'].sum() > 6000: # 100 horas
        xp += 500
        conquistas.append("🧙‍♂️ Mago dos Estudos (100h)")

    # Lógica de Nível RPG
    xp_base_nivel = 500
    nivel = int(xp / xp_base_nivel) + 1
    xp_neste_nivel = xp % xp_base_nivel
    progresso_pct = (xp_neste_nivel / xp_base_nivel) * 100
    
    return xp, nivel, progresso_pct, conquistas

def plot_heatmap_atividade(df):
    """Gera Heatmap Estilo GitHub (Score)"""
    if len(df) < 1: return None
    
    df_heat = df.copy()
    df_heat['Data'] = pd.to_datetime(df_heat['Data'])
    # Normalizar para pegar dia da semana e semana do ano
    df_heat['Semana'] = df_heat['Data'].dt.isocalendar().week
    df_heat['Dia'] = df_heat['Data'].dt.weekday # 0=Seg, 6=Dom
    
    # Pivotar dados
    try:
        heatmap_data = df_heat.pivot_table(index='Dia', columns='Semana', values='Score_diario', aggfunc='max')
        # Preencher buracos com None ou 0
        heatmap_data = heatmap_data.fillna(0)
    except:
        return None

    dias_label = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=dias_label,
        colorscale='Greens',
        showscale=False,
        ygap=2, xgap=2
    ))
    fig.update_layout(
        height=200, margin=dict(t=20, b=20, l=40, r=20),
        title="🧩 Mapa de Consistência (Semanas)",
        title_font_size=14,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, tickmode='linear', dtick=2),
        yaxis=dict(showgrid=False, zeroline=False)
    )
    return fig

def gerar_html_interativo(df):
    """Gera relatório HTML interativo com Plotly"""
    if df.empty: return None
    
    # Recriar gráficos chave
    fig_line = px.line(df, x='Data', y='Score_diario', title='Evolução do Score', markers=True, template='plotly_dark')
    fig_scat = px.scatter(df, x='Sono_h', y='Score_diario', color='Bem_estar', size='Motivacao', title='Correlação: Sono vs Score', template='plotly_dark')
    
    html_string = f"""
    <html>
    <head>
        <title>Relatório Nexus</title>
        <style>body {{ background-color: #0E1117; color: white; font-family: sans-serif; padding: 20px; }} h1 {{ color: #4F8BF9; }}</style>
    </head>
    <body>
        <h1 align="center">Relatório de Performance Nexus</h1>
        <p align="center">Gerado em {date.today()}</p>
        <hr>
        <h3>📈 Evolução Temporal</h3>
        {fig_line.to_html(full_html=False, include_plotlyjs='cdn')}
        <br>
        <h3>💤 Análise de Sono & Performance</h3>
        {fig_scat.to_html(full_html=False, include_plotlyjs='cdn')}
    </body>
    </html>
    """
    return html_string.encode('utf-8')

# --- Aplicação Principal ---
def main():
    apply_custom_styles()
    
    # --- SIDEBAR: Gamificação e Filtros ---
    with st.sidebar:
        st.markdown("### 👤 Perfil & Nível")
        
        if 'df' not in st.session_state:
            st.session_state.df = load_data()
        
        # Cálculo de XP
        xp_total, nivel, progresso, conquistas = calcular_xp_nivel(st.session_state.df)
        
        col_lvl, col_xp = st.columns([0.3, 0.7])
        with col_lvl:
            st.markdown(f"<h1 style='text-align:center; color:#4F8BF9; margin:0;'>{nivel}</h1>", unsafe_allow_html=True)
            st.caption("Nível")
        with col_xp:
            st.write(f"**XP Total:** {xp_total}")
            st.markdown(f"""
                <div class="xp-container">
                    <div class="xp-fill" style="width: {progresso}%;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.7em; color:#9CA3AF; margin-top:2px;">
                    <span>{int(progresso)}%</span>
                    <span>Próx. Nível</span>
                </div>
            """, unsafe_allow_html=True)
            
        if conquistas:
            with st.expander("🏆 Conquistas"):
                for c in conquistas: st.success(c)
        
        st.markdown("---")
        st.markdown("### 📅 Filtros")
        periodo = st.selectbox("Período de Análise", ["Últimos 7 dias", "Últimos 30 dias", "Tudo"])
        
    # --- HEADER ---
    st.markdown("## 🚀 Nexus | Painel de Controle")
    
    # Filtragem de Dados
    df_full = st.session_state.df
    if not df_full.empty:
        if periodo == "Últimos 7 dias":
            df = df_full[df_full['Data'] > (date.today() - timedelta(days=7))]
        elif periodo == "Últimos 30 dias":
            df = df_full[df_full['Data'] > (date.today() - timedelta(days=30))]
        else:
            df = df_full
    else:
        df = df_full

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard & Heatmap", "📝 Novo Registro", "🎯 Metas", "📤 Relatórios"])

    # --- TAB 1: DASHBOARD ---
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
                delta_html = f"{'+' if diff >=0 else ''}{diff:.0f} pts"
                delta_color = color_metric

            # Cards KPI
            k1, k2, k3, k4 = st.columns(4)
            with k1: metric_card("Score Hoje", f"{last['Score_diario']:.0f}", delta_html, delta_color)
            with k2: metric_card("Estudo Total", f"{(df['Estudo_min'].sum()/60):.1f}h", f"{df['Estudo_min'].sum()} min", "#4F8BF9")
            with k3: metric_card("Treino Total", f"{(df['Treino_min'].sum()/60):.1f}h", f"{df['Treino_min'].sum()} min", "#FFA500")
            with k4: metric_card("Média Sono", f"{df['Sono_h'].mean():.1f}h", "Horas/Noite", "#AB63FA")
            
            st.markdown("<br>", unsafe_allow_html=True)

            # MAPA DE CALOR (Heatmap GitHub Style)
            heatmap_fig = plot_heatmap_atividade(df_full) # Usa df_full para mostrar histórico completo
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True)
            
            # Gráficos Principais
            c_radar, c_main = st.columns([0.4, 0.6])
            
            with c_radar:
                st.markdown("##### 🕸️ Radar de Equilíbrio")
                # Normalização Inteligente
                # Estudo: 1440 min (24h) = nota 10
                # Treino: 120 min (2h) = nota 10
                vals = last.copy()
                r_estudo = min((vals['Estudo_min'] / 1440) * 10, 10)
                r_treino = min((vals['Treino_min'] / 120) * 10, 10)
                r_sono = min(vals['Sono_h'], 10)
                
                categories = ['Estudo', 'Treino', 'Sono', 'Nutrição', 'Motivação', 'Relações']
                values = [r_estudo, r_treino, r_sono, vals['Nutricao'], vals['Motivacao'], vals['Relacoes']]
                values += [values[0]]
                categories += [categories[0]]
                
                fig_radar = go.Figure(go.Scatterpolar(
                    r=values, theta=categories, fill='toself', line_color='#4F8BF9', fillcolor='rgba(79, 139, 249, 0.3)'
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 10], showticklabels=False, linecolor='rgba(255,255,255,0.1)')),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=40, r=40)
                )
                st.plotly_chart(fig_radar, use_container_width=True)
                
            with c_main:
                st.markdown("##### 📈 Correlação: Estudo vs Score")
                fig_combo = go.Figure()
                # Eixo Esquerdo: Estudo
                fig_combo.add_trace(go.Bar(
                    x=df['Data'], y=df['Estudo_min'], name="Estudo (min)",
                    marker_color='rgba(79, 139, 249, 0.4)', yaxis='y'
                ))
                # Eixo Direito: Score (Linha Amarela)
                fig_combo.add_trace(go.Scatter(
                    x=df['Data'], y=df['Score_diario'], name="Score",
                    mode='lines+markers', line=dict(color='#FFA500', width=3), yaxis='y2'
                ))
                fig_combo.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(title="Minutos Estudo", gridcolor='rgba(255,255,255,0.05)'),
                    yaxis2=dict(title="Score (0-100)", overlaying='y', side='right', range=[0, 110], showgrid=False),
                    legend=dict(orientation="h", y=1.1, x=0), margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig_combo, use_container_width=True)
        else:
            st.info("👋 Bem-vindo ao Nexus! Comece registrando seus dados na aba 'Novo Registro'.")

    # --- TAB 2: REGISTRO ---
    with tab2:
        c1, _ = st.columns([0.6, 0.4])
        with c1:
            st.markdown("#### 📝 Diário de Bordo")
            with st.form("entry_form"):
                d1, d2 = st.columns(2)
                with d1:
                    st.info("Produtividade")
                    dt = st.date_input("Data", date.today())
                    estudo = st.number_input("⏱️ Estudo (minutos)", min_value=0, max_value=1440, value=60, step=15)
                    treino = st.number_input("🏋️ Treino (minutos)", 0, 300, 45, step=5)
                    sono = st.number_input("💤 Sono (horas)", 0.0, 24.0, 7.0, 0.5)
                    
                    if estudo > 720: # Alerta de validação
                        st.warning("⚠️ Atenção: Mais de 12h de estudo registradas.")

                with d2:
                    st.success("Subjetivo (1-10)")
                    bem_estar = st.slider("Bem-estar", 1, 10, 7)
                    nutri = st.slider("Nutrição", 1, 10, 7)
                    motiv = st.slider("Motivação", 1, 10, 7)
                    rela = st.slider("Relações", 1, 10, 7)
                    org = st.toggle("✅ Organização cumpida?", value=True)
                
                obs = st.text_area("Notas do dia", placeholder="O que aprendi hoje?")
                
                if st.form_submit_button("💾 Salvar Registro", type="primary"):
                    entry = {
                        "Data": dt, "Estudo_min": estudo, "Organizacao": 1 if org else 0,
                        "Treino_min": treino, "Bem_estar": bem_estar, "Sono_h": sono,
                        "Nutricao": nutri, "Motivacao": motiv, "Relacoes": rela, "Observacoes": obs
                    }
                    with st.spinner("Sincronizando..."):
                        if save_entry_google(entry):
                            st.cache_data.clear()
                            st.session_state.df = load_data()
                            st.toast("Salvo com sucesso!", icon="✅")
                            st.rerun()

    # --- TAB 3: METAS ---
    with tab3:
        # Sistema Simples de Metas
        st.markdown("### 🎯 Metas Semanais")
        if not df.empty:
            last_7 = df.tail(7)
            
            # Meta Estudo: 4h/dia (240 min)
            media_estudo = last_7['Estudo_min'].mean()
            meta_estudo = 240
            prog_estudo = min(media_estudo / meta_estudo, 1.0)
            
            st.write(f"**Estudo Diário (Média 7 dias)**: {media_estudo:.0f} / {meta_estudo} min")
            st.progress(prog_estudo)
            
            # Meta Score: 70
            media_score = last_7['Score_diario'].mean()
            meta_score = 70
            prog_score = min(media_score / meta_score, 1.0)
            
            st.write(f"**Score Médio**: {media_score:.1f} / {meta_score}")
            st.progress(prog_score)
        else:
            st.info("Registre dados para ver suas metas.")

    # --- TAB 4: RELATÓRIOS ---
    with tab4:
        st.markdown("### 🗄️ Base de Dados & Exportação")
        st.dataframe(df_full.sort_values("Data", ascending=False), use_container_width=True, height=300)
        
        c_exp1, c_exp2 = st.columns(2)
        
        with c_exp1:
            csv = df_full.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV (Excel)", csv, "nexus_data.csv", "text/csv", use_container_width=True)
            
        with c_exp2:
            html_report = gerar_html_interativo(df_full)
            if html_report:
                st.download_button("🌐 Baixar Relatório HTML Interativo", html_report, "nexus_report.html", "text/html", use_container_width=True)

if __name__ == "__main__":
    main()
