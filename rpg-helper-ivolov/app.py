import streamlit as st
from database import RPGDatabase
import random
import agent_ai

st.set_page_config(page_title="RPG Manager", page_icon="🐉", layout="centered")

if 'log' not in st.session_state: st.session_state.log = []

db = RPGDatabase()

# --- Função Auxiliar Inteligente de Rolagem ---
def roll_attack_details(name, atk_bonus, dice_str, dmg_bonus):
    # 1. Rola Acerto (d20)
    d20 = random.randint(1, 20)
    total_hit = d20 + atk_bonus
    
    is_crit = (d20 == 20)
    
    # 2. Interpreta o dado de dano (ex: "2d6")
    try:
        num_dice, sides = map(int, dice_str.lower().split('d'))
    except:
        num_dice, sides = 1, 4 # Fallback
        
    # 3. Rola Dano
    dmg_rolls = [random.randint(1, sides) for _ in range(num_dice)]
    raw_dmg = sum(dmg_rolls)
    
    # Se for crítico, rola o dobro de dados
    crit_dmg = 0
    if is_crit:
        crit_rolls = [random.randint(1, sides) for _ in range(num_dice)]
        crit_dmg = sum(crit_rolls)
        
    total_dmg = raw_dmg + crit_dmg + dmg_bonus
    
    # Monta a string explicativa (ex: "1d6+2")
    if dmg_bonus > 0: bonus_str = f"+{dmg_bonus}"
    elif dmg_bonus < 0: bonus_str = f"{dmg_bonus}"
    else: bonus_str = ""
    
    return {
        "name": name,
        "d20": d20,
        "total_hit": total_hit,
        "is_crit": is_crit,
        "dmg_str": f"{raw_dmg} (dado) {bonus_str}",
        "total_dmg": total_dmg,
        "desc_crit": f" + {crit_dmg} (crítico)" if is_crit else ""
    }

def add_log(msg):
    st.session_state.log.insert(0, msg)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("🐉 RPG Manager")
    mode = st.radio("Modo:", ["Jogar", "Criar Personagem"])
    st.markdown("---")

    selected_char_id = None

    if mode == "Jogar":
        # Seletor de Personagem
        all_chars = db.get_all_characters()
        if not all_chars:
            st.warning("Crie um personagem primeiro!")
        else:
            options = {f"{c[1]} (Nv {c[3]})": c[0] for c in all_chars}
            selection = st.selectbox("Herói:", list(options.keys()))
            selected_char_id = options[selection]
            
            # Botão de Apagar (NOVO)
            col_del1, col_del2 = st.columns([3, 1])
            with col_del2:
                if st.button("🗑️", help="Apagar Personagem permanentemente"):
                    db.delete_character(selected_char_id)
                    st.warning("Personagem deletado!")
                    st.rerun()

            # --- MENU DE ADICIONAR ATAQUE NOVO ---
            with st.expander("⚙️ Gerenciar Ataques"):
                st.caption("Novo Ataque:")
                new_atk_name = st.text_input("Nome", value="Espada")
                c1, c2 = st.columns(2)
                new_atk_bonus = c1.number_input("Acerto (+)", value=5)
                new_dmg_bonus = c2.number_input("Dano (+)", value=3)
                new_dice = st.selectbox("Dado", ["1d4", "1d6", "1d8", "1d10", "1d12", "2d6"])
                
                if st.button("Salvar Ataque"):
                    db.add_action(selected_char_id, new_atk_name, new_atk_bonus, new_dice, new_dmg_bonus)
                    st.success("Adicionado!")
                    st.rerun()

# ==========================================
# ÁREA PRINCIPAL
# ==========================================

