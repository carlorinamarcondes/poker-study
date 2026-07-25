import streamlit as st
from supabase import create_client, Client
from openai import OpenAI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
import json
import re

st.set_page_config(page_title="Poker Study Buddy", layout="wide")

# --- Conexoes ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("PokerMind - Master Edition")
st.caption("Revisao pos-jogo, analise ICM e simulador de decisoes")

# ===================== RANGE CHART =====================

RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


def cell_label(i, j):
    if i == j:
        return f"{RANKS[i]}{RANKS[j]}"
    elif i < j:
        return f"{RANKS[i]}{RANKS[j]}s"
    else:
        return f"{RANKS[j]}{RANKS[i]}o"


def build_range_chart(raise_hands=None, call_hands=None):
    raise_hands = [h.strip() for h in (raise_hands or [])]
    call_hands = [h.strip() for h in (call_hands or [])]
    n = len(RANKS)

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor('#16213e')
    fig.patch.set_facecolor('#16213e')

    for i in range(n):
        for j in range(n):
            label = cell_label(i, j)
            if label in raise_hands:
                color = '#27ae60'
            elif label in call_hands:
                color = '#e67e22'
            else:
                color = '#922b21'

            rect = plt.Rectangle(
                [j, n - 1 - i], 0.93, 0.93,
                facecolor=color, edgecolor='#16213e', linewidth=1.5
            )
            ax.add_patch(rect)
            ax.text(
                j + 0.465, n - 1 - i + 0.465, label,
                ha='center', va='center',
                fontsize=6.2, color='white',
                fontweight='bold', fontfamily='monospace'
            )

    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')

    legend = [
        mpatches.Patch(color='#27ae60', label='Raise / Bet'),
        mpatches.Patch(color='#e67e22', label='Call'),
        mpatches.Patch(color='#922b21', label='Fold'),
    ]
    ax.legend(
        handles=legend, loc='lower right', fontsize=11,
        facecolor='#1a1a2e', edgecolor='#aaa', labelcolor='white'
    )
    plt.tight_layout()
    return fig


# ===================== AI =====================

def call_ai(prompt):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Voce e um coach de poker especializado em Sit & Go, "
                    "teoria dos jogos e ICM. "
                    "Responda SEMPRE em portugues do Brasil. "
                    "Quando pedido, retorne APENAS JSON valido, sem texto extra."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
        max_tokens=1800
    )
    return response.choices[0].message.content


def parse_json(raw):
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {
        "analise": raw,
        "pontos_fortes": [],
        "pontos_melhoria": [],
        "range_raise": [],
        "range_call": [],
        "decisao_ideal": "?",
        "nota": "?"
    }


def build_review_prompt(data, icm=False):
    icm_bloco = ""
    if icm:
        icm_bloco = (
            f"\nEsta e uma ANALISE ICM. Sobram {data.get('jogadores_restantes', '?')} jogadores. "
            f"Estrutura: {data.get('estrutura', '?')}. "
            "A sobrevivencia e o salto de payout pesam mais do que o EV de chips puro."
        )

    return f"""
Analise esta mao de Sit & Go para o Master:

MASTER:
- Cartas: {data.get('cartas_master', '?')}
- Posicao: {data.get('posicao_master', '?')}
- Stack: {data.get('stack_master', '?')} BBs
- Blinds: {data.get('blinds', '?')}
- Jogadores restantes: {data.get('jogadores_restantes', '?')}
- Estrutura de premiacao: {data.get('estrutura', '?')}

BOARD:
- Flop: {data.get('flop', '-')}
- Turn: {data.get('turn', '-')}
- River: {data.get('river', '-')}

OPONENTE:
- Cartas: {data.get('cartas_oponente', 'desconhecidas')}
- Posicao: {data.get('posicao_oponente', 'desconhecida')}
- Stack: {data.get('stack_oponente', 'desconhecido')}
- Tendencias: {data.get('tendencias_oponente', 'nao informadas')}

DESCRICAO DA MAO:
{data.get('acao', '?')}
{icm_bloco}

Retorne APENAS este JSON (sem texto fora dele):
{{
  "analise": "analise detalhada de 3 a 5 paragrafos",
  "pontos_fortes": ["ponto 1", "ponto 2"],
  "pontos_melhoria": ["ponto 1", "ponto 2"],
  "decisao_ideal": "Raise ou Call ou Fold",
  "range_raise": ["AA", "KK", "AKs", "AKo"],
  "range_call": ["JJ", "TT", "AQs"],
  "nota": 7
}}

Para range_raise e range_call, liste as maos que voce jogaria dessa forma
nessa posicao e situacao. Use: pares como "AA", suited como "AKs", offsuit como "AKo".
"""


