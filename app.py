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
        st.header("Hero e board")

        hand_cards = st.text_input(
            "Suas cartas",
            placeholder="Ex.: Ad Ks"
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
        st.header("Oponente")

        opponent_position = st.selectbox(
            "Posicao do oponente",
            ["Desconhecida", "SB", "BB", "UTG", "MP", "CO", "BTN"]
        )

        opponent_stack = st.number_input(
            "Stack do oponente (BBs)",
            min_value=0,
            value=100
        )

        opponent_cards = st.text_input(
            "Cartas do oponente",
            placeholder="Ex.: Qh Jd (deixe vazio se nao houve showdown)"
        )

    st.subheader("Acao e duvida")

    action_history = st.text_area(
        "Sua acao / linha completa da mao",
        placeholder=(
            "Ex.: Hero abre 2.5 BB no BTN. BB paga. "
            "Flop: BB check, Hero aposta 33% do pote, BB paga. "
            "Turn: BB check..."
        ),
        height=150
    )

    opponent_action = st.text_area(
        "Acao do oponente",
        placeholder=(
            "Ex.: BB pagou pre-flop, deu check no flop, "
            "pagou a c-bet e deu check no turn."
        ),
        height=120
    )

    user_question = st.text_area(
        "Sua duvida principal",
        placeholder="Ex.: Devo apostar no turn ou dar check-back?"
    )

    st.divider()

    if "analise_ia" not in st.session_state:
        st.session_state.analise_ia = ""

    botao_analise, botao_salvar = st.columns(2)

    with botao_analise:
        if st.button("Analisar com IA", type="secondary"):
            if hand_cards.strip() and action_history.strip():
                with st.spinner("O treinador esta pensando..."):
                    try:
                        cartas_vilao = (
                            opponent_cards.strip()
                            if opponent_cards.strip()
                            else "Desconhecidas"
                        )

                        prompt = f"""
Voce e um treinador profissional de poker. Analise esta mao para estudo.

Modalidade: {modalidade}
Posicao do Hero: {hero_pos}
Stack efetivo: {effective_stack} BBs
Cartas do Hero: {hand_cards.strip()}

Posicao do oponente: {opponent_position}
Stack do oponente: {opponent_stack} BBs
Cartas do oponente: {cartas_vilao}

Board:
Flop: {flop.strip() or "Nao informado"}
Turn: {turn.strip() or "Nao informado"}
River: {river.strip() or "Nao informado"}

Linha completa / acao do Hero:
{action_history.strip()}

Acao do oponente:
{opponent_action.strip() or "Nao informada"}

Duvida principal:
{user_question.strip() or "Nao informada"}

Faca uma analise tecnica e didatica em portugues.
Explique:
1. Ranges provaveis do Hero e do oponente.
2. Pontos importantes de pre-flop, flop, turn e river disponiveis.
3. Acoes alternativas e tamanhos de aposta possiveis.
4. Se a linha escolhida parece boa, discutivel ou um erro.
5. Uma conclusao pratica e curta para estudo.

Nao invente informacoes ausentes. Se algo importante estiver faltando,
diga exatamente o que precisaria saber para avaliar melhor.
"""

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "Voce e um expert em poker, com abordagem "
                                        "tecnica, equilibrada e focada em estudo."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )

                        st.session_state.analise_ia = (
                            response.choices[0].message.content
                        )

                    except Exception as error:
                        st.error(f"Erro na analise: {error}")
            else:
                st.warning(
                    "Preencha pelo menos as suas cartas e a linha da mao para analisar."
                )

    if st.session_state.analise_ia:
        st.subheader("Analise da IA")
        st.info(st.session_state.analise_ia)

    with botao_salvar:
        if st.button("Salvar na Biblioteca", type="primary"):
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
                        "aprendizado": st.session_state.analise_ia,
                        "cartas_oponente": opponent_cards.strip(),
                        "posicao_oponente": opponent_position,
                        "stack_oponente": opponent_stack,
                        "acao_oponente": opponent_action.strip()
                    }

                    supabase.table("maos").insert(data).execute()

                    st.success("Mao salva com sucesso!")
                    st.session_state.analise_ia = ""
                    st.balloons()

                except Exception as error:
                    st.error(f"Erro ao salvar: {error}")
            else:
                st.warning(
                    "Preencha pelo menos as suas cartas e a linha da mao antes de salvar."
                )

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
                    f"{data_salva} | Hero: {mao.get('cartas', '-')} "
                    f"| {mao.get('posicao', '-')} "
                    f"| Vilao: {mao.get('posicao_oponente', '-')}"
                )

                with st.expander(titulo):
                    hero_col, vilao_col = st.columns(2)

                    with hero_col:
                        st.write("**Hero**")
                        st.write(f"Cartas: {mao.get('cartas') or '-'}")
                        st.write(f"Posicao: {mao.get('posicao') or '-'}")
                        st.write(f"Stack efetivo: {mao.get('stack') or '-'} BB")

                    with vilao_col:
                        st.write("**Oponente**")
                        st.write(
                            f"Cartas: {mao.get('cartas_oponente') or 'Desconhecidas'}"
                        )
                        st.write(
                            f"Posicao: {mao.get('posicao_oponente') or 'Desconhecida'}"
                        )
                        st.write(
                            f"Stack: {mao.get('stack_oponente') or '-'} BB"
                        )

                    st.write("**Board**")
                    st.write(
                        f"Flop: {mao.get('flop') or '-'} | "
                        f"Turn: {mao.get('turn') or '-'} | "
                        f"River: {mao.get('river') or '-'}"
                    )

                    st.write("**Linha da mao / acao do Hero**")
                    st.write(mao.get("acao") or "-")

                    st.write("**Acao do oponente**")
                    st.write(mao.get("acao_oponente") or "-")

                    st.write("**Duvida**")
                    st.write(mao.get("duvida") or "-")

                    st.write("**Analise da IA / aprendizado**")
                    st.write(mao.get("aprendizado") or "-")

    except Exception as error:
        st.error(f"Erro ao carregar biblioteca: {error}")
