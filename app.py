import streamlit as st
from supabase import create_client, Client
from openai import OpenAI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
import json
import re
from treys import Card, Evaluator

_evaluator = Evaluator()

st.set_page_config(page_title="PokerMind", layout="wide")

# --- Conexoes ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("PokerMind - Master Edition")
st.caption("Revisao pos-jogo, analise ICM e simulador de decisoes")

# ================================================================
# CONSTANTES
# ================================================================
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
ALL_RANKS = RANKS[:]
ALL_SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'h': '♥', 'd': '♦', 's': '♠', 'c': '♣'}
SUIT_COLORS  = {'h': '#c0392b', 'd': '#c0392b', 's': '#1a1a2e', 'c': '#1a6b3a'}

# ================================================================
# RANGE CHART (tabela de equidade pre-flop)
# ================================================================
EQUITY_TABLE = {
    'AA':85,'KK':82,'QQ':80,'JJ':77,'TT':75,'99':72,'88':69,
    '77':67,'66':64,'55':62,'44':60,'33':58,'22':55,
    'AKs':67,'AQs':66,'AJs':65,'ATs':64,'A9s':62,'A8s':61,
    'A7s':60,'A6s':59,'A5s':59,'A4s':58,'A3s':57,'A2s':56,
    'AKo':65,'AQo':64,'AJo':63,'ATo':62,'A9o':60,'A8o':59,
    'A7o':58,'A6o':57,'A5o':57,'A4o':56,'A3o':55,'A2o':54,
    'KQs':62,'KJs':61,'KTs':60,'K9s':58,'K8s':56,'K7s':55,
    'K6s':54,'K5s':53,'K4s':52,'K3s':51,'K2s':50,
    'KQo':60,'KJo':59,'KTo':58,'K9o':56,'K8o':54,'K7o':53,
    'K6o':52,'K5o':51,'K4o':50,'K3o':49,'K2o':48,
    'QJs':58,'QTs':57,'Q9s':55,'Q8s':53,'Q7s':52,'Q6s':51,
    'Q5s':50,'Q4s':49,'Q3s':48,'Q2s':47,
    'QJo':56,'QTo':55,'Q9o':53,'Q8o':51,'Q7o':50,'Q6o':49,
    'Q5o':48,'Q4o':47,'Q3o':46,'Q2o':45,
    'JTs':55,'J9s':53,'J8s':51,'J7s':50,'J6s':48,'J5s':47,
    'J4s':46,'J3s':45,'J2s':44,
    'JTo':53,'J9o':51,'J8o':49,'J7o':48,'J6o':46,'J5o':45,
    'J4o':44,'J3o':43,'J2o':42,
    'T9s':52,'T8s':50,'T7s':48,'T6s':47,'T5s':45,'T4s':44,
    'T3s':43,'T2s':42,
    'T9o':50,'T8o':48,'T7o':46,'T6o':45,'T5o':43,'T4o':42,
    'T3o':41,'T2o':40,
    '98s':49,'97s':47,'96s':46,'95s':44,'94s':43,'93s':42,'92s':41,
    '98o':47,'97o':45,'96o':44,'95o':42,'94o':41,'93o':40,'92o':39,
    '87s':46,'86s':45,'85s':43,'84s':42,'83s':41,'82s':40,
    '87o':44,'86o':43,'85o':41,'84o':40,'83o':39,'82o':38,
    '76s':44,'75s':43,'74s':41,'73s':40,'72s':39,
    '76o':42,'75o':41,'74o':39,'73o':38,'72o':37,
    '65s':42,'64s':41,'63s':39,'62s':38,
    '65o':40,'64o':39,'63o':37,'62o':36,
    '54s':40,'53s':39,'52s':37,'54o':38,'53o':37,'52o':35,
    '43s':38,'42s':37,'43o':36,'42o':35,'32s':36,'32o':34,
}

# ================================================================
# EQUITY DINAMICA COM TREYS
# ================================================================

def board_to_tuple(board):
    """Normaliza board para tuple imutavel (usado como cache key)."""
    if not board:
        return ()
    if isinstance(board, str):
        cards = [c.strip() for c in board.split() if c.strip()]
    elif isinstance(board, (list, tuple)):
        cards = [c for c in board if c]
    else:
        return ()
    return tuple(cards)

def get_hole_cards_for_label(label, excluded_set):
    """Retorna dois card strings para um label canonico (ex: 'AKs'), evitando excluded."""
    suits_all = ['h', 'd', 'c', 's']
    if len(label) == 2:  # Par: AA, KK...
        rank = label[0]
        for s1, s2 in [('h','s'),('h','d'),('h','c'),('s','d'),('s','c'),('d','c')]:
            c1, c2 = f"{rank}{s1}", f"{rank}{s2}"
            if c1 not in excluded_set and c2 not in excluded_set:
                return c1, c2
    elif label.endswith('s'):  # Suited: AKs, QJs...
        r1, r2 = label[0], label[1]
        for suit in suits_all:
            c1, c2 = f"{r1}{suit}", f"{r2}{suit}"
            if c1 not in excluded_set and c2 not in excluded_set:
                return c1, c2
    else:  # Offsuit: AKo, QJo...
        r1, r2 = label[0], label[1]
        for s1 in suits_all:
            for s2 in suits_all:
                if s1 != s2:
                    c1, c2 = f"{r1}{s1}", f"{r2}{s2}"
                    if c1 not in excluded_set and c2 not in excluded_set:
                        return c1, c2
    return None, None

