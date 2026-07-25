--- a//home/ubuntu/app.py
+++ b//home/ubuntu/app.py
@@ -1034,43 +1034,43 @@
-  1033	            r1, r2, r3, r4 = st.columns(4)
-  1034	            r1.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
-  1035	            r2.metric("Flop",     f"{result.get('nota_flop','?')}/10")
-  1036	            r3.metric("Turn",     f"{result.get('nota_turn','?')}/10")
-  1037	            r4.metric("River",    f"{result.get('nota_river','?')}/10")
-  1038	
-  1039	            st.markdown("**Analise geral:**")
-  1040	            st.info(result.get("analise_geral", ""))
-  1041	
-  1042	            with st.expander("Detalhes por rua"):
-  1043	                for rua in ("preflop","flop","turn","river"):
-  1044	                    txt = result.get(rua, "")
-  1045	                    if txt:
-  1046	                        st.markdown(f"**{rua.upper()}:** {txt}")
-  1047	
-  1048	            ideal = result.get("decisao_ideal","")
-  1049	            if ideal:
-  1050	                st.markdown("**Linha ideal:**")
-  1051	                st.warning(ideal)
-  1052	
-  1053	            fortes = result.get("pontos_fortes",[])
-  1054	            melhoria = result.get("pontos_melhoria",[])
-  1055	            c_left, c_right = st.columns(2)
-  1056	            with c_left:
-  1057	                if fortes:
-  1058	                    st.markdown("**Pontos fortes:**")
-  1059	                    for p in fortes: st.markdown(f"- {p}")
-  1060	            with c_right:
-  1061	                if melhoria:
-  1062	                    st.markdown("**O que melhorar:**")
-  1063	                    for p in melhoria: st.markdown(f"- {p}")
-  1064	
-  1065	            st.markdown("**Range recomendado:**")
-  1066	            fig_range = build_range_chart(
-  1067	                raise_hands=result.get("range_raise",[]),
-  1068	                call_hands=result.get("range_call",[])
-  1069	            )
-  1070	            st.pyplot(fig_range)
-  1071	            plt.close(fig_range)
-  1072	
-  1073	            if st.button("Nova mao", type="primary"):
-  1074	                st.session_state.sim = init_sim()
-  1075	                st.rerun()
+  1033	            folded_pf = sim.get("folded_preflop", False)
+  1034	            if folded_pf:
+  1035	                st.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
+  1036	            else:
+  1037	                r1, r2, r3, r4 = st.columns(4)
+  1038	                r1.metric("Pre-flop", f"{result.get('nota_preflop','?')}/10")
+  1039	                r2.metric("Flop",     f"{result.get('nota_flop','?')}/10")
+  1040	                r3.metric("Turn",     f"{result.get('nota_turn','?')}/10")
+  1041	                r4.metric("River",    f"{result.get('nota_river','?')}/10")
+  1042	
+  1043	            st.markdown("**Analise geral:**")
+  1044	            st.info(result.get("analise_geral", ""))
+  1045	
+  1046	            with st.expander("Detalhes por rua"):
+  1047	                for rua in ("preflop","flop","turn","river"):
+  1048	                    txt = result.get(rua, "")
+  1049	                    if txt:
+  1050	                        st.markdown(f"**{rua.upper()}:** {txt}")
+  1051	
+  1052	            ideal = result.get("decisao_ideal","")
+  1053	            if ideal:
+  1054	                st.markdown("**Linha ideal:**")
+  1055	                st.warning(ideal)
+  1056	
+  1057	            fortes = result.get("pontos_fortes",[])
+  1058	            melhoria = result.get("pontos_melhoria",[])
+  1059	            c_left, c_right = st.columns(2)
+  1060	            with c_left:
+  1061	                if fortes:
+  1062	                    st.markdown("**Pontos fortes:**")
+  1063	                    for p in fortes: st.markdown(f"- {p}")
+  1064	            with c_right:
+  1065	                if melhoria:
+  1066	                    st.markdown("**O que melhorar:**")
+  1067	                    for p in melhoria: st.markdown(f"- {p}")
+  1068	
+  1069	            st.markdown("**Range recomendado:**")
+  1070	            fig_range = build_range_chart(
+  1071	                raise_hands=result.get("range_raise",[]),
+  1072	                call_hands=result.get("range_call",[])
+  1073	            )
+  1074	            st.pyplot(fig_range)
+  1075	            plt.close(fig_range)
@@ -1078,39 +1078,43 @@
-  1077	# ============================================================
-  1078	# ABA BIBLIOTECA
-  1079	# ============================================================
-  1080	with aba_biblioteca:
-  1081	    st.subheader("Suas maos salvas")
-  1082	    try:
-  1083	        resp = (
-  1084	            supabase.table("maos")
-  1085	            .select("*")
-  1086	            .order("created_at", desc=True)
-  1087	            .limit(30)
-  1088	            .execute()
-  1089	        )
-  1090	        maos = resp.data
-  1091	        if not maos:
-  1092	            st.info("Nenhuma mao salva ainda. Registre sua primeira mao na aba Nova Revisao!")
-  1093	        else:
-  1094	            for mao in maos:
-  1095	                nota_label = mao.get("nota","?")
-  1096	                titulo = (
-  1097	                    f"{mao.get('cartas_master','?')}  |  "
-  1098	                    f"{mao.get('posicao_master','?')}  |  "
-  1099	                    f"Nota: {nota_label}/10"
-  1100	                )
-  1101	                with st.expander(titulo):
-  1102	                    col_a, col_b = st.columns(2)
-  1103	                    with col_a:
-  1104	                        st.markdown(f"**Stack:** {mao.get('stack_master','?')} BBs")
-  1105	                        st.markdown(f"**Flop:** {mao.get('flop','-')}")
-  1106	                        st.markdown(f"**Turn:** {mao.get('turn','-')}")
-  1107	                        st.markdown(f"**River:** {mao.get('river','-')}")
-  1108	                    with col_b:
-  1109	                        if mao.get("cartas_oponente"):
-  1110	                            st.markdown(f"**Oponente:** {mao['cartas_oponente']}")
-  1111	                        st.markdown("**Analise da IA:**")
-  1112	                        st.info(mao.get("analise_ia",""))
-  1113	    except Exception as e:
-  1114	        st.error(f"Erro ao carregar biblioteca: {e}")
-  1115	
+  1077	            if st.button("Nova mao", type="primary"):
+  1078	                st.session_state.sim = init_sim()
+  1079	                st.rerun()
+  1080	
+  1081	# ============================================================
+  1082	# ABA BIBLIOTECA
+  1083	# ============================================================
+  1084	with aba_biblioteca:
+  1085	    st.subheader("Suas maos salvas")
+  1086	    try:
+  1087	        resp = (
+  1088	            supabase.table("maos")
+  1089	            .select("*")
+  1090	            .order("created_at", desc=True)
+  1091	            .limit(30)
+  1092	            .execute()
+  1093	        )
+  1094	        maos = resp.data
+  1095	        if not maos:
+  1096	            st.info("Nenhuma mao salva ainda. Registre sua primeira mao na aba Nova Revisao!")
+  1097	        else:
+  1098	            for mao in maos:
+  1099	                nota_label = mao.get("nota","?")
+  1100	                titulo = (
+  1101	                    f"{mao.get('cartas_master','?')}  |  "
+  1102	                    f"{mao.get('posicao_master','?')}  |  "
+  1103	                    f"Nota: {nota_label}/10"
+  1104	                )
+  1105	                with st.expander(titulo):
+  1106	                    col_a, col_b = st.columns(2)
+  1107	                    with col_a:
+  1108	                        st.markdown(f"**Stack:** {mao.get('stack_master','?')} BBs")
+  1109	                        st.markdown(f"**Flop:** {mao.get('flop','-')}")
+  1110	                        st.markdown(f"**Turn:** {mao.get('turn','-')}")
+  1111	                        st.markdown(f"**River:** {mao.get('river','-')}")
+  1112	                    with col_b:
+  1113	                        if mao.get("cartas_oponente"):
+  1114	                            st.markdown(f"**Oponente:** {mao['cartas_oponente']}")
+  1115	                        st.markdown("**Analise da IA:**")
+  1116	                        st.info(mao.get("analise_ia",""))
+  1117	    except Exception as e:
+  1118	        st.error(f"Erro ao carregar biblioteca: {e}")
+  1119	
