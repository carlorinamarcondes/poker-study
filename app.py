--- a//home/ubuntu/app.py
+++ b//home/ubuntu/app.py
@@ -1185,51 +1185,48 @@
-  1184	            st.markdown("**Range recomendado:**")
-  1185	            fig_range = build_range_chart(
-  1186	                raise_hands=result.get("range_raise",[]),
-  1187	                call_hands=result.get("range_call",[])
-  1188	            )
-  1189	            st.pyplot(fig_range)
-  1190	            plt.close(fig_range)
-  1191	
-  1192	            if st.button("Nova mao", type="primary"):
-  1193	                st.session_state.sim = init_sim()
-  1194	                st.rerun()
-  1195	
-  1196	# ============================================================
-  1197	# ABA BIBLIOTECA
-  1198	# ============================================================
-  1199	with aba_biblioteca:
-  1200	    st.subheader("Suas maos salvas")
-  1201	    try:
-  1202	        resp = (
-  1203	            supabase.table("maos")
-  1204	            .select("*")
-  1205	            .order("created_at", desc=True)
-  1206	            .limit(30)
-  1207	            .execute()
-  1208	        )
-  1209	        maos = resp.data
-  1210	        if not maos:
-  1211	            st.info("Nenhuma mao salva ainda. Registre sua primeira mao na aba Nova Revisao!")
-  1212	        else:
-  1213	            for mao in maos:
-  1214	                nota_label = mao.get("nota","?")
-  1215	                titulo = (
-  1216	                    f"{mao.get('cartas_master','?')}  |  "
-  1217	                    f"{mao.get('posicao_master','?')}  |  "
-  1218	                    f"Nota: {nota_label}/10"
-  1219	                )
-  1220	                with st.expander(titulo):
-  1221	                    col_a, col_b = st.columns(2)
-  1222	                    with col_a:
-  1223	                        st.markdown(f"**Stack:** {mao.get('stack_master','?')} BBs")
-  1224	                        st.markdown(f"**Flop:** {mao.get('flop','-')}")
-  1225	                        st.markdown(f"**Turn:** {mao.get('turn','-')}")
-  1226	                        st.markdown(f"**River:** {mao.get('river','-')}")
-  1227	                    with col_b:
-  1228	                        if mao.get("cartas_oponente"):
-  1229	                            st.markdown(f"**Oponente:** {mao['cartas_oponente']}")
-  1230	                        st.markdown("**Analise da IA:**")
-  1231	                        st.info(mao.get("analise_ia",""))
-  1232	    except Exception as e:
-  1233	        st.error(f"Erro ao carregar biblioteca: {e}")
-  1234	
+  1184	            result["decisao_ideal"] = result.get("decisao_ideal", result.get("decisao_correta", "?"))
+  1185	            result["analise"] = result.get("analise_geral", result.get("analise", ""))
+  1186	            show_result(result, key_suffix="showdown",
+  1187	                        board=sim["board"])
+  1188	
+  1189	            if st.button("Nova mao", type="primary"):
+  1190	                st.session_state.sim = init_sim()
+  1191	                st.rerun()
+  1192	
+  1193	# ============================================================
+  1194	# ABA BIBLIOTECA
+  1195	# ============================================================
+  1196	with aba_biblioteca:
+  1197	    st.subheader("Suas maos salvas")
+  1198	    try:
+  1199	        resp = (
+  1200	            supabase.table("maos")
+  1201	            .select("*")
+  1202	            .order("created_at", desc=True)
+  1203	            .limit(30)
+  1204	            .execute()
+  1205	        )
+  1206	        maos = resp.data
+  1207	        if not maos:
+  1208	            st.info("Nenhuma mao salva ainda. Registre sua primeira mao na aba Nova Revisao!")
+  1209	        else:
+  1210	            for mao in maos:
+  1211	                nota_label = mao.get("nota","?")
+  1212	                titulo = (
+  1213	                    f"{mao.get('cartas_master','?')}  |  "
+  1214	                    f"{mao.get('posicao_master','?')}  |  "
+  1215	                    f"Nota: {nota_label}/10"
+  1216	                )
+  1217	                with st.expander(titulo):
+  1218	                    col_a, col_b = st.columns(2)
+  1219	                    with col_a:
+  1220	                        st.markdown(f"**Stack:** {mao.get('stack_master','?')} BBs")
+  1221	                        st.markdown(f"**Flop:** {mao.get('flop','-')}")
+  1222	                        st.markdown(f"**Turn:** {mao.get('turn','-')}")
+  1223	                        st.markdown(f"**River:** {mao.get('river','-')}")
+  1224	                    with col_b:
+  1225	                        if mao.get("cartas_oponente"):
+  1226	                            st.markdown(f"**Oponente:** {mao['cartas_oponente']}")
+  1227	                        st.markdown("**Analise da IA:**")
+  1228	                        st.info(mao.get("analise_ia",""))
+  1229	    except Exception as e:
+  1230	        st.error(f"Erro ao carregar biblioteca: {e}")
+  1231	