# --- MODO CRIAR PERSONAGEM ---
if mode == "Criar Personagem":
    st.header("🧙‍♂️ Criar com IA (Groq)")
    
    api_key = st.text_input("Cole sua Groq API Key (gsk_...):", type="password")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("Arraste seu PDF (Editável, Imagem ou Scan)", type="pdf")
    
    if uploaded_file and api_key:
        if st.button("✨ Invocar IA Generativa"):
            with st.spinner("O Mestre está analisando sua ficha..."):
                # 1. Chama a IA (Agent AI)
                
                data = agent_ai.extract_character_data(uploaded_file, api_key)
                
                if "error" in data:
                    st.error(data["error"])
                else:
                    # Debug Visual
                    with st.expander("🔍 Ver JSON da IA (Clique para conferir)"):
                        st.json(data)

                    try:
                        # 2. TRATAMENTO DE DADOS (O FIX DO ERRO)
                        # A IA as vezes manda {"FOR": 10}, mas o banco quer "FOR: 10"
                        raw_attrs = data.get('atributos', 'FOR 10 | DES 10')
                        
                        if isinstance(raw_attrs, dict):
                            # Se for dicionário, converte para texto
                            attrs_str = " | ".join([f"{k}: {v}" for k,v in raw_attrs.items()])
                        else:
                            # Se não, garante que é string
                            attrs_str = str(raw_attrs)

                        # 3. CRIA O PERSONAGEM NO BANCO
                        new_id = db.seed_character(
                            data.get('nome', 'Sem Nome'), 
                            data.get('classe', 'Aventureiro'), 
                            data.get('nivel', 1), 
                            data.get('hp_max', 10), 
                            attrs_str # <--- Agora isso é garantido que é Texto
                        )
                        st.write(f"✅ Personagem criado com ID: {new_id}")

                        # 4. SALVA OS ATAQUES
                        lista_ataques = data.get('ataques', [])
                        if not lista_ataques:
                            st.warning("⚠️ Nenhum ataque físico encontrado.")
                        
                        for atk in lista_ataques:
                            n_arma = atk.get('nome', 'Arma Desconhecida')
                            v_acerto = atk.get('acerto', 0)
                            v_dado = atk.get('dado', '1d4')
                            v_bonus = atk.get('dano_bonus', 0)
                            db.add_action(new_id, n_arma, v_acerto, v_dado, v_bonus)
                            st.caption(f"💾 Ataque salvo: {n_arma}")
                        
                        # [NOVO] 4.1 SALVAR RECURSOS DE CLASSE (KI, FÚRIA, ETC)
                        lista_recursos = data.get('recursos_classe', [])
                        
                        # Fallback para Monge (Caso a IA esqueça o Ki)
                        classe_char = data.get('classe', '').lower()
                        if 'monge' in classe_char or 'monk' in classe_char:
                            tem_ki = any('ki' in r['nome'].lower() for r in lista_recursos)
                            if not tem_ki:
                                lista_recursos.append({"nome": "Pontos de Ki", "max": data.get('nivel', 1), "resumo": "Recupera em descanso curto."})

                        # Loop de Salvamento
                        for rec in lista_recursos:
                            nome_rec = rec.get('nome', 'Recurso')
                            max_rec = rec.get('max', 1)
                            desc_rec = rec.get('resumo', '') # <--- AQUI PEGAMOS A DESCRIÇÃO
                            
                            # Atualiza chamando o novo parametro 'desc'
                            db.update_resource_direct(new_id, nome_rec, max_rec, desc=desc_rec)
                            st.caption(f"🔋 Recurso: {nome_rec}")
                        # 5. SALVAR INFO DE CONJURAÇÃO
                        s_info = data.get('spell_info', {})
                        
                        if s_info.get('habilidade_chave'):
                            db.update_resource_direct(new_id, "Hab. Conjuração", s_info.get('habilidade_chave'))
                        if s_info.get('cd_tr'):
                            db.update_resource_direct(new_id, "CD Magia (DC)", s_info.get('cd_tr'))
                        if s_info.get('atk_magia'):
                            db.update_resource_direct(new_id, "Atk Magia (Mod)", s_info.get('atk_magia'))

                        # 6. SALVAR LISTA DE MAGIAS COM DESCRIÇÃO
                        lista_magias = data.get('magias', [])
                        for mag in lista_magias:
                            # Pega a descrição que a IA gerou (ou deixa vazio)
                            desc = mag.get('resumo', 'Sem descrição.')
                            
                            db.add_spell(
                                new_id, 
                                mag.get('nome'), 
                                mag.get('nivel', 0), 
                                description=desc
                            )
                            st.caption(f"✨ {mag.get('nome')} (Nv {mag.get('nivel')})")

                        st.success(f"Sucesso! **{data.get('nome')}** está pronto para jogar.")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
                        # Dica extra para debugar:
                        st.write("Dados que tentamos salvar:", data)

    elif uploaded_file and not api_key:
        st.warning("⚠️ Você precisa colar a API Key para a mágica funcionar.")


