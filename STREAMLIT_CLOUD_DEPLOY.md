# 🚀 Guia de Deploy no Streamlit Cloud

Este guia detalha como fazer deploy do Bid AI Agent no Streamlit Cloud.

---

## 📋 Pré-requisitos

- ✅ Conta GitHub com repositório do projeto
- ✅ Conta no Streamlit Cloud (gratuita): https://share.streamlit.io/

---

## 🔧 Passo a Passo

### **1. Criar App no Streamlit Cloud**

1. Acesse: https://share.streamlit.io/
2. Clique em **"New app"**
3. Preencha as informações:
   - **Repository**: `souzabrunoj/bid-ai-agent` (seu repositório)
   - **Branch**: `main`
   - **Main file path**: `ui/app.py`
   - **App URL**: Escolha um nome (ex: `souza-ai-licitacao`)

### **2. Configurar Secrets (IMPORTANTE)**

Antes de fazer deploy, você **DEVE** configurar as variáveis de ambiente:

1. Na página do seu app, clique em **"Advanced settings"** (ou Settings após o deploy)
2. Vá em **"Secrets"**
3. Cole o seguinte conteúdo:

```toml
# Disable LLM for cloud deployment (no local model available)
LLM_ENABLED = false

# Optional configurations
DEBUG_MODE = false
LOG_LEVEL = "INFO"
MAX_FILE_SIZE_MB = 50
```

4. Clique em **"Save"**

### **3. Deploy**

1. Clique em **"Deploy!"**
2. Aguarde a instalação das dependências (~2-5 minutos)
3. Seu app estará online em: `https://[seu-app-name].streamlit.app`

---

## ⚠️ Limitações na Versão Cloud

### **1. Sem Modelo LLM Local**

**Problema**: O modelo `.gguf` é muito grande para o Streamlit Cloud.

**Solução**: O sistema usa extração baseada em regras (ainda funcional, mas menos preciso).

**Alternativa**: Para produção, integre uma API de LLM:
- OpenAI GPT-4
- Anthropic Claude
- Hugging Face Inference API

### **2. Pasta `documentos/` Não Persiste**

**Problema**: Arquivos não são mantidos entre deploys ou reinicializações.

**Solução Atual**: Upload de documentos a cada sessão.

**Alternativa**: Para produção, use armazenamento persistente:
- AWS S3
- Google Cloud Storage
- Supabase Storage

### **3. Performance de OCR**

**Problema**: OCR pode ser lento no plano gratuito.

**Solução**: O app funciona, mas pode demorar para PDFs escaneados.

**Alternativa**: Para produção, use serviços de OCR em nuvem:
- Google Cloud Vision API
- AWS Textract
- Azure Computer Vision

---

## 🔍 Troubleshooting

### **Erro: "ModuleNotFoundError: No module named 'llama_cpp'"**

**Causa**: Dependência `llama-cpp-python` falha ao instalar no cloud.

**Solução**:
1. Vá em Settings → Secrets
2. Adicione: `LLM_ENABLED = false`
3. Reinicie o app

### **Erro: "Path traversal attempt detected"**

**Causa**: Upload de arquivos em paths temporários.

**Solução**: Já corrigido no código (permite `/tmp` paths).

### **App Lento ou Timeout**

**Causa**: OCR de muitos documentos grandes.

**Solução**:
- Reduza o tamanho dos PDFs
- Processe menos documentos por vez
- Use PDFs com texto nativo (não escaneados)

### **Erro: "Resource limits exceeded"**

**Causa**: Plano gratuito tem limites de memória/CPU.

**Solução**:
- Upgrade para Streamlit Cloud Pro
- Ou deploy em servidor próprio (ver `DEPLOYMENT.md`)

---

## 🎯 Funcionalidades na Versão Cloud

✅ **Funcionam Normalmente:**
- Upload de edital (PDF)
- Upload de documentos da empresa (PDF e ZIP)
- Extração de texto e OCR
- Detecção de datas de validade
- Visualização de documentos
- Classificação básica de documentos
- Comparação de requisitos
- Geração de relatórios

⚠️ **Funcionalidades Limitadas:**
- Extração de requisitos do edital (usa regras, não LLM)
- Precisão da classificação (sem fine-tuning do LLM)

❌ **Não Funcionam:**
- Modelo LLM local
- Persistência de documentos entre sessões

---

## 🔄 Atualizar App Após Mudanças

Sempre que você fizer push de novas mudanças no GitHub:

1. O Streamlit Cloud detecta automaticamente
2. Faz rebuild automático
3. Ou clique em **"Reboot"** para forçar atualização

---

## 💰 Custos

### **Streamlit Cloud Free:**
- ✅ 1 app privado
- ✅ 1 GB RAM
- ✅ 1 CPU compartilhado
- ❌ Sem armazenamento persistente

### **Streamlit Cloud Pro ($20/mês):**
- ✅ 3 apps privados
- ✅ 4 GB RAM
- ✅ 2 CPUs dedicados
- ✅ Melhor performance

---

## 📊 Monitoramento

Para ver logs e métricas:

1. Acesse seu app no Streamlit Cloud
2. Clique em **"Manage app"**
3. Veja:
   - **Logs**: Erros e debug
   - **Analytics**: Visitantes e uso
   - **Settings**: Configurações

---

## 🚀 Alternativas de Deploy

Se o Streamlit Cloud não atender suas necessidades:

1. **Heroku**: Deploy com Dockerfile (ver `DEPLOYMENT.md`)
2. **AWS EC2**: Servidor dedicado
3. **Google Cloud Run**: Serverless com containers
4. **DigitalOcean App Platform**: Deploy simples
5. **Self-hosted**: Seu próprio servidor

Veja `DEPLOYMENT.md` para instruções detalhadas.

---

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs no Streamlit Cloud
2. Consulte a documentação: https://docs.streamlit.io/deploy
3. Abra issue no GitHub do projeto
4. Entre em contato com suporte do Streamlit

---

## ✅ Checklist de Deploy

- [ ] Repositório no GitHub atualizado
- [ ] Arquivo `packages.txt` presente
- [ ] Arquivo `requirements.txt` atualizado
- [ ] Secrets configurados (LLM_ENABLED = false)
- [ ] App criado no Streamlit Cloud
- [ ] Main file configurado: `ui/app.py`
- [ ] Deploy iniciado
- [ ] App funcionando (testar upload e processamento)
- [ ] URL compartilhada com usuários

---

**Pronto! Seu app está no ar! 🎉**
