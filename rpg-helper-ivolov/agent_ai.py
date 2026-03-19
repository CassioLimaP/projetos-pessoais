import os
from groq import Groq
import json
import re
from pypdf import PdfReader

# --- FUNÇÃO AUXILIAR: CAÇADOR DE JSON ---
def find_and_parse_json(text):
    try:
        start = text.find('{')
        if start != -1:
            balance = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '{': balance += 1
                elif text[i] == '}': balance -= 1
                if balance == 0:
                    end = i + 1
                    break
            if end != -1: return json.loads(text[start:end])
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match: return json.loads(match.group())
        return json.loads(text)
    except: return None

# --- FUNÇÃO 2: ENRIQUECER MAGIAS (CORREÇÃO DE NÍVEL) ---
def enrich_spells(client, spell_list):
    if not spell_list: return {}
    # Pega apenas os nomes para a IA processar rápido
    lista_texto = ", ".join([s.get('nome', '') for s in spell_list[:20]])

    prompt = f"""
    Você é um Mestre de D&D 5e.
    1. Gere descrições táticas para as magias.
    2. **CORRIJA O NÍVEL:** Diga o nível REAL (0 para Truques).
    
    LISTA: {lista_texto}
    
    JSON (Responda APENAS JSON):
    {{
        "Bola de Fogo": {{ "nivel_real": 3, "resumo": "Explosão 8d6 Fogo." }},
        "Mãos Mágicas": {{ "nivel_real": 0, "resumo": "Mão espectral que flutua." }}
    }}
    """
    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1, 
        )
        return find_and_parse_json(chat.choices[0].message.content) or {}
    except: return {}

# --- FUNÇÃO 1: LEITOR DE PDF (AGORA COM DESCRIÇÃO DE RECURSOS) ---
def extract_character_data(pdf_file, api_key):
    try: client = Groq(api_key=api_key)
    except Exception as e: return {"error": f"Groq Error: {str(e)}"}

    try:
        reader = PdfReader(pdf_file)
        text_data = ""
        form_data = ""
        fields = reader.get_form_text_fields()
        if fields:
            for k, v in fields.items():
                if v: form_data += f"{k}: {v}\n"
        for i, page in enumerate(reader.pages):
            if i > 3: break 
            text_data += page.extract_text() + "\n"
    except Exception as e: return {"error": f"PDF Error: {str(e)}"}

    # PROMPT ATUALIZADO: Pede resumo dos recursos
    prompt = """
    Extraia dados da ficha D&D 5e.
    
    RECURSOS DE CLASSE:
    Procure por Ki, Fúria, Forma Selvagem, etc.
    Adicione um 'resumo' explicando como recupera (Curto/Longo) ou para que serve.
    
    JSON OBRIGATÓRIO:
    {
        "nome": "string",
        "classe": "string",
        "nivel": int,
        "hp_max": int,
        "atributos": "string",
        "recursos_classe": [
            {"nome": "Pontos de Ki", "max": 5, "resumo": "Recupera em Descanso Curto. Usado para Rajada de Golpes."}
        ],
        "spell_info": { "habilidade_chave": "string", "cd_tr": int, "atk_magia": int },
        "ataques": [{"nome": "string", "acerto": 0, "dado": "string", "dano_bonus": 0}],
        "magias": [{"nome": "Nome", "nivel": 0}]
    }
    DADOS:
    """ + form_data + "\n" + text_data

    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1, 
        )
        data = find_and_parse_json(chat.choices[0].message.content)
        if not data: return {"error": "Falha JSON IA 1"}

        # --- MESCLAGEM DE CORREÇÃO (MAGIAS) ---
        if 'magias' in data and data['magias']:
            correcoes = enrich_spells(client, data['magias'])
            for mag in data['magias']:
                nome = mag.get('nome')
                if correcoes and nome in correcoes:
                    mag['resumo'] = correcoes[nome].get('resumo', '')
                    # AQUI ESTÁ A CORREÇÃO DO NÍVEL:
                    if 'nivel_real' in correcoes[nome]:
                        mag['nivel'] = correcoes[nome]['nivel_real']

        return data
    except Exception as e: return {"error": str(e)}
