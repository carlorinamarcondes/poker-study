import streamlit as st
from supabase import create_client, Client
from openai import OpenAI

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "analise_ia" not in st.session_state:
    st.session_state.analise_ia = ""

st.title("Poker Study Buddy")
st.caption("Revisao de Sit & Go para o Master")

aba_revisao, aba_biblioteca = st.tabs(["Nova Revisao", "Biblioteca de Maos"])

with aba_revisao:
    st.subheader("Registrar uma mao para o Master")

    with st.sidebar:
        st.header("Dados do torneio")
        modalidade = st.selectbox("Modalidade", ["Sit & Go", "Spin & Go", "MTT", "Cash Game"])
        blinds = st.text_input("Blinds atuais", placeholder="Ex.: 100 / 200")
        ante = st.number_input("Ante", min_value=0, value=0)
        total_jogadores = st.number_input("Total de jogadores", min_value=2, value=9)
        jogadores_restantes = st.number_input("Jogadores restantes", min_value=2, value=9)
        fase_torneio = st.selectbox("Fase do torneio", ["Inicio", "Meio do torneio", "Bolha", "ITM / Premiado", "Heads-up", "Final"])
        estrutura_premiacao = st.text_input("Estrutura de premiacao", placeholder="Ex.: 50% / 30% / 20%")

    st.subheader("Master e oponente")
    master_col, vilao_col = st.columns(2)

    with master_col:
        st.markdown("#### Master")
        master_pos = st.selectbox("Posicao do Master", ["SB", "BB", "UTG", "MP", "CO", "BTN"])
        master_stack = st.number_input("Stack do Master (BBs)", min_value=1, value=20)
        hand_cards = st.text_input("Cartas do Master", placeholder="Ex.: Ad Ks")

    with vilao_col:
        st.markdown("#### Oponente principal")
        opponent_position = st.selectbox("Posicao do oponente", ["Desconhecida", "SB", "BB", "UTG", "MP", "CO", "BTN"])
        opponent_stack = st.number_input("Stack do oponente (BBs)", min_value=0, value=20)
        opponent_cards = st.text_input("Cartas do oponente", placeholder="Ex.: Qh Jd")

    effective_stack = min(master_stack, opponent_stack) if opponent_stack > 0 else master_stack
    st.info("Stack efetivo para a mao: " + str(effective_stack) + " BBs")

    st.subheader("Board")
    board_col1, board_col2, board_col3 = st.columns(3)
    with board_col1:
        flop = st.text_input("Flop", placeholder="Ex.: 2h 7s 9c")
    with board_col2:
        turn = st.text_input("Turn", placeholder="Ex.: Jh")
    with board_col3:
        river = st.text_input("River", placeholder="Ex.: As")

    st.subheader("Acao e duvida")
    action_history = st.text_area("Linha completa da mao", placeholder="Descreva a sequencia de acoes do Master...", height=150)
    opponent_action = st.text_area("Acao do oponente", placeholder="O que o vilao fez durante as ruas?", height=110)
    user_question = st.text_area("Sua duvida principal", placeholder="Qual ponto da jogada o Master quer analisar?")

    st.divider()
    botao_analise, botao_salvar = st.columns(2)

    with botao_analise:
        if st.button("Analisar com IA", type="secondary"):
            if hand_cards.strip() and action_history.strip():
                with st.spinner("O treinador esta analisando a jogada do Master..."):
                    try:
                        cartas_vilao = opponent_cards.strip() if opponent_cards.strip() else "Desconhecidas"

                        prompt = (
                            "Voce e um treinador profissional de poker. Analise esta mao para o Master.\n\n"
                            "DADOS DO TORNEIO\n"
                            "Modalidade: " + modalidade + "\n"
                            "Blinds: " + blinds + " | Ante: " + str(ante) + "\n"
                            "Jogadores restantes: " + str(jogadores_restantes) + " de " + str(total_jogadores) + "\n"
                            "Fase: " + fase_torneio + " | Premiacao: " + estrutura_premiacao + "\n\n"
                            "MASTER\n"
                            "Posicao: " + master_pos + "\n"
                            "Stack: " + str(master_stack) + " BBs\n"
                            "Cartas: " + hand_cards.strip() + "\n\n"
                            "OPONENTE\n"
                            "Posicao: " + opponent_position + "\n"
                            "Stack: " + str(opponent_stack) + " BBs\n"
                            "Cartas: " + cartas_vilao + "\n"
                            "Stack Efetivo: " + str(effective_stack) + " BBs\n\n"
                            "BOARD\n"
                            "Flop: " + flop.strip() + " | Turn: " + turn.strip() + " | River: " + river.strip() + "\n\n"
                            "LINHA DO MASTER\n"
                            + action_history.strip() + "\n\n"
                            "ACAO DO OPONENTE\n"
                            + opponent_action.strip() + "\n\n"
                            "DUVIDA DO MASTER\n"
                            + user_question.strip() + "\n\n"
                            "Analise de forma tecnica e didatica em portugues. "
                            "Trate o jogador como Master. "
                            "Considere ICM quando aplicavel. "
                            "Estruture: 1. Resumo do spot. 2. ICM e bolha. "
                            "3. Ranges. 4. Analise por rua. 5. Conclusao pratica."
                        )

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Voce e um coach de poker focado em ensinar o Master."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        st.session_state.analise_ia = response.choices[0].message.content
                    except Exception as error:
                        st.error("Erro na analise: " + str(error))
            else:
                st.warning("Preencha as cartas e a linha da mao.")

    if st.session_state.analise_ia:
        st.subheader("Analise para o Master")
        st.info(st.session_state.analise_ia)

    with botao_salvar:
        if st.button("Salvar na Biblioteca", type="primary"):
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
                    st.success("Mao do Master salva com sucesso!")
                    st.session_state.analise_ia = ""
                    st.balloons()
                except Exception as error:
                    st.error("Erro ao salvar: " + str(error))
            else:
                st.warning("Preencha os campos obrigatorios antes de salvar.")

