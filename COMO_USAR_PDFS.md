# 📄 Como Usar PDFs para Treinar o Modelo

Guia rápido para adicionar seus editais em PDF como exemplos de treinamento.

---

## 🖥️ Método 1: Via Interface (MAIS FÁCIL! ⭐)

### **Passo 1: Abra a aplicação**

```bash
streamlit run ui/app.py
```

### **Passo 2: Use a sidebar de Training**

1. Na **sidebar esquerda**, procure a seção **🎓 Training**
2. Clique em **"📤 Upload Edital for Training"**
3. Selecione o PDF do edital
4. Clique em **"🚀 Process & Add to Training"**
5. Aguarde o processamento
6. Pronto! ✅

**O sistema vai automaticamente:**
- ✅ Extrair todos os documentos exigidos
- ✅ Classificar por categoria
- ✅ Salvar o arquivo JSON em `training/examples/`
- ✅ Salvar o PDF em `training/source_editals/`

**Vantagens:**
- 🎯 Mais fácil e visual
- ⚡ Feedback instantâneo
- 📊 Mostra resumo da extração
- 🔄 Já atualiza automaticamente

---

## 🚀 Método 2: Via Linha de Comando

### **Passo 1: Organize seus PDFs**

Crie uma pasta e coloque todos os editais:

```bash
mkdir editais_treino
cp ~/Downloads/edital*.pdf editais_treino/
```

### **Passo 2: Execute o extrator em lote**

```bash
python batch_extract_pdfs.py editais_treino/
```

Quando perguntar seu nome, digite (será salvo nos metadados):
```
Your name (for metadata) [Batch]: Seu Nome
```

### **Passo 3: Aguarde o processamento**

O script vai:
- ✅ Extrair texto de cada PDF
- ✅ Identificar documentos exigidos
- ✅ Classificar por categoria
- ✅ Gerar arquivos JSON em `training/examples/`

### **Passo 4: Revise os arquivos gerados**

Abra os arquivos JSON criados em `training/examples/` e verifique:
- ✅ Nomes dos documentos estão corretos?
- ✅ Categorias fazem sentido?
- ✅ Descrições estão completas?

### **Passo 5: Teste!**

```bash
streamlit run ui/app.py
```

Upload o mesmo edital e veja a precisão melhorar! 🎯

---

## 📝 Processar Um PDF Por Vez

Se preferir revisar cada extração:

```bash
python extract_from_pdf.py edital_001.pdf
```

O script vai:
1. Extrair e mostrar os documentos encontrados
2. Perguntar se você quer editar o nome
3. Perguntar se quer adicionar notas
4. Salvar o arquivo JSON

---

## 📂 Estrutura de Pastas Sugerida

```
bid-ai-agent/
├── editais_treino/          # ← SEUS PDFs AQUI
│   ├── pregao_001_2026.pdf
│   ├── pregao_002_2026.pdf
│   └── tomada_precos_003.pdf
│
├── training/
│   └── examples/            # ← JSON gerados automaticamente
│       ├── pregao_001_2026.json
│       ├── pregao_002_2026.json
│       └── tomada_precos_003.json
```

---

## 🎯 Exemplo Completo

```bash
# 1. Criar pasta para PDFs
mkdir editais_treino

# 2. Copiar seus PDFs
cp ~/Downloads/*.pdf editais_treino/

# 3. Processar todos
python batch_extract_pdfs.py editais_treino/

# 4. Ver quantos foram criados
ls -l training/examples/*.json | wc -l

# 5. Testar a aplicação
streamlit run ui/app.py
```

---

## ⚙️ Opções Avançadas

### **Processar PDFs específicos**

```bash
python batch_extract_pdfs.py \
    edital1.pdf \
    edital2.pdf \
    edital3.pdf
```

### **Processar com revisão manual**

Use o script individual para revisar cada um:

```bash
for pdf in editais_treino/*.pdf; do
    python extract_from_pdf.py "$pdf"
done
```

---

## 🔍 Verificando a Qualidade

Depois de adicionar exemplos, compare:

### **Antes:**
```
❌ Documentos Faltantes: 7/10 (30% de precisão)
```

### **Depois (com 5+ exemplos):**
```
✅ Documentos Encontrados: 8/10 (80% de precisão)
```

---

## 🛠️ Troubleshooting

### **"No meaningful text extracted"**

O PDF está escaneado. O OCR será usado automaticamente, mas pode demorar mais.

**Solução:** Aguarde. O Tesseract está processando.

### **"Too many requirements found"**

O PDF tem muito texto não relacionado aos documentos.

**Solução:** Revise o JSON gerado e remova requisitos incorretos manualmente.

### **"Wrong category assigned"**

A classificação automática errou.

**Solução:** Edite o arquivo JSON e corrija a categoria:

```json
{
  "name": "CND Federal",
  "category": "regularidade_fiscal",  ← Corrija aqui se necessário
  ...
}
```

Categorias válidas:
- `habilitacao_juridica`
- `regularidade_fiscal`
- `qualificacao_tecnica`
- `qualificacao_economica`
- `proposta_comercial`
- `outros`

---

## 📊 Quantos PDFs Preciso?

| Quantidade | Resultado Esperado |
|------------|-------------------|
| 2-3 PDFs | Melhora básica (~15%) |
| 5-8 PDFs | Melhora boa (~30%) |
| 10-15 PDFs | Melhora significativa (~50%) |
| 20+ PDFs | Performance máxima (~60-70%) |

**Recomendação:** Comece com **5 editais** dos tipos que você mais processa.

---

## ✅ Checklist

- [ ] Crie pasta `editais_treino/`
- [ ] Copie PDFs dos editais para a pasta
- [ ] Execute `python batch_extract_pdfs.py editais_treino/`
- [ ] Aguarde processamento
- [ ] Revise JSONs gerados em `training/examples/`
- [ ] Corrija categorias/descrições se necessário
- [ ] Teste: `streamlit run ui/app.py`
- [ ] Compare precisão antes/depois

---

## 🎉 Pronto!

Agora o sistema vai usar seus exemplos para melhorar a extração automaticamente!

**Dica:** Quanto mais editais **variados** você adicionar, melhor o sistema fica em reconhecer diferentes formatos e terminologias.

---

## 📞 Precisa de Ajuda?

- Consulte `TRAINING_GUIDE.md` para mais detalhes
- Execute `python extract_from_pdf.py --help` para ver opções
- Veja exemplos em `training/examples/`
