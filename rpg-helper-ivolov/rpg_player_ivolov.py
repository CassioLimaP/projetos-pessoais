#@CassioLimaP
#feito com Gemini 
import streamlit as st

# --- Configuração da Página ---
st.set_page_config(page_title="Ivolov: Assistente", page_icon="🐉", layout="centered")

# --- Estado (Memória) ---
if 'hp' not in st.session_state: st.session_state.hp = 115
if 'ki' not in st.session_state: st.session_state.ki = 14
if 'log' not in st.session_state: st.session_state.log = []

def add_log(msg):
    st.session_state.log.insert(0, msg)

# --- Sidebar: Recursos ---
with st.sidebar:
    st.header("📊 Recursos")
    
    # Chi
    st.markdown("### 🌀 Pontos de Chi")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        if st.button("➖", key="ki_sub"): 
            if st.session_state.ki > 0: 
                st.session_state.ki -= 1
                add_log("➖ Gastou 1 Chi")
    with c2:
        if st.button("➕", key="ki_add"): 
            if st.session_state.ki < 14: st.session_state.ki += 1
    with c3:
        st.write(f"## {st.session_state.ki} / 14")
    st.progress(st.session_state.ki / 14)

    st.markdown("---")
    
    # Vida
    st.markdown("### ❤️ Pontos de Vida")
    cur_hp = st.number_input("HP Atual", value=st.session_state.hp, max_value=115, label_visibility="collapsed")
    if cur_hp != st.session_state.hp:
        st.session_state.hp = cur_hp
    st.progress(st.session_state.hp / 115)
    
    st.markdown("---")
    if st.button("💤 Descanso Curto (Reset)"):
        st.session_state.ki = 14
        add_log("💤 Chi recuperado.")
        st.rerun()

# --- Estrutura Principal em Abas ---
st.title("👊 Ivolov Inovich")
st.caption("Monge Nível 14 | Caminho da Mão Aberta")

tab_game, tab_rules = st.tabs(["🎮 Mesa de Jogo", "📖 Grimório de Habilidades"])

# ==========================================
# ABA 1: MESA DE JOGO (Onde a ação acontece)
# ==========================================
with tab_game:
    col_act, col_bon = st.columns(2)

    with col_act:
        st.header("1️⃣ Ação")
        with st.expander("⚔️ Atacar (2 Golpes)", expanded=True):
            st.markdown("### `1d20 + 8` (Acerto)")
            st.markdown("### `1d8 + 3` (Dano)")
            st.caption("Tipo: Impacto (Mágico)")

        with st.expander("❤️ Integridade Corporal"):
            st.write("Recupere **42** HP.")
            if st.button("Usar Cura"):
                st.session_state.hp = min(115, st.session_state.hp + 42)
                add_log("❤️ Usou Integridade (+42 HP)")
                st.rerun()

    with col_bon:
        st.header("2️⃣ Ação Bônus")
        t_b1, t_b2 = st.tabs(["Luta", "Movimento"])
        
        with t_b1:
            st.info("**Artes Marciais (Grátis):** 1 Soco (`1d8+3`)")
            st.markdown("---")
            st.caption("Gasta 1 Chi 👇")
            if st.button("👊 Rajada de Golpes"):
                if st.session_state.ki > 0:
                    st.session_state.ki -= 1
                    add_log("🔥 Rajada de Golpes (2 ataques)")
                    st.rerun()
            st.write("**Efeito:** 2 Socos (`1d8+3` cada) + Efeito Mão Aberta.")

        with t_b2:
            st.caption("Gasta 1 Chi 👇")
            if st.button("🛡️ Defesa Paciente"):
                if st.session_state.ki > 0:
                    st.session_state.ki -= 1
                    add_log("🛡️ Defesa Paciente (Dodge)")
                    st.rerun()
            st.caption("Efeito: Esquiva (Inimigos têm Desvantagem).")
            
            if st.button("💨 Passo do Vento"):
                if st.session_state.ki > 0:
                    st.session_state.ki -= 1
                    add_log("💨 Passo do Vento (Dash/Disengage)")
                    st.rerun()
            st.caption("Efeito: Desengajar ou Disparar + Pulo Dobrado.")

    st.markdown("---")
    st.subheader("⚡ Reações")
    c_r1, c_r2 = st.columns(2)
    with c_r1:
        st.info("**🏹 Aparar Projéteis**")
        st.code("Redução = 1d10 + 17")
    with c_r2:
        st.warning("**😵 Golpe Atordoante**")
        if st.button("Gastar 1 Chi (Stun)"):
            if st.session_state.ki > 0:
                st.session_state.ki -= 1
                add_log("⚡ Tentou Atordoar")
                st.rerun()
        st.write("Inimigo faz **CON Save (CD 13)**.")

    with st.expander("📜 Log de Combate"):
        for m in st.session_state.log: st.write(m)

