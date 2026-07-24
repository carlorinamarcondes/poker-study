import streamlit as st
from supabase import create_client, Client
from openai import OpenAI

st.set_page_config(
    page_title="Poker Study Buddy",
    layout="wide"
)

# Conexoes
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(url, key)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "analise_ia" not in st.session_state:
    st.session_state.analise_ia = ""

st.title("♠️ Poker Study Buddy")
st.caption("Revisao de Sit & Go para o Master")

aba_revisao, aba_biblioteca = st.tabs(
    ["📝 Nova Revisao", "📚 Biblioteca de Maos"]
)

with aba_revisao:
    st.subheader("Registrar uma mao para o Master")

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

    st.subheader("Master e oponente")

    master_col, vilao_col = st.columns(2)

    with master_col:
        st.markdown("#### ⭐ Master")

        master_pos = st.selectbox(
            "Posicao do Master",
            ["SB", "BB", "UTG", "MP", "CO", "BTN"]
        )

        master_stack = st.number_input(
            "Stack do Master (BBs)",
            min_value=1,
            value=20
        )

        hand_cards = st.text_input(
            "Cartas do Master",
            placeholder="Ex.: Ad Ks"
        )

    with vilao_col:
        st.markdown("#### 👤 Oponente principal")

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
            placeholder="Ex.: Qh Jd"
        )

    effective_stack = min(master_stack, opponent_stack) if opponent_stack > 0 else master_stack

    st.info(f"Stack efetivo para a mao: {effective_stack} BBs")

    st.subheader("Board")

    board_col1, board_col2, board_col3 = st.columns(3)

    with board_col1:
        flop = st.text_input("Flop", placeholder="Ex.: 2h 7s 9c")

    with board_col2:
        turn = st.text_input("Turn", placeholder="Ex.: Jh")

    with board_col3:
        river = st.text_input("River", placeholder="Ex.: As")

    st.subheader("Acao e duvida")

    action_history = st.text_area(
        "Linha completa da mao (Acoes do Master)",
        placeholder="Descreva a sequencia de acoes do Master...",
        height=150
    )

    opponent_action = st.text_area(
        "Acao do oponente",
        placeholder="O que o vilao fez durante as ruas?",
        height=110
    )

    user_question = st.text_area(
        "Sua duvida principal",
        placeholder="Qual ponto da jogada o Master quer analisar?"
    )

    st.divider()

    botao_analise, botao_salvar = st.columns(2)

    with botao_analise:
        if st.button("🚀 Analisar com IA", type="secondary"):
            if hand_cards.strip() and action_history.strip():
                with st.spinner("O treinador esta analisando a jogada do Master..."):
                    try:
                        cartas_vilao = opponent_cards.strip() if opponent_cards.strip() else "Desconhecidas"

                        prompt = f"""
Voce e um treinador profissional de poker. Analise esta mao para o Master (seu aluno).

DADOS DO TORNEIO
Modalidade: {modalidade}
Blinds: {blinds} | Ante: {ante}
Jogadores restantes: {jogadores_restantes} de {total_jogadores}
Fase: {fase_torneio} | Premiacao: {estrutura_premiacao}

ESTATISTICAS DA MAO
Posicao do Master: {master_pos}
Stack do Master: {master_stack} BBs
Cartas do Master: {hand_cards.strip()}

Posicao do oponente: {opponent_position}
Stack do oponente: {opponent_stack} BBs
Cartas do oponente: {cartas_vilao}
Stack Efetivo: {effective_stack} BBs

BOARD
{flop.strip()} / {turn.strip()} / {river.strip()}

LINHA DO MASTER
{action_history.strip()}

ACAO DO OPONENTE
{opponent_action.strip()}

DUVIDA DO MASTER
{user_question.strip()}

Analise de forma tecnica. Trate o jogador como 'Master'. Foque em ICM, ranges e se a jogada foi lucrativa a longo prazo.
"""

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Voce e um coach de poker focado em ensinar o Master."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        st.session_state.analise_ia = response.choices[0].message.content
                    except Exception as error:
                        st.error(f"Erro na analise: {error}")
            else:
                st.warning("Preencha as cartas e a linha da mao.")

    if st.session_state.analise_ia:
        st.subheader("Analise para o Master")
        st.info(st.session_state.analise_ia)

    with botao_salvar:
        if st.button("💾 Salvar na Biblioteca", type="primary"):
            if hand_cards.strip() and action_history.strip():
                try:
                    data = {
                        "modalidade": modalidade,
                        "posicao": master_pos,
                        "stack": effective_stack,
                        "cartas": hand_cards.strip(),
                        "flop": flop.strip(),
                        "turn": turn.strip(),
                        "river": river.strip(),
                        "acao": action_history.strip(),
                        "duvida": user_question.strip(),
                        "aprendizado": st.session_state.analise_ia,
                        "cartas_oponente": opponent_cards.strip(),