def run_equity_mc(c1_str, c2_str, board_strs, n_sim=80):
    """Monte Carlo: equity de c1+c2 vs oponente aleatorio dado o board."""
    try:
        hero = [Card.new(c1_str), Card.new(c2_str)]
        board_cards = [Card.new(c) for c in board_strs]
        known = set(hero + board_cards)

        full_deck = [Card.new(r + s)
                     for r in 'AKQJT98765432'
                     for s in 'shdc']
        available = [c for c in full_deck if c not in known]

        remaining = 5 - len(board_cards)  # cartas que faltam no board
        wins = 0
        for _ in range(n_sim):
            sample = random.sample(available, remaining + 2)
            opp = sample[:2]
            extra = sample[2:]
            full_board = board_cards + extra
            h_score = _evaluator.evaluate(full_board, hero)
            o_score = _evaluator.evaluate(full_board, opp)
            if h_score <= o_score:  # menor score = mao melhor
                wins += 1
        return round(wins / n_sim * 100, 1)
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def calculate_all_equities(board_tuple):
    """
    Calcula equity real de todas as 169 maos canonicas dado o board atual.
    Cacheado por board — so recalcula quando o board muda.
    """
    if not board_tuple:
        return EQUITY_TABLE  # pre-flop: usa tabela estatica

    excluded = set(board_tuple)
    result = {}
    n = len(RANKS)
    for i in range(n):
        for j in range(n):
            label = cell_label_static(i, j)
            c1, c2 = get_hole_cards_for_label(label, excluded)
            if c1 is None:
                result[label] = EQUITY_TABLE.get(label, 50)
                continue
            eq = run_equity_mc(c1, c2, list(board_tuple), n_sim=80)
            result[label] = eq if eq is not None else EQUITY_TABLE.get(label, 50)
    return result

def cell_label_static(i, j):
    """Versao sem depender de cell_label (definida abaixo)."""
    if i == j:
        return f"{RANKS[i]}{RANKS[j]}"
    elif i < j:
        return f"{RANKS[i]}{RANKS[j]}s"
    else:
        return f"{RANKS[j]}{RANKS[i]}o"

def cell_label(i, j):
    if i == j:
        return f"{RANKS[i]}{RANKS[j]}"
    elif i < j:
        return f"{RANKS[i]}{RANKS[j]}s"
    else:
        return f"{RANKS[j]}{RANKS[i]}o"

def build_range_chart(raise_hands=None, call_hands=None, equity_dict=None):
    raise_hands = [h.strip() for h in (raise_hands or [])]
    call_hands  = [h.strip() for h in (call_hands  or [])]
    eq_source   = equity_dict if equity_dict else EQUITY_TABLE
    n = len(RANKS)
    fig, ax = plt.subplots(figsize=(14, 14))
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
            rect = plt.Rectangle([j, n-1-i], 0.93, 0.93,
                                  facecolor=color, edgecolor='#16213e', linewidth=1.5)
            ax.add_patch(rect)
            ax.text(j+0.465, n-1-i+0.64, label,
                    ha='center', va='center', fontsize=12,
                    color='white', fontweight='bold', fontfamily='monospace')
            eq = eq_source.get(label, '-')
            eq_str = f"{eq}%" if isinstance(eq, (int, float)) else str(eq)
            ax.text(j+0.465, n-1-i+0.26, eq_str,
                    ha='center', va='center', fontsize=10,
                    color='#f0f0f0', fontfamily='monospace')
    ax.set_xlim(0, n); ax.set_ylim(0, n)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_aspect('equal')
    legend = [
        mpatches.Patch(color='#27ae60', label='Raise / Bet'),
        mpatches.Patch(color='#e67e22', label='Call'),
        mpatches.Patch(color='#922b21', label='Fold'),
    ]
    ax.legend(handles=legend, loc='lower right', fontsize=13,
              facecolor='#1a1a2e', edgecolor='#aaa', labelcolor='white')
    plt.tight_layout()
    return fig

# ================================================================
# MESA VISUAL
# ================================================================
def draw_card_on_ax(ax, cx, cy, card_str, face_down=False, scale=1.0):
    w, h = 0.78 * scale, 1.08 * scale
    if face_down:
        bg = mpatches.FancyBboxPatch(
            (cx - w/2, cy - h/2), w, h,
            boxstyle="round,pad=0.05",
            facecolor='#1565c0', edgecolor='#90caf9', linewidth=2)
        ax.add_patch(bg)
        ax.text(cx, cy, '?', ha='center', va='center',
                fontsize=int(16*scale), color='white', fontweight='bold')
    else:
        if not card_str or len(card_str) < 2:
            return
        rank     = card_str[:-1]
        suit_chr = card_str[-1].lower()
        clr      = SUIT_COLORS.get(suit_chr, '#333')
        sym      = SUIT_SYMBOLS.get(suit_chr, '?')
        bg = mpatches.FancyBboxPatch(
            (cx - w/2, cy - h/2), w, h,
            boxstyle="round,pad=0.05",
            facecolor='#fafafa', edgecolor='#bbb', linewidth=1.5)
        ax.add_patch(bg)
        ax.text(cx, cy + 0.18*scale, rank,
                ha='center', va='center',
                fontsize=int(18*scale), color=clr, fontweight='bold')
        ax.text(cx, cy - 0.23*scale, sym,
                ha='center', va='center',
                fontsize=int(14*scale), color=clr)

