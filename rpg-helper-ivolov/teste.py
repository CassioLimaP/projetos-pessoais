from google import genai
import sys

# Pega a chave do terminal
print("--- TESTE DA NOVA BIBLIOTECA (google-genai) ---")
api_key = input("Cole sua API Key: ").strip()

try:
    # A nova forma de conectar
    client = genai.Client(api_key=api_key)
    
    # Lista de nomes possíveis para tentar
    nomes_teste = ["gemini-1.5-flash", "gemini-1.5-flash-001", "gemini-1.5-flash-latest"]
    
    sucesso = False
    
    for nome_modelo in nomes_teste:
        print(f"\nTentando conectar com: '{nome_modelo}'...")
        try:
            response = client.models.generate_content(
                model=nome_modelo,
                contents="Responda apenas: OK"
            )
            print(f"✅ SUCESSO! O modelo correto para você é: {nome_modelo}")
            print(f"Resposta da IA: {response.text}")
            sucesso = True
            break # Para no primeiro que funcionar
        except Exception as e:
            print(f"❌ Falha com '{nome_modelo}'. Erro: {e}")

    if not sucesso:
        print("\n⚠️ Nenhum modelo funcionou. Verifique se sua API Key é válida.")

except Exception as e:
    print(f"Erro fatal na configuração: {e}")
