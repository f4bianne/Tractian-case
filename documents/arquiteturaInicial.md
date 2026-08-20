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
