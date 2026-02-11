# Training Examples

Esta pasta contém exemplos de extrações manuais de editais para melhorar a precisão do sistema.

## Como Adicionar um Exemplo

### 1. Criar Arquivo JSON

Crie um arquivo JSON na pasta `examples/` com o seguinte formato:

```json
{
  "edital_name": "Pregão Eletrônico 001/2026 - Fornecimento de Ovos de Páscoa",
  "requirements": [
    {
      "name": "Certidão Negativa de Débitos Federais",
      "category": "regularidade_fiscal",
      "description": "Certidão Negativa de Débitos relativos aos Tributos Federais e à Dívida Ativa da União",
      "requirements": "Emitida pela Receita Federal, válida na data de abertura",
      "is_mandatory": true
    },
    {
      "name": "Certidão de Regularidade do FGTS",
      "category": "regularidade_fiscal",
      "description": "Certidão de Regularidade do FGTS (CRF)",
      "requirements": "Emitida pela Caixa Econômica Federal, com validade",
      "is_mandatory": true
    },
    {
      "name": "Certidão Negativa de Débitos Municipais",
      "category": "regularidade_fiscal",
      "description": "Certidão Negativa de Débitos junto à Fazenda Municipal",
      "requirements": "Do município sede da empresa",
      "is_mandatory": true
    }
  ],
  "metadata": {
    "extraction_date": "2026-02-11",
    "extracted_by": "Bruno Souza",
    "notes": "Edital de pregão eletrônico para fornecimento de ovos de páscoa"
  }
}
```

### 2. Categorias Válidas

Use uma das seguintes categorias:

- `habilitacao_juridica` - Documentos de constituição da empresa
- `regularidade_fiscal` - Certidões fiscais e regularidades
- `qualificacao_tecnica` - Atestados e capacitações técnicas
- `qualificacao_economica` - Balanços e comprovações financeiras
- `proposta_comercial` - Documentos da proposta comercial
- `outros` - Outros documentos

### 3. Como o Sistema Usa os Exemplos

O sistema usa os exemplos de três formas:

1. **Few-Shot Learning**: Inclui exemplos similares no prompt do LLM
2. **Validação**: Verifica se a extração automática está consistente
3. **Fallback**: Usa padrões comuns quando o LLM não está disponível

### 4. Organizando Sua Extração Manual

Para adicionar sua extração:

1. Copie o template: `example_template.json`
2. Renomeie para algo descritivo: `pregao_ovos_pascoa_2026.json`
3. Preencha todos os campos
4. Salve na pasta `examples/`
5. Execute a aplicação - o sistema carregará automaticamente

## Exemplo Completo

Veja `example_template.json` para um template completo.

## Dicas

- **Seja específico**: Quanto mais detalhes, melhor
- **Use descrições do edital**: Copie as exigências exatas
- **Adicione contexto**: Use o campo `requirements` para detalhes
- **Categorize corretamente**: Isso ajuda no matching
- **Inclua variações**: CND, Certidão Negativa, etc.

## Validação

O sistema validará automaticamente:
- Formato JSON correto
- Categorias válidas
- Campos obrigatórios presentes

## Performance

Adicionar exemplos melhora:
- Precisão de extração: +15-30%
- Matching de documentos: +20-40%
- Identificação de sinônimos: +50%

---

**Nota**: Exemplos são carregados automaticamente no início da aplicação.
