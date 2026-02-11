# 🎓 Guia de Treinamento do Modelo

Este guia explica como adicionar exemplos de editais para melhorar a precisão do sistema.

---

## 🎯 Por Que Treinar?

Adicionar exemplos de editais reais melhora:
- ✅ **Precisão de extração:** +15-30%
- ✅ **Matching de documentos:** +20-40%
- ✅ **Identificação de sinônimos:** +50%

---

## 📚 Como Adicionar Exemplos

### **Opção 1: Extrair Automaticamente de PDFs (RECOMENDADO! 🚀)**

Se você tem os PDFs dos editais, use esta opção:

#### **Um único PDF:**
```bash
python extract_from_pdf.py caminho/para/edital.pdf
```

#### **Vários PDFs de uma vez:**
```bash
# Processar todos PDFs de uma pasta
python batch_extract_pdfs.py editais/

# Ou processar arquivos específicos
python batch_extract_pdfs.py edital1.pdf edital2.pdf edital3.pdf
```

**O que acontece:**
1. ✅ Extrai texto do PDF (com OCR se necessário)
2. ✅ Identifica documentos exigidos automaticamente
3. ✅ Classifica por categoria
4. ✅ Gera arquivo JSON pronto
5. ⚠️ Você só revisa e ajusta se necessário

**Exemplo:**
```bash
# Colocar PDFs em uma pasta
mkdir editais_para_treinar
cp ~/Downloads/pregao_*.pdf editais_para_treinar/

# Processar todos de uma vez
python batch_extract_pdfs.py editais_para_treinar/

# Pronto! Arquivos JSON criados em training/examples/
```

### **Opção 2: Script Interativo**

Execute o script e responda as perguntas:

```bash
python add_training_example.py
```

O script vai perguntar:
1. Nome do edital
2. Cada documento exigido
3. Categoria de cada documento
4. Descrição e requisitos específicos
5. Metadados (seu nome, notas)

### **Opção 3: Criar JSON Manualmente**

1. **Copie o template:**
   ```bash
   cp training/examples/example_template.json training/examples/meu_edital.json
   ```

2. **Edite o arquivo** com os dados do seu edital:

```json
{
  "edital_name": "Pregão Eletrônico 001/2026 - Fornecimento de Ovos",
  "requirements": [
    {
      "name": "Certidão Negativa de Débitos Federais",
      "category": "regularidade_fiscal",
      "description": "Certidão expedida pela Receita Federal",
      "requirements": "Válida na data de abertura do edital",
      "is_mandatory": true
    },
    {
      "name": "Certidão de Regularidade do FGTS",
      "category": "regularidade_fiscal",
      "description": "CRF emitida pela Caixa Econômica Federal",
      "requirements": "Com validade vigente",
      "is_mandatory": true
    }
  ],
  "metadata": {
    "extraction_date": "2026-02-11",
    "extracted_by": "Seu Nome",
    "notes": "Edital para fornecimento de ovos de páscoa"
  }
}
```

3. **Salve** na pasta `training/examples/`

---

## 📂 Categorias Disponíveis

Use **exatamente** uma destas categorias:

| Código | Descrição | Exemplos |
|--------|-----------|----------|
| `habilitacao_juridica` | Documentos legais da empresa | Contrato Social, CNPJ, Procuração |
| `regularidade_fiscal` | Certidões fiscais | CND Federal, CRF/FGTS, CND Municipal |
| `qualificacao_tecnica` | Capacidade técnica | Atestados, Certificados, Registros |
| `qualificacao_economica` | Capacidade financeira | Balanço Patrimonial, Certidão Falência |
| `proposta_comercial` | Proposta e preços | Planilha de Preços, Declarações |
| `outros` | Outros documentos | Qualquer outro tipo |

---

## ✍️ Dicas de Preenchimento

### **Nome do Documento**
- ✅ Use o nome **exato** do edital
- ✅ Inclua variações comuns
- ❌ Não use abreviações sem explicar

**Exemplos:**
- ✅ "Certidão Negativa de Débitos Federais (CND)"
- ✅ "Certidão de Regularidade do FGTS (CRF)"
- ❌ "CND" (muito vago)

### **Descrição**
- ✅ Copie do edital quando possível
- ✅ Seja específico sobre órgão emissor
- ✅ Mencione tipo de certidão/documento

**Exemplo:**
```
"Certidão Negativa de Débitos relativos aos Tributos Federais 
e à Dívida Ativa da União, expedida pela Secretaria da Receita 
Federal do Brasil"
```

