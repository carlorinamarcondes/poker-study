import streamlit as st

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

st.title("♠️ Poker Study Buddy")
st.subheader("Ferramenta de Revisão de Mãos para Estudantes de Poker")

with st.sidebar:
    st.header("Configurações da Sessão")
    modalidade = st.selectbox("Modalidade", ["Cash Game", "MTT (Torneio)", "Spin & Go"])
    hero_pos = st.selectbox("Posição do Hero", ["SB", "BB", "UTG", "MP", "CO", "BTN"])
    effective_stack = st.number_input("Stack Efetivo (em BBs)", value=100)

col1, col2 = st.columns(2)

with col1:
    st.header("🃏 A Mão")
    hand_cards = st.text_input("Suas Cartas (ex: Ad Ks)", placeholder="Ad Ks")
    
    st.header("🏟️ O Board")
    flop = st.text_input("Flop (ex: 2h 7s 9c)", placeholder="2h 7s 9c")
    turn = st.text_input("Turn", placeholder="Jh")
    river = st.text_input("River", placeholder="As")

with col2:
    st.header("📑 Ação e Dúvida")
    action_history = st.text_area("Descreva a ação (ex: Abri 2.5bb do BTN, BB deu call...)", height=150)
    user_question = st.text_area("O que te deixou em dúvida?", placeholder="Ex: Devo barrilar esse turn ou dar check-back?")

st.divider()

if st.button("🚀 Salvar e Analisar com IA"):
    if hand_cards and action_history:
        st.success("Mão salva na biblioteca!")
        st.info("Aqui entrará a integração com a IA para analisar os conceitos de Poker envolvidos.")
        
        with st.expander("Ver rascunho de análise conceitual", expanded=True):
            st.markdown(f"""
            ### Pré-Análise do Spot:
            - **Range de {hero_pos}:** Seu range tem vantagem em boards com cartas altas.
            - **SPR:** O stack efetivo de {effective_stack}BB dita a agressividade.
            - **Ponto de Atenção:** "{user_question}"
            """)
    else:
        st.warning("Por favor, preencha pelo menos suas cartas e a descrição da ação.")

st.sidebar.divider()
st.sidebar.write("Total de mãos revisadas hoje: 0")