def draw_poker_table(hero_cards, opp_cards, board, pot, street, face_down_opp=True):
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor('#0a120a')
    ax.set_facecolor('#0a120a')

    # Feltro
    table = mpatches.Ellipse((6.5, 4), 11.2, 6.4,
                              facecolor='#1a5c2a', edgecolor='#c8a84b', linewidth=8)
    ax.add_patch(table)
    inner = mpatches.Ellipse((6.5, 4), 10.3, 5.6,
                              facecolor='none', edgecolor='#6b3d1e', linewidth=4)
    ax.add_patch(inner)

    # Pot
    ax.text(6.5, 5.1, f'POT: {pot}', ha='center', va='center',
            fontsize=13, color='#ffd700', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0d3320',
                      edgecolor='#ffd700', alpha=0.85))

    # Street
    street_map = {'preflop':'PRE-FLOP','flop':'FLOP',
                  'turn':'TURN','river':'RIVER','showdown':'SHOWDOWN'}
    ax.text(6.5, 4.4, street_map.get(street, ''), ha='center', va='center',
            fontsize=10, color='#90ee90', style='italic')

    # Oponente (topo)
    ax.text(6.5, 7.15, 'Oponente', ha='center', va='center', fontsize=11,
            color='#ffcccc',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#3d0000', alpha=0.7))
    opp_list = opp_cards.split() if isinstance(opp_cards, str) else (opp_cards or ['?','?'])
    for i, card in enumerate(opp_list[:2]):
        draw_card_on_ax(ax, 5.9 + i*1.3, 6.38, card,
                        face_down=(face_down_opp and street != 'showdown'))

    # Board (centro)
    board_list = board if isinstance(board, list) else []
    if board_list:
        total_w = len(board_list) * 1.45 - 0.15
        xs = 6.5 - total_w/2 + 0.55
        for i, card in enumerate(board_list):
            draw_card_on_ax(ax, xs + i*1.45, 3.78, card, scale=1.05)

    # Master (base)
    ax.text(6.5, 0.82, 'Master', ha='center', va='center', fontsize=11,
            color='#aaddff', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#001a33', alpha=0.7))
    hero_list = hero_cards.split() if isinstance(hero_cards, str) else (hero_cards or [])
    for i, card in enumerate(hero_list[:2]):
        draw_card_on_ax(ax, 5.9 + i*1.3, 1.55, card)

    ax.set_xlim(0.5, 12.5)
    ax.set_ylim(0.1, 8.3)
    ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout(pad=0.3)
    return fig

# ================================================================
# FORCA PRE-FLOP
# ================================================================
PREFLOP_STRENGTH = {
    'AA':99,'KK':96,'QQ':92,'JJ':88,'TT':84,'99':79,'88':74,
    '77':69,'66':64,'55':59,'44':54,'33':49,'22':44,
    'AKs':90,'AQs':83,'AJs':79,'ATs':76,'A9s':71,'A8s':68,
    'A7s':65,'A6s':62,'A5s':64,'A4s':61,'A3s':59,'A2s':57,
    'AKo':85,'AQo':77,'AJo':73,'ATo':69,'A9o':64,'A8o':61,
    'A7o':58,'A6o':55,'A5o':57,'A4o':54,'A3o':51,'A2o':49,
    'KQs':78,'KJs':75,'KTs':72,'K9s':67,'K8s':62,'K7s':58,
    'K6s':55,'K5s':52,'KQo':72,'KJo':69,'KTo':66,'K9o':61,'K8o':56,
    'QJs':73,'QTs':70,'Q9s':65,'Q8s':60,'QJo':67,'QTo':64,'Q9o':59,
    'JTs':71,'J9s':65,'J8s':60,'JTo':65,'J9o':59,
    'T9s':66,'T8s':61,'T7s':56,'T9o':60,'T8o':55,
    '98s':62,'97s':57,'98o':56,'97o':51,
    '87s':59,'86s':54,'87o':53,'86o':48,
    '76s':56,'75s':51,'76o':50,'75o':45,
    '65s':53,'65o':47,'54s':51,'54o':45,
    '43s':47,'43o':41,'32s':43,'32o':37,
}

def get_preflop_strength(cards):
    parts = cards.split()
    if len(parts) != 2:
        return 45
    c1, c2 = parts[0], parts[1]
    if len(c1) < 2 or len(c2) < 2:
        return 45
    r1, s1 = c1[:-1], c1[-1].lower()
    r2, s2 = c2[:-1], c2[-1].lower()
    rank_order = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    v1 = rank_order.index(r1) if r1 in rank_order else 0
    v2 = rank_order.index(r2) if r2 in rank_order else 0
    if v1 < v2:
        r1, r2 = r2, r1
        s1, s2 = s2, s1
    if r1 == r2:
        key = f"{r1}{r2}"
    elif s1 == s2:
        key = f"{r1}{r2}s"
    else:
        key = f"{r1}{r2}o"
    return PREFLOP_STRENGTH.get(key, 42)

# ================================================================
# LOGICA DO OPONENTE — PRE-FLOP (fixa por tipo)
# ================================================================
def opp_preflop_action(opp_type, hero_action, strength, bb):
    """Retorna (acao_str, valor_em_chips)"""
    if opp_type == 'Nit':
        if strength >= 88:
            if hero_action in ('check', 'limp'):
                return 'raise', int(bb * 3)
            if hero_action == 'raise':
                return '3-bet', int(bb * 9)
            return 'call', 0
        elif strength >= 69:
            if hero_action in ('check', 'limp'):
                return 'raise', int(bb * 2.5)
            if hero_action == 'raise':
                return 'call', 0
            return 'fold', 0
        elif strength >= 55:
            if hero_action in ('check', 'limp'):
                return 'limp', int(bb)
            return 'fold', 0
        else:
            return 'fold', 0

    elif opp_type == 'Passivo':
        if strength >= 92:
            if hero_action == 'raise':
                return '3-bet', int(bb * 8)
            return 'limp', int(bb)
        elif strength >= 50:
            if hero_action == 'raise':
                return 'call', 0
            return 'limp', int(bb)
        elif strength >= 38:
            if hero_action == 'raise':
                return 'fold', 0
            return 'limp', int(bb)
        else:
            return 'fold', 0

    else:  # Agressivo
        if strength >= 84:
            if hero_action in ('check', 'limp'):
                return 'raise', int(bb * 3)
            if hero_action == 'raise':
                return '3-bet', int(bb * 10)
            return '4-bet', int(bb * 22)
        elif strength >= 58:
            if hero_action in ('check', 'limp'):
                return 'raise', int(bb * 2.5)
            if hero_action == 'raise':
                return 'call', 0
            return 'fold', 0
        elif strength >= 35:
            if hero_action in ('check', 'limp'):
                return 'raise', int(bb * 2.5)
            return 'fold', 0
        else:
            if hero_action in ('check', 'limp') and random.random() < 0.25:
                return 'raise', int(bb * 2.5)
            return 'fold', 0

# ================================================================
# LOGICA DO OPONENTE — POS-FLOP (por tipo)
# ================================================================
def opp_postflop_action(opp_type, pot, hero_action='none'):
    """Retorna (acao_str, valor_em_chips)"""
    r = random.random()
    if hero_action == 'none':
        # Oponente age primeiro
        if opp_type == 'Nit':
            if r < 0.25:
                return 'bet', int(pot * 0.55)
            return 'check', 0
        elif opp_type == 'Passivo':
            if r < 0.18:
                return 'bet', int(pot * 0.45)
            return 'check', 0
        else:  # Agressivo
            if r < 0.65:
                return 'bet', int(pot * 0.75)
            return 'check', 0
    else:
        # Oponente responde a raise do Master
        if opp_type == 'Nit':
            if r < 0.25:
                return 'call', 0
            return 'fold', 0
        elif opp_type == 'Passivo':
            if r < 0.55:
                return 'call', 0
            return 'fold', 0
        else:  # Agressivo
            if r < 0.45:
                return 'call', 0
            elif r < 0.65:
                return 'fold', 0
            return 're-raise', int(pot * 1.2)

# ================================================================
# AI — ANALISE FINAL DA MAO COMPLETA
# ================================================================
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
        max_tokens=2000
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
            f"\nEsta e uma ANALISE ICM. Sobram {data.get('jogadores_restantes','?')} jogadores. "
            f"Estrutura: {data.get('estrutura','?')}. "
            "A sobrevivencia e o salto de payout pesam mais do que o EV de chips puro."
        )
    return f"""
Analise esta mao de Sit & Go para o Master:

MASTER:
- Cartas: {data.get('cartas_master','?')}
- Posicao: {data.get('posicao_master','?')}
- Stack: {data.get('stack_master','?')} BBs
- Blinds: {data.get('blinds','?')}
- Jogadores restantes: {data.get('jogadores_restantes','?')}
- Estrutura de premiacao: {data.get('estrutura','?')}

BOARD: Flop {data.get('flop','-')} | Turn {data.get('turn','-')} | River {data.get('river','-')}

OPONENTE:
- Cartas: {data.get('cartas_oponente','desconhecidas')}
- Posicao: {data.get('posicao_oponente','desconhecida')}
- Stack: {data.get('stack_oponente','desconhecido')}
- Tendencias: {data.get('tendencias_oponente','nao informadas')}

DESCRICAO DA MAO: {data.get('acao','?')}
{icm_bloco}

Retorne APENAS este JSON:
{{
  "analise": "analise detalhada de 3 a 5 paragrafos",
  "pontos_fortes": ["ponto 1","ponto 2"],
  "pontos_melhoria": ["ponto 1","ponto 2"],
  "decisao_ideal": "Raise ou Call ou Fold",
  "range_raise": ["AA","KK","AKs","AKo"],
  "range_call": ["JJ","TT","AQs"],
  "nota": 7
}}
"""

def build_full_sim_analysis_prompt(hand, actions_log, folded_preflop=False):
    if folded_preflop:
        return f"""
O Master fez FOLD no pre-flop nesta situacao de Sit & Go.

SITUACAO:
- Cartas do Master: {hand['cartas']}
- Posicao do Master: {hand['posicao']}
- Tipo do Oponente: {hand['opp_type']}
- Stack: {hand['stack']} BBs
- Blinds: {hand['blinds']}

LINHA DE ACOES:
{actions_log}

Avalie APENAS a decisao de fold pre-flop. Nao avalie flop/turn/river pois a mao nao chegou la.

Retorne APENAS este JSON:
{{
  "analise_geral": "analise curta de 1 a 2 paragrafos sobre o fold pre-flop",
  "preflop": "avaliacao detalhada do fold pre-flop",
  "flop": "",
  "turn": "",
  "river": "",
  "nota_preflop": 7,
  "nota_flop": null,
  "nota_turn": null,
  "nota_river": null,
  "nota_geral": 7,
  "decisao_ideal": "o que o Master deveria ter feito no pre-flop",
  "pontos_fortes": ["ponto 1"],
  "pontos_melhoria": ["ponto 1"],
  "range_raise": ["AA","KK","AKs"],
  "range_call": ["JJ","TT","AQs"]
}}
"""
    return f"""
Analise a MAO COMPLETA do Master em um Sit & Go, rua por rua.

SITUACAO:
- Cartas do Master: {hand['cartas']}
- Cartas do Oponente: {hand['opp_cards']}
- Posicao do Master: {hand['posicao']}
- Tipo do Oponente: {hand['opp_type']}
- Stack: {hand['stack']} BBs
- Blinds: {hand['blinds']}

LINHA DE ACOES:
{actions_log}

Avalie cada decisao do Master rua por rua. So avalie ruas que realmente aconteceram na mao.

Retorne APENAS este JSON:
{{
  "analise_geral": "analise da linha completa em 3 paragrafos",
  "preflop": "avaliacao pre-flop",
  "flop": "avaliacao flop",
  "turn": "avaliacao turn",
  "river": "avaliacao river",
  "nota_preflop": 7,
  "nota_flop": 8,
  "nota_turn": 6,
  "nota_river": 7,
  "nota_geral": 7,
  "decisao_ideal": "qual linha ideal o Master deveria ter jogado",
  "pontos_fortes": ["ponto 1"],
  "pontos_melhoria": ["ponto 1"],
  "range_raise": ["AA","KK","AKs"],
  "range_call": ["JJ","TT","AQs"]
}}
"""

def calcular_pot_odds(pot, aposta):
    if aposta <= 0:
        return None, None
    pote_total = pot + aposta
    pot_odds_pct = round(aposta / pote_total * 100, 1)
    ratio = round(pote_total / aposta, 2)
    return pot_odds_pct, ratio

def build_single_sim_prompt(hand, decisao_master):
    pot_odds_pct, ratio = calcular_pot_odds(hand['pot'], hand['aposta_oponente'])
    if pot_odds_pct:
        pot_block = (
            f"- Pot odds: {pot_odds_pct}% (equity minima para call ser lucrativo)\n"
            f"- Ratio pote/aposta: {ratio}:1"
        )
    else:
        pot_block = "- Sem aposta do oponente (Master age primeiro)"
    return f"""
Avalie esta decisao do Master em um Sit & Go com criterio estatistico rigoroso.

SITUACAO:
- Cartas: {hand['cartas']}
- Posicao: {hand['posicao']}
- Stack: {hand['stack']} BBs
- Blinds: {hand['blinds']}
- Jogadores restantes: {hand['jogadores_restantes']}
- Board: Flop {hand['flop']} | Turn {hand['turn']}
- Pote: {hand['pot']} fichas
- Aposta do oponente: {hand['aposta_oponente']} fichas
{pot_block}

DECISAO DO MASTER: {decisao_master}

REGRA DE PONTUACAO:
- Acertou: nota 6-10 | Errou: nota 0-5

Retorne APENAS este JSON:
{{
  "decisao_correta": "Fold ou Call ou Raise",
  "acertou": true,
  "equity_estimada": 42,
  "equity_minima_para_call": {pot_odds_pct if pot_odds_pct else 0},
  "ev_decisao_master": -15,
  "ev_decisao_correta": 30,
  "explicacao": "explicacao clara de 2 a 3 paragrafos",
  "raciocinio_ideal": "passo a passo",
  "range_raise": ["AA","KK","AKs"],
  "range_call": ["JJ","TT","AQs"],
  "nota": 7
}}
"""

# ================================================================
# EXIBICAO DE RESULTADO (revisao)
# ================================================================
def show_result(parsed, key_suffix="", board=None):
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
            for p in fortes: st.markdown(f"- {p}")
        if melhoria:
            st.markdown("**O que melhorar:**")
            for p in melhoria: st.markdown(f"- {p}")
    with col_right:
        board_t = board_to_tuple(board)
        is_dynamic = len(board_t) >= 3
        if is_dynamic:
            label_chart = f"**Range recomendado — equity calculada para board `{' '.join(board_t)}`:**"
        else:
            label_chart = "**Range recomendado — equity pre-flop:**"
        st.markdown(label_chart)
        with st.spinner("Calculando equidades para o board atual...") if is_dynamic else st.empty():
            eq_dict = calculate_all_equities(board_t)
        fig = build_range_chart(
            raise_hands=parsed.get("range_raise", []),
            call_hands=parsed.get("range_call", []),
            equity_dict=eq_dict,
        )
        st.pyplot(fig)
        plt.close(fig)

# ================================================================
# GERACAO DE CARTAS ALEATORIAS
# ================================================================
def random_card(used):
    while True:
        card = random.choice(ALL_RANKS) + random.choice(ALL_SUITS)
        if card not in used:
            used.add(card)
            return card

def generate_full_hand():
    used = set()
    hero_c1 = random_card(used)
    hero_c2 = random_card(used)
    opp_c1  = random_card(used)
    opp_c2  = random_card(used)
    flop    = [random_card(used) for _ in range(3)]
    turn    = random_card(used)
    river   = random_card(used)
    blinds_opts = ["25/50","50/100","100/200","200/400"]
    blinds = random.choice(blinds_opts)
    bb = int(blinds.split('/')[1])
    return {
        "cartas":    f"{hero_c1} {hero_c2}",
        "opp_cards": f"{opp_c1} {opp_c2}",
        "flop":      flop,
        "turn":      turn,
        "river":     river,
        "posicao":   random.choice(["BTN","CO","MP","UTG","SB","BB"]),
        "stack":     random.choice([8,10,12,15,20,25]),
        "jogadores": random.randint(3, 9),
        "blinds":    blinds,
        "bb":        bb,
        "pot":       bb * 1.5,
        "opp_type":  "Agressivo",  # definido pelo usuario
    }

# ================================================================
# INICIALIZACAO DO ESTADO DO SIMULADOR
# ================================================================
def init_sim():
    return {
        "phase":    "start",
        "hand":     None,
        "board":    [],
        "pot":      0,
        "actions":  [],  # lista de dicts {street, who, action, amount}
        "opp_act":  None,  # acao atual do oponente esperando resposta
        "result":   None,
    }

if "sim" not in st.session_state:
    st.session_state.sim = init_sim()

# ================================================================
# TABS
# ================================================================
aba_revisao, aba_simulador, aba_biblioteca = st.tabs([
    "Nova Revisao", "Simulador", "Biblioteca"
])

# ============================================================
# ABA REVISAO
# ============================================================
with aba_revisao:
    st.subheader("Registrar uma mao para estudo")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Cartas e Board")
        cartas_master  = st.text_input("Suas cartas (Master)", placeholder="Ex.: Ad Ks")
        flop_val       = st.text_input("Flop", placeholder="Ex.: 2h 7s 9c")
        turn_val       = st.text_input("Turn", placeholder="Ex.: Jh")
        river_val      = st.text_input("River", placeholder="Ex.: As")

    with col2:
        st.markdown("#### Situacao do torneio")
        posicao_master = st.selectbox("Sua posicao", ["BTN","SB","BB","UTG","MP","CO"])
        stack_master   = st.number_input("Seu stack (BBs)", min_value=1, value=20)
        blinds_val     = st.text_input("Blinds atuais", placeholder="Ex.: 100/200")
        jogadores_val  = st.number_input("Jogadores restantes", min_value=2, max_value=9, value=6)
        estrutura_val  = st.selectbox("Estrutura de premiacao", [
            "Top 3 pagam (9-max)",
            "Top 2 pagam (6-max)",
            "Heads-up (2 jogadores)",
            "Winner-take-all",
        ])

    acao_val = st.text_area("Descreva a acao da mao",
                            placeholder="Ex.: Abri 2.5BB no BTN, BB 3-betou, fui all-in...",
                            height=100)

    with st.expander("Informacoes opcionais do oponente"):
        col3, col4 = st.columns(2)
        with col3:
            cartas_op    = st.text_input("Cartas do oponente", placeholder="Ex.: Kd Qh")
            posicao_op   = st.selectbox("Posicao do oponente",
                                        ["Desconhecida","BTN","SB","BB","UTG","MP","CO"])
        with col4:
            stack_op     = st.text_input("Stack do oponente (BBs)", placeholder="Ex.: 15")
            tendencias_op= st.text_area("Tendencias do oponente",
                                        placeholder="Ex.: Muito agressivo, nao faz fold ao c-bet",
                                        height=80)

    btn1, btn2 = st.columns(2)
    with btn1:
        analisar     = st.button("Analisar mao", use_container_width=True, type="primary")
    with btn2:
        analisar_icm = st.button("Analisar com ICM", use_container_width=True)

    if analisar or analisar_icm:
        if not cartas_master or not flop_val or not acao_val:
            st.warning("Preencha ao menos: suas cartas, o flop e a descricao da acao.")
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
                    raw    = call_ai(build_review_prompt(data_rev, icm=analisar_icm))
                    parsed = parse_json(raw)
                    st.divider()
                    st.subheader("Resultado da analise")
                    board_revisao = " ".join(filter(None, [flop_val, turn_val, river_val]))
                    show_result(parsed, key_suffix="revisao", board=board_revisao)
                    try:
                        nota_num = parsed.get("nota")
                        if isinstance(nota_num, str):
                            nota_num = int(nota_num) if nota_num.isdigit() else None
                        supabase.table("maos").insert({
                            "cartas_master":  cartas_master,
                            "posicao_master": posicao_master,
                            "stack_master":   int(stack_master),
                            "flop":           flop_val,
                            "turn":           turn_val,
                            "river":          river_val,
                            "acao":           acao_val,
                            "cartas_oponente":cartas_op,
                            "analise_ia":     parsed.get("analise",""),
                            "nota":           nota_num,
                        }).execute()
                        st.success("Mao salva na biblioteca!")
                    except Exception as e:
                        st.warning(f"Analise feita, mas nao foi possivel salvar: {e}")
                except Exception as e:
                    st.error(f"Erro na analise: {e}")

# ============================================================
# ABA SIMULADOR — rua por rua
# ============================================================
with aba_simulador:
    st.subheader("Simulador de Decisoes — Mao Completa")
    st.caption("Jogue uma mao do pre-flop ao river. A IA avalia cada decisao ao final.")

    sim = st.session_state.sim

    # --- Tipo de oponente (sempre visivel) ---
    if sim["phase"] == "start":
        opp_type_sel = st.selectbox(
            "Tipo de oponente",
            ["Agressivo", "Passivo", "Nit"],
            help="Define como o oponente vai agir."
        )
        if st.button("Gerar nova mao", type="primary"):
            hand = generate_full_hand()
            hand["opp_type"] = opp_type_sel
            strength = get_preflop_strength(hand["cartas"])
            opp_a, opp_v = opp_preflop_action(
                opp_type_sel, "check", strength, hand["bb"]
            )
            sim.update({
                "phase":   "preflop_master",
                "hand":    hand,
                "board":   [],
                "pot":     hand["pot"],
                "actions": [],
                "opp_act": {"action": opp_a, "value": opp_v},
                "result":  None,
            })
            st.rerun()

    else:
        hand   = sim["hand"]
        board  = sim["board"]
        pot    = sim["pot"]
        phase  = sim["phase"]

        # Mapa de fase → street para a mesa visual
        phase_street_map = {
            "preflop_master":  "preflop",
            "preflop_3bet":    "preflop",
            "flop_master":     "flop",
            "turn_master":     "turn",
            "river_master":    "river",
            "showdown":        "showdown",
        }
        current_street = phase_street_map.get(phase, "preflop")

        # Mesa visual
        fig_table = draw_poker_table(
            hero_cards=hand["cartas"],
            opp_cards=hand["opp_cards"],
            board=board,
            pot=int(pot),
            street=current_street,
            face_down_opp=(phase != "showdown"),
        )
        st.pyplot(fig_table)
        plt.close(fig_table)

        # Info do topo
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Cartas", hand["cartas"])
        i2.metric("Posicao", hand["posicao"])
        i3.metric("Stack", f"{hand['stack']} BBs")
        i4.metric("Blinds", hand["blinds"])

        st.divider()

        # --------------------------------------------------
        # PRE-FLOP — Master responde a acao do oponente
        # --------------------------------------------------
        if phase == "preflop_master":
            opp_a = sim["opp_act"]
            if opp_a["action"] in ("raise","3-bet","4-bet"):
                st.warning(
                    f"Oponente **{opp_a['action']}** para {opp_a['value']} fichas. "
                    "O que voce faz?"
                )
            elif opp_a["action"] == "limp":
                st.info("Oponente **limpa** (call do BB). O que voce faz?")
            else:
                st.info(f"Oponente **{opp_a['action']}**. O que voce faz?")

            bf, bc, br = st.columns(3)
            with bf:
                if st.button("FOLD", key="pf_fold", use_container_width=True):
                    sim["actions"].append(
                        {"street":"preflop","who":"master","action":"fold","amount":0}
                    )
                    sim["phase"] = "showdown"
                    sim["board"] = hand["flop"] + [hand["turn"], hand["river"]]
                    sim["folded_preflop"] = True
                    with st.spinner("Analisando mao..."):
                        log = "\n".join(
                            f"{a['street'].upper()} | {a['who']}: {a['action']} {a['amount']}"
                            for a in sim["actions"]
                        )
                        raw = call_ai(build_full_sim_analysis_prompt(hand, log, folded_preflop=True))
                        sim["result"] = parse_json(raw)
                    st.rerun()
            with bc:
                if st.button("CALL", key="pf_call", use_container_width=True):
                    sim["actions"].append(
                        {"street":"preflop","who":"master","action":"call","amount":opp_a["value"]}
                    )
                    sim["pot"] = pot + opp_a["value"]
                    opp_postflop, opp_val = opp_postflop_action(hand["opp_type"], sim["pot"])
                    sim["board"] = hand["flop"][:]
                    sim["opp_act"] = {"action": opp_postflop, "value": opp_val}
                    sim["phase"] = "flop_master"
                    st.rerun()
            with br:
                if st.button("RAISE", key="pf_raise", use_container_width=True, type="primary"):
                    raise_val = int(hand["bb"] * 2.5)
                    sim["actions"].append(
                        {"street":"preflop","who":"master","action":"raise","amount":raise_val}
                    )
                    sim["pot"] = pot + raise_val
                    strength = get_preflop_strength(hand["opp_cards"])
                    opp_resp, opp_rval = opp_preflop_action(
                        hand["opp_type"], "raise", strength, hand["bb"]
                    )
                    sim["opp_act"] = {"action": opp_resp, "value": opp_rval}
                    if opp_resp == "3-bet":
                        sim["phase"] = "preflop_3bet"
                    elif opp_resp == "fold":
                        sim["actions"].append(
                            {"street":"preflop","who":"oponente","action":"fold","amount":0}
                        )
                        sim["phase"] = "showdown"
                        sim["board"] = hand["flop"] + [hand["turn"], hand["river"]]
                        with st.spinner("Analisando mao..."):
                            log = "\n".join(
                                f"{a['street'].upper()} | {a['who']}: {a['action']} {a['amount']}"
                                for a in sim["actions"]
                            )
                            raw = call_ai(build_full_sim_analysis_prompt(hand, log))
                            sim["result"] = parse_json(raw)
                    else:
                        sim["board"] = hand["flop"][:]
                        opp_postflop, opp_val = opp_postflop_action(hand["opp_type"], sim["pot"])
                        sim["opp_act"] = {"action": opp_postflop, "value": opp_val}
                        sim["phase"] = "flop_master"
                    st.rerun()

        # --------------------------------------------------
        # PRE-FLOP — Oponente fez 3-bet, Master responde
        # --------------------------------------------------
        elif phase == "preflop_3bet":
            opp_a = sim["opp_act"]
            st.warning(
                f"Oponente fez **{opp_a['action']}** para {opp_a['value']} fichas! "
                "O que voce faz?"
            )
            bf2, bc2, br2 = st.columns(3)
            with bf2:
                if st.button("FOLD", key="3bet_fold", use_container_width=True):
                    sim["actions"].append(
                        {"street":"preflop","who":"master","action":"fold","amount":0}
                    )
                    sim["phase"] = "showdown"
                    sim["board"] = hand["flop"] + [hand["turn"], hand["river"]]
                    sim["folded_preflop"] = True
                    with st.spinner("Analisando mao..."):
                        log = "\n".join(
                            f"{a['street'].upper()} | {a['who']}: {a['action']} {a['amount']}"
                            for a in sim["actions"]
                        )
                        raw = call_ai(build_full_sim_analysis_prompt(hand, log, folded_preflop=True))
                        sim["result"] = parse_json(raw)
                    st.rerun()
            with bc2:
                if st.button("CALL", key="3bet_call", use_container_width=True):
                    sim["actions"].append(
                        {"street":"preflop","who":"master","action":"call","amount":opp_a["value"]}
                    )
                    sim["pot"] += opp_a["value"]
                    opp_postflop, opp_val = opp_postflop_action(hand["opp_type"], sim["pot"])
                    sim["board"] = hand["flop"][:]
                    sim["opp_act"] = {"action": opp_postflop, "value": opp_val}
                    sim["phase"] = "flop_master"
                    st.rerun()
            with br2:
                if st.button("4-BET", key="3bet_4bet", use_container_width=True, type="primary"):
                    val4 = int(hand["bb"] * 22)
                    sim["actions"].append(
                        {"street":"preflop","who":"master","action":"4-bet","amount":val4}
                    )
                    sim["pot"] += val4
                    sim["board"] = hand["flop"] + [hand["turn"], hand["river"]]
                    sim["phase"] = "showdown"
                    with st.spinner("Analisando mao..."):
                        log = "\n".join(
                            f"{a['street'].upper()} | {a['who']}: {a['action']} {a['amount']}"
                            for a in sim["actions"]
                        )
                        raw = call_ai(build_full_sim_analysis_prompt(hand, log))
                        sim["result"] = parse_json(raw)
                    st.rerun()

        # --------------------------------------------------
        # FLOP / TURN / RIVER — logica identica por rua
        # --------------------------------------------------
        elif phase in ("flop_master", "turn_master", "river_master"):
            street_label = {"flop_master":"FLOP","turn_master":"TURN","river_master":"RIVER"}[phase]
            opp_a = sim["opp_act"]

            if opp_a["action"] == "bet":
                st.warning(
                    f"**{street_label}** — Oponente **aposta {opp_a['value']} fichas** "
                    f"(pot: {int(pot)}). O que voce faz?"
                )
                bf3, bc3, br3 = st.columns(3)
                buttons = [
                    ("FOLD",  bf3, "fold",  0),
                    ("CALL",  bc3, "call",  opp_a["value"]),
                    ("RAISE", br3, "raise", opp_a["value"] * 2),
                ]
            else:
                st.info(
                    f"**{street_label}** — Oponente **checa** (pot: {int(pot)}). "
                    "O que voce faz?"
                )
                bf3, bc3, br3 = st.columns(3)
                buttons = [
                    ("CHECK", bf3, "check", 0),
                    ("BET",   bc3, "bet",   int(pot * 0.6)),
                    ("RAISE", br3, "raise", int(pot * 0.75)),
                ]

            next_phase = {
                "flop_master":  "turn_master",
                "turn_master":  "river_master",
                "river_master": "showdown",
            }[phase]
            next_board_card = {
                "flop_master":  hand["turn"],
                "turn_master":  hand["river"],
                "river_master": None,
            }[phase]

            for btn_label, col, action_str, amount in buttons:
                with col:
                    key_btn = f"{phase}_{action_str}"
                    is_primary = action_str in ("raise","bet")
                    if st.button(btn_label, key=key_btn,
                                 use_container_width=True,
                                 type="primary" if is_primary else "secondary"):
                        sim["actions"].append({
                            "street": street_label.lower(),
                            "who": "master",
                            "action": action_str,
                            "amount": amount,
                        })
                        sim["pot"] += amount

                        if action_str == "fold" or next_phase == "showdown":
                            if next_board_card:
                                sim["board"].append(next_board_card)
                            sim["board"] = hand["flop"] + [hand["turn"], hand["river"]]
                            sim["phase"] = "showdown"
                            with st.spinner("Analisando mao completa..."):
                                log = "\n".join(
                                    f"{a['street'].upper()} | {a['who']}: {a['action']} {a['amount']}"
                                    for a in sim["actions"]
                                )
                                raw = call_ai(build_full_sim_analysis_prompt(hand, log))
                                sim["result"] = parse_json(raw)
                        else:
                            if next_board_card:
                                sim["board"].append(next_board_card)
                            opp_next, opp_nval = opp_postflop_action(hand["opp_type"], sim["pot"])
                            sim["opp_act"] = {"action": opp_next, "value": opp_nval}
                            sim["phase"] = next_phase
                        st.rerun()

        # --------------------------------------------------
        # SHOWDOWN — resultado final
        # --------------------------------------------------
        elif phase == "showdown":
            result = sim.get("result", {})
            st.success("Mao concluida! Aqui esta a analise completa:")

            nota_g = result.get("nota_geral", "?")
            st.markdown(f"### Nota geral: **{nota_g} / 10**")

            folded_pf = sim.get("folded_preflop", False)
            if folded_pf:
                st.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
            else:
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
                r2.metric("Flop",     f"{result.get('nota_flop','?')}/10")
                r3.metric("Turn",     f"{result.get('nota_turn','?')}/10")
                r4.metric("River",    f"{result.get('nota_river','?')}/10")

            st.markdown("**Analise geral:**")
            st.info(result.get("analise_geral", ""))

            with st.expander("Detalhes por rua"):
                for rua in ("preflop","flop","turn","river"):
                    txt = result.get(rua, "")
                    if txt:
                        st.markdown(f"**{rua.upper()}:** {txt}")

            ideal = result.get("decisao_ideal","")
            if ideal:
                st.markdown("**Linha ideal:**")
                st.warning(ideal)

            fortes = result.get("pontos_fortes",[])
            melhoria = result.get("pontos_melhoria",[])
            c_left, c_right = st.columns(2)
            with c_left:
                if fortes:
                    st.markdown("**Pontos fortes:**")
                    for p in fortes: st.markdown(f"- {p}")
            with c_right:
                if melhoria:
                    st.markdown("**O que melhorar:**")
                    for p in melhoria: st.markdown(f"- {p}")

            result["decisao_ideal"] = result.get("decisao_ideal", result.get("decisao_correta", "?"))
            result["analise"] = result.get("analise_geral", result.get("analise", ""))
            show_result(result, key_suffix="showdown",
                        board=sim["board"])

            if st.button("Nova mao", type="primary"):
                st.session_state.sim = init_sim()
                st.rerun()

# ============================================================
# ABA BIBLIOTECA
# ============================================================
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
            st.info("Nenhuma mao salva ainda. Registre sua primeira mao na aba Nova Revisao!")
        else:
            for mao in maos:
                nota_label = mao.get("nota","?")
                titulo = (
                    f"{mao.get('cartas_master','?')}  |  "
                    f"{mao.get('posicao_master','?')}  |  "
                    f"Nota: {nota_label}/10"
                )
                with st.expander(titulo):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Stack:** {mao.get('stack_master','?')} BBs")
                        st.markdown(f"**Flop:** {mao.get('flop','-')}")
                        st.markdown(f"**Turn:** {mao.get('turn','-')}")
                        st.markdown(f"**River:** {mao.get('river','-')}")
                    with col_b:
                        if mao.get("cartas_oponente"):
                            st.markdown(f"**Oponente:** {mao['cartas_oponente']}")
                        st.markdown("**Analise da IA:**")
                        st.info(mao.get("analise_ia",""))
    except Exception as e:
        st.error(f"Erro ao carregar biblioteca: {e}")
