from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import openai
from dotenv import load_dotenv  # Importa a biblioteca dotenv

app = Flask(__name__)
CORS(app)

# Caminho para salvar os históricos e os dados das empresas
HISTORICO_PATH = 'historico_conversa.json'
DADOS_EMPRESAS_PATH = 'empresas.json'

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')  # Carrega a chave da API

# Carregar dados das empresas
def carregar_dados_empresas():
    if os.path.exists(DADOS_EMPRESAS_PATH):
        with open(DADOS_EMPRESAS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

dados_empresas = carregar_dados_empresas()  # Carregando os dados no início

# Função para ler o histórico de conversa
def ler_historico():
    if os.path.exists(HISTORICO_PATH):
        with open(HISTORICO_PATH, 'r') as f:
            return json.load(f)
    return {}

# Função para salvar o histórico de conversa
def salvar_historico(historico):
    with open(HISTORICO_PATH, 'w') as f:
        json.dump(historico, f)

# Função para obter resposta do chatbot usando OpenAI GPT
def obter_resposta_do_openai(user_id, mensagem):
    try:
        historico = ler_historico()
        mensagens = historico.get(user_id, [])

        # Construa o prompt para enviar ao modelo, incluindo os dados das empresas
        prompt = "Aqui estão algumas informações sobre empresas, quando eu fizer alguma pergunta relacionado a empresas eu quero que você utilize esse dados:\n\n"
        for empresa in dados_empresas:
            prompt += f"Nome: {empresa['companyname']}, Ticker: {empresa['ticker']}, Preço: {empresa['price']}, Margem Bruta: {empresa['margembruta']}, Margem Líquida: {empresa['margemliquida']}, Valor de Mercado: {empresa['valordemercado']}, Segmento: {empresa['segmentname']}\n"

        prompt += f"\nUsuário: {mensagem}\nIA:"

        resposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            n=1,
            stop=None,
            temperature=0.7
        )
        return resposta['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"

@app.route('/conversa', methods=['POST'])
def nova_conversa():
    dados = request.json
    user_id = dados.get('user_id')
    mensagem = dados.get('mensagem')

    historico = ler_historico()

    # Inicializa o histórico para o usuário, se não existir
    if user_id not in historico:
        historico[user_id] = []

    # Adiciona a mensagem do usuário ao histórico
    historico[user_id].append({"mensagem": mensagem, "resposta": None})

    # Obter a resposta do Gemini
    resposta = obter_resposta_do_openai(user_id, mensagem)

    # Atualiza o histórico com a resposta
    historico[user_id][-1]['resposta'] = resposta

    # Salva o histórico atualizado
    salvar_historico(historico)

    return jsonify({"mensagem": mensagem, "resposta": resposta})

@app.route('/historico/<user_id>', methods=['GET'])
def obter_historico(user_id):
    historico = ler_historico()
    if user_id in historico:
        return jsonify(historico[user_id])
    else:
        return jsonify({"mensagem": "Nenhum histórico encontrado para este usuário."}), 404

if __name__ == '__main__':
    app.run(debug=True)
