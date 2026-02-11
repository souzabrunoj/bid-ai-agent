🧾 Roteiro de Requisitos e Passos
Agente de IA Local para Organização de Documentos de Licitação
1️⃣ Objetivo do Sistema

Criar um agente de IA local que:

Receba um edital de licitação

Receba os documentos da empresa

Analise automaticamente as exigências do edital

Gere uma pasta organizada com todos os documentos exigidos

Gere um checklist final (OK / vencido / faltante)

2️⃣ Requisitos Funcionais
RF01 — Upload do edital

O sistema deve permitir upload de 1 edital em PDF.

O sistema deve salvar o edital localmente.

RF02 — Upload de documentos da empresa

O sistema deve permitir upload de múltiplos documentos (PDF).

Os documentos devem ser armazenados localmente.

RF03 — Leitura do edital

O agente deve:

Extrair o texto do edital

Identificar todos os documentos exigidos

Classificar os documentos por categoria:

Habilitação jurídica

Regularidade fiscal

Qualificação técnica

Qualificação econômico-financeira

RF04 — Classificação dos documentos da empresa

O agente deve:

Identificar o tipo de cada documento

Extrair data de validade quando existir

Associar documentos às categorias corretas

RF05 — Comparação exigido × disponível

O sistema deve indicar:

Documentos corretos

Documentos vencidos

Documentos faltantes

RF06 — Geração da pasta final

O sistema deve:

Criar estrutura de diretórios padronizada

Copiar os documentos corretos

Não copiar documentos vencidos sem aviso

RF07 — Checklist final

O sistema deve gerar um arquivo checklist.txt contendo:

Lista de documentos exigidos

Status de cada documento

Observações (vencido / ausente)

3️⃣ Requisitos Não Funcionais
RNF01 — Execução local

Todo o processamento deve ocorrer localmente.

RNF02 — Segurança

Nenhum documento deve ser enviado para a nuvem sem autorização explícita.

RNF03 — Auditabilidade

O sistema deve permitir verificação manual do resultado.

RNF04 — Manutenibilidade

Código modular, com responsabilidades bem definidas.

4️⃣ Arquitetura do Agente
Componentes

Interface Gráfica (UI)

Agente Leitor de Edital

Agente Classificador de Documentos

Agente Comparador

Gerador de Output

5️⃣ Estrutura de Pastas do Projeto
licitacao_agent/
├── ui/
│   └── app.py
├── agent/
│   ├── edital_reader.py
│   ├── document_classifier.py
│   ├── comparator.py
│   └── folder_generator.py
├── input/
│   ├── edital.pdf
│   └── documentos_empresa/
├── output/
│   └── licitacao_resultado/
├── main.py
└── requirements.txt

6️⃣ Passo a Passo de Implementação
Passo 1 — Preparar ambiente

Instalar Python 3.10+

Criar ambiente virtual

Instalar dependências

Passo 2 — Criar leitura de PDF

Implementar extração de texto do edital

Validar leitura de PDFs escaneados

Passo 3 — Criar prompt jurídico

Definir prompt fixo para extração de exigências

Retornar JSON estruturado

Passo 4 — Implementar classificador de documentos

Identificar tipo de documento por:

Nome do arquivo

Conteúdo textual

Extrair validade com regex + IA

Passo 5 — Implementar comparador

Comparar exigências do edital com documentos disponíveis

Classificar resultados

Passo 6 — Criar gerador de pastas

Criar diretórios padronizados

Copiar arquivos

Gerar checklist

Passo 7 — Criar interface gráfica

Implementar upload do edital

Implementar upload múltiplo de documentos

Exibir checklist e status final

Passo 8 — Testes

Testar com edital real

Testar documentos incompletos

Validar resultados manualmente

7️⃣ Critérios de Aceitação

✔ Upload funcional

✔ Extração correta das exigências

✔ Classificação correta dos documentos

✔ Pasta final organizada

✔ Checklist claro e confiável

