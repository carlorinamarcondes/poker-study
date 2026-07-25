--- a//home/ubuntu/app.py
+++ b//home/ubuntu/app.py
@@ -1159,21 +1159,21 @@
-  1158	            nota_g = result.get("nota_geral", "?")
-  1159	            st.markdown(f"### Nota geral: **{nota_g} / 10**")
-  1160	
-  1161	            folded_pf = sim.get("folded_preflop", False)
-  1162	            if folded_pf:
-  1163	                st.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
-  1164	            else:
-  1165	                r1, r2, r3, r4 = st.columns(4)
-  1166	                r1.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
-  1167	                r2.metric("Flop",     f"{result.get('nota_flop','?')}/10")
-  1168	                r3.metric("Turn",     f"{result.get('nota_turn','?')}/10")
-  1169	                r4.metric("River",    f"{result.get('nota_river','?')}/10")
-  1170	
-  1171	            st.markdown("**Analise geral:**")
-  1172	            st.info(result.get("analise_geral", ""))
-  1173	
-  1174	            with st.expander("Detalhes por rua"):
-  1175	                for rua in ("preflop","flop","turn","river"):
-  1176	                    txt = result.get(rua, "")
-  1177	                    if txt:
-  1178	                        st.markdown(f"**{rua.upper()}:** {txt}")
+  1158	            # Revela tipo do oponente se era aleatorio
+  1159	            if hand.get("opp_type_hidden", False):
+  1160	                tipo_icons = {"Agressivo": "🔥", "Passivo": "🐢", "Nit": "🧊"}
+  1161	                icone = tipo_icons.get(hand["opp_type"], "🎲")
+  1162	                st.info(
+  1163	                    f"{icone} **Revelacao!** O oponente era do tipo **{hand['opp_type']}**. "
+  1164	                    "Voce conseguiu ler o perfil dele durante a mao?"
+  1165	                )
+  1166	
+  1167	            nota_g = result.get("nota_geral", "?")
+  1168	            st.markdown(f"### Nota geral: **{nota_g} / 10**")
+  1169	
+  1170	            folded_pf = sim.get("folded_preflop", False)
+  1171	            if folded_pf:
+  1172	                st.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
+  1173	            else:
+  1174	                r1, r2, r3, r4 = st.columns(4)
+  1175	                r1.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
+  1176	                r2.metric("Flop",     f"{result.get('nota_flop','?')}/10")
+  1177	                r3.metric("Turn",     f"{result.get('nota_turn','?')}/10")
+  1178	                r4.metric("River",    f"{result.get('nota_river','?')}/10")
@@ -1181,25 +1181,25 @@
-  1180	            ideal = result.get("decisao_ideal","")
-  1181	            if ideal:
-  1182	                st.markdown("**Linha ideal:**")
-  1183	                st.warning(ideal)
-  1184	
-  1185	            fortes = result.get("pontos_fortes",[])
-  1186	            melhoria = result.get("pontos_melhoria",[])
-  1187	            c_left, c_right = st.columns(2)
-  1188	            with c_left:
-  1189	                if fortes:
-  1190	                    st.markdown("**Pontos fortes:**")
-  1191	                    for p in fortes: st.markdown(f"- {p}")
-  1192	            with c_right:
-  1193	                if melhoria:
-  1194	                    st.markdown("**O que melhorar:**")
-  1195	                    for p in melhoria: st.markdown(f"- {p}")
-  1196	
-  1197	            result["decisao_ideal"] = result.get("decisao_ideal", result.get("decisao_correta", "?"))
-  1198	            result["analise"] = result.get("analise_geral", result.get("analise", ""))
-  1199	            show_result(result, key_suffix="showdown",
-  1200	                        board=sim["board"])
-  1201	
-  1202	            if st.button("Nova mao", type="primary"):
-  1203	                st.session_state.sim = init_sim()
-  1204	                st.rerun()
+  1180	            st.markdown("**Analise geral:**")
+  1181	            st.info(result.get("analise_geral", ""))
+  1182	
+  1183	            with st.expander("Detalhes por rua"):
+  1184	                for rua in ("preflop","flop","turn","river"):
+  1185	                    txt = result.get(rua, "")
+  1186	                    if txt:
+  1187	                        st.markdown(f"**{rua.upper()}:** {txt}")
+  1188	
+  1189	            ideal = result.get("decisao_ideal","")
+  1190	            if ideal:
+  1191	                st.markdown("**Linha ideal:**")
+  1192	                st.warning(ideal)
+  1193	
+  1194	            fortes = result.get("pontos_fortes",[])
+  1195	            melhoria = result.get("pontos_melhoria",[])
+  1196	            c_left, c_right = st.columns(2)
+  1197	            with c_left:
+  1198	                if fortes:
+  1199	                    st.markdown("**Pontos fortes:**")
+  1200	                    for p in fortes: st.markdown(f"- {p}")
+  1201	            with c_right:
+  1202	                if melhoria:
+  1203	                    st.markdown("**O que melhorar:**")
+  1204	                    for p in melhoria: st.markdown(f"- {p}")
@@ -1207,39 +1207,48 @@
-  1206	# ============================================================
-  1207	# ABA BIBLIOTECA
-  1208	# ============================================================
-  1209	with aba_biblioteca:
-  1210	    st.subheader("Suas maos salvas")
-  1211	    try:
-  1212	        resp = (
-  1213	            supabase.table("maos")
-  1214	            .select("*")
-  1215	            .order("created_at", desc=True)
-  1216	            .limit(30)
-  1217	            .execute()
-  1218	        )
-  1219	        maos = resp.data
-  1220	        if not maos:
-  1221	            st.info("Nenhuma mao salva ainda. Registre sua primeira mao na aba Nova Revisao!")
-  1222	        else:
-  1223	            for mao in maos:
-  1224	                nota_label = mao.get("nota","?")
-  1225	                titulo = (
-  1226	                    f"{mao.get('cartas_master','?')}  |  "
-  1227	                    f"{mao.get('posicao_master','?')}  |  "
-  1228	                    f"Nota: {nota_label}/10"
-  1229	                )
-  1230	                with st.expander(titulo):
-  1231	                    col_a, col_b = st.columns(2)
-  1232	                    with col_a:
-  1233	                        st.markdown(f"**Stack:** {mao.get('stack_master','?')} BBs")
-  1234	                        st.markdown(f"**Flop:** {mao.get('flop','-')}")
-  1235	                        st.markdown(f"**Turn:** {mao.get('turn','-')}")
-  1236	                        st.markdown(f"**River:** {mao.get('river','-')}")
-  1237	                    with col_b:
-  1238	                        if mao.get("cartas_oponente"):
-  1239	                            st.markdown(f"**Oponente:** {mao['cartas_oponente']}")
-  1240	                        st.markdown("**Analise da IA:**")
-  1241	                        st.info(mao.get("analise_ia",""))
-  1242	    except Exception as e:
-  1243	        st.error(f"Erro ao carregar biblioteca: {e}")
-  1244	
+  1206	            result["decisao_ideal"] = result.get("decisao_ideal", result.get("decisao_correta", "?"))
+  1207	            result["analise"] = result.get("analise_geral", result.get("analise", ""))
+  1208	            show_result(result, key_suffix="showdown",
+  1209	                        board=sim["board"])
+  1210	
+  1211	            if st.button("Nova mao", type="primary"):
+  1212	                st.session_state.sim = init_sim()
+  1213	                st.rerun()
+  1214	
+  1215	# ============================================================
+  1216	# ABA BIBLIOTECA
+  1217	# ============================================================
+  1218	with aba_biblioteca:
+  1219	    st.subheader("Suas maos salvas")
+  1220	    try:
+  1221	        resp = (
+  1222	            supabase.table("maos")
+  1223	            .select("*")
+  1224	            .order("created_at", desc=True)
+  1225	            .limit(30)
+  1226	            .execute()
+  1227	        )
+  1228	        maos = resp.data
+  1229	        if not maos:
+  1230	            st.info("Nenhuma mao salva ainda. Registre sua primeira mao na aba Nova Revisao!")
+  1231	        else:
+  1232	            for mao in maos:
+  1233	                nota_label = mao.get("nota","?")
+  1234	                titulo = (
+  1235	                    f"{mao.get('cartas_master','?')}  |  "
+  1236	                    f"{mao.get('posicao_master','?')}  |  "
+  1237	                    f"Nota: {nota_label}/10"
+  1238	                )
+  1239	                with st.expander(titulo):
+  1240	                    col_a, col_b = st.columns(2)
+  1241	                    with col_a:
+  1242	                        st.markdown(f"**Stack:** {mao.get('stack_master','?')} BBs")
+  1243	                        st.markdown(f"**Flop:** {mao.get('flop','-')}")
+  1244	                        st.markdown(f"**Turn:** {mao.get('turn','-')}")
+  1245	                        st.markdown(f"**River:** {mao.get('river','-')}")
+  1246	                    with col_b:
+  1247	                        if mao.get("cartas_oponente"):
+  1248	                            st.markdown(f"**Oponente:** {mao['cartas_oponente']}")
+  1249	                        st.markdown("**Analise da IA:**")
+  1250	                        st.info(mao.get("analise_ia",""))
+  1251	    except Exception as e:
+  1252	        st.error(f"Erro ao carregar biblioteca: {e}")
+  1253	
