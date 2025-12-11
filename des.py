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
import os

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
        
        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 2px;
        }
        .badge-success {
            background: rgba(0, 204, 150, 0.2);
            color: #00CC96;
            border: 1px solid rgba(0, 204, 150, 0.3);
        }
        .badge-warning {
            background: rgba(255, 165, 0, 0.2);
            color: #FFA500;
            border: 1px solid rgba(255, 165, 0, 0.3);
        }
        .badge-danger {
            background: rgba(239, 85, 59, 0.2);
            color: #EF553B;
            border: 1px solid rgba(239, 85, 59, 0.3);
        }
        
        /* Progress bars */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #4F8BF9 0%, #764ba2 100%);
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

# --- Funções de Análise Avançada ---
def calcular_metricas_avancadas(df):
    """Calcula métricas avançadas e retorna DataFrame modificado e matriz de correlação"""
    if len(df) == 0:
        return df, None
    
    df_analise = df.copy()
    
    # Série temporal de 7 dias
    df_analise['Media_Movel_7'] = df_analise['Score_diario'].rolling(7, min_periods=1).mean()
    
    # Identificar padrões
    df_analise['Tendencia_Score'] = df_analise['Score_diario'].diff()
    
    # Dia da semana em inglês (evita problemas de locale)
    df_analise['Dia_Semana_Num'] = pd.to_datetime(df_analise['Data']).dt.dayofweek
    df_analise['Dia_Semana'] = df_analise['Dia_Semana_Num'].map({
        0: 'Segunda', 1: 'Terça', 2: 'Quarta', 
        3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
    })
    
    # Correlações
    metricas_correlacao = ['Estudo_min', 'Sono_h', 'Treino_min', 'Bem_estar', 
                          'Nutricao', 'Motivacao', 'Relacoes', 'Score_diario']
    
    # Verificar colunas existentes
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
        # Conquista de consistência
        ultimos_7 = df.tail(7)
        dias_consecutivos = (ultimos_7['Score_diario'] >= 70).sum()
        
        if dias_consecutivos >= 7:
            pontos += 100
            conquistas.append("🏆 7 dias consecutivos com score ≥70")
        
        # Conquista de melhoria
        if len(df) >= 14:
            media_primeira_semana = df['Score_diario'].iloc[-14:-7].mean()
            media_segunda_semana = df['Score_diario'].iloc[-7:].mean()
            if media_segunda_semana > media_primeira_semana + 5:
                pontos += 50
                conquistas.append("📈 Melhoria consistente nas últimas 2 semanas")
    
    # Conquista de estudo
    total_estudo = df['Estudo_min'].sum()
    if total_estudo > 10000:  # ~167 horas
        pontos += 50
        conquistas.append("📚 +10000 minutos de estudo acumulado")
    
    # Conquista de treino
    total_treino = df['Treino_min'].sum()
    if total_treino > 3000:  # 50 horas
        pontos += 30
        conquistas.append("💪 +3000 minutos de treino acumulado")
    
    # Conquista de organização
    dias_organizados = df['Organizacao'].sum()
    if dias_organizados >= 30:
        pontos += 40
        conquistas.append("✅ +30 dias organizados")
    
    return pontos, conquistas

def previsao_tendencia(df):
    """Previsão simples baseada em média móvel"""
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
            return "⏳ Coletando mais dados...", "#9CA3AF"
    return "⏳ Coletando mais dados...", "#9CA3AF"

def analisar_fatores_influencia(df):
    """Identifica quais fatores mais influenciam o score"""
    if len(df) > 10:
        features = ['Estudo_min', 'Sono_h', 'Treino_min', 
                   'Bem_estar', 'Nutricao', 'Motivacao', 'Relacoes', 'Organizacao']
        # Verificar quais features existem nos dados
        features_existentes = [f for f in features if f in df.columns]
        
        if len(features_existentes) > 1:
            X = df[features_existentes].fillna(df[features_existentes].mean())
            y = df['Score_diario']
            
            # Calcula correlações simples
            correlacoes = X.corrwith(y).abs().sort_values(ascending=False)
            
            importancia = pd.DataFrame({
                'fator': correlacoes.index,
                'correlacao': correlacoes.values
            })
            
            return importancia.head(5)
    return None

