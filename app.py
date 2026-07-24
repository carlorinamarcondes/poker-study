import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

# Credenciais guardadas nos Secrets do Streamlit Cloud
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("♠️ Poker Study Buddy")
st.caption("Revisão pós-jogo e biblioteca pessoal de estudo")

aba_revisao, aba_biblioteca = st.tabs(
    ["📝 Nova Revisão", "📚 Biblioteca de Mãos"]
)

with aba_revisao:
    st.subheader("Registrar uma mão para estudo")

    with st.sidebar:
        st.header("Configurações da mão")
        modalidade = st.selectbox(
            "Modalidade",
            ["Cash Game", "MTT", "Spin & Go"]
        )
        hero_pos = st.selectbox(
            "Posição do Hero",
            ["SB", "BB", "UTG", "MP", "CO", "BTN"]
        )
        effective_stack = st.number_input(
            "Stack efetivo (BBs)",
            min_value=1,
            value=100
        )

    col1, col2 = st.columns(2)

    with col1:
        st.header("🃏 Cartas e board")
        hand_cards = st.text_input(
            "Suas cartas",
            placeholder="Ex.: Ad Ks",
            help="Use: s = espadas, h = copas, d = ouros, c = paus."
        )
        flop = st.text_input(
            "Flop",
            placeholder="Ex.: 2h 7s 9c"
        )
        turn = st.text_input(
            "Turn",
            placeholder="Ex.: Jh"
        )
        river = st.text_input(
            "River",
            placeholder="Ex.: As"
        )

    with col2:
        st.header("📑 Ação e reflexão")
        action_history = st.text_area(
            "Descrição da ação",
            placeholder=(
                "Ex.: Abri 2,5 B
