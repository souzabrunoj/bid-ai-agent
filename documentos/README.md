# Documentos da Empresa

Esta pasta contém os documentos permanentes da empresa.

## Como Nomear os Arquivos

Use nomes claros e descritivos para facilitar a identificação automática:

### ✅ Bons Nomes:

**Habilitação Jurídica:**
- `contrato_social.pdf`
- `cnpj.pdf`
- `estatuto_social.pdf`

**Regularidade Fiscal:**
- `cnd_federal.pdf` - Certidão Negativa Federal
- `cnd_estadual.pdf` - Certidão Negativa Estadual
- `cnd_municipal.pdf` - Certidão Negativa Municipal
- `crf_fgts.pdf` - Regularidade FGTS
- `cndt_trabalhista.pdf` - Certidão Negativa Trabalhista

**Qualificação Técnica:**
- `atestado_capacidade_tecnica.pdf`
- `registro_profissional_crea.pdf`
- `cat_acervo_tecnico.pdf`

**Qualificação Econômica:**
- `balanco_patrimonial_2025.pdf`
- `demonstracao_contabil_2025.pdf`
- `certidao_negativa_falencia.pdf`

### ❌ Evite:
- `doc1.pdf` - muito genérico
- `arquivo.pdf` - não identifica conteúdo
- `Scan_20260211.pdf` - não descreve documento

## Atualização de Documentos

Quando um documento vencer:
1. Gere o novo documento
2. **Substitua** o arquivo antigo mantendo o mesmo nome
3. Execute o processamento novamente

Exemplo:
- `cnd_federal.pdf` venceu em 15/01/2026
- Gere nova CND Federal
- Salve como `cnd_federal.pdf` (mesmo nome)
- Sistema detectará automaticamente a nova data

## Organização

Você pode criar subpastas se preferir:

```
documentos/
├── habilitacao/
│   ├── contrato_social.pdf
│   └── cnpj.pdf
├── fiscal/
│   ├── cnd_federal.pdf
│   ├── cnd_estadual.pdf
│   └── crf_fgts.pdf
└── tecnica/
    └── atestado_capacidade.pdf
```

O sistema busca em todas as subpastas automaticamente.
