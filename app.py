import streamlit as st
from supabase import create_client, Client

# Configuração das credenciais (puxando dos Secrets)
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

st.title("♠️ Poker Study Buddy")
st.subheader("Ferramenta de Revisão de Mãos")

with st.sidebar:
    st.header("Configurações")
    modalidade = st.selectbox("Modalidade", ["Cash Game", "MTT", "Spin & Go"])
    hero_pos = st.selectbox("Posição", ["SB", "BB", "UTG", "MP", "CO", "BTN"])
    effective_stack = st.number_input("Stack (BBs)", value=100)

col1, col2 = st.columns(2)

with col1:
    st.header("🃏 A Mão")
    hand_cards = st.text_input("Suas Cartas", placeholder="Ad Ks")
    flop = st.text_input("Flop", placeholder="2h 7s 9c")
    turn = st.text_input("Turn")
    river = st.text_input("River")

with col2:
    st.header("📑 Ação e Dúvida")
    action_history = st.text_area("Descrição da ação")
    user_question = st.text_area("O que te deixou em dúvida?")

st.divider()

if st.button("🚀 Salvar Revisão"):
    if hand_cards and action_history:
        try:
            # Prepara os dados para o Supabase
            data = {
                "modalidade": modalidade,
                "posicao": hero_pos,
                "stack": effective_stack,
                "cartas": hand_cards,
                "flop": flop,
                "turn": turn,
                "river": river,
                "acao": action_history,
                "duvida": user_question
            }
            
            # Tenta inserir na tabela 'maos'
            response = supabase.table("maos").insert(data).execute()
            
            st.success("✅ Mão salva com sucesso no banco de dados!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
    else:
        st.warning("Preencha as cartas e a ação antes de salvar.")
