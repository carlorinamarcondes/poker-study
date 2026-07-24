import streamlit as st
from supabase import create_client, Client
from openai import OpenAI

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

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
        opponent_cards = st.text_input(
            "Cartas do oponente",
            placeholder="Ex.: Qh Jd (deixe em branco se nao souber)"
        )
        flop = st.text_input("Flop", placeholder="Ex.: 2h 7s 9c")
        turn = st.text_input("Turn", placeholder="Ex.: Jh")
        river = st.text_input("River", placeholder="Ex.: As")

    with col2:
        st.header("Acao e Analise")
        action_history = st.text_area("Descricao da acao", height=150)
        user_question = st.text_area("Sua duvida principal?")

    st.divider()

    col_btn1, col_btn2 = st.columns(2)

    analise_ia = ""

    with col_btn1:
        if st.button("Analisar com IA", type="secondary"):
            if hand_cards and action_history:
                with st.spinner("O treinador esta pensando..."):
                    try:
                        prompt = f"""
                        Voce e um treinador de poker profissional. Analise a seguinte jogada:
                        Modalidade: {modalidade}
                        Posicao do Hero: {hero_pos}
                        Stack Efetivo: {effective_stack} BBs
                        Mao do Hero: {hand_cards}
                        Cartas do oponente: {opponent_cards if opponent_cards else "Desconhecidas"}
                        Board: {flop} / {turn} / {river}
                        Acao descrita: {action_history}
                        Duvida do jogador: {user_question}

                        Forneca uma analise tecnica, mencionando range, equidade e se a linha escolhida foi lucrativa.
                        Seja direto e use termos de poker.
                        """

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Voce e um expert em poker."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        analise_ia = response.choices[0].message.content
                        st.info(analise_ia)
                    except Exception as e:
                        st.error(f"Erro na analise: {e}")
            else:
                st.warning("Preencha a mao e a acao para analisar.")

    with col_btn2:
        if st.button("Salvar na Biblioteca", type="primary"):
            if hand_cards and action_history:
                try:
                    data = {
                        "modalidade": modalidade,
                        "posicao": hero_pos,
                        "stack": effective_stack,
                        "cartas": hand_cards,
                        "cartas_oponente": opponent_cards,
                        "flop": flop,
                        "turn": turn,
                        "river": river,
                        "acao": action_history,
                        "duvida": user_question,
                        "aprendizado": analise_ia
                    }
                    supabase.table("maos").insert(data).execute()
                    st.success("Mao salva com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha pelo menos as suas cartas e a descricao da acao.")

with aba_biblioteca:
    st.subheader("Suas maos salvas")
    try:
        res = supabase.table("maos").select("*").order("created_at", desc=True).execute()
        maos = res.data

        if not maos:
            st.info("Ainda nao ha maos salvas. Registre a primeira na aba Nova Revisao.")
        else:
            st.metric("Total de maos salvas", len(maos))

            for mao in maos:
                data_salva = mao.get("created_at", "")[:10]
                titulo = (
                    f"{data_salva} | {mao.get('cartas', '-')} "
                    f"| {mao.get('posicao', '-')} "
                    f"| {mao.get('modalidade', '-')}"
                )

                with st.expander(titulo):
                    d1, d2, d3 = st.columns(3)
                    d1.write(f"**Stack:** {mao.get('stack', '-')} BB")
                    d2.write(f"**Flop:** {mao.get('flop') or '-'}")
                    d3.write(f"**Turn/River:** {mao.get('turn') or '-'} / {mao.get('river') or '-'}")

                    st.write(f"**Cartas do oponente:** {mao.get('cartas_oponente') or 'Desconhecidas'}")
                    st.write(f"**Acao:** {mao.get('acao') or '-'}")
                    st.write(f"**Duvida:** {mao.get('duvida') or '-'}")
                    st.write(f"**Analise/Aprendizado:** {mao.get('aprendizado') or '-'}")

    except Exception as e:
        st.error(f"Erro ao carregar biblioteca: {e}")
