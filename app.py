import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import os
import re
import pandas as pd
import urllib.parse
from datetime import datetime
from fpdf import FPDF
from pymongo import MongoClient

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- CONEXÃO MONGODB BLINDADA ---
@st.cache_resource
def iniciar_conexao():
    try:
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        password = urllib.parse.quote_plus(password_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        client.admin.command('ping')
        return client['technoboltgym']
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    .result-card-unificado { 
        background-color: #0d0d0d !important; border-left: 5px solid #3b82f6;
        border-radius: 12px; padding: 25px; margin-top: 15px; border: 1px solid #1a1a1a;
        line-height: 1.7; color: #e0e0e0;
    }
    .result-card-unificado b, .result-card-unificado strong { color: #3b82f6; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #3b82f6 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- UTILITÁRIOS E PDF ---
def gerar_pdf_elite(nome, conteudo, titulo, data_analise):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"TECHNOBOLT - LAUDO TECNICO: {titulo.upper()}", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Paciente/Atleta: {nome} | Data: {data_analise}", ln=True, align='C')
    pdf.ln(10)
    
    texto = conteudo.replace('**', '').replace('###', '').replace('🚀', '').replace('•', '-')
    pdf.multi_cell(0, 7, texto.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf_out = pdf.output(dest='S')
    return bytes(pdf_out, 'latin-1') if isinstance(pdf_out, str) else bytes(pdf_out)

# --- MOTOR DE IA ---
def realizar_scan_phd(prompt, img_pil):
    img_byte_arr = io.BytesIO(); img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    for key in chaves:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            response = model.generate_content([prompt, img_blob])
            return response.text
        except: continue
    return None

# --- ACESSO ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    t1, t2 = st.tabs(["🔐 Login", "📝 Cadastro"])
    with t1:
        u = st.text_input("User").lower().strip(); p = st.text_input("Pass", type="password")
        if st.button("ACESSAR HUB"):
            udata = db.usuarios.find_one({"usuario": u})
            if udata and udata['senha'] == p and udata['status'] == 'ativo':
                st.session_state.logado = True; st.session_state.user_atual = u; st.session_state.is_admin = udata.get('is_admin', False); st.rerun()
            else: st.error("Acesso negado.")
    with t2:
        n_n = st.text_input("Nome"); n_u = st.text_input("Login").lower().strip(); n_p = st.text_input("Senha", type="password")
        if st.button("CADASTRAR"):
            if n_n and n_u and n_p:
                db.usuarios.insert_one({"usuario": n_u, "senha": n_p, "nome": n_n, "status": "pendente", "avaliacoes_restantes": 0, "historico_dossies": []})
                st.success("Solicitado!")
    st.stop()

user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})

# ADMIN
if st.session_state.is_admin:
    with st.expander("🛠️ ADMIN PANEL"):
        for usr in list(db.usuarios.find({"usuario": {"$ne": "admin"}})):
            c1, c2, c3 = st.columns([2, 2, 2])
            c1.write(usr['usuario'])
            if c2.button(f"Ativar/Renovar {usr['usuario']}", key=usr['usuario']):
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"status": "ativo", "avaliacoes_restantes": 4}}); st.rerun()

