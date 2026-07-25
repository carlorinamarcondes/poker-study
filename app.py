--- a//home/ubuntu/app.py
+++ b//home/ubuntu/app.py
@@ -536,63 +536,103 @@
-   535	
-   536	            if acertou:
-   537	                st.success(
-   538	                    f"Decisao correta! A jogada ideal era **{decisao_correta}**."
-   539	                )
-   540	            else:
-   541	                st.error(
-   542	                    f"Nao foi a melhor opcao. A jogada ideal era **{decisao_correta}**."
-   543	                )
-   544	
-   545	            raciocinio = result.get("raciocinio_ideal", "")
-   546	            if raciocinio:
-   547	                st.markdown("**Raciocinio ideal:**")
-   548	                st.info(raciocinio)
-   549	
-   550	            show_result(result, key_suffix="simulador")
-   551	
-   552	# =========== ABA BIBLIOTECA ===========
-   553	with aba_biblioteca:
-   554	    st.subheader("Suas maos salvas")
-   555	
-   556	    try:
-   557	        resp = (
-   558	            supabase.table("maos")
-   559	            .select("*")
-   560	            .order("created_at", desc=True)
-   561	            .limit(30)
-   562	            .execute()
-   563	        )
-   564	        maos = resp.data
-   565	
-   566	        if not maos:
-   567	            st.info(
-   568	                "Nenhuma mao salva ainda. "
-   569	                "Registre sua primeira mao na aba Nova Revisao!"
-   570	            )
-   571	        else:
-   572	            for mao in maos:
-   573	                nota_label = mao.get("nota", "?")
-   574	                titulo = (
-   575	                    f"{mao.get('cartas_master', '?')}  |  "
-   576	                    f"{mao.get('posicao_master', '?')}  |  "
-   577	                    f"Nota: {nota_label}/10"
-   578	                )
-   579	                with st.expander(titulo):
-   580	                    col_a, col_b = st.columns(2)
-   581	                    with col_a:
-   582	                        st.markdown(
-   583	                            f"**Stack:** {mao.get('stack_master', '?')} BBs"
-   584	                        )
-   585	                        st.markdown(f"**Flop:** {mao.get('flop', '-')}")
-   586	                        st.markdown(f"**Turn:** {mao.get('turn', '-')}")
-   587	                        st.markdown(f"**River:** {mao.get('river', '-')}")
-   588	                    with col_b:
-   589	                        if mao.get("cartas_oponente"):
-   590	                            st.markdown(
-   591	                                f"**Oponente:** {mao['cartas_oponente']}"
-   592	                            )
-   593	                        st.markdown("**Analise da IA:**")
-   594	                        st.info(mao.get("analise_ia", ""))
-   595	    except Exception as e:
-   596	        st.error(f"Erro ao carregar biblioteca: {e}")
-   597	
+   535	            nota = result.get("nota", "?")
+   536	
+   537	            # Garantia de pontuacao coerente com o acerto
+   538	            try:
+   539	                nota_num = int(nota)
+   540	                if acertou and nota_num < 6:
+   541	                    nota_num = 6
+   542	                if not acertou and nota_num > 5:
+   543	                    nota_num = 5
+   544	                nota = nota_num
+   545	            except (ValueError, TypeError):
+   546	                pass
+   547	
+   548	            if acertou:
+   549	                st.success(
+   550	                    f"Decisao correta! A jogada ideal era **{decisao_correta}**."
+   551	                )
+   552	            else:
+   553	                st.error(
+   554	                    f"Nao foi a melhor opcao. A jogada ideal era **{decisao_correta}**."
+   555	                )
+   556	
+   557	            # Painel de estatisticas
+   558	            equity = result.get("equity_estimada", "?")
+   559	            equity_min = result.get("equity_minima_para_call", "?")
+   560	            ev_master = result.get("ev_decisao_master", "?")
+   561	            ev_correto = result.get("ev_decisao_correta", "?")
+   562	
+   563	            st.markdown("#### Estatisticas da decisao")
+   564	            s1, s2, s3, s4, s5 = st.columns(5)
+   565	            s1.metric("Nota", f"{nota}/10")
+   566	            s2.metric("Equity estimada", f"{equity}%")
+   567	            s3.metric("Equity minima p/ call", f"{equity_min}%")
+   568	
+   569	            try:
+   570	                ev_m = float(ev_master)
+   571	                ev_c = float(ev_correto)
+   572	                s4.metric(
+   573	                    "EV da sua decisao",
+   574	                    f"{ev_m:+.0f}",
+   575	                    delta=f"{ev_m - ev_c:+.0f} vs ideal",
+   576	                    delta_color="normal"
+   577	                )
+   578	                s5.metric("EV da decisao ideal", f"{ev_c:+.0f}")
+   579	            except (TypeError, ValueError):
+   580	                s4.metric("EV da sua decisao", str(ev_master))
+   581	                s5.metric("EV da decisao ideal", str(ev_correto))
+   582	
+   583	            raciocinio = result.get("raciocinio_ideal", "")
+   584	            if raciocinio:
+   585	                st.markdown("**Raciocinio passo a passo:**")
+   586	                st.info(raciocinio)
+   587	
+   588	            # Sobrescreve a nota no resultado para show_result usar a corrigida
+   589	            result["nota"] = nota
+   590	            show_result(result, key_suffix="simulador")
+   591	
+   592	# =========== ABA BIBLIOTECA ===========
+   593	with aba_biblioteca:
+   594	    st.subheader("Suas maos salvas")
+   595	
+   596	    try:
+   597	        resp = (
+   598	            supabase.table("maos")
+   599	            .select("*")
+   600	            .order("created_at", desc=True)
+   601	            .limit(30)
+   602	            .execute()
+   603	        )
+   604	        maos = resp.data
+   605	
+   606	        if not maos:
+   607	            st.info(
+   608	                "Nenhuma mao salva ainda. "
+   609	                "Registre sua primeira mao na aba Nova Revisao!"
+   610	            )
+   611	        else:
+   612	            for mao in maos:
+   613	                nota_label = mao.get("nota", "?")
+   614	                titulo = (
+   615	                    f"{mao.get('cartas_master', '?')}  |  "
+   616	                    f"{mao.get('posicao_master', '?')}  |  "
+   617	                    f"Nota: {nota_label}/10"
+   618	                )
+   619	                with st.expander(titulo):
+   620	                    col_a, col_b = st.columns(2)
+   621	                    with col_a:
+   622	                        st.markdown(
+   623	                            f"**Stack:** {mao.get('stack_master', '?')} BBs"
+   624	                        )
+   625	                        st.markdown(f"**Flop:** {mao.get('flop', '-')}")
+   626	                        st.markdown(f"**Turn:** {mao.get('turn', '-')}")
+   627	                        st.markdown(f"**River:** {mao.get('river', '-')}")
+   628	                    with col_b:
+   629	                        if mao.get("cartas_oponente"):
+   630	                            st.markdown(
+   631	                                f"**Oponente:** {mao['cartas_oponente']}"
+   632	                            )
+   633	                        st.markdown("**Analise da IA:**")
+   634	                        st.info(mao.get("analise_ia", ""))
+   635	    except Exception as e:
+   636	        st.error(f"Erro ao carregar biblioteca: {e}")
+   637	