def show_result(parsed, key_suffix=""):
    col_left, col_right = st.columns([1, 1])

    with col_left:
        decisao = parsed.get("decisao_ideal", "?")
        nota = parsed.get("nota", "?")
        m1, m2 = st.columns(2)
        m1.metric("Decisao ideal", decisao)
        m2.metric("Nota", f"{nota} / 10")

        st.markdown("**Analise:**")
        st.info(parsed.get("analise", ""))

        fortes = parsed.get("pontos_fortes", [])
        melhoria = parsed.get("pontos_melhoria", [])
        if fortes:
            st.markdown("**Pontos fortes:**")
            for p in fortes:
                st.markdown(f"- {p}")
        if melhoria:
            st.markdown("**O que melhorar:**")
            for p in melhoria:
                st.markdown(f"- {p}")

    with col_right:
        st.markdown("**Range recomendado para essa situacao:**")
        fig = build_range_chart(
            raise_hands=parsed.get("range_raise", []),
            call_hands=parsed.get("range_call", [])
        )
        st.pyplot(fig, key=f"chart_{key_suffix}")


# ===================== SIMULADOR =====================

ALL_RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
ALL_SUITS = ['s', 'h', 'd', 'c']


def random_card(used):
    while True:
        card = random.choice(ALL_RANKS) + random.choice(ALL_SUITS)
        if card not in used:
            used.add(card)
            return card


def generate_situation():
    used = set()
    c1 = random_card(used)
    c2 = random_card(used)
    flop = [random_card(used) for _ in range(3)]
    turn = random_card(used)

    aposta_oponente = random.choice([0, 0, 30, 50, 100, 150, 200])
    pot = random.randint(2, 10) * 50

    return {
        "cartas": f"{c1} {c2}",
        "flop": " ".join(flop),
        "turn": turn,
        "posicao": random.choice(["BTN", "SB", "BB", "UTG", "MP", "CO"]),
        "stack": random.choice([8, 10, 12, 15, 20, 25]),
        "jogadores_restantes": random.randint(3, 9),
        "blinds": random.choice(["25/50", "50/100", "100/200", "200/400"]),
        "pot": pot,
        "aposta_oponente": aposta_oponente,
    }


def build_simulator_prompt(hand, decisao_master):
    return f"""
Avalie esta decisao do Master em um Sit & Go:

SITUACAO:
- Cartas: {hand['cartas']}
- Posicao: {hand['posicao']}
- Stack: {hand['stack']} BBs
- Blinds: {hand['blinds']}
- Jogadores restantes: {hand['jogadores_restantes']}
- Board: Flop {hand['flop']} | Turn {hand['turn']}
- Pote atual: {hand['pot']} fichas
- Aposta do oponente: {hand['aposta_oponente']} fichas

DECISAO DO MASTER: {decisao_master}

Retorne APENAS este JSON:
{{
  "decisao_correta": "Fold ou Call ou Raise",
  "acertou": true,
  "explicacao": "explicacao clara e didatica de 2 a 3 paragrafos",
  "raciocinio_ideal": "como pensar nessa situacao passo a passo",
  "range_raise": ["AA", "KK", "AKs"],
  "range_call": ["JJ", "TT", "AQs"],
  "nota": 8
}}
"""


# ===================== TABS =====================

aba_revisao, aba_simulador, aba_biblioteca = st.tabs([
    "Nova Revisao", "Simulador", "Biblioteca"
])

