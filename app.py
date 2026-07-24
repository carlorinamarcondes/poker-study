import streamlit as st
from supabase import create_client, Client
from openai import OpenAI

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

# Inicializa clientes
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Poker Study Buddy")
st.caption("Revisao com IA e biblioteca pessoal de estudo")

aba_revisao, aba_biblioteca = st.tabs(
    ["Nova Revisao", "Biblioteca de Maos"]
)

with aba_revisao:
    st.subheader("Registrar uma mao para estudo")

    with st.sidebar:
        st.header("Configuracoes")
        modalidade = st.selectbox("Modalidade", ["Cash Game", "MTT", "Spin & Go"])
        hero_pos = st.selectbox("Posicao", ["SB", "BB", "UTG", "MP", "CO", "BTN"])
        effective_stack = st.number_input("Stack (BBs)", min_value=1, value=100)

    col1, col2 = st.columns(2)

    with col1:
        st.header("Cartas e board")
        hand_cards = st.text_input("Suas cartas", placeholder="Ex.: Ad Ks")
        flop = st.text_input("Flop", placeholder="Ex.: 2h 7s 9c")
        turn = st.text_input("Turn", placeholder="Ex.: Jh")
        river = st.text_input("River", placeholder="Ex.: As")

    with col2:
        st.header("Acao e Analise")
        action_history = st.text_area("Descricao da acao", height=150)
        user_question = st.text_area("Sua dúvida principal?")
        
    st.divider()
    
    col_btn1, col_btn2 = st.columns(2)
    
    analise_ia = ""

    with col_btn1:
        if st.button("🚀 Analisar com IA", type="secondary"):
            if hand_cards and action_history:
                with st.spinner("O treinador está pensando..."):
                    try:
                        prompt = f"""
                        Voce é um treinador de poker profissional. Analise a seguinte jogada:
                        Modalidade: {modalidade}
                        Posicao do Hero: {hero_pos}
                        Stack Efetivo: {effective_stack} BBs
                        Mao do Hero: {hand_cards}
                        Board: {flop} / {turn} / {river}
                        Acao descrita: {action_history}
                        Duda do jogador: {user_question}
                        
                        Forneça uma análise técnica, mencionando range, equidade e se a linha escolhida foi lucrativa.
                        Seja direto e use termos de poker.
                        """
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "system", "content": "Voce é um expert em poker."},
                                      {"role": "user", "content": prompt}]
                        )
                        analise_ia = response.choices[0].message.content
                        st.info(analise_ia)
                    except Exception as e:
                        st.error(f"Erro na análise: {e}")
            else:
                st.warning("Preencha a mão e a ação para analisar.")

    with col_btn2:
        if st.button("💾 Salvar na Biblioteca", type="primary"):
            try:
                data = {
                    "modalidade": modalidade,
                    "posicao": hero_pos,
                    "stack": effective_stack,
                    "cartas": hand_cards,
                    "flop": flop, "turn": turn, "river": river,
                    "acao": action_history,
                    "duvida": user_question,
                    "aprendizado": analise_ia # Salva a analise da IA se existir
                }
                supabase.table("maos").insert(data).execute()
                st.success("Mao salva com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

with aba_biblioteca:
    st.subheader("Suas maos salvas")
    try:
        res = supabase.table("maos").select("*").order("created_at", desc=True).execute()
        for mao in res.data:
            with st.expander(f"{mao['created_at'][:10]} | {mao['cartas']} | {mao['posicao']}"):
                st.write(f"**Acao:** {mao['acao']}")
                st.write(f"**Analise/Aprendizado:** {mao['aprendizado']}")
    except Exception as e:
        st.error(f"Erro: {e}")