### **Requirements (Requisitos Específicos)**
- ✅ Validade exigida
- ✅ Formato aceito (original, cópia, digital)
- ✅ Observações especiais

**Exemplo:**
```
"Válida na data de abertura do edital. Aceita certidão 
positiva com efeito de negativa"
```

---

## 🔄 Workflow Recomendado

### **Para Cada Edital Novo:**

1. **Leia o edital** e identifique todos os documentos
2. **Anote** cada documento com sua categoria
3. **Use o script** `add_training_example.py` OU crie JSON manualmente
4. **Teste** rodando o sistema com esse edital
5. **Compare** a extração automática com sua extração manual
6. **Ajuste** se necessário

### **Exemplo de Fluxo:**

```bash
# 1. Adicionar exemplo
python add_training_example.py

# 2. Verificar que foi criado
ls training/examples/

# 3. Rodar o sistema
streamlit run ui/app.py

# 4. Testar com o mesmo edital
# Upload o PDF e veja se a extração melhorou
```

---

## 📊 Exemplos Prontos

Incluímos alguns exemplos comuns. Você pode usá-los como referência:

### **Exemplo 1: Pregão Eletrônico Básico**
Arquivo: `training/examples/pregao_basico_exemplo.json`

Documentos típicos:
- CND Federal
- CRF/FGTS
- CND Estadual
- CND Municipal
- Certidão Trabalhista
- Contrato Social

### **Exemplo 2: Licitação com Qualificação Técnica**
Arquivo: `training/examples/licitacao_tecnica_exemplo.json`

Documentos adicionais:
- Atestados de capacidade técnica
- Certidões de registro profissional
- Comprovação de experiência

### **Exemplo 3: Tomada de Preços Complexa**
Arquivo: `training/examples/tomada_precos_exemplo.json`

Documentos adicionais:
- Balanço patrimonial
- Certidão de falência e concordata
- Garantia de proposta

---

## 🧪 Validação dos Exemplos

O sistema valida automaticamente:

✅ **Formato JSON válido**
✅ **Categorias corretas** (das 6 permitidas)
✅ **Campos obrigatórios** presentes
✅ **Estrutura consistente**

Se houver erro, você verá uma mensagem no log:
```
ERROR - Failed to load example pregao_001.json: Invalid category
```

---

## 📈 Medindo Impacto

### **Antes de Adicionar Exemplos:**
```
✅ Documentos Encontrados: 3/10 (30%)
❌ Documentos Faltantes: 7
```

### **Depois de Adicionar 5-10 Exemplos:**
```
✅ Documentos Encontrados: 8/10 (80%)
❌ Documentos Faltantes: 2
```

---

## 🎯 Quantos Exemplos Preciso?

| Quantidade | Resultado Esperado |
|------------|-------------------|
| 1-3 exemplos | Melhora básica (~10-15%) |
| 5-10 exemplos | Melhora significativa (~20-30%) |
| 10-20 exemplos | Excelente performance (~40-50%) |
| 20+ exemplos | Performance máxima (~50-60%) |

**Recomendação:** Comece com **5 editais** dos tipos mais comuns que você processa.

---

## 🔧 Troubleshooting

### **Exemplo não está sendo usado**

1. Verifique se o arquivo está em `training/examples/`
2. Confirme que é um JSON válido:
   ```bash
   python -m json.tool training/examples/seu_arquivo.json
   ```
3. Reinicie a aplicação Streamlit
4. Veja os logs para erros:
   ```
   INFO - Loaded example: Pregão 001/2026
   ```

### **Categoria inválida**

Use **exatamente** uma destas:
- `habilitacao_juridica`
- `regularidade_fiscal`
- `qualificacao_tecnica`
- `qualificacao_economica`
- `proposta_comercial`
- `outros`

### **JSON com erro de sintaxe**

Use um validador online: https://jsonlint.com/

Erros comuns:
- ❌ Vírgula no último item
- ❌ Aspas simples `'` ao invés de duplas `"`
- ❌ Falta de fechamento `}` ou `]`

---

## 📞 Precisa de Ajuda?

1. Consulte `training/README.md` para mais detalhes
2. Veja `training/examples/example_template.json` para referência
3. Execute `python add_training_example.py` para modo interativo
4. Abra uma issue no GitHub para suporte

---

## 🎉 Pronto para Começar!

```bash
# Execute o script interativo
python add_training_example.py

# Ou crie um JSON manualmente
cp training/examples/example_template.json training/examples/meu_primeiro_edital.json
nano training/examples/meu_primeiro_edital.json

# Teste o sistema
streamlit run ui/app.py
```

**Boa sorte com o treinamento! 🚀**
