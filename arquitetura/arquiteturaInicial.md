## Arquitetura [Proposta]: Industrial Agent Reliability Platform (Tractian)
 
## Resumo
 
Este documento descreve a arquitetura planejada para um agente de atendimento voltado ao contexto industrial da TRACTIAN, capaz de investigar tickets de clientes através da API fornecida, consultar diferentes fontes de dados e produzir uma decisão fundamentada. O projeto foi desenhado, mas não implementado até o momento. O que segue é o plano de arquitetura que guiaria a construção.
 
A ideia central é que o agente não apenas gere uma resposta: ele deve reconhecer quando as evidências forem insuficientes ou conflitantes e, nesses casos, encaminhar o caso para um engenheiro humano de forma estruturada, entregando todo o contexto necessário para reduzir o tempo de investigação.
 
O diferencial da proposta está em quatro pontos que se conectam:
 
1. **Camada de abstração entre o agente e a API**. A API não foi desenhada para receber um agente diretamente, então o agente nunca veria os endpoints crus, apenas um conjunto controlado de tools (funções Python com schemas Pydantic).
2. **Trace de execução**. Cada investigação geraria um registro completo (tools chamadas, argumentos, resultados, evidências, conflitos, decisão, incertezas), que serviria de base para avaliar o agente e ficaria persistido junto com o histórico de casos.
3. **Confirmação humana + Intelligent Handoff.** Ações de alto impacto passariam por aprovação antes de executar; quando a evidência não fosse suficiente, o agente não diria apenas "não consegui resolver": entregaria um pacote estruturado com o que já foi investigado, evidências, conflitos entre fontes, dados faltantes e hipóteses, para que o engenheiro comece da decisão, não da investigação do zero.
4. **Avaliação adaptativa em ciclo fechado.** O trace alimentaria checks programáticos e LLM judges, que alimentariam análise de falhas e descoberta de novos cenários, que realimentariam tanto a bateria de testes quanto o próprio agente.

## Camadas (planejadas)
 
1. **Interface de demonstração (Streamlit / Gradio):** receberia o ticket do cliente, exporia histórico de casos.
2. **Agente (LangGraph / Pydantic AI + LLM aberto):** interpretaria o ticket, planejaria a investigação, escolheria tools, analisaria evidências, decidiria (orientar / agir / escalar), reconheceria incerteza.
3. **Abstraction / Tool Layer:** interface controlada entre o agente e a API (funções Python + schemas Pydantic). Tools de leitura: get_asset, get_asset_analyses, get_analysis, get_baseline, get_rms, get_spectrum, get_data_quality, get_model, search_knowledge, get_knowledge_doc. Tools de ação, exigiriam confirmação humana: reprocess_analysis, request_specialist_analysis, request_model_retraining, escalate_case.
4. **API industrial TRACTIAN (FastAPI, fornecida pela Tractian):** empresas, ativos, análises, dados técnicos, modelos, conhecimento.
5. **Camada de decisão (regras Python sobre confiança e conflito):** se evidência suficiente, vai para Geração de resposta (LLM + trace como contexto); se ação de impacto, vai para Confirmação humana (aprovação na interface) e depois Intelligent Handoff; se incerteza ou conflito, vai direto para Intelligent Handoff (modelo Pydantic estruturado) e daí para o engenheiro.
6. **Trace:** registro completo da execução (tools, argumentos, resultados, evidências, conflitos, decisão, incertezas), alimentado tanto pela geração de resposta quanto pelo handoff.
7. **Persistência:** casos, gabaritos e histórico (JSON / SQLite local), que também alimentaria de volta a interface de demonstração.
8. **Avaliação adaptativa (ciclo):** checks programáticos, comparação trace x gabarito e LLM judges alimentam a Failure Analysis (agrupamento de falhas, padrões de erro, causa raiz), que alimenta a Scenario Discovery (LLM judge, seed da API, novos cenários e regressões). A partir daí, dois loops de feedback: (a) novos cenários/regressões realimentam a execução de testes (17 casos), disparando novamente o agente; (b) feedback direto para melhoria do agente, sem passar por um novo cenário.

## Decisões de projeto (premissas do plano)
 
- Confiança mínima para responder sozinho: abaixo do limiar, ou diante de conflito entre fontes, ou com múltiplas lacunas de dados, o agente deveria escalar em vez de arriscar uma resposta.
- Nenhuma ação de alto impacto sem confirmação humana: reprocessar análise, solicitar especialista, solicitar retreinamento e escalar seriam sempre confirmadas antes de executar; mesmo após confirmadas, o caso seguiria registrado no Intelligent Handoff.
- A explicação ao cliente deveria ser simples: termos internos (baseline, RMS, detection_mode) ficariam no trace e no handoff para o engenheiro; a resposta ao cliente seria em linguagem direta.
- O agente não teria acesso ao gabarito (eval/, docs/test-scenarios.md, data/cases.parquet): a avaliação seria aplicada depois da execução, sobre o trace.
- Duas malhas de feedback distintas na avaliação: uma geraria novos cenários/regressões que realimentariam a bateria de testes; outra devolveria feedback diretamente ao agente, permitindo ajuste sem esperar um novo ciclo completo de cenários.
- Persistência separada do trace: casos, gabaritos e histórico ficariam em um armazenamento próprio (JSON/SQLite), o que permitiria à interface exibir histórico sem reprocessar traces.
- Componentes determinísticos vs. baseados em LLM: agente, geração de resposta e scenario discovery dependeriam de LLM; camada de tools, trace, decisão, confirmação, handoff, execução de cenários e failure analysis seriam determinísticos, distinção útil para saber onde a avaliação precisaria ser mais rigorosa.

### Diagrama

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