# ==========================================
# ABA 2: GRIMÓRIO (Explicação das Skills)
# ==========================================
with tab_rules:
    st.header("📖 Descrição das Habilidades")
    
    st.subheader("🥋 Caminho da Mão Aberta")
    with st.expander("Técnica da Mão Aberta (Nível 3)"):
        st.markdown("""
        Sempre que acertar um ataque vindo da **Rajada de Golpes**, você pode impor um efeito:
        1.  **Derrubar:** O alvo deve passar em teste de **DES (CD 13)** ou cair no chão (Prone).
        2.  **Empurrar:** O alvo deve passar em teste de **FOR (CD 13)** ou ser empurrado 4,5m (15ft).
        3.  **Desorientar:** O alvo **não pode usar reações** até o final do próximo turno dele (sem teste).
        """)
    
    with st.expander("Integridade Corporal (Nível 6)"):
        st.markdown("""
        Como uma **Ação**, você pode recuperar pontos de vida iguais a `3 x Seu Nível de Monge`.
        * **Cura Atual:** 42 HP.
        * **Uso:** Uma vez por descanso longo.
        """)

    with st.expander("Tranquilidade (Nível 11)"):
        st.markdown("""
        No final de um descanso longo, você ganha o efeito da magia **Santuário (CD 13)**.
        * Se um inimigo tentar te atacar, ele deve passar num teste de Sabedoria ou perder o ataque (ou escolher outro alvo).
        * O efeito termina se você atacar ou conjurar uma magia que afete um inimigo.
        """)

    st.subheader("🛡️ Defesa e Sobrevivência")
    with st.expander("Evasão (Nível 7)"):
        st.markdown("""
        Quando você faz um teste de resistência de **Destreza** para levar metade do dano (ex: Bola de Fogo):
        * **Se passar:** Você não leva **nenhum dano**.
        * **Se falhar:** Você leva apenas **metade do dano**.
        """)
    
    with st.expander("Alma de Diamante (Nível 14)"):
        st.markdown("""
        1.  Você tem proficiência em **TODOS** os testes de resistência (incluindo Morte).
        2.  Sempre que falhar em um teste de resistência, pode gastar **1 Ponto de Chi** para rolar novamente e pegar o segundo resultado.
        """)
        
    with st.expander("Outras Passivas"):
        st.markdown("""
        * **Pureza do Corpo (Nv 10):** Imune a doenças e veneno.
        * **Queda Suave (Nv 4):** Reação para reduzir dano de queda em `5 x Nível` (70 de dano).
        * **Língua do Sol e da Lua (Nv 13):** Você entende todos os idiomas falados e qualquer criatura que tenha um idioma entende o que você fala.
        * **Movimento Sem Armadura:** Você pode andar pelas paredes e sobre a água durante seu turno.
        """)
    
    st.subheader("⚔️ Combate e Chi")
    with st.expander("Golpe Atordoante (Nv 5)"):
        st.markdown("""
        Ao acertar um ataque corpo a corpo, gaste **1 Chi**. O alvo faz teste de **CON (CD 13)**.
        * **Falha:** A condição **Atordoado (Stunned)** dura até o final do seu próximo turno.
        * *Atordoado:* Incapacitado, falha automática em testes de Força/Destreza, ataques contra ele têm Vantagem.
        """)
        
    with st.expander("Ataques Mágicos (Nv 6)"):
        st.markdown("Seus ataques desarmados contam como mágicos para superar resistências.")
