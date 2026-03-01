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

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Diário de Desenvolvimento",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Profissional Mobile-First ---
def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #ec4899;
            --accent: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-elevated: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: rgba(148, 163, 184, 0.1);
        }

        * { box-sizing: border-box; }
        
        html, body, [class*="css"] { 
            font-family: 'Inter', sans-serif; 
            -webkit-font-smoothing: antialiased;
        }
        
        .stApp { 
            background: linear-gradient(180deg, var(--bg-dark) 0%, #1a1f2e 100%);
            min-height: 100vh;
        }

        .mobile-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            padding: 1.5rem 1rem;
            margin: -1rem -1rem 1.5rem -1rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        }
        
        .mobile-header h1 {
            color: white;
            font-size: 1.75rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.02em;
        }
        
        .mobile-header p {
            color: rgba(255,255,255,0.9);
            font-size: 0.9rem;
            margin: 0.5rem 0 0 0;
            font-weight: 500;
        }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .metric-card:hover::before { opacity: 1; }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
            border-color: rgba(99, 102, 241, 0.3);
        }

        .metric-card.featured {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
        }
        
        .metric-card.featured::before { opacity: 1; }

        .metric-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            margin-bottom: 0.75rem;
            background: rgba(99, 102, 241, 0.1);
        }
        
        .metric-icon.study { background: rgba(59, 130, 246, 0.1); }
        .metric-icon.workout { background: rgba(16, 185, 129, 0.1); }
        .metric-icon.sleep { background: rgba(139, 92, 246, 0.1); }
        .metric-icon.score { 
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(236, 72, 153, 0.2));
        }

        .metric-label {
            color: var(--text-secondary);
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }

        .metric-value {
            color: var(--text-primary);
            font-size: 1.875rem;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.02em;
        }

        .metric-sub {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            margin-top: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            background: rgba(255,255,255,0.05);
        }

        .metric-sub.positive { color: var(--accent); background: rgba(16, 185, 129, 0.1); }
        .metric-sub.negative { color: var(--danger); background: rgba(239, 68, 68, 0.1); }
        .metric-sub.neutral { color: var(--text-secondary); }

        .chart-container {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }

        .chart-title {
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .stForm {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
        }

        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input {
            background: var(--bg-elevated) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            color: var(--text-primary) !important;
            font-weight: 500;
        }

        .stSlider > div > div > div {
            background: var(--bg-elevated) !important;
        }
        
        .stSlider [role="slider"] {
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            border: 2px solid var(--bg-card) !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
        }

        .stToggle > div > div > div {
            background: var(--bg-elevated) !important;
        }
        
        .stToggle [aria-checked="true"] > div {
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        }

        div.stButton > button {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            padding: 0.875rem 1.5rem;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.9375rem;
            width: 100%;
            transition: all 0.3s;
            box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.4);
        }
        
        div.stButton > button:active { transform: translateY(0); }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: var(--bg-card);
            padding: 0.5rem;
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px !important;
            padding: 0.75rem 1rem !important;
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--text-secondary);
            border: none !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.375rem 0.875rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }
        
        .badge-success {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .badge-warning {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .animate-in {
            animation: fadeInUp 0.6s ease-out forwards;
        }

        @media (max-width: 768px) {
            .metric-value { font-size: 1.5rem; }
            .metric-card { padding: 1rem; }
            .stTabs [data-baseweb="tab"] { padding: 0.5rem 0.75rem !important; font-size: 0.75rem !important; }
            .chart-container { padding: 1rem; }
            .mobile-header h1 { font-size: 1.5rem; }
        }

        @media (max-width: 768px) {
            [data-testid="stSidebar"] { width: 100% !important; }
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb {
            background: var(--bg-elevated);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--primary); }
        </style>
    """, unsafe_allow_html=True)

# --- Componentes Visuais ---
def metric_card_modern(label, value, subtext=None, icon="📊", featured=False, delay=0):
    featured_class = "featured" if featured else ""
    sub_class = "neutral"
    
    if subtext:
        if "+" in str(subtext) or "↑" in str(subtext):
            sub_class = "positive"
        elif "-" in str(subtext) or "↓" in str(subtext):
            sub_class = "negative"
    
    icon_class = ""
    if "estudo" in label.lower() or "study" in label.lower():
        icon_class = "study"
    elif "treino" in label.lower() or "workout" in label.lower():
        icon_class = "workout"
    elif "sono" in label.lower() or "sleep" in label.lower():
        icon_class = "sleep"
    elif "score" in label.lower():
        icon_class = "score"
    
    st.markdown(f"""
    <div class="metric-card {featured_class} animate-in" style="animation-delay: {delay}ms">
        <div class="metric-icon {icon_class}">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-sub {sub_class}">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)

# --- Funções de Data em Português ---
def formatar_data_extenso(data_obj):
    """Converte data para formato 'dia de mês de ano' em português"""
    meses = {
        1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
        5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
        9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
    }
    
    if isinstance(data_obj, str):
        data_obj = pd.to_datetime(data_obj).date()
    
    dia = data_obj.day
    mes = meses[data_obj.month]
    ano = data_obj.year
    
    return f"{dia} de {mes} de {ano}"

def formatar_data_curta(data_obj):
    """Converte data para formato 'dia/mês'"""
    if isinstance(data_obj, str):
        data_obj = pd.to_datetime(data_obj).date()
    return f"{data_obj.day}/{data_obj.month}"

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
        
        if "Estudo_h" in df.columns:
            df.rename(columns={"Estudo_h": "Estudo_min"}, inplace=True)

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
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- Funções de Análise ---
def calcular_metricas_avancadas(df):
    if len(df) == 0:
        return df, None
    
    df_analise = df.copy()
    df_analise['Media_Movel_7'] = df_analise['Score_diario'].rolling(7, min_periods=1).mean()
    df_analise['Tendencia_Score'] = df_analise['Score_diario'].diff()
    
    df_analise['Dia_Semana_Num'] = pd.to_datetime(df_analise['Data']).dt.dayofweek
    df_analise['Dia_Semana'] = df_analise['Dia_Semana_Num'].map({
        0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
    })
    
    metricas_correlacao = ['Estudo_min', 'Sono_h', 'Treino_min', 'Bem_estar', 
                          'Nutricao', 'Motivacao', 'Relacoes', 'Score_diario']
    
    cols_existentes = [col for col in metricas_correlacao if col in df_analise.columns]
    if len(cols_existentes) > 1:
        matriz_correlacao = df_analise[cols_existentes].corr()
    else:
        matriz_correlacao = None
    
    return df_analise, matriz_correlacao

def calcular_pontos_recompensa(df):
    pontos = 0
    conquistas = []
    
    if len(df) >= 7:
        ultimos_7 = df.tail(7)
        dias_consecutivos = (ultimos_7['Score_diario'] >= 70).sum()
        
        if dias_consecutivos >= 7:
            pontos += 100
            conquistas.append("🏆 7 dias consecutivos com score ≥70")
        
        if len(df) >= 14:
            media_primeira_semana = df['Score_diario'].iloc[-14:-7].mean()
            media_segunda_semana = df['Score_diario'].iloc[-7:].mean()
            if media_segunda_semana > media_primeira_semana + 5:
                pontos += 50
                conquistas.append("📈 Melhoria consistente")
    
    total_estudo = df['Estudo_min'].sum()
    if total_estudo > 10000:
        pontos += 50
        conquistas.append("📚 +10 mil minutos de estudo")
    
    total_treino = df['Treino_min'].sum()
    if total_treino > 3000:
        pontos += 30
        conquistas.append("💪 +3 mil minutos de treino")
    
    dias_organizados = df['Organizacao'].sum()
    if dias_organizados >= 30:
        pontos += 40
        conquistas.append("✅ +30 dias organizados")
    
    return pontos, conquistas

def previsao_tendencia(df):
    if len(df) >= 5:
        ultimos_scores = df['Score_diario'].tail(5).values
        x = np.arange(len(ultimos_scores))
        try:
            z = np.polyfit(x, ultimos_scores, 1)
            tendencia = z[0]
            
            if tendencia > 2:
                return "📈 Tendência positiva forte", "#10b981"
            elif tendencia > 0.5:
                return "↗️ Tendência positiva", "#34d399"
            elif tendencia < -2:
                return "📉 Tendência negativa forte", "#ef4444"
            elif tendencia < -0.5:
                return "↘️ Tendência negativa", "#f59e0b"
            else:
                return "➡️ Estável", "#94a3b8"
        except:
            return "⏳ Coletando dados...", "#94a3b8"
    return "⏳ Coletando dados...", "#94a3b8"

def carregar_metas():
    if 'metas' not in st.session_state:
        st.session_state.metas = {
            'estudo': 240,
            'treino': 60,
            'sono': 8.0,
            'score': 70,
            'nutricao': 7,
            'motivacao': 7,
            'organizacao': 5,
        }
    return st.session_state.metas

def verificar_metas(df, metas):
    if len(df) == 0:
        return {}
    
    ultima_semana = df.tail(7) if len(df) >= 7 else df
    
    return {
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

# --- Gráficos Aprimorados ---
def criar_grafico_linha_progresso(df):
    if len(df) < 2:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[formatar_data_curta(d) for d in df['Data']],
        y=df['Score_diario'],
        mode='lines+markers',
        name='Score Diário',
        line=dict(color='#6366f1', width=3),
        marker=dict(size=8, color='#6366f1', line=dict(width=2, color='#1e293b')),
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.1)',
        hovertemplate='%{x}<br>Score: %{y:.0f}<extra></extra>'
    ))
    
    if len(df) >= 7:
        df_temp = df.copy()
        df_temp['MA7'] = df_temp['Score_diario'].rolling(window=7).mean()
        fig.add_trace(go.Scatter(
            x=[formatar_data_curta(d) for d in df_temp['Data']],
            y=df_temp['MA7'],
            mode='lines',
            name='Média 7 dias',
            line=dict(color='#ec4899', width=2, dash='dash'),
            hovertemplate='%{x}<br>Média: %{y:.1f}<extra></extra>'
        ))
    
    fig.add_hline(y=70, line_dash="dot", line_color="#10b981", 
                  annotation_text="Meta", annotation_position="right")
    
    fig.update_layout(
        title=dict(text='Evolução do Score ao Longo do Tempo', font=dict(size=16, color='#f8fafc')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11),
            title='Data'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(148, 163, 184, 0.1)',
            range=[0, 105],
            tickfont=dict(size=11),
            title='Score'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='x unified'
    )
    
    return fig