def gerar_relatorio_pdf(df):
    """Gera gráficos para relatório"""
    if len(df) < 2:
        return None
    
    try:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Relatório de Auto-Desenvolvimento', fontsize=16, fontweight='bold')
        
        # Gráfico 1: Evolução do Score
        axes[0, 0].plot(df['Data'], df['Score_diario'], marker='o', linewidth=2, color='#4F8BF9')
        axes[0, 0].set_title('Evolução do Score Diário', fontsize=12)
        axes[0, 0].set_xlabel('Data')
        axes[0, 0].set_ylabel('Score (0-100)')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Gráfico 2: Distribuição de Estudo
        horas_estudo = df['Estudo_min'] / 60
        axes[0, 1].hist(horas_estudo, bins=10, edgecolor='black', alpha=0.7, color='#00CC96')
        axes[0, 1].set_title('Distribuição de Horas de Estudo', fontsize=12)
        axes[0, 1].set_xlabel('Horas de Estudo')
        axes[0, 1].set_ylabel('Frequência')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Gráfico 3: Correlação entre Sono e Score
        axes[1, 0].scatter(df['Sono_h'], df['Score_diario'], alpha=0.6, color='#AB63FA')
        axes[1, 0].set_title('Relação Sono vs Score', fontsize=12)
        axes[1, 0].set_xlabel('Horas de Sono')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Gráfico 4: Média por Dia da Semana
        if 'Dia_Semana' in df.columns:
            dias_ordem = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            
            # Criar ordenação manual
            df_dias = df.copy()
            df_dias['Dia_Order'] = pd.Categorical(
                df_dias['Dia_Semana'], 
                categories=dias_ordem, 
                ordered=True
            )
            media_dias = df_dias.groupby('Dia_Order')['Score_diario'].mean()
            
            axes[1, 1].bar(range(len(media_dias)), media_dias.values, color='#FFA500', alpha=0.7)
            axes[1, 1].set_title('Score Médio por Dia da Semana', fontsize=12)
            axes[1, 1].set_xlabel('Dia da Semana')
            axes[1, 1].set_ylabel('Score Médio')
            axes[1, 1].set_xticks(range(len(dias_ordem)))
            axes[1, 1].set_xticklabels(dias_ordem, rotation=45)
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Converter para bytes
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return buf
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")
        return None

# --- Sistema de Metas ---
def carregar_metas():
    """Carrega metas do session state ou inicializa padrões"""
    if 'metas' not in st.session_state:
        st.session_state.metas = {
            'estudo': 240,      # 4 horas
            'treino': 60,       # 1 hora
            'sono': 8.0,        # 8 horas
            'score': 70,        # Score mínimo
            'nutricao': 7,      # Nutrição mínima
            'motivacao': 7,     # Motivação mínima
            'organizacao': 5,   # Dias organizados por semana
        }
    return st.session_state.metas

def verificar_metas(df, metas):
    """Verifica progresso em relação às metas"""
    if len(df) == 0:
        return {}
    
    ultima_semana = df.tail(7) if len(df) >= 7 else df
    
    resultados = {
        'estudo': {
            'meta': metas['estudo'],
            'real': ultima_semana['Estudo_min'].mean(),
            'atingido': ultima_semana['Estudo_min'].mean() >= metas['estudo']
        },
        'treino': {
            'meta': metas['treino'],
            'real': ultima_semana['Treino_min'].mean(),
            'atingido': ultima_semana['Treino_min'].mean() >= metas['treino']
        },
        'sono': {
            'meta': metas['sono'],
            'real': ultima_semana['Sono_h'].mean(),
            'atingido': ultima_semana['Sono_h'].mean() >= metas['sono']
        },
        'score': {
            'meta': metas['score'],
            'real': ultima_semana['Score_diario'].mean(),
            'atingido': ultima_semana['Score_diario'].mean() >= metas['score']
        },
        'organizacao': {
            'meta': metas['organizacao'],
            'real': ultima_semana['Organizacao'].sum(),
            'atingido': ultima_semana['Organizacao'].sum() >= metas['organizacao']
        }
    }
    
    return resultados