# --- SIDEBAR & DASHBOARD ---
with st.sidebar:
    st.title("TechnoBolt Gym")
    st.write(f"Créditos: {user_doc.get('avaliacoes_restantes', 0)}")
    if st.button("LOGOUT"): st.session_state.logado = False; st.rerun()
    
    if user_doc.get('historico_dossies'):
        st.divider()
        st.subheader("📈 Evolução Biométrica")
        pesos = [a.get('peso_reg', 80) for a in user_doc['historico_dossies']]
        datas = [a['data'].split()[0] for a in user_doc['historico_dossies']]
        if len(pesos) > 1:
            df_evolucao = pd.DataFrame({"Data": datas, "Peso (kg)": pesos})
            st.line_chart(df_evolucao.set_index("Data"))
    
    st.divider()
    peso_atual = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    altura = st.number_input("Altura (cm)", 100, 250, 175)
    obj = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    res_alim = st.text_area("Restrições Alimentares", "Nenhuma")
    res_med = st.text_area("Medicamentos em Uso", "Nenhum")
    res_fis = st.text_area("Restrições Físicas/Lesões", "Nenhuma")
    up = st.file_uploader("📸 Scanner de Imagem", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO ---
if up and st.button("🚀 INICIAR ANALISE CLINICA"):
    if user_doc.get('avaliacoes_restantes', 0) > 0 or st.session_state.is_admin:
        with st.status("🧬 PROCESSANDO LAUDO..."):
            img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            img.thumbnail((600, 600)); imc = peso_atual / ((altura/100)**2)
            
            prompt_mestre = f"""VOCÊ É UM CONSELHO TÉCNICO DE ESPECIALISTAS PHD. 
            PACIENTE/ATLETA: {user_doc['nome']} | OBJETIVO: {obj} | IMC: {imc:.2f}
            RESTRIÇÕES: Alimentar: {res_alim} | Médica: {res_med} | Física: {res_fis}

            ESCREVA 4 RELATÓRIOS TÉCNICOS ABAIXO DAS SEGUINTES TAGS. 
            NÃO USE SAUDAÇÕES OU TÍTULOS REPETITIVOS. 
            USE LINGUAGEM ESTRITAMENTE TÉCNICA E PROFISSIONAL (LAUDO CLÍNICO).
            EXPLIQUE TODOS OS TERMOS TÉCNICOS ENTRE PARÊNTESES DE FORMA INTUITIVA.

            [AVALIACAO]
            PhD em Antropometria (ISAK 4). Analise a cineantropometria (estudo das medidas humanas) para determinar o somatotipo predominante (tipo físico), BF% (percentual de gordura) e desvios cinemáticos (erros de movimento) ou posturais. 
            Considere restrição física: {res_fis}. 
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações técnicas para maximizar a homeostase (equilíbrio interno) e estética funcional.

            [NUTRICAO]
            PhD em Nutrologia e Metabolismo. Prescreva planejamento dietético extenso (2 alternativas por refeição). 
            Respeite RIGOROSAMENTE as restrições alimentares: {res_alim}. 
            Explique termos como Termogênese Induzida pela Dieta (energia gasta na digestão) e Densidade Nutricional (riqueza de nutrientes por caloria).
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações para otimizar a síntese proteica (construção de tecido) e aporte energético.

            [SUPLEMENTACAO]
            PhD em Farmacologia Aplicada. Prescreva de 3 a 10 suplementos via Nexo Metabólico (conexão entre processos químicos).
            Verifique interações com: {res_med}. Explique Biodisponibilidade (taxa de absorção do nutriente) e Sinergismo Nutricional (quando substâncias potencializam uma à outra).
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações sobre o 'timing' nutricional e empilhamento ergogênico (substâncias que aumentam performance).

            [TREINO]
            PhD em Biomecânica e Fisiologia do Exercício. Prescreva protocolo de 7 dias (8-10 exerc/dia). 
            Adapte para: {res_fis}. Estrutura: NOME DO EXERCÍCIO | SÉRIES | REPS | JUSTIFICATIVA BIOMECÂNICA (SEM TABELAS).
            Explique Braço de Momento (distância da alavanca de força) e Tensão Mecânica (estresse físico nas fibras).
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações sobre cadência (velocidade do movimento) e recrutamento de unidades motoras.
            """
            
            res = realizar_scan_phd(prompt_mestre, img)
            if res:
                def ext(ti, tp=None):
                    p = f"\\{ti}\\s*(.*?)\\s*(?=\\{tp}|$)" if tp else f"\\{ti}\\s*(.*)"
                    m = re.search(p, res, re.DOTALL | re.IGNORECASE)
                    return m.group(1).strip() if m else "..."
                
                analise = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "peso_reg": peso_atual,
                    "r1": ext("[AVALIACAO]", "[NUTRICAO]"), "r2": ext("[NUTRICAO]", "[SUPLEMENTACAO]"),
                    "r3": ext("[SUPLEMENTACAO]", "[TREINO]"), "r4": ext("[TREINO]", None)
                }
                db.usuarios.update_one({"usuario": st.session_state.user_atual}, {
                    "$push": {"historico_dossies": analise},
                    "$inc": {"avaliacoes_restantes": -1} if not st.session_state.is_admin else {"avaliacoes_restantes": 0}
                })
                st.rerun()

# --- EXIBIÇÃO ---
if user_doc.get('historico_dossies'):
    hist = user_doc['historico_dossies']
    sel = st.selectbox("📅 Consultar Laudos Anteriores", [a['data'] for a in reversed(hist)])
    d = next(a for a in hist if a['data'] == sel)
    tabs = st.tabs(["📊 Antropometria", "🥗 Nutrologia", "💊 Suplementação", "🏋️ Biomecânica", "📜 Laudo Completo"])
    cs = [d['r1'], d['r2'], d['r3'], d['r4']]; ts = ["Antropometria", "Nutrologia", "Suplementacao", "Biomecanica"]
    for i, tab in enumerate(tabs[:4]):
        with tab:
            st.markdown(f"<div class='result-card-unificado'>{cs[i].replace('\n', '<br>')}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 Baixar PDF {ts[i]}", data=gerar_pdf_elite(user_doc['nome'], cs[i], ts[i], d['data']), file_name=f"{ts[i]}.pdf", key=f"{ts[i]}_{sel}")
    with tabs[4]:
        f_t = f"LAUDO ANTROPOMÉTRICO:\n{d['r1']}\n\nLAUDO NUTROLÓGICO:\n{d['r2']}\n\nLAUDO DE SUPLEMENTAÇÃO:\n{d['r3']}\n\nLAUDO BIOMECÂNICO:\n{d['r4']}"
        st.markdown(f"<div class='result-card-unificado'>{f_t.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
        st.download_button("📥 BAIXAR LAUDO COMPLETO", data=gerar_pdf_elite(user_doc['nome'], f_t, "Laudo Completo", d['data']), file_name="Laudo_Completo.pdf", key=f"f_{sel}")