def criar_grafico_comparativo(df):
    if len(df) < 2:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[formatar_data_curta(d) for d in df['Data']],
        y=df['Estudo_min'],
        name='Estudo (min)',
        marker_color='rgba(59, 130, 246, 0.6)',
        yaxis='y',
        hovertemplate='%{x}<br>Estudo: %{y} min<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=[formatar_data_curta(d) for d in df['Data']],
        y=df['Treino_min'],
        mode='lines+markers',
        name='Treino (min)',
        line=dict(color='#10b981', width=3),
        marker=dict(size=6),
        yaxis='y2',
        hovertemplate='%{x}<br>Treino: %{y} min<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text='Estudo vs Treino', font=dict(size=16, color='#f8fafc')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title='Minutos Estudo',
            showgrid=True,
            gridcolor='rgba(148, 163, 184, 0.1)',
            tickfont=dict(size=10)
        ),
        yaxis2=dict(
            title='Minutos Treino',
            overlaying='y',
            side='right',
            showgrid=False,
            tickfont=dict(size=10)
        ),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor='center'),
        margin=dict(l=0, r=0, t=40, b=0),
        barmode='group'
    )
    
    return fig

def criar_radar_performance(df):
    if len(df) == 0:
        return None
    
    last = df.iloc[-1]
    
    categories = ['Estudo', 'Treino', 'Sono', 'Nutrição', 'Motivação', 'Relações', 'Bem-estar']
    
    values = [
        min((last['Estudo_min'] / 240) * 10, 10),
        min((last['Treino_min'] / 60) * 10, 10),
        min(last['Sono_h'], 10),
        last['Nutricao'],
        last['Motivacao'],
        last['Relacoes'],
        last['Bem_estar']
    ]
    
    values += values[:1]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.2)',
        line=dict(color='#6366f1', width=2),
        name='Hoje'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[7]*8,
        theta=categories + [categories[0]],
        fill='none',
        line=dict(color='rgba(148, 163, 184, 0.3)', width=1, dash='dash'),
        name='Meta (7)',
        showlegend=True
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                showticklabels=False,
                gridcolor='rgba(148, 163, 184, 0.2)'
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color='#94a3b8'),
                gridcolor='rgba(148, 163, 184, 0.2)'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor='center'),
        margin=dict(l=40, r=40, t=20, b=40)
    )
    
    return fig

