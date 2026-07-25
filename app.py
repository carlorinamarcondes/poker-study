--- a//home/ubuntu/app.py
+++ b//home/ubuntu/app.py
@@ -208,2 +208,2 @@
-   207	        st.pyplot(fig, key=f"chart_{key_suffix}")
-   208	
+   207	        st.pyplot(fig)
+   208	        plt.close(fig)
@@ -211,5 +211,5 @@
-   210	# ===================== SIMULADOR =====================
-   211	
-   212	ALL_RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
-   213	ALL_SUITS = ['s', 'h', 'd', 'c']
-   214	
+   210	
+   211	# ===================== SIMULADOR =====================
+   212	
+   213	ALL_RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
+   214	ALL_SUITS = ['s', 'h', 'd', 'c']
@@ -217,7 +217,7 @@
-   216	def random_card(used):
-   217	    while True:
-   218	        card = random.choice(ALL_RANKS) + random.choice(ALL_SUITS)
-   219	        if card not in used:
-   220	            used.add(card)
-   221	            return card
-   222	
+   216	
+   217	def random_card(used):
+   218	    while True:
+   219	        card = random.choice(ALL_RANKS) + random.choice(ALL_SUITS)
+   220	        if card not in used:
+   221	            used.add(card)
+   222	            return card
@@ -225,22 +225,22 @@
-   224	def generate_situation():
-   225	    used = set()
-   226	    c1 = random_card(used)
-   227	    c2 = random_card(used)
-   228	    flop = [random_card(used) for _ in range(3)]
-   229	    turn = random_card(used)
-   230	
-   231	    aposta_oponente = random.choice([0, 0, 30, 50, 100, 150, 200])
-   232	    pot = random.randint(2, 10) * 50
-   233	
-   234	    return {
-   235	        "cartas": f"{c1} {c2}",
-   236	        "flop": " ".join(flop),
-   237	        "turn": turn,
-   238	        "posicao": random.choice(["BTN", "SB", "BB", "UTG", "MP", "CO"]),
-   239	        "stack": random.choice([8, 10, 12, 15, 20, 25]),
-   240	        "jogadores_restantes": random.randint(3, 9),
-   241	        "blinds": random.choice(["25/50", "50/100", "100/200", "200/400"]),
-   242	        "pot": pot,
-   243	        "aposta_oponente": aposta_oponente,
-   244	    }
-   245	
+   224	
+   225	def generate_situation():
+   226	    used = set()
+   227	    c1 = random_card(used)
+   228	    c2 = random_card(used)
+   229	    flop = [random_card(used) for _ in range(3)]
+   230	    turn = random_card(used)
+   231	
+   232	    aposta_oponente = random.choice([0, 0, 30, 50, 100, 150, 200])
+   233	    pot = random.randint(2, 10) * 50
+   234	
+   235	    return {
+   236	        "cartas": f"{c1} {c2}",
+   237	        "flop": " ".join(flop),
+   238	        "turn": turn,
+   239	        "posicao": random.choice(["BTN", "SB", "BB", "UTG", "MP", "CO"]),
+   240	        "stack": random.choice([8, 10, 12, 15, 20, 25]),
+   241	        "jogadores_restantes": random.randint(3, 9),
+   242	        "blinds": random.choice(["25/50", "50/100", "100/200", "200/400"]),
+   243	        "pot": pot,
+   244	        "aposta_oponente": aposta_oponente,
+   245	    }
@@ -248,28 +248,28 @@
-   247	def build_simulator_prompt(hand, decisao_master):
-   248	    return f"""
-   249	Avalie esta decisao do Master em um Sit & Go:
-   250	
-   251	SITUACAO:
-   252	- Cartas: {hand['cartas']}
-   253	- Posicao: {hand['posicao']}
-   254	- Stack: {hand['stack']} BBs
-   255	- Blinds: {hand['blinds']}
-   256	- Jogadores restantes: {hand['jogadores_restantes']}
-   257	- Board: Flop {hand['flop']} | Turn {hand['turn']}
-   258	- Pote atual: {hand['pot']} fichas
-   259	- Aposta do oponente: {hand['aposta_oponente']} fichas
-   260	
-   261	DECISAO DO MASTER: {decisao_master}
-   262	
-   263	Retorne APENAS este JSON:
-   264	{{
-   265	  "decisao_correta": "Fold ou Call ou Raise",
-   266	  "acertou": true,
-   267	  "explicacao": "explicacao clara e didatica de 2 a 3 paragrafos",
-   268	  "raciocinio_ideal": "como pensar nessa situacao passo a passo",
-   269	  "range_raise": ["AA", "KK", "AKs"],
-   270	  "range_call": ["JJ", "TT", "AQs"],
-   271	  "nota": 8
-   272	}}
-   273	"""
-   274	
+   247	
+   248	def build_simulator_prompt(hand, decisao_master):
+   249	    return f"""
+   250	Avalie esta decisao do Master em um Sit & Go:
+   251	
+   252	SITUACAO:
+   253	- Cartas: {hand['cartas']}
+   254	- Posicao: {hand['posicao']}
+   255	- Stack: {hand['stack']} BBs
+   256	- Blinds: {hand['blinds']}
+   257	- Jogadores restantes: {hand['jogadores_restantes']}
+   258	- Board: Flop {hand['flop']} | Turn {hand['turn']}
+   259	- Pote atual: {hand['pot']} fichas
+   260	- Aposta do oponente: {hand['aposta_oponente']} fichas
+   261	
+   262	DECISAO DO MASTER: {decisao_master}
+   263	
+   264	Retorne APENAS este JSON:
+   265	{{
+   266	  "decisao_correta": "Fold ou Call ou Raise",
+   267	  "acertou": true,
+   268	  "explicacao": "explicacao clara e didatica de 2 a 3 paragrafos",
+   269	  "raciocinio_ideal": "como pensar nessa situacao passo a passo",
+   270	  "range_raise": ["AA", "KK", "AKs"],
+   271	  "range_call": ["JJ", "TT", "AQs"],
+   272	  "nota": 8
+   273	}}
+   274	"""
... (1 more changes)