Tennologia para usar na intercafe grafica
- Streamlit

🖥️ Layout da Tela — Agente de IA para Licitações (Local)
🎯 Princípios de UI

Fluxo linear (top → bottom)

Poucas decisões por vez

Feedback claro (status, erros, resultado)

Tudo visível sem navegação complexa

🧱 Estrutura Geral da Tela
┌────────────────────────────────────┐
│  📑 Agente de Licitação (Local)     │
│  Organizador automático de editais  │
├────────────────────────────────────┤
│  1️⃣ Upload do Edital                │
│  [ Selecionar arquivo PDF ]         │
│  (nome_do_edital.pdf)               │
├────────────────────────────────────┤
│  2️⃣ Documentos da Empresa           │
│  [ Selecionar múltiplos PDFs ]      │
│  contrato_social.pdf                │
│  cnpj.pdf                           │
│  certidao_fgts.pdf                  │
│  ...                                │
├────────────────────────────────────┤
│  ⚙️ Opções (opcional)                │
│  [ ] Validar datas de validade      │
│  [ ] Incluir documentos vencidos    │
│  [ ] Gerar checklist detalhado      │
├────────────────────────────────────┤
│  ▶️ Processar Licitação              │
│  (barra de progresso)               │
├────────────────────────────────────┤
│  📋 Resultado                        │
│  ✔ Documentos OK (8)                │
│  ⚠ Vencidos (1)                     │
│  ✖ Faltantes (2)                    │
│                                     │
│  [ Abrir pasta final ]              │
│  [ Baixar checklist ]               │
└────────────────────────────────────┘

🧩 Componentes da Tela (detalhados)
🟦 Cabeçalho

Título: “Agente de Licitação”

Subtítulo: “Organizador automático de documentos”

📌 Sem menus, sem distração.

📄 Seção 1 — Upload do Edital

FileUploader (PDF)

Exibe:

Nome do arquivo

Tamanho

Validação:

Apenas 1 arquivo

Apenas PDF

📂 Seção 2 — Documentos da Empresa

FileUploader (multiple)

Lista dinâmica:

Nome dos arquivos

Validação:

PDF apenas

Pelo menos 1 documento

⚙️ Seção 3 — Opções (checkbox)

(opcional, mas recomendada)

Validar datas de validade

Permitir incluir documentos vencidos

Gerar checklist detalhado

📌 Default: tudo ligado (segurança jurídica).

▶️ Botão principal

Texto: “Processar licitação”

Estado:

Desabilitado até uploads completos

Loading durante execução

📋 Seção 4 — Resultado

Exibição após processamento:

Indicadores

✔ OK

⚠ Vencidos

✖ Faltantes

Ações

Abrir pasta final

Baixar checklist

🎨 Visual (Streamlit-friendly)

Layout em coluna única

Ícones simples (emoji ou st.icon)

Cores suaves:

Verde → OK

Amarelo → Atenção

Vermelho → Faltante

🧠 UX importante (não esquecer)

Erros claros:

“Edital não enviado”

“Nenhum documento enviado”

Mensagem final:

“Revise os documentos antes do envio oficial.”

🧪 Estados da Tela
Estado	O que aparece
Inicial	Uploads + botão desativado
Processando	Spinner + barra
Sucesso	Resultado + ações
Erro	Mensagem clara + retry

Repo nanme
…or create a new repository on the command line
echo "# bid-ai-agent" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:souzabrunoj/bid-ai-agent.git
git push -u origin main

Proximos Passos
8️⃣ Riscos e Mitigações
Risco	Mitigação
Edital mal formatado	Prompt robusto + validação humana
Documento vencido	Validação automática + aviso
PDF escaneado	OCR
Falso positivo	Human-in-the-loop

9️⃣ Evoluções Futuras (Backlog)

OCR automático

Download ZIP

Histórico de licitações

Geração automática de declarações

Multi-agente especializado

🔑 Princípio fundamental

O agente organiza e analisa.
A responsabilidade jurídica final é humana.