import streamlit as st
from supabase import create_client, Client
from openai import OpenAI

st.set_page_config(
    page_title="Poker Study Buddy",
    layout="wide"
)

# Connections
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(url, key)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "analise_ia" not in st.session_state:
    st.session_state.analise_ia = ""

st.title("Poker Study Buddy")
st.caption("Revisao de Sit & Go com IA e biblioteca de maos")

aba_revisao, aba_biblioteca = st.tabs(
    ["Nova Revisao", "Biblioteca de Maos"]
)

with aba_revisao:
    st.subheader("Registrar uma mao para estudo")

    with st.sidebar:
        st.header("Dados do torneio")

        modalidade = st.selectbox(
            "Modalidade",
            ["Sit & Go", "Spin & Go", "MTT", "Cash Game"]
        )

        blinds = st.text_input(
            "Blinds atuais",
            placeholder="Ex.: 100 / 200"
        )

        ante = st.number_input(
            "Ante",
            min_value=0,
            value=0
        )

        total_jogadores = st.number_input(
            "Total de jogadores",
            min_value=2,
            value=9
        )

        jogadores_restantes = st.number_input(
            "Jogadores restantes",
            min_value=2,
            value=9
        )

        fase_torneio = st.selectbox(
            "Fase do torneio",
            [
                "Inicio",
                "Meio do torneio",
                "Bolha",
                "ITM / Premiado",
                "Heads-up",
                "Final"
            ]
        )

        estrutura_premiacao = st.text_input(
            "Estrutura de premiacao",
            placeholder="Ex.: 50% / 30% / 20%"
        )

    st.subheader("Hero e oponente")

    hero_col, vilao_col = st.columns(2)

    with hero_col:
        st.markdown("#### Hero")

        hero_pos = st.selectbox(
            "Posicao do Hero",
            ["SB", "BB", "UTG", "MP", "CO", "BTN"]
        )

        hero_stack = st.number_input(
            "Stack do Hero (BBs)",
            min_value=1,
            value=20
        )

        hand_cards = st.text_input(
            "Cartas do Hero",
            placeholder="Ex.: Ad Ks"
        )

    with vilao_col:
        st.markdown("#### Oponente principal")

        opponent_position = st.selectbox(
            "Posicao do oponente",
            ["Desconhecida", "SB", "BB", "UTG", "MP", "CO", "BTN"]
        )

        opponent_stack = st.number_input(
            "Stack do oponente (BBs)",
            min_value=0,
            value=20
        )

        opponent_cards = st.text_input(
            "Cartas do oponente",
            placeholder="Ex.: Qh Jd - deixe vazio se nao houve showdown"
        )

    effective_stack = min(hero_stack, opponent_stack) if opponent_stack > 0 else hero_stack

    st.info(f"Stack efetivo para a mao: {effective_stack} BBs")

    st.subheader("Board")

    board_col1, board_col2, board_col3 = st.columns(3)

    with board_col1:
        flop = st.text_input(
            "Flop",
            placeholder="Ex.: 2h 7s 9c"
        )

    with board_col2:
        turn = st.text_input(
            "Turn",
            placeholder="Ex.: Jh"
        )

    with board_col3:
        river = st.text_input(
            "River",
            placeholder="Ex.: As"
        )

    st.subheader("Acao e duvida")

    action_history = st.text_area(
        "Linha completa da mao",
        placeholder=(
            "Ex.: Hero abre 2.5 BB no BTN. BB paga. "
            "Flop: BB check, Hero aposta 33% do pote, BB paga. "
            "Turn: BB check, Hero aposta 60%..."
        ),
        height=150
    )

    opponent_action = st.text_area(
        "Acao do oponente",
        placeholder=(
            "Ex.: BB paga pre-flop, da check no flop, "
            "paga a c-bet e da check no turn."
        ),
        height=110
    )

    user_question = st.text_area(
        "Sua duvida principal",
        placeholder=(
            "Ex.: Na bolha, com 14 BBs, este spot e shove, "
            "min-raise ou fold?"
        )
    )

    st.divider()

    botao_analise, botao_salvar = st.columns(2)

    with botao_analise:
        if st.button("Analisar com IA", type="secondary"):
            if hand_cards.strip() and action_history.strip():
                with st.spinner("O treinador esta analisando a mao..."):
                    try:
                        cartas_vilao = (
                            opponent_cards.strip()
                            if opponent_cards.strip()
                            else "Desconhecidas"
                        )

                        prompt = f"""
Voce e um treinador profissional de poker especializado em Sit & Go,
ICM, push-fold e estrategia de torneios.

Analise a mao abaixo em portugues, com foco em estudo pratico.

DADOS DO TORNEIO
Modalidade: {modalidade}
Blinds: {blinds or "Nao informados"}
Ante: {ante}
Jogadores restantes: {jogadores_restantes} de {total_jogadores}
Fase do torneio: {fase_torneio}
Estrutura de premiacao: {estrutura_premiacao or "Nao informada"}

HERO
Posicao: {hero_pos}
Stack: {hero_stack} BBs
Cartas: {hand_cards.strip()}

OPONENTE PRINCIPAL
Posicao: {opponent_position}
Stack: {opponent_stack} BBs
Cartas: {cartas_vilao}

STACK EFETIVO
{effective_stack} BBs

BOARD
Flop: {flop.strip() or "Nao informado"}
Turn: {turn.strip() or "Nao informado"}
River: {river.strip() or "Nao informado"}

LINHA COMPLETA DA MAO
{action_history.strip()}

ACAO DO OPONENTE
{opponent_action.strip() or "Nao informada"}

DUVIDA PRINCIPAL
{user_question.strip() or "Nao informada"}

Estruture a resposta desta forma:
1. Resumo do spot.
2. Consideracoes de ICM e pressao de bolha, quando aplicavel.
3. Range provavel do Hero e do oponente.
4. Analise da melhor linha por rua: pre-flop, flop, turn e river.
5. Avaliacao dos tamanhos de aposta e alternativas.
6. Conclusao objetiva: melhor decisao pratica e principal aprendizado.

Nao invente informacoes que nao foram fornecidas.
Se faltarem dados importantes, diga quais dados fariam diferenca.
"""

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "Voce e um coach de poker tecnico, didatico "
                                        "e honesto. Priorize ICM em Sit & Go, mas "
                                        "nao trate recomendacoes como certeza quando "
                                        "faltarem dados."
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
                    "Preencha as cartas do Hero e a linha completa da mao antes de analisar."
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
                        "acao_oponente": opponent_action.strip(),
                        "blinds": blinds.strip(),
                        "ante": ante,
                        "jogadores_restantes": jogadores_restantes,
                        "total_jogadores": total_jogadores,
                        "estrutura_premiacao": estrutura_premiacao.strip(),
                        "fase_torneio": fase_torneio
                    }

                    supabase.table("maos").insert(data).execute()

                    st.success("Mao salva na biblioteca com sucesso!")
                    st.session_state.analise_ia = ""
                    st.balloons()

                except Exception as error:
                    st.error(f"Erro ao salvar: {error}")
            else:
                st.warning(
                    "Preencha as cartas do Hero e a linha completa da mao antes de salvar."
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
                    f"| {mao.get('fase_torneio', '-')}"
                )

                with st.expander(titulo):
                    torneio_col, hero_col, vilao_col = st.columns(3)

                    with torneio_col:
                        st.markdown("**Torneio**")
                        st.write(f"Modalidade: {mao.get('modalidade') or '-'}")
                        st.write(f"Blinds: {mao.get('blinds') or '-'}")
                        st.write(f"Ante: {mao.get('ante') or 0}")
                        st.write(
                            f"Jogadores: "
                            f"{mao.get('jogadores_restantes') or '-'} de "
                            f"{mao.get('total_jogadores') or '-'}"
                        )
                        st.write(f"Fase: {mao.get('fase_torneio') or '-'}")
                        st.write(
                            f"Premiacao: {mao.get('estrutura_premiacao') or '-'}"
                        )

                    with hero_col:
                        st.markdown("**Hero**")
                        st.write(f"Cartas: {mao.get('cartas') or '-'}")
                        st.write(f"Posicao: {mao.get('posicao') or '-'}")
                        st.write(
                            f"Stack efetivo: {mao.get('stack') or '-'} BBs"
                        )

                    with vilao_col:
                        st.markdown("**Oponente**")
                        st.write(
                            f"Cartas: "
                            f"{mao.get('cartas_oponente') or 'Desconhecidas'}"
                        )
                        st.write(
                            f"Posicao: "
                            f"{mao.get('posicao_oponente') or 'Desconhecida'}"
                        )
                        st.write(
                            f"Stack: {mao.get('stack_oponente') or '-'} BBs"
                        )

                    st.markdown("**Board**")
                    st.write(
                        f"Flop: {mao.get('flop') or '-'} | "
                        f"Turn: {mao.get('turn') or '-'} | "
                        f"River: {mao.get('river') or '-'}"
                    )

                    st.markdown("**Linha completa da mao**")
                    st.write(mao.get("acao") or "-")

                    st.markdown("**Acao do oponente**")
                    st.write(mao.get("acao_oponente") or "-")

                    st.markdown("**Duvida**")
                    st.write(mao.get("duvida") or "-")

                    st.markdown("**Analise da IA / aprendizado**")
                    st.write(mao.get("aprendizado") or "-")

    except Exception as error:
        st.error(f"Erro ao carregar a biblioteca: {error}")