with aba_biblioteca:
    st.subheader("Biblioteca do Master")
    try:
        resposta = supabase.table("maos").select("*").order("created_at", desc=True).execute()
        maos = resposta.data

        if not maos:
            st.info("Nenhuma mao registrada ainda.")
        else:
            st.metric("Total de maos salvas", len(maos))
            for mao in maos:
                titulo = (
                    mao.get("created_at", "")[:10]
                    + " | Master: " + str(mao.get("cartas", "-"))
                    + " | " + str(mao.get("posicao", "-"))
                    + " vs " + str(mao.get("posicao_oponente", "-"))
                )
                with st.expander(titulo):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown("**Torneio**")
                        st.write("Blinds: " + str(mao.get("blinds") or "-"))
                        st.write("Fase: " + str(mao.get("fase_torneio") or "-"))
                        st.write("Jogadores: " + str(mao.get("jogadores_restantes") or "-") + "/" + str(mao.get("total_jogadores") or "-"))
                    with c2:
                        st.markdown("**Master**")
                        st.write("Cartas: " + str(mao.get("cartas") or "-"))
                        st.write("Stack: " + str(mao.get("stack") or "-") + " BB")
                    with c3:
                        st.markdown("**Oponente**")
                        st.write("Cartas: " + str(mao.get("cartas_oponente") or "?"))
                        st.write("Stack: " + str(mao.get("stack_oponente") or "-") + " BB")

                    st.markdown("**Acao do Master**")
                    st.write(mao.get("acao") or "-")
                    st.markdown("**Analise e Aprendizado**")
                    st.write(mao.get("aprendizado") or "Sem analise gerada.")
    except Exception as error:
        st.error("Erro na biblioteca: " + str(error))