def criar_heatmap_semanal(df):
    if len(df) < 7:
        return None
    
    df_temp = df.copy()
    df_temp['Dia'] = pd.to_datetime(df_temp['Data']).dt.day_name()
    df_temp['Semana'] = pd.to_datetime(df_temp['Data']).dt.isocalendar().week
    
    pivot = df_temp.pivot_table(values='Score_diario', index='Semana', columns='Dia', aggfunc='mean')
    
    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dias_pt = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    pivot = pivot.reindex(columns=[d for d in dias_ordem if d in pivot.columns])
    
    fig = px.imshow(
        pivot,
        labels=dict(x="Dia da Semana", y="Semana", color="Score"),
        x=[dias_pt[dias_ordem.index(d)] for d in pivot.columns],
        color_continuous_scale=['#ef4444', '#f59e0b', '#10b981', '#6366f1'],
        aspect="auto"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    return fig

# --- Aplicação Principal ---
def main():
    apply_custom_styles()
    
    data_atual = date.today()
    data_formatada = formatar_data_extenso(data_atual)
    
    # Header com título atualizado
    st.markdown(f"""
    <div class="mobile-header">
        <h1>📓 Diário de Desenvolvimento</h1>
        <p>{data_formatada}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Menu")
        
        periodo = st.selectbox(
            "Período de Análise",
            ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todo o período"],
            index=1
        )
        
        st.markdown("---")
        
        if 'df' not in st.session_state:
            st.session_state.df = load_data()
        
        pontos, conquistas = calcular_pontos_recompensa(st.session_state.df)
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(236,72,153,0.2)); border-radius: 12px; margin-bottom: 1rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🏆</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #f8fafc;">{pontos}</div>
            <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">Pontos</div>
        </div>
        """, unsafe_allow_html=True)
        
        if conquistas:
            with st.expander("🎖️ Conquistas"):
                for c in conquistas:
                    st.success(c)
        
        st.markdown("---")
        st.caption(f"📊 {len(st.session_state.df)} registros")
        st.caption("Diário de Desenvolvimento v1.0")

    # Carregar dados
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    df_full = st.session_state.df

    # Filtrar por período
    if not df_full.empty:
        hoje = date.today()
        if periodo == "Últimos 7 dias":
            df = df_full[df_full['Data'] > hoje - timedelta(days=7)]
        elif periodo == "Últimos 30 dias":
            df = df_full[df_full['Data'] > hoje - timedelta(days=30)]
        elif periodo == "Últimos 90 dias":
            df = df_full[df_full['Data'] > hoje - timedelta(days=90)]
        else:
            df = df_full
    else:
        df = df_full

    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📝 Registro", "🎯 Metas", "📈 Análises"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        if not df.empty and len(df) > 0:
            last = df.iloc[-1]
            data_ultimo_registro = formatar_data_extenso(last['Data'])
            
            # KPIs principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta = ""
                if len(df) > 1:
                    diff = last['Score_diario'] - df.iloc[-2]['Score_diario']
                    delta = f"{'+' if diff >= 0 else ''}{diff:.0f} pts"
                metric_card_modern("Score Hoje", f"{last['Score_diario']:.0f}", delta, "🎯", featured=True, delay=0)
            
            with col2:
                total_estudo = df['Estudo_min'].sum()
                horas = total_estudo / 60
                metric_card_modern("Total Estudo", f"{horas:.1f}h", f"{total_estudo} min", "📚", delay=100)
            
            with col3:
                total_treino = df['Treino_min'].sum()
                metric_card_modern("Total Treino", f"{total_treino} min", "Acumulado", "💪", delay=200)
            
            with col4:
                media_sono = df['Sono_h'].mean()
                metric_card_modern("Média Sono", f"{media_sono:.1f}h", "Qualidade", "😴", delay=300)

            st.markdown(f"<p style='color: #94a3b8; font-size: 0.875rem; margin-top: 1rem;'>Último registro: {data_ultimo_registro}</p>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Gráfico principal de linha
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">📈 Progresso ao Longo do Tempo</div>', unsafe_allow_html=True)
            
            fig_linha = criar_grafico_linha_progresso(df)
            if fig_linha:
                st.plotly_chart(fig_linha, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Grid de gráficos secundários
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">🕸️ Performance Atual</div>', unsafe_allow_html=True)
                fig_radar = criar_radar_performance(df)
                if fig_radar:
                    st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_right:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">⚡ Estudo vs Treino</div>', unsafe_allow_html=True)
                fig_comp = criar_grafico_comparativo(df)
                if fig_comp:
                    st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # Heatmap semanal
            if len(df) >= 7:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">🔥 Mapa de Calor Semanal</div>', unsafe_allow_html=True)
                fig_heat = criar_heatmap_semanal(df)
                if fig_heat:
                    st.plotly_chart(fig_heat, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # Insights
            st.markdown("#### 💡 Insights")
            tendencia, cor = previsao_tendencia(df)
            
            cols = st.columns(3)
            with cols[0]:
                st.info(f"**Tendência:** {tendencia}")
            with cols[1]:
                if len(df) >= 7:
                    media_7 = df.tail(7)['Score_diario'].mean()
                    st.info(f"**Média 7 dias:** {media_7:.1f} pts")
            with cols[2]:
                melhor_dia = df.loc[df['Score_diario'].idxmax()]
                data_melhor = formatar_data_extenso(melhor_dia['Data'])
                st.info(f"**Recorde:** {melhor_dia['Score_diario']:.0f} pts ({formatar_data_curta(melhor_dia['Data'])})")

        else:
            st.info("👈 Comece registrando seus dados na aba 'Registro'!")

    # --- TAB 2: REGISTRO ---
    with tab2:
        col_form, _ = st.columns([0.7, 0.3])
        
        with col_form:
            st.markdown("### 📝 Novo Registro Diário")
            data_hoje = date.today()
            st.markdown(f"<p style='color: #94a3b8; margin-bottom: 1rem;'>Data de hoje: {formatar_data_extenso(data_hoje)}</p>", unsafe_allow_html=True)
            
            with st.form("entry_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**⏱️ Métricas Quantitativas**")
                    data_input = st.date_input("Data do registro", date.today())
                    estudo_min = st.number_input("📚 Estudo (minutos)", 0, 1440, 60, step=10)
                    treino_min = st.number_input("💪 Treino (minutos)", 0, 300, 45, step=5)
                    sono_h = st.slider("😴 Sono (horas)", 0.0, 12.0, 7.0, 0.5)
                
                with col2:
                    st.markdown("**🧠 Métricas Qualitativas (1-10)**")
                    bem_estar = st.slider("Bem-estar", 1, 10, 7)
                    nutricao = st.slider("Nutrição", 1, 10, 7)
                    motivacao = st.slider("Motivação", 1, 10, 7)
                    relacoes = st.slider("Relacionamentos", 1, 10, 7)
                    organizacao = st.toggle("✅ Dia organizado?", value=True)
                
                st.markdown("---")
                observacoes = st.text_area("📝 Observações do dia", placeholder="Como foi seu dia? Alguma conquista ou dificuldade?", height=100)
                
                submitted = st.form_submit_button("💾 Salvar Registro", type="primary", use_container_width=True)
                
                if submitted:
                    entry = {
                        "Data": data_input,
                        "Estudo_min": estudo_min,
                        "Organizacao": 1 if organizacao else 0,
                        "Treino_min": treino_min,
                        "Bem_estar": bem_estar,
                        "Sono_h": sono_h,
                        "Nutricao": nutricao,
                        "Motivacao": motivacao,
                        "Relacoes": relacoes,
                        "Observacoes": observacoes
                    }
                    
                    with st.spinner("Salvando..."):
                        if save_entry_google(entry):
                            st.cache_data.clear()
                            st.session_state.df = load_data()
                            st.success(f"✅ Registro de {formatar_data_extenso(data_input)} salvo com sucesso!")
                            st.balloons()
                            st.rerun()

    # --- TAB 3: METAS ---
    with tab3:
        st.markdown("### 🎯 Configuração de Metas")
        
        metas = carregar_metas()
        
        col_meta, col_prog = st.columns([0.5, 0.5])
        
        with col_meta:
            with st.form("metas_form"):
                st.markdown("**📚 Metas Diárias**")
                meta_estudo = st.number_input("Meta Estudo (min/dia)", 0, 1440, metas['estudo'])
                meta_treino = st.number_input("Meta Treino (min/dia)", 0, 300, metas['treino'])
                meta_sono = st.slider("Meta Sono (h/dia)", 4.0, 12.0, metas['sono'], 0.5)
                
                st.markdown("**🎯 Metas de Performance**")
                meta_score = st.slider("Score Mínimo", 0, 100, metas['score'])
                meta_org = st.slider("Dias Organizados/Semana", 0, 7, metas['organizacao'])
                
                if st.form_submit_button("💾 Atualizar Metas", use_container_width=True):
                    st.session_state.metas = {
                        'estudo': meta_estudo,
                        'treino': meta_treino,
                        'sono': meta_sono,
                        'score': meta_score,
                        'nutricao': metas['nutricao'],
                        'motivacao': metas['motivacao'],
                        'organizacao': meta_org
                    }
                    st.success("Metas atualizadas!")
        
        with col_prog:
            st.markdown("**📊 Progresso nas Metas**")
            
            if len(df) > 0:
                resultados = verificar_metas(df, st.session_state.metas)
                
                for key, val in resultados.items():
                    emoji = {"estudo": "📚", "treino": "💪", "sono": "😴", "score": "🎯", "organizacao": "✅"}.get(key, "•")
                    
                    progresso = min((val['real'] / val['meta']) * 100, 100)
                    status = "✅" if val['atingido'] else "⏳"
                    cor = "#10b981" if val['atingido'] else "#6366f1"
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span style="color: #f8fafc; font-weight: 600;">{emoji} {key.title()}</span>
                            <span style="color: {cor}; font-weight: 700;">{status} {val['real']:.1f}/{val['meta']}</span>
                        </div>
                        <div style="background: #334155; border-radius: 8px; height: 8px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, {cor}, {cor}aa); width: {progresso}%; height: 100%; border-radius: 8px; transition: width 0.5s;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Adicione registros para ver o progresso!")

    # --- TAB 4: ANÁLISES ---
    with tab4:
        st.markdown("### 📈 Análises Detalhadas")
        
        col_dados, col_export = st.columns([0.7, 0.3])
        
        with col_dados:
            st.markdown("**📋 Histórico Completo**")
            
            # Preparar dataframe para exibição com data formatada
            df_display = df_full.copy()
            df_display['Data_Formatada'] = df_display['Data'].apply(formatar_data_extenso)
            df_display = df_display.sort_values(by="Data", ascending=False)
            
            st.dataframe(
                df_display[['Data_Formatada', 'Score_diario', 'Estudo_min', 'Treino_min', 'Sono_h', 'Observacoes']].style.background_gradient(subset=['Score_diario'], cmap='viridis'),
                use_container_width=True,
                height=400,
                column_config={
                    "Data_Formatada": "Data",
                    "Score_diario": "Score",
                    "Estudo_min": "Estudo (min)",
                    "Treino_min": "Treino (min)",
                    "Sono_h": "Sono (h)",
                    "Observacoes": "Observações"
                }
            )
        
        with col_export:
            st.markdown("**💾 Exportar Dados**")
            
            # Adicionar data formatada ao CSV
            df_export = df_full.copy()
            df_export['Data_Extenso'] = df_export['Data'].apply(formatar_data_extenso)
            
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                csv,
                "diario_desenvolvimento.csv",
                "text/csv",
                use_container_width=True
            )
            
            json_data = df_export.to_json(orient='records', indent=2)
            st.download_button(
                "📊 Download JSON",
                json_data,
                "diario_desenvolvimento.json",
                "application/json",
                use_container_width=True
            )
            
            st.markdown("---")
            
            if len(df) > 0:
                st.markdown("**📊 Estatísticas**")
                st.metric("Melhor Score", f"{df['Score_diario'].max():.0f}")
                st.metric("Média Geral", f"{df['Score_diario'].mean():.1f}")
                st.metric("Total Registros", len(df))

if __name__ == "__main__":
    main()