# --- MODO JOGAR ---
if mode == "Jogar" and selected_char_id:
    # Desempacota dados
    char_data, resources, actions = db.get_character_full(selected_char_id)
    
    # --- Sidebar Controles Rápidos ---
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**HP:** {char_data[5]} / {char_data[4]}")
        col_hp1, col_hp2 = st.columns(2)
        if col_hp1.button("-1 HP"): 
            db.update_hp(selected_char_id, max(0, char_data[5]-1))
            st.rerun()
        if col_hp2.button("+1 HP"): 
            db.update_hp(selected_char_id, min(char_data[4], char_data[5]+1))
            st.rerun()

    # --- Ficha ---
    st.title(f"👊 {char_data[1]}")
    st.caption(f"{char_data[2]} | AC {char_data[6]}")

    tab1, tab2, tab3, tab4 = st.tabs(["⚔️ Ações", "✨ Grimório", "❤️ Status", "📜 Log"])

    # --- ABA 1: AÇÕES (Combate) ---
    with tab1:
        st.subheader("Ataques Disponíveis")
        
        if not actions:
            st.info("Nenhum ataque configurado.")
        
        cols = st.columns(2) 
        for i, action in enumerate(actions):
            col = cols[i % 2]
            
            # Formata Dano (ex: 1d6+2)
            dice = action[4]
            bonus = action[5]
            if bonus > 0: dano_txt = f"{dice}+{bonus}"
            elif bonus < 0: dano_txt = f"{dice}{bonus}"
            else: dano_txt = f"{dice}"
            
            # Label Completo
            label = f"⚔️ {action[2]} (+{action[3]})  |  💥 {dano_txt}"
            
            if col.button(label, use_container_width=True, key=f"atk_{action[0]}"):
                res = roll_attack_details(action[2], action[3], action[4], action[5])
                
                emoji = "🔥CRÍTICO!🔥" if res['is_crit'] else "🎲"
                st.toast(f"{emoji} Acerto: {res['total_hit']} | Dano: {res['total_dmg']}")
                add_log(f"{action[2]}: Acerto {res['total_hit']} | Dano {res['total_dmg']}")
                
                st.markdown("---")
                c_dano, c_info = st.columns([1, 2])
                c_dano.metric(label="💥 DANO TOTAL", value=res['total_dmg'], 
                              delta="Crítico!" if res['is_crit'] else None, delta_color="normal")
                c_info.info(f"Dados: {res['d20']} (d20) + {action[3]} = {res['total_hit']} Acerto\nDano: {res['dmg_str']}{res['desc_crit']}")

    # --- ABA 2: GRIMÓRIO ---
    with tab2:
        st.subheader(f"📖 Grimório de {char_data[1]}")
        
        res_hab = db.get_resource_value(selected_char_id, "Hab. Conjuração")
        res_cd = db.get_resource_value(selected_char_id, "CD Magia (DC)")
        res_atk = db.get_resource_value(selected_char_id, "Atk Magia (Mod)") or 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Atributo", str(res_hab) if res_hab else "?")
        c2.metric("CD (Save DC)", res_cd if res_cd else "?")
        c3.metric("Bônus Atk", f"+{res_atk}")
        
        st.divider()
        
        # Agora spells traz 4 coisas: nome, nivel, escola, DESCRICAO
        spells = db.get_spells(selected_char_id) 
        
        if not spells:
            st.info("Nenhuma magia encontrada.")
        else:
            current_lvl = -1
            for nome, nivel, escola, desc in spells: # <--- Desempacota descrição
                if nivel != current_lvl:
                    current_lvl = nivel
                    st.markdown("---")
                    label = "✨ Truques" if nivel == 0 else f"🔥 Círculo {nivel}"
                    st.markdown(f"#### {label}")
                
                # Layout: Botão de Conjurar
                icon = "✨" if nivel == 0 else "🔥"
                label_magia = f"{icon} {nome}"
                
                # Botão Principal
                if st.button(label_magia, use_container_width=True, key=f"cast_{nome}_{nivel}_{random.randint(0,999)}"):
                    d20 = random.randint(1, 20)
                    total = d20 + int(res_atk)
                    st.toast(f"🔮 {nome}: {total} pra acertar!")
                    add_log(f"Conjurou {nome}: Resultado {total}")
                    st.metric(f"Resultado: {nome}", total, delta=f"Natural: {d20}")

                # Explicação Expansível (Embaixo do botão)
                with st.expander(f"📜 Detalhes de {nome}"):
                    st.write(f"**Efeito:** {desc}")
                    st.caption(f"Escola: {escola} | Nível: {nivel}")

    # --- ABA 3: STATUS ---
    with tab3:
        st.subheader("Gerenciar Recursos")
        
        # Pega os recursos do banco atualizados
        # resources retorna tuplas: (id, char_id, name, max, current, description)
        
        if not resources:
            st.info("Nenhum recurso especial (como Ki ou Fúria) encontrado.")
        
        for r in resources:
            # Layout: Nome e Controles
            c1, c2, c3 = st.columns([3, 1, 1])
            
            # PROTEÇÃO DE ÍNDICE: Verifica se temos dados suficientes
            # Tenta pegar Nome (pos 2), Max (pos 3) e Atual (pos 4)
            try:
                # Se o SELECT for "id, char_id, name, max, current, desc"
                # name=2, max=3, current=4, desc=5
                
                # Se o seu SELECT for específico, os índices mudam. 
                # Vamos tentar pelo padrão do SELECT *
                nome_res = r[2] if len(r) > 2 else "Recurso"
                val_max = r[3] if len(r) > 3 else 1
                val_atual = r[4] if len(r) > 4 else 0
                
                c1.markdown(f"**{nome_res}**")
                c1.caption(f"Disponível: {val_atual} / {val_max}")
                
                # Botões (Usando os valores seguros)
                if c2.button("➖", key=f"dec_{r[0]}") and val_atual > 0:
                    db.update_resource(r[0], val_atual-1)
                    st.rerun()
                if c3.button("➕", key=f"inc_{r[0]}") and val_atual < val_max:
                    db.update_resource(r[0], val_atual+1)
                    st.rerun()
                
                # Descrição (Posição 5, se existir)
                if len(r) > 5 and r[5]:
                    st.info(f"ℹ️ {r[5]}")
                    
            except Exception as e:
                st.error(f"Erro ao ler recurso ID {r[0]}: {e}")
                
            st.divider()

    # --- ABA 4: LOG ---
    with tab4:
        st.subheader("Histórico de Rolagens")
        if st.button("Limpar Log"):
            st.session_state.log = []
            st.rerun()
            
        for msg in st.session_state.log:
            st.markdown(f"- {msg}")