# --- Aplicação Principal ---
def main():
    apply_custom_styles()
    
    with st.sidebar:
        st.title("⚙️ Configurações")
        
        st.markdown("### 📅 Período")
        periodo = st.selectbox(
            "Selecione o período:",
            ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todo o período"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🎮 Sistema de Gamificação")
        if 'df' not in st.session_state:
            st.session_state.df = load_data()
        
        pontos, conquistas = calcular_pontos_recompensa(st.session_state.df)
        st.metric("🏆 Pontos Totais", pontos)
        
        if conquistas:
            with st.expander("🎖️ Conquistas Desbloqueadas"):
                for c in conquistas:
                    st.success(c)
        
        st.markdown("---")
        st.caption(f"📊 {len(st.session_state.df)} registros carregados")
        st.caption("Nexus Tracker v3.0")

    st.markdown("# 🚀 Painel de Evolução Pessoal")

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
        elif periodo == "Últimos 90 dias":
            cutoff = date.today() - timedelta(days=90)
            df = df_full[df_full['Data'] > cutoff]
        else:
            df = df_full
    else:
        df = df_full

    # Calcular métricas avançadas
    df_analise, matriz_correlacao = calcular_metricas_avancadas(df)
    
    # Carregar metas
    metas = carregar_metas()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📝 Novo Registro", "🎯 Metas", "📈 Relatórios"])

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
            with c1: metric_card("Score Hoje", f"{last['Score_diario']:.0f}", delta_html, delta_color, gradient=True)
            with c2: metric_card("Total Estudo", f"{horas_estudo:.1f}h", f"{total_estudo_min} min totais", "#4F8BF9")
            with c3: metric_card("Treino Físico", f"{df['Treino_min'].sum()} min", "Acumulado Período", "#FFA500")
            with c4: metric_card("Média Sono", f"{df['Sono_h'].mean():.1f}h", "Qualidade do descanso", "#AB63FA")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # KPIs Avançados
            st.markdown("#### 📈 Métricas de Desempenho")
            
            # Calcular métricas avançadas
            eficiencia = 0
            if df['Estudo_min'].sum() > 0:
                eficiencia = df['Score_diario'].mean() / (df['Estudo_min'].mean() / 60) if df['Estudo_min'].mean() > 0 else 0
            
            resultados_metas = verificar_metas(df, metas)
            consistencia = 0
            if len(df) > 0:
                dias_acima_meta = (df['Score_diario'] > metas['score']).sum()
                consistencia = (dias_acima_meta / len(df)) * 100
            
            c5, c6, c7, c8 = st.columns(4)
            with c5: 
                metric_card("Eficiência", f"{eficiencia:.2f}", "Score por hora estudo", "#00CC96")
            with c6: 
                metric_card("Consistência", f"{consistencia:.1f}%", 
                          f"{dias_acima_meta}/{len(df)} dias", "#7FDBFF")
            with c7: 
                media_movel = df_analise['Media_Movel_7'].iloc[-1] if len(df_analise) > 0 else 0
                metric_card("Média Móvel", f"{media_movel:.1f}", "Últimos 7 dias", "#FFA500")
            with c8: 
                dias_organizado = df['Organizacao'].sum()
                metric_card("Dias Org.", f"{dias_organizado}", f"Total período", "#764ba2")

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
                vals_radar['Estudo_min'] = (vals_radar['Estudo_min'] / 1440) * 10
                
                # 2. Treino: Escala onde 2 horas (120 min) = nota 10
                vals_radar['Treino_min'] = min((vals_radar['Treino_min'] / 120) * 10, 10)
                
                # 3. Sono: Escala onde 10 horas = nota 10
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
                st.markdown("##### 📈 Evolução: Estudo vs Score")
                
                fig_combo = go.Figure()
                
                # Barra de Estudo (Eixo Y1 - Esquerda)
                fig_combo.add_trace(go.Bar(
                    x=df['Data'], y=df['Estudo_min'], name="Estudo (min)",
                    marker_color='rgba(79, 139, 249, 0.4)', yaxis='y'
                ))
                
                # Linha de Score (Eixo Y2 - Direita) - COR AMARELA (#FFA500)
                fig_combo.add_trace(go.Scatter(
                    x=df['Data'], y=df['Score_diario'], name="Score do Dia",
                    mode='lines+markers', 
                    line=dict(color='#FFA500', width=3), # Linha Amarela
                    yaxis='y2' # Eixo secundário
                ))
                
                fig_combo.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    
                    # Eixo Y1 (Estudo)
                    yaxis=dict(
                        title="Minutos de Estudo", 
                        showgrid=True, 
                        gridcolor='rgba(255,255,255,0.05)'
                    ),
                    
                    # Eixo Y2 (Score) - Para escala 0-100 não ficar "amassada"
                    yaxis2=dict(
                        title="Score (0-100)", 
                        overlaying='y', 
                        side='right', 
                        showgrid=False,
                        range=[0, 110] # Um pouco de margem acima de 100
                    ),
                    
                    legend=dict(orientation="h", y=1.1, x=0),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig_combo, use_container_width=True)

            # Análises Avançadas
            st.markdown("#### 🔍 Análises Detalhadas")
            
            col_corr, col_week = st.columns([0.5, 0.5])
            
            with col_corr:
                if matriz_correlacao is not None:
                    st.markdown("##### 🔗 Correlação entre Fatores")
                    fig_corr = px.imshow(matriz_correlacao, 
                                       text_auto='.2f',
                                       color_continuous_scale='RdBu',
                                       aspect="auto")
                    fig_corr.update_layout(height=400)
                    st.plotly_chart(fig_corr, use_container_width=True)
            
            with col_week:
                if len(df_analise) > 0 and 'Dia_Semana' in df_analise.columns:
                    st.markdown("##### 📅 Performance por Dia da Semana")
                    
                    dias_ordem = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                    df_semana = df_analise.copy()
                    
                    # Ordenar manualmente
                    df_semana['Dia_Order'] = pd.Categorical(
                        df_semana['Dia_Semana'], 
                        categories=dias_ordem, 
                        ordered=True
                    )
                    
                    media_semana = df_semana.groupby('Dia_Order').agg({
                        'Score_diario': 'mean',
                        'Estudo_min': 'mean',
                        'Sono_h': 'mean'
                    })
                    
                    fig_semana = go.Figure()
                    fig_semana.add_trace(go.Bar(
                        x=media_semana.index,
                        y=media_semana['Score_diario'],
                        name='Score Médio',
                        marker_color='#4F8BF9'
                    ))
                    
                    fig_semana.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(tickfont=dict(color='#9CA3AF')),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#9CA3AF'))
                    )
                    
                    st.plotly_chart(fig_semana, use_container_width=True)
            
            # Insights Automáticos
            st.markdown("#### 💡 Insights Automáticos")
            
            insights = []
            
            if len(df) >= 3:
                ultimos_3 = df.tail(3)
                
                # Sono vs Estudo
                if ultimos_3['Sono_h'].mean() < 6 and ultimos_3['Estudo_min'].mean() > 360:
                    insights.append("⚠️ **Alerta**: Pouco sono com muito estudo pode reduzir eficiência")
                
                # Tendência de score
                if len(df) >= 5:
                    scores_recentes = df['Score_diario'].tail(5)
                    if scores_recentes.iloc[0] > scores_recentes.iloc[-1] + 10:
                        insights.append("📉 **Tendência**: Score em queda nos últimos dias")
                
                # Organização vs Produtividade
                if ultimos_3['Organizacao'].mean() < 0.5 and ultimos_3['Score_diario'].mean() < 70:
                    insights.append("📋 **Sugestão**: Melhorar organização pode aumentar produtividade")
            
            # Fatores de influência
            importancia = analisar_fatores_influencia(df)
            if importancia is not None and not importancia.empty:
                fator_principal = importancia.iloc[0]['fator']
                correlacao = importancia.iloc[0]['correlacao']
                insights.append(f"🎯 **Descoberta**: {fator_principal} tem alta correlação ({correlacao:.2f}) com seu score")
            
            # Exibir insights
            if insights:
                for insight in insights[:4]:  # Limitar a 4 insights
                    st.info(insight)
            else:
                st.info("Continue registrando dados para receber insights personalizados!")
                
            # Tendência
            st.markdown("#### 📊 Análise de Tendência")
            col_trend, col_hist = st.columns([0.5, 0.5])
            
            with col_trend:
                tendencia, cor = previsao_tendencia(df)
                st.markdown(f"**Previsão de Tendência**: <span style='color:{cor}; font-weight:bold'>{tendencia}</span>", 
                           unsafe_allow_html=True)
                
            with col_hist:
                st.markdown("##### Distribuição de Scores")
                fig_hist = px.histogram(df, x='Score_diario', nbins=15, 
                                       color_discrete_sequence=['#4F8BF9'])
                fig_hist.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig_hist, use_container_width=True)

        else:
            st.info("👈 Nenhum dado encontrado. Inicie seus registros na aba 'Novo Registro'!")

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
                observacoes = st.text_area("📖 Diário de Bordo", placeholder="Insights do dia...", height=100)
                
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
                    with st.spinner("Processando..."):
                        if save_entry_google(entry):
                            st.cache_data.clear()
                            st.session_state.df = load_data() 
                            st.toast("✅ Registro salvo com sucesso!", icon="✅")
                            st.rerun()

    # --- ABA 3: METAS ---
    with tab3:
        st.markdown("### 🎯 Sistema de Metas Personalizadas")
        
        col_metas, col_progresso = st.columns([0.5, 0.5])
        
        with col_metas:
            st.markdown("#### Definir Metas")
            
            with st.form("metas_form"):
                st.subheader("Metas Diárias")
                meta_estudo = st.number_input("Estudo (min/dia)", 0, 1440, metas['estudo'])
                meta_treino = st.number_input("Treino (min/dia)", 0, 300, metas['treino'])
                meta_sono = st.slider("Sono (h/dia)", 4.0, 12.0, metas['sono'], 0.5)
                
                st.subheader("Metas de Bem-estar")
                meta_score = st.slider("Score Mínimo Diário", 0, 100, metas['score'])
                meta_nutricao = st.slider("Nutrição Mínima", 1, 10, metas['nutricao'])
                meta_motivacao = st.slider("Motivação Mínima", 1, 10, metas['motivacao'])
                meta_organizacao = st.slider("Dias Organizados/Semana", 0, 7, metas['organizacao'])
                
                submitted_metas = st.form_submit_button("💾 Salvar Metas")
                
                if submitted_metas:
                    st.session_state.metas = {
                        'estudo': meta_estudo,
                        'treino': meta_treino,
                        'sono': meta_sono,
                        'score': meta_score,
                        'nutricao': meta_nutricao,
                        'motivacao': meta_motivacao,
                        'organizacao': meta_organizacao
                    }
                    st.success("Metas atualizadas com sucesso!")
        
        with col_progresso:
            st.markdown("#### Progresso Atual")
            
            if len(df) > 0:
                resultados = verificar_metas(df, st.session_state.metas)
                
                for key, result in resultados.items():
                    st.markdown(f"**{key.title()}**")
                    progresso = min((result['real'] / result['meta']) * 100, 150)
                    st.progress(min(progresso/100, 1), 
                              text=f"{result['real']:.1f} / {result['meta']} "
                                   f"({progresso:.1f}%)")
                    
                    if result['atingido']:
                        st.success("✅ Meta atingida!")
                    else:
                        st.warning(f"⏳ Faltam {result['meta'] - result['real']:.1f} para atingir a meta")
                    
                    st.markdown("---")
            else:
                st.info("Adicione registros para ver seu progresso em relação às metas!")
        
        # Estatísticas de metas
        if len(df) > 0:
            st.markdown("#### 📊 Estatísticas de Metas")
            
            # Calcular taxa de sucesso
            resultados = verificar_metas(df, st.session_state.metas)
            metas_atingidas = sum(1 for r in resultados.values() if r['atingido'])
            total_metas = len(resultados)
            taxa_sucesso = (metas_atingidas / total_metas) * 100 if total_metas > 0 else 0
            
            col_success, col_streak, col_best = st.columns(3)
            with col_success:
                metric_card("Taxa de Sucesso", f"{taxa_sucesso:.1f}%", 
                          f"{metas_atingidas}/{total_metas} metas", 
                          "#00CC96" if taxa_sucesso > 70 else "#FFA500")
            
            with col_streak:
                # Calcular sequência atual
                sequencia_atual = 0
                if len(df) > 0:
                    for i in range(len(df)-1, -1, -1):
                        if df.iloc[i]['Score_diario'] >= st.session_state.metas['score']:
                            sequencia_atual += 1
                        else:
                            break
                metric_card("Sequência Atual", f"{sequencia_atual} dias", 
                          "Dias acima do score mínimo", "#4F8BF9")
            
            with col_best:
                melhor_score = df['Score_diario'].max() if len(df) > 0 else 0
                metric_card("Melhor Score", f"{melhor_score:.0f}", "Recorde pessoal", "#AB63FA")

    # --- ABA 4: RELATÓRIOS ---
    with tab4:
        st.markdown("### 📈 Relatórios Avançados")
        
        col_dados, col_relatorio = st.columns([0.6, 0.4])
        
        with col_dados:
            st.markdown("#### 📊 Dados Completos")
            st.dataframe(
                df_full.sort_values(by="Data", ascending=False), 
                use_container_width=True,
                height=400
            )
            
            # Botões de exportação
            col_csv, col_json = st.columns(2)
            with col_csv:
                csv = df_full.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Baixar CSV", 
                    csv, 
                    "nexus_backup.csv", 
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
        
        with col_relatorio:
            st.markdown("#### 🖼️ Relatório Gráfico")
            
            if len(df) > 1:
                st.markdown("##### Gerar Relatório Visual")
                st.info("Clique no botão abaixo para gerar um relatório gráfico com análise completa dos seus dados.")
                
                if st.button("📊 Gerar Relatório Gráfico", use_container_width=True, type="primary"):
                    with st.spinner("Gerando relatório..."):
                        relatorio_img = gerar_relatorio_pdf(df)
                        
                        if relatorio_img:
                            st.image(relatorio_img, caption="Relatório Gráfico Completo")
                            
                            # Botão para baixar a imagem
                            st.download_button(
                                "📷 Baixar Imagem do Relatório",
                                relatorio_img,
                                "relatorio_nexus.png",
                                "image/png",
                                use_container_width=True
                            )
            else:
                st.warning("Adicione mais registros para gerar relatórios gráficos completos.")
            
            # Resumo Estatístico
            if len(df) > 0:
                st.markdown("##### 📈 Resumo Estatístico")
                
                resumo_stats = pd.DataFrame({
                    'Métrica': [
                        'Média Score', 'Melhor Score', 'Pior Score',
                        'Média Estudo (h)', 'Média Sono (h)', 'Média Treino (min)'
                    ],
                    'Valor': [
                        f"{df['Score_diario'].mean():.1f}",
                        f"{df['Score_diario'].max():.1f}",
                        f"{df['Score_diario'].min():.1f}",
                        f"{df['Estudo_min'].mean()/60:.1f}",
                        f"{df['Sono_h'].mean():.1f}",
                        f"{df['Treino_min'].mean():.0f}"
                    ]
                })
                st.dataframe(resumo_stats, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
