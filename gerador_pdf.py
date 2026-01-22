from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

def gerar_curriculo(dados, nome_arquivo):
    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    
    story = []
    styles = getSampleStyleSheet()

    # Estilos Personalizados (Azul Info Center)
    cor_azul = colors.HexColor("#003399")
    
    # Definição dos estilos de texto
    estilo_nome = ParagraphStyle('Nome', parent=styles['Heading1'], fontSize=22, textColor=cor_azul, spaceAfter=10)
    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading2'], fontSize=14, textColor=cor_azul, spaceBefore=15, spaceAfter=5, borderPadding=5)
    estilo_normal = styles['Normal']
    estilo_pequeno = ParagraphStyle('Pequeno', parent=styles['Normal'], fontSize=9, textColor=colors.grey)

    # --- 1. Cabeçalho (Dados Pessoais) ---
    # O .get('campo', ['Valor Padrão'])[0] serve para pegar o item da lista que o HTML envia
    nome = dados.get('nome', [''])[0]
    story.append(Paragraph(nome.upper(), estilo_nome))
    
    # Montar linha de contato
    contato = []
    if 'telefone' in dados and dados['telefone'][0]: contato.append(f"Tel: {dados['telefone'][0]}")
    if 'email' in dados and dados['email'][0]: contato.append(f"Email: {dados['email'][0]}")
    if 'endereco' in dados and dados['endereco'][0]: contato.append(f"Endereço: {dados['endereco'][0]}")
    if 'nascimento' in dados and dados['nascimento'][0]: contato.append(f"Nasc: {dados['nascimento'][0]}")
    
    # Junta os contatos com uma barra " | "
    story.append(Paragraph(" | ".join(contato), estilo_pequeno))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))

    # --- 2. Objetivo ---
    if 'objetivo' in dados and dados['objetivo'][0]:
        story.append(Paragraph("OBJETIVO PROFISSIONAL", estilo_titulo))
        story.append(Paragraph(dados['objetivo'][0], estilo_normal))

    # --- 3. Experiência Profissional ---
    # Verifica se existe o campo de empresa
    if 'exp_empresa[]' in dados:
        empresas = dados.get('exp_empresa[]', [])
        cargos = dados.get('exp_cargo[]', [])
        inicios = dados.get('exp_inicio[]', [])
        finais = dados.get('exp_fim[]', [])
        resumos = dados.get('exp_resumo[]', [])

        # Se tiver pelo menos uma empresa preenchida
        tem_experiencia = False
        for emp in empresas:
            if emp.strip(): tem_experiencia = True
        
        if tem_experiencia:
            story.append(Paragraph("EXPERIÊNCIA PROFISSIONAL", estilo_titulo))
            
            for i in range(len(empresas)):
                if not empresas[i]: continue # Pula campos vazios
                
                # Formatação: Empresa - Cargo (Negrito)
                cargo_atual = cargos[i] if i < len(cargos) else ''
                texto_empresa = f"<b>{empresas[i]}</b> - {cargo_atual}"
                story.append(Paragraph(texto_empresa, estilo_normal))
                
                # Data
                inicio = inicios[i] if i < len(inicios) else ''
                fim = finais[i] if i < len(finais) else ''
                if inicio or fim:
                    story.append(Paragraph(f"Período: {inicio} a {fim}", estilo_pequeno))
                
                # Resumo das atividades
                if i < len(resumos) and resumos[i]:
                    story.append(Paragraph(resumos[i], estilo_normal))
                
                story.append(Spacer(1, 8))

    # --- 4. Formação Acadêmica ---
    if 'formacao_curso[]' in dados:
        cursos = dados.get('formacao_curso[]', [])
        escolas = dados.get('formacao_escola[]', [])
        anos = dados.get('formacao_ano[]', [])

        tem_formacao = False
        for cur in cursos:
            if cur.strip(): tem_formacao = True

        if tem_formacao:
            story.append(Paragraph("FORMAÇÃO ACADÊMICA", estilo_titulo))

            for i in range(len(cursos)):
                if not cursos[i]: continue
                
                escola = escolas[i] if i < len(escolas) else ''
                ano = anos[i] if i < len(anos) else ''
                
                texto = f"<b>{cursos[i]}</b><br/>{escola}"
                if ano:
                    texto += f" - Conclusão: {ano}"
                
                story.append(Paragraph(texto, estilo_normal))
                story.append(Spacer(1, 6))

    # --- 5. Qualificações ---
    if 'qualificacoes' in dados and dados['qualificacoes'][0]:
        story.append(Paragraph("QUALIFICAÇÕES E CURSOS", estilo_titulo))
        # Quebra as linhas do textarea para exibir bonitinho no PDF
        qualif = dados['qualificacoes'][0].replace('\n', '<br/>')
        story.append(Paragraph(qualif, estilo_normal))

    # --- Rodapé ---
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("Documento gerado automaticamente via Info Center Digital", estilo_pequeno))

    # Gera o PDF final
    doc.build(story)