# =========== ABA REVISAO ===========
with aba_revisao:
    st.subheader("Registrar uma mao para estudo")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Cartas e Board")
        cartas_master = st.text_input(
            "Suas cartas (Master)", placeholder="Ex.: Ad Ks"
        )
        flop_val = st.text_input("Flop", placeholder="Ex.: 2h 7s 9c")
        turn_val = st.text_input("Turn", placeholder="Ex.: Jh")
        river_val = st.text_input("River", placeholder="Ex.: As")

    with col2:
        st.markdown("#### Situacao do torneio")
        posicao_master = st.selectbox(
            "Sua posicao", ["BTN", "SB", "BB", "UTG", "MP", "CO"]
        )
        stack_master = st.number_input("Seu stack (BBs)", min_value=1, value=20)
        blinds_val = st.text_input("Blinds atuais", placeholder="Ex.: 100/200")
        jogadores_val = st.number_input(
            "Jogadores restantes na mesa", min_value=2, max_value=9, value=6
        )
        estrutura_val = st.selectbox(
            "Estrutura de premiacao",
            [
                "Top 3 pagam (9-max)",
                "Top 2 pagam (6-max)",
                "Heads-up (2 jogadores)",
                "Winner-take-all",
            ],
        )

    acao_val = st.text_area(
        "Descreva a acao da mao",
        placeholder="Ex.: Abri 2.5BB no BTN, BB 3-betou, fui all-in...",
        height=100,
    )

    with st.expander("Informacoes opcionais do oponente (preencha se souber)"):
        col3, col4 = st.columns(2)
        with col3:
            cartas_op = st.text_input(
                "Cartas do oponente", placeholder="Ex.: Kd Qh"
            )
            posicao_op = st.selectbox(
                "Posicao do oponente",
                ["Desconhecida", "BTN", "SB", "BB", "UTG", "MP", "CO"],
            )
        with col4:
            stack_op = st.text_input(
                "Stack do oponente (BBs)", placeholder="Ex.: 15"
            )
            tendencias_op = st.text_area(
                "Tendencias do oponente",
                placeholder="Ex.: Muito agressivo, nao faz fold ao c-bet",
                height=80,
            )

    btn1, btn2 = st.columns(2)
    with btn1:
        analisar = st.button(
            "Analisar mao", use_container_width=True, type="primary"
        )
    with btn2:
        analisar_icm = st.button(
            "Analisar com ICM", use_container_width=True
        )

    if analisar or analisar_icm:
        if not cartas_master or not flop_val or not acao_val:
            st.warning(
                "Preencha ao menos: suas cartas, o flop e a descricao da acao."
            )
        else:
            data_rev = {
                "cartas_master": cartas_master,
                "posicao_master": posicao_master,
                "stack_master": stack_master,
                "blinds": blinds_val,
                "jogadores_restantes": jogadores_val,
                "estrutura": estrutura_val,
                "flop": flop_val,
                "turn": turn_val,
                "river": river_val,
                "acao": acao_val,
                "cartas_oponente": cartas_op or "desconhecidas",
                "posicao_oponente": posicao_op,
                "stack_oponente": stack_op or "desconhecido",
                "tendencias_oponente": tendencias_op or "nao informadas",
            }

            with st.spinner("Analisando sua mao..."):
                try:
                    raw = call_ai(
                        build_review_prompt(data_rev, icm=analisar_icm)
                    )
                    parsed = parse_json(raw)

                    st.divider()
                    st.subheader("Resultado da analise")
                    show_result(parsed, key_suffix="revisao")

                    try:
                        nota_num = parsed.get("nota")
                        if isinstance(nota_num, str):
                            nota_num = int(nota_num) if nota_num.isdigit() else None
                        supabase.table("maos").insert({
                            "cartas_master": cartas_master,
                            "posicao_master": posicao_master,
                            "stack_master": int(stack_master),
                            "flop": flop_val,
                            "turn": turn_val,
                            "river": river_val,
                            "acao": acao_val,
                            "cartas_oponente": cartas_op,
                            "analise_ia": parsed.get("analise", ""),
                            "nota": nota_num,
                        }).execute()
                        st.success("Mao salva na biblioteca!")
                    except Exception as e:
                        st.warning(f"Analise feita, mas nao foi possivel salvar: {e}")

                except Exception as e:
                    st.error(f"Erro na analise: {e}")

# =========== ABA SIMULADOR ===========
with aba_simulador:
    st.subheader("Simulador de Decisoes")
    st.caption(
        "O app gera uma situacao real de Sit & Go. "
        "Voce decide — a IA avalia se foi a jogada certa."
    )

    if "sim_hand" not in st.session_state:
        st.session_state.sim_hand = None
        st.session_state.sim_result = None
        st.session_state.sim_decided = False
        st.session_state.sim_decisao = None

    if st.button("Gerar nova mao", type="primary"):
        st.session_state.sim_hand = generate_situation()
        st.session_state.sim_result = None
        st.session_state.sim_decided = False
        st.session_state.sim_decisao = None

    if st.session_state.sim_hand:
        hand = st.session_state.sim_hand
        st.divider()

        c1, c2, c3 = st.columns(3)
        c1.metric("Suas cartas", hand["cartas"])
        c1.metric("Posicao", hand["posicao"])
        c2.metric("Stack", f"{hand['stack']} BBs")
        c2.metric("Blinds", hand["blinds"])
        c3.metric("Jogadores restantes", hand["jogadores_restantes"])
        c3.metric("Pote", f"{hand['pot']} fichas")

        st.markdown(
            f"**Board:** `{hand['flop']}` &nbsp;|&nbsp; Turn: `{hand['turn']}`"
        )

        if hand["aposta_oponente"] > 0:
            st.warning(
                f"O oponente apostou **{hand['aposta_oponente']} fichas**. "
                "O que voce faz?"
            )
        else:
            st.info("Sua vez de agir primeiro. O que voce faz?")

        if not st.session_state.sim_decided:
            bf, bc, br = st.columns(3)
            with bf:
                if st.button("FOLD", use_container_width=True):
                    st.session_state.sim_decided = True
                    st.session_state.sim_decisao = "Fold"
                    st.rerun()
            with bc:
                if st.button("CALL", use_container_width=True):
                    st.session_state.sim_decided = True
                    st.session_state.sim_decisao = "Call"
                    st.rerun()
            with br:
                if st.button("RAISE", use_container_width=True, type="primary"):
                    st.session_state.sim_decided = True
                    st.session_state.sim_decisao = "Raise"
                    st.rerun()

        if (
            st.session_state.sim_decided
            and st.session_state.sim_result is None
        ):
            with st.spinner("A IA esta avaliando sua decisao..."):
                try:
                    raw = call_ai(
                        build_simulator_prompt(hand, st.session_state.sim_decisao)
                    )
                    st.session_state.sim_result = parse_json(raw)
                except Exception as e:
                    st.error(f"Erro: {e}")

        if st.session_state.sim_result:
            result = st.session_state.sim_result
            st.divider()

            acertou = result.get("acertou", False)
            decisao_correta = result.get("decisao_correta", "?")

            if acertou:
                st.success(
                    f"Decisao correta! A jogada ideal era **{decisao_correta}**."
                )
            else:
                st.error(
                    f"Nao foi a melhor opcao. A jogada ideal era **{decisao_correta}**."
                )

            raciocinio = result.get("raciocinio_ideal", "")
            if raciocinio:
                st.markdown("**Raciocinio ideal:**")
                st.info(raciocinio)

            show_result(result, key_suffix="simulador")

# =========== ABA BIBLIOTECA ===========
with aba_biblioteca:
    st.subheader("Suas maos salvas")

    try:
        resp = (
            supabase.table("maos")
            .select("*")
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        maos = resp.data

        if not maos:
            st.info(
                "Nenhuma mao salva ainda. "
                "Registre sua primeira mao na aba Nova Revisao!"
            )
        else:
            for mao in maos:
                nota_label = mao.get("nota", "?")
                titulo = (
                    f"{mao.get('cartas_master', '?')}  |  "
                    f"{mao.get('posicao_master', '?')}  |  "
                    f"Nota: {nota_label}/10"
                )
                with st.expander(titulo):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(
                            f"**Stack:** {mao.get('stack_master', '?')} BBs"
                        )
                        st.markdown(f"**Flop:** {mao.get('flop', '-')}")
                        st.markdown(f"**Turn:** {mao.get('turn', '-')}")
                        st.markdown(f"**River:** {mao.get('river', '-')}")
                    with col_b:
                        if mao.get("cartas_oponente"):
                            st.markdown(
                                f"**Oponente:** {mao['cartas_oponente']}"
                            )
                        st.markdown("**Analise da IA:**")
                        st.info(mao.get("analise_ia", ""))
    except Exception as e:
        st.error(f"Erro ao carregar biblioteca: {e}")
