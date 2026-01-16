# Extração de Matriz Curricular de PPC para CSV

Este documento explica como solicitar a extração de dados de matriz curricular de documentos PPC (Projeto Pedagógico de Curso) em formato PDF para CSV estruturado.

## Objetivo

Converter matrizes curriculares de PPCs em formato CSV padronizado, facilitando análise, importação em sistemas acadêmicos e processamento de dados.

## Estrutura do CSV Gerado

O CSV produzido contém as seguintes colunas:

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| nome_curso | Nome completo do curso | Análise e Desenvolvimento de Sistemas |
| ano_perfil | Ano e período do perfil curricular | 2019.2 |
| modulo | Número do módulo/período | 1, 2, 3, etc. |
| disciplina | Nome da disciplina | Programação Orientada a Objetos |
| creditos | Número de créditos | 4 |
| ch_aula | Carga horária em horas-aula | 80 |
| ch_relogio | Carga horária em horas-relógio | 60 |
| pre_requisito | Disciplina(s) pré-requisito | Introdução à Programação |
| co_requisito | Disciplina(s) co-requisito | Banco de Dados I |

## Template de Prompt

Ao solicitar a extração, use o seguinte template:

```
Leia a matriz curricular indicada na página [NÚMERO] do PPC e me retorne um CSV com os seguintes campos:

nome do curso, ano do perfil, módulo, disciplina, créditos, carga horária aula, carga horária relógio, pré-requisito, co-requisito

[OPCIONAL] Remova as linhas com optativas genéricas (Optativa 1, Optativa 2, etc.) e inclua os componentes indicados na seção "COMPONENTE CURRICULAR OPTATIVO"
```

## Exemplo de Prompt Completo

```
Leia a matriz curricular indicada na página 50 do PPC e me retorne um CSV com os seguintes campos: 

nome do curso, ano do perfil, módulo, disciplina, créditos, carga horária aula, carga horária relógio, pré-requisito, co-requisito

Remova as linhas com optativas genéricas (Optativa 1, Optativa 2, Optativa 3 e Optativa 4) e inclua os componentes indicados na seção: COMPONENTE CURRICULAR OPTATIVO
```

## Informações Importantes para Incluir

### Obrigatórias:
1. **Número da página** onde está a matriz curricular
2. **Campos desejados** no CSV (use a lista acima)
3. **Arquivo PDF** anexado à mensagem

### Opcionais:
4. **Tratamento de optativas**: Se o PPC tem optativas genéricas que devem ser expandidas
5. **Seção específica**: Nome da seção no PDF onde estão as optativas detalhadas
6. **Formato especial**: Se há algum formato específico necessário para pré/co-requisitos

## Variações Comuns em PPCs

Dependendo do PPC, você pode precisar ajustar:

### Nomenclatura de Períodos
- "módulo" vs "período" vs "semestre"
- Especifique qual termo usar no prompt

### Cargas Horárias
Alguns PPCs podem ter:
- CH Total
- CH Teórica / CH Prática
- CH Presencial / CH EAD

Especifique quais colunas você precisa.

### Pré/Co-requisitos
Alguns PPCs indicam:
- Por código da disciplina
- Por nome completo
- Em tabela separada

Indique se precisa buscar essa informação em outra seção.

## Exemplo de Prompt para Outro PPC

```
Leia a matriz curricular da página 45 do PPC anexado e gere um CSV com:

nome_curso, ano_perfil, semestre, componente_curricular, creditos, ch_teorica, ch_pratica, ch_total, prerequisitos

Observações:
- Use "semestre" ao invés de "módulo"
- Inclua tanto CH teórica quanto prática
- Os pré-requisitos estão indicados na página 46, inclua-os no CSV
```

## Pós-processamento

Após receber o CSV, você pode:

1. Importar em planilhas (Excel, Google Sheets)
2. Processar com Python/Pandas para análises
3. Importar em sistemas acadêmicos (SIGAA, Moodle, etc.)
4. Gerar visualizações do fluxo curricular

## Dicas

- Se o PDF estiver com OCR ruim, limpe o texto antes ou use um PDF de melhor qualidade
- Verifique se há disciplinas em múltiplas páginas
- Confirme os dados críticos (carga horária total, número de disciplinas)
- Para optativas, verifique se há limites de escolha por módulo

## Exemplo de Verificação

Após gerar o CSV, valide:

```bash
# Contar linhas (disciplinas + header)
wc -l matriz_curricular.csv

# Ver estrutura
head -5 matriz_curricular.csv

# Contar disciplinas por módulo
cut -d',' -f3 matriz_curricular.csv | sort | uniq -c
```

## Troubleshooting

**Problema**: Disciplinas com nomes quebrados
**Solução**: O PDF pode ter quebras de linha. Especifique no prompt para juntar linhas quebradas.

**Problema**: Pré-requisitos não identificados
**Solução**: Indique explicitamente a página/seção onde estão os pré-requisitos.

**Problema**: Carga horária inconsistente
**Solução**: Verifique se o PPC usa hora-aula de 45 ou 50 minutos e especifique no prompt.

---

## Metadata

- **Versão**: 1.0
- **Data**: 2025-01-16
- **Formato CSV**: UTF-8, separador vírgula
- **Exemplo base**: PPC ADS IFPE Campus Paulista 2019.2
