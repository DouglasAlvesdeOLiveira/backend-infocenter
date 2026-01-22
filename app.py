import os
from flask import Flask, request, send_file, redirect, url_for, jsonify
from flask_cors import CORS
import mercadopago
from gerador_pdf import gerar_curriculo

app = Flask(__name__)

# --- 1. CONFIGURAÇÃO DE SEGURANÇA (CORS) ---
# Isso permite que o seu site no Netlify converse com esse sistema Python
# Quando subir pro Netlify, troque o "*" pelo seu domínio (ex: "https://infocenter.netlify.app") para mais segurança.
CORS(app, resources={r"/*": {"origins": "*"}})

# --- 2. CONFIGURAÇÃO DO MERCADO PAGO ---
# Tenta pegar o token das Variáveis de Ambiente do Render (segurança máxima)
# Se não achar, usa uma string vazia (modo teste sem pagamento)
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")

if MP_ACCESS_TOKEN:
    sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
    print("Mercado Pago: ATIVADO")
else:
    sdk = None
    print("Mercado Pago: DESATIVADO (Modo Teste)")

# Pasta temporária para salvar os PDFs
UPLOAD_FOLDER = 'curriculos_gerados'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- 3. ROTAS DO SISTEMA ---

@app.route('/')
def health_check():
    """Rota apenas para verificar se o servidor está online no Render."""
    return jsonify({"status": "online", "service": "API Info Center", "version": "1.0"})

@app.route('/processar_curriculo', methods=['POST'])
def processar():
    try:
        # A. Recebe os dados do formulário HTML
        dados = request.form.to_dict(flat=False)
        
        # B. Cria um nome de arquivo único
        # Usa o primeiro nome + telefone para evitar duplicidade
        primeiro_nome = dados.get('nome', ['Cliente'])[0].split()[0]
        # Limpa o telefone para ficar apenas números
        telefone = dados.get('telefone', ['0000'])[0]
        telefone_limpo = "".join(filter(str.isdigit, telefone))
        
        nome_arquivo = f"curriculo_{primeiro_nome}_{telefone_limpo}.pdf"
        caminho_completo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        # C. Gera o PDF usando o script auxiliar
        gerar_curriculo(dados, caminho_completo)
        print(f"PDF Gerado: {caminho_completo}")

        # D. LÓGICA DE PAGAMENTO VS DOWNLOAD DIRETO
        
        # URL do seu Backend (O Render cria essa URL automaticamente, ex: https://api-infocenter.onrender.com)
        # O request.host_url pega o domínio atual onde o Python está rodando
        base_url = request.host_url.rstrip('/')

        if sdk:
            # --- MODO COM PAGAMENTO (MERCADO PAGO) ---
            preference_data = {
                "items": [
                    {
                        "title": "Criação de Currículo Profissional - Info Center",
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": 15.00
                    }
                ],
                "back_urls": {
                    # O cliente volta para o Render para baixar o arquivo
                    "success": f"{base_url}/download/{nome_arquivo}",
                    "failure": "https://seu-site-no-netlify.app/", # Coloque seu site Netlify aqui
                    "pending": "https://seu-site-no-netlify.app/"
                },
                "auto_return": "approved"
            }
            
            preference_response = sdk.preference().create(preference_data)
            link_pagamento = preference_response["response"]["init_point"]
            
            # Redireciona o cliente para a tela do Mercado Pago
            return redirect(link_pagamento)
        
        else:
            # --- MODO TESTE (GRÁTIS) ---
            # Se não tiver token configurado, baixa direto
            return redirect(url_for('download_file', filename=nome_arquivo))

    except Exception as e:
        print(f"Erro ao processar: {e}")
        return f"Ocorreu um erro ao gerar o documento: {str(e)}", 500

@app.route('/download/<filename>')
def download_file(filename):
    """Rota que entrega o arquivo para o cliente baixar."""
    try:
        caminho = os.path.join(UPLOAD_FOLDER, filename)
        return send_file(caminho, as_attachment=True)
    except FileNotFoundError:
        return "Arquivo não encontrado ou expirado. Por favor, gere novamente.", 404

if __name__ == '__main__':
    # O Render define a porta automaticamente na variável PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)