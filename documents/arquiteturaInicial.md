# Arquitetura — Industrial Agent Reliability Platform

## Resumo

Agente de atendimento para o contexto industrial da TRACTIAN, capaz de investigar tickets de
clientes através da API fornecida, consultar diferentes fontes de dados e produzir uma decisão
fundamentada. O agente não apenas gera uma resposta: ele reconhece quando as evidências são
insuficientes ou conflitantes e, nesses casos, encaminha o caso para um engenheiro humano de forma
estruturada — entregando todo o contexto necessário para reduzir o tempo de investigação.

O diferencial da solução está em três pontos que se conectam:

1. **Camada de abstração** entre o agente e a API — a API não foi desenhada para receber um agente
   diretamente, então o agente nunca vê os 17 endpoints crus, só um conjunto controlado de tools.
2. **Trace de execução** — cada investigação gera um registro completo (tools chamadas, argumentos,
   resultados, evidências, conflitos, decisão, incertezas), que é a base para avaliar o agente.
3. **Intelligent Handoff** — quando a evidência não é suficiente, o agente não diz apenas "não
   consegui resolver": entrega um pacote com o que já foi investigado, evidências, conflitos entre
   fontes, dados faltantes e hipóteses, para que o engenheiro comece da decisão, não da investigação
   do zero.

## Camadas

```
Cliente (ticket)
      ↓
1. Agente — interpreta o ticket, planeja a investigação, escolhe tools, analisa evidências,
   decide (orientar / agir / escalar), reconhece incerteza
      ↓
2. Abstraction / Tool Layer — interface controlada entre o agente e a API
   get_asset · get_asset_analyses · get_analysis · get_baseline · get_rms · get_spectrum ·
   get_data_quality · get_model · search_knowledge · get_knowledge_doc
   (ações, exigem confirmação humana: reprocess_analysis · request_specialist_analysis ·
   request_model_retraining · escalate_case)
      ↓
3. API industrial TRACTIAN — empresas, ativos, análises, dados técnicos, modelos, conhecimento
      ↓
4. Decision Layer — evidência suficiente e sem conflito?
   sim → orientar/agir (com confirmação)     não → Intelligent Handoff → engenheiro
      ↓
5. Trace — registro completo da execução (tools, argumentos, resultados, evidências, conflitos,
   decisão, incertezas)
      ↓
6. Avaliação adaptativa — checks programáticos → LLM judges → failure analysis →
   scenario discovery → novos cenários/regressões → nova versão do agente (ciclo)
```

## Decisões de projeto

- **Confiança mínima para responder sozinho**: abaixo do limiar, ou diante de conflito entre
  fontes, ou com múltiplas lacunas de dados, o agente escala em vez de arriscar uma resposta.
- **Nenhuma ação de alto impacto sem confirmação humana** — reprocessar análise, solicitar
  especialista, solicitar retreinamento e escalar são sempre confirmadas antes de executar.
- **A explicação ao cliente é simples** — termos internos (baseline, RMS, detection_mode) ficam no
  trace e no handoff para o engenheiro; a resposta ao cliente é em linguagem direta.
- **O agente não tem acesso ao gabarito** (`eval/`, `docs/test-scenarios.md`, `data/cases.parquet`)
  — a avaliação é aplicada depois da execução, sobre o trace.

``` mermaid
---
config:
  layout: dagre
  theme: base
  themeVariables:
    lineColor: '#FFFFFF'
    primaryColor: '#FFFFFF'
    primaryTextColor: '#000000'
    primaryBorderColor: '#FFFFFF'
---
flowchart LR
    U["Cliente<br>ticket"] --> FE["Interface de demonstração<br>Streamlit ou Gradio"]
    FE --> AG["Agente de atendimento<br>LangGraph / Pydantic AI + LLM aberto"]
    AG --> TL["Camada de tools<br>funções Python + schemas Pydantic"] & TR["Trace<br>modelo Pydantic + log JSON"]
    TL --> IND["API industrial<br>FastAPI · fornecida pela Tractian"]
    IND --> DEC["Camada de decisão<br>regras Python sobre confiança e conflito"]
    DEC -- evidência suficiente --> GEN["Geração de resposta<br>LLM + trace como contexto"]
    DEC -- ação de impacto --> CONF["Confirmação humana<br>aprovação na interface"]
    DEC -- incerteza / conflito --> HAND["Intelligent Handoff<br>modelo Pydantic estruturado"]
    CONF --> HAND
    GEN --> TR
    HAND --> TR
    RUN["Execução dos cenários<br>script Python · 17 casos"] --> AG
    TR --> EVAL["EVAL / AVALIAÇÃO<br><br>
    Checks programáticos<br>
    Comparação trace × gabarito<br>
    LLM Judge<br>
    Métricas de desempenho"] & DB[("Casos · gabaritos · histórico<br>JSON / SQLite local")]
    EVAL --> FA["Failure Analysis<br><br>
    Agrupamento de falhas<br>
    Padrões de erro<br>
    Análise de causa"]
    FA --> SD["Scenario Discovery<br><br>
    LLM Judge<br>
    Seed da API<br>
    Novos cenários e regressões"]
    SD -. novos cenários / regressões .-> RUN
    SD -. feedback para melhoria .-> AG
    DB --> FE

     AG:::ai
     TL:::deterministic
     TR:::deterministic
     IND:::deterministic
     DEC:::deterministic
     GEN:::ai
     CONF:::deterministic
     HAND:::deterministic
     RUN:::deterministic
     EVAL:::evaluation
     DB:::storage
     FA:::deterministic
     SD:::ai
    classDef deterministic stroke:#2E7D32
    classDef ai stroke:#EF6C00
    classDef storage stroke:#1565C0
    classDef evaluation stroke:#6A1B9A,stroke-width:3px
```