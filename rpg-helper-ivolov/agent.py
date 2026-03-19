from pypdf import PdfReader
import re

def extract_from_pdf(uploaded_file):
    """
    O Agente que lê o PDF e tenta extrair os dados principais.
    Funciona melhor com Fichas Editáveis (Formulários).
    """
    reader = PdfReader(uploaded_file)
    fields = reader.get_fields()
    
    # Dicionário padrão caso falhe a leitura
    char_data = {
        "name": "Desconhecido",
        "classe": "Aventureiro",
        "level": 1,
        "max_hp": 10,
        "stats": "STR 10 | DEX 10 | CON 10",
        "resources": {}
    }

    if fields:
        # --- LÓGICA PARA FICHA EDITÁVEL (MAIS PRECISA) ---
        # Tenta pegar valores dos campos comuns de D&D 5e
        # Os nomes dos campos variam, então tentamos algumas chaves comuns
        
        # Nome
        char_data["name"] = _get_field(fields, ["CharacterName", "Nome", "Name", "Character Name"], "Heroi")
        
        # Classe e Nível
        class_level = _get_field(fields, ["ClassLevel", "Classe", "Class"], "Guerreiro 1")
        # Pequena regex para separar "Monk 14" em "Monk" e "14"
        match = re.search(r"(\D+)\s*(\d+)", class_level)
        if match:
            char_data["classe"] = match.group(1).strip()
            char_data["level"] = int(match.group(2))
        else:
            char_data["classe"] = class_level
        
        # HP
        hp_str = _get_field(fields, ["HPMax", "HPMaxtotal", "Vida"], "10")
        try:
            char_data["max_hp"] = int(hp_str)
        except:
            char_data["max_hp"] = 10

        # Atributos (Simples string para visualização)
        str_val = _get_field(fields, ["STR", "Forca", "STRmod"], "10")
        dex_val = _get_field(fields, ["DEX", "Destreza", "DEXmod"], "10")
        con_val = _get_field(fields, ["CON", "Constituicao", "CONmod"], "10")
        char_data["stats"] = f"STR {str_val} | DEX {dex_val} | CON {con_val}"
        
        # Recursos Específicos (Detectar se é Monge para adicionar Chi)
        if "monk" in char_data["classe"].lower() or "monge" in char_data["classe"].lower():
            char_data["resources"]["Pontos de Chi"] = char_data["level"]

    else:
        # --- LÓGICA DE TEXTO BRUTO (FALLBACK) ---
        # Se o PDF não for editável, extraímos o texto cru
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        # Aqui entraria uma IA (LLM) para ler o texto bagunçado
        char_data["name"] = "PDF Não-Editável (Leitura manual necessária)"
    
    return char_data

def _get_field(fields, keys, default):
    """Função auxiliar que procura por várias chaves possíveis no PDF."""
    for key in keys:
        if key in fields and fields[key].value:
            return str(fields[key].value)
        # Tenta procurar chaves parciais (ex: 'STR' dentro de 'Ability-STR')
        for f_key in fields:
            if key in f_key and fields[f_key].value:
                 return str(fields[f_key].value)
    return default
