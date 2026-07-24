import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("Poker Study Buddy")
st.caption("Revisao pos-jogo e biblioteca pessoal de estudo")

aba_revisao, aba_biblioteca = st.tabs(
    ["Nova Revisao", "Biblioteca de Maos"]
)

with aba_revisao:
    st.subheader("Registrar uma mao para estudo")

    with st.sidebar:
        st.header("Configuracoes da mao")
        modalidade = st.selectbox(
            "Modalidade",
            ["Cash Game", "MTT", "Spin & Go"]
        )
        hero_pos = st.selectbox(
            "Posicao do Hero",
            ["SB", "BB", "UTG", "MP", "CO", "BTN"]
        )
        effective_stack = st.number_input(
            "Stack efetivo (BBs)",
            min_value=1,
            value=100
        )

    col1, col2 = st.columns(2)

    with col1:
        st.header("Cartas e board")
        hand_cards = st.text_input(
            "Suas cartas",
            placeholder="Ex.: Ad Ks",
            help="Use: s = espadas, h = copas, d = ouros, c = paus."
        )
        flop = st.text_input("Flop", placeholder="Ex.: 2h 7s 9c")
        turn = st.text_input("Turn", placeholder="Ex.: Jh")
        river = st.text_input("River", placeholder="Ex.: As")

    with col2:
        st.header("Acao e reflexao")
        action_history = st.text_area(
            "Descricao da acao",
            placeholder="Ex.: Abri 2.5 BB do BTN, BB pagou. No flop, BB deu check, apostei 33% do pote...",
            height=150
        )
        user_question = st.text_area(
            "O que te deixou em duvida?",
            placeholder="Ex.: Devo continuar apostando no turn ou dar check-back?"
        )
        tags = st.text_input(
            "Tags",
            placeholder="Ex.: BTN vs BB, SRP, c-bet, turn"
        )
        aprendizado = st.text_area(
            "Licao/aprendizado",
            placeholder="Preencha depois da revisao."
        )

    if st.button("Salvar revisao", type="primary"):
        if hand_cards.strip() and action_history.strip():
            try:
                data = {
                    "modalidade": modalidade,
                    "posicao": hero_pos,
                    "stack": effective_stack,
                    "cartas": hand_cards.strip(),
                    "flop": flop.strip(),
                    "turn": turn.strip(),
                    "river": river.strip(),
                    "acao": action_history.strip(),
                    "duvida": user_question.strip(),
                    "tags": tags.strip(),
                    "aprendizado": aprendizado.strip()
                }

                supabase.table("maos").insert(data).execute()
                st.success("Mao salva na biblioteca com sucesso!")
                st.balloons()

            except Exception as error:
                st.error(f"Erro ao salvar: {error}")
        else:
            st.warning("Preencha pelo menos as suas cartas e a descricao da acao.")

with aba_biblioteca:
    st.subheader("Suas maos salvas")

    try:
        resposta = (
            supabase
            .table("maos")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        maos = resposta.data

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

                    st.write("**Acao**")
                    st.write(mao.get("acao") or "-")
                    st.write("**Duvida**")
                    st.write(mao.get("duvida") or "-")
                    st.write("**Tags**")
                    st.write(mao.get("tags") or "-")
                    st.write("**Aprendizado**")
                    st.write(mao.get("aprendizado") or "-")

    except Exception as error:
        st.error(f"Nao foi possivel carregar a biblioteca: {error}")
