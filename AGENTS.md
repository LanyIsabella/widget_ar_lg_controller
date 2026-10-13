# AGENTS.md — LG AC Controller

## 1. Visão geral

Desenvolver um widget desktop para Windows, utilizando Python, que permita monitorar e controlar pela rede um ar-condicionado **LG Split Hi Wall Dual Inverter Voice** já conectado ao Wi-Fi e associado ao aplicativo **LG ThinQ**.

O widget deverá ser compacto, responsivo e de uso cotidiano, oferecendo acesso rápido aos controles do ar-condicionado sem necessidade de abrir o aplicativo no celular. A aplicação deve ser capaz de funcionar em segundo plano e disponibilizar um ícone na bandeja do sistema.

**Escopo de comunicação:** priorizar a integração por rede com a API oficial **LG ThinQ Connect**, quando disponível e compatível. A comunicação via nuvem não deve ser apresentada como comunicação direta LAN. A operação exclusivamente local, sem internet, não é requisito inicial e dependerá de investigação específica.

## 2. Objetivos

### Objetivo geral

Construir uma aplicação desktop Windows em Python que apresente o estado do ar-condicionado e execute seus comandos suportados por uma integração de rede comprovadamente funcional.

### Objetivos específicos

- Investigar a compatibilidade do equipamento com a API LG ThinQ Connect e suas condições de uso.
- Implementar autenticação, descoberta e seleção do dispositivo por mecanismos suportados.
- Consultar e exibir o estado real do equipamento.
- Enviar comandos de controle somente quando suportados e autorizados.
- Construir interface compacta com PySide6, temas claro e escuro e controles acessíveis.
- Executar em segundo plano com bandeja do sistema e inicialização automática opcional.
- Garantir tratamento de falhas, persistência de preferências e armazenamento seguro de segredos.
- Criar testes automatizados e empacotamento para distribuição em Windows.

## 3. Tecnologias e critérios de escolha

- **Linguagem:** Python 3.12 ou superior, conforme compatibilidade das dependências.
- **Interface:** PySide6 (Qt for Python), com widgets e componentes reutilizáveis.
- **Integração LG:** API oficial ThinQ Connect como primeira opção; avaliar bibliotecas e SDKs Python, incluindo `thinqconnect`, apenas após conferir documentação, manutenção, licença e compatibilidade real.
- **Concorrência:** mecanismos assíncronos ou workers compatíveis com Qt, sem bloquear a thread da interface.
- **Configurações:** Pydantic Settings ou solução equivalente, evitando complexidade desnecessária.
- **Credenciais:** armazenamento seguro com Windows Credential Manager, por biblioteca adequada, ou mecanismo equivalente do sistema operacional.
- **Testes:** pytest com mocks/fakes da integração e testes específicos de integração quando houver dispositivo acessível.
- **Empacotamento:** PyInstaller ou alternativa fundamentada.
- **Dependências:** priorizar ferramentas open-source bem mantidas.

Não assumir que a simples existência de uma biblioteca implica suporte ao modelo de ar-condicionado. Não introduzir dependências sem necessidade justificada.

## 4. Requisitos funcionais

### 4.1. Identificação e conectividade

- Configurar a conexão com LG ThinQ pelos métodos oficiais disponíveis.
- Listar os dispositivos associados à conta, quando a API permitir.
- Selecionar e persistir a identificação do ar-condicionado desejado.
- Exibir status de autenticação e comunicação.
- Indicar operação pendente, falha, indisponibilidade e última sincronização bem-sucedida.
- Permitir atualizar manualmente o estado.

### 4.2. Controles do ar-condicionado

Implementar **somente após confirmação de suporte do equipamento e da API**:

1. Ligar e desligar.
2. Consultar e alterar a temperatura configurada.
3. Consultar e alterar o modo de operação disponível (por exemplo: refrigeração, ventilação, desumidificação ou automático, quando suportados).
4. Consultar e alterar a velocidade do ventilador.
5. Consultar e alterar a oscilação ou posição das aletas, se suportadas.
6. Exibir outras medições ou atributos apenas se efetivamente retornados pela integração.

Não presumir faixas de temperatura, nomes de modos ou comandos universais; obter capacidades do dispositivo ou documentar a origem da restrição. Diferenciar temperatura-alvo de temperatura ambiente, caso ambas existam.

### 4.3. Sincronização e confirmação

- Exibir valores confirmados pela integração.
- Não apresentar um comando enviado como concluído sem confirmação apropriada.
- Sinalizar alterações em andamento e erros de execução.
- Tratar atrasos, expiração de sessão, limitação de requisições e quedas de conectividade.
- Definir política conservadora e configurável de atualização periódica, conforme limites documentados da API.
- Não enviar comandos repetidamente em ciclos de atualização de estado.

### 4.4. Widget e experiência desktop

- Janela compacta e independente, não um widget integrado ao painel nativo de Widgets do Windows 11.
- Interface minimalista, legível, responsiva e compatível com escalonamento de DPI.
- Possibilidade de mover a janela pela área de trabalho.
- Alternância entre temas claro e escuro.
- Opção de manter a janela acima das demais, configurável.
- Mostrar temperatura-alvo, status ligado/desligado, modo e ventilação sempre que disponíveis.
- Desabilitar ou ocultar opções não suportadas.
- Minimizar/ocultar para bandeja do sistema e restaurar por ícone/menu.
- Evitar fechamento acidental quando a intenção for apenas ocultar o widget; oferecer ação explícita para encerrar.
- Opção de inicialização com Windows, desativada por padrão.
- Preservar preferências de janela e interface entre execuções.

### 4.5. Configurações

- Integração e conta/dispositivo selecionado.
- Preferência de tema e comportamento da janela.
- Inicialização automática.
- Frequência de sincronização dentro dos limites permitidos pela integração.
- Processo simples para desconectar, revogar ou renovar credenciais conforme o mecanismo suportado.

## 5. Estratégia obrigatória de comunicação pela rede

O dispositivo já está conectado ao Wi-Fi e é controlado pelo aplicativo LG ThinQ. A primeira opção técnica é integração **via internet/serviços em nuvem** por uma interface oficial da LG, caso essa interface disponibilize o modelo e as operações necessárias.

### 5.1. Pesquisa de viabilidade

Antes de implementar comandos reais:

1. Localizar e consultar documentação oficial atualizada da LG ThinQ Connect/API.
2. Verificar elegibilidade, região, requisitos de conta, credenciais, autorização, limites de uso e políticas de acesso.
3. Identificar bibliotecas/SDKs Python relevantes e comparar confiabilidade, manutenção, licença e cobertura funcional.
4. Validar se o equipamento específico aparece na lista de dispositivos e quais capacidades expõe.
5. Determinar se a leitura de estado e os comandos pretendidos são realmente suportados.
6. Documentar incompatibilidades, dependência da nuvem e indisponibilidade offline.

Não inventar endpoints, comandos, permissões ou compatibilidade. Se a alternativa oficial não for viável, documentar opções tecnicamente fundamentadas e solicitar aprovação antes de utilizar APIs não oficiais ou protocolos não documentados.

### 5.2. Prova de conceito (primeira entrega)

Criar um script CLI de diagnóstico, separado da interface gráfica, para:

- Iniciar autenticação pelo método permitido pela API.
- Listar os dispositivos visíveis à conta.
- Identificar o dispositivo-alvo.
- Consultar as capacidades e o estado atual.
- Registrar resultados sem expor dados sensíveis.
- Quando autorizado pelo usuário, testar um comando seguro e reversível e verificar a confirmação de estado.

A etapa somente estará **validada para o equipamento real** após execução e confirmação com o aparelho físico. Testes simulados demonstram a lógica do código, mas **não** comprovam compatibilidade real.

### 5.3. Segurança

- Não solicitar nem gravar senha LG em arquivos de texto.
- Preferir fluxos oficiais de autenticação/autorização; não contornar mecanismos do fabricante.
- Armazenar tokens/segredos no cofre do sistema operacional.
- Não versionar `.env` com segredos nem inserir tokens em logs, capturas ou documentação.
- Utilizar TLS, controlar timeout e tratar falhas de rede.
- Respeitar escopos de acesso e limites de requisições.

### 5.4. Redes locais

Não prometer operação pela LAN nem funcionamento sem internet. Avaliar integração local apenas como pesquisa futura e independente, caso o usuário solicite, com confirmação de suporte real e requisitos de segurança.

## 6. Arquitetura

Manter separação entre apresentação, domínio, serviços e integração externa.

```text
lg-ac-controller/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
├── docs/
│   ├── architecture.md
│   ├── integration-feasibility.md
│   └── development-plan.md
├── assets/
├── src/
│   └── lg_ac_controller/
│       ├── __init__.py
│       ├── main.py
│       ├── ui/
│       │   ├── widget.py
│       │   ├── tray.py
│       │   ├── components/
│       │   └── themes/
│       ├── domain/
│       │   └── models.py
│       ├── services/
│       │   ├── ac_service.py
│       │   └── sync_service.py
│       ├── integrations/
│       │   ├── base.py
│       │   └── thinq_provider.py
│       ├── config/
│       │   └── settings.py
│       └── utils/
│           └── logging.py
├── scripts/
│   └── diagnose_thinq.py
└── tests/
    ├── unit/
    └── integration/
```

A estrutura é uma proposta inicial e pode ser simplificada. Não gerar arquivos vazios apenas para reproduzir a árvore.

### Contratos e responsabilidades

- **`ACProvider`** (`integrations/base.py`): contrato abstrato de listagem, consulta de capacidades, leitura de estado e execução de comandos.
- **`ThinQProvider`**: implementação da integração ThinQ, responsável pelos detalhes de comunicação e autenticação suportada.
- **`ACService`**: valida capacidades, traduz ações da interface para operações do provedor e trata erros do domínio.
- **`SyncService`**: coordena leitura periódica, atualização manual e reconciliação entre estado solicitado e confirmado.
- **UI**: recebe dados prontos para exibição e envia intenções ao serviço, sem chamar diretamente endpoints externos.
- **Configuração**: persiste preferências não sensíveis separadamente de credenciais.

Permitir troca futura de provedor sem reescrever os controles visuais.

## 7. Padrões de desenvolvimento

- Adotar PEP 8 e type hints.
- Aplicar princípios SOLID quando melhorarem a manutenção, sem abstrações desnecessárias.
- Criar funções e componentes pequenos com responsabilidade clara.
- Evitar lógica de comunicação com a LG dentro de classes de interface.
- Não executar chamadas de rede na thread principal do Qt.
- Usar sinais/slots ou outro mecanismo seguro entre workers e UI.
- Centralizar tratamento de exceções e definir erros compreensíveis para o usuário.
- Registrar eventos técnicos com níveis adequados de log, sem dados sensíveis.
- Documentar decisões técnicas e dependências importantes.
- Não adicionar funcionalidades não solicitadas como requisito obrigatório.
- Evitar operações destrutivas sem autorização explícita.

## 8. Testes e qualidade

Criar testes para:

- Mapeamento de capacidades e estado do equipamento.
- Ligar/desligar e alterações de temperatura, modo e ventilação quando suportados.
- Tratamento de timeouts, falhas de autenticação e conexão.
- Comandos indisponíveis e valores fora das capacidades informadas.
- Sincronização após comando e consistência do estado apresentado.
- Persistência das preferências.
- Comportamento básico da interface e bandeja do sistema, quando automatizável.

Usar mocks/fakes para testes unitários. Manter testes que exigem conta ou hardware separados e executados apenas em ambiente autorizado.

Critérios mínimos:

- Os testes automatizados relevantes passam.
- O aplicativo não congela durante operações de rede.
- Erros recebem tratamento e feedback claros.
- Não há credenciais expostas no repositório ou nos logs.
- O widget não afirma que o ar-condicionado mudou de estado sem confirmação.

## 9. Entregas e ordem obrigatória de implementação

### Etapa 1 — Viabilidade e integração mínima

- Pesquisar documentação oficial e opções de SDK.
- Documentar métodos de autenticação, regiões, limites e operações disponíveis.
- Configurar projeto e script de diagnóstico.
- Autenticar, listar dispositivos e consultar capacidades/estado.
- Testar comando controlado somente com autorização.
- Registrar evidências do que foi realmente testado.

**Portão de decisão:** não declarar viabilidade comprovada nem iniciar os controles reais do widget sem confirmar uma integração funcional. Se o hardware não estiver acessível, é permitido avançar com um protótipo de interface com dados simulados, desde que claramente identificado como simulação.

### Etapa 2 — Base da aplicação

- Estabelecer organização de código, contratos de domínio e serviços.
- Criar configuração e armazenamento seguro de credenciais.
- Implementar tratamento de erros e logging.
- Preparar testes automatizados.

### Etapa 3 — Widget PySide6

- Construir janela compacta e controles básicos.
- Implementar tema claro/escuro.
- Adicionar bandeja do sistema e comportamento de mostrar/ocultar.
- Adicionar indicadores de conexão e sincronização.
- Validar comportamento com provedor simulado antes da integração final.

### Etapa 4 — Integração funcional

- Conectar serviço e interface ao provedor validado.
- Habilitar apenas controles suportados pelo modelo.
- Tratar autenticação, expiração, reconexão e erros.
- Confirmar sincronização do estado após comandos.
- Testar com equipamento físico.

### Etapa 5 — Empacotamento e distribuição

- Revisar testes e documentação.
- Configurar inicialização automática opcional.
- Criar executável com PyInstaller.
- Validar instalação/execução em Windows limpo, quando possível.
- Documentar dependências, permissões, configuração e limitações.

## 10. Documentação

Manter:

- **`README.md`**: visão geral, instalação, execução e uso.
- **`docs/integration-feasibility.md`**: fontes consultadas, API/SDK escolhido, testes feitos, compatibilidade confirmada e limitações.
- **`docs/architecture.md`**: módulos, contratos e fluxo de dados/comandos.
- **`docs/development-plan.md`**: etapas, itens concluídos, pendências e próximos passos.

Separar claramente fatos confirmados, hipóteses técnicas, dependências externas e funcionalidades planejadas.

## 11. Instruções de operação para agentes de IA

Ao receber uma tarefa:

1. Ler este `AGENTS.md` e os documentos pertinentes.
2. Inspecionar o código existente antes de propor alterações.
3. Identificar o objetivo, os módulos afetados e as dependências.
4. Apresentar uma abordagem proporcional à complexidade.
5. Implementar de forma incremental e consistente com a arquitetura.
6. Executar testes e verificações pertinentes.
7. Informar arquivos alterados, resultados validados e limitações remanescentes.

### Ao iniciar o projeto do zero

**Executar primeiro a Etapa 1.** Investigar e documentar a viabilidade da integração pela rede antes de construir uma solução que pressuponha comandos ou endpoints inexistentes. Criar a menor prova de conceito funcional possível.

### Restrições obrigatórias

- Não inventar endpoints, recursos, comandos ou compatibilidade LG.
- Não apresentar biblioteca de terceiros como oficialmente suportada sem verificação.
- Não armazenar segredos no repositório.
- Não alterar funcionalidades existentes sem avaliar impacto.
- Não excluir arquivos/dados nem alterar preferências do usuário sem necessidade e autorização.
- Não simular sucesso de comandos reais na UI.
- Não executar liga/desliga ou outras ações físicas sem autorização durante a fase de diagnóstico.

## 12. Critérios de conclusão

A versão funcional inicial poderá ser considerada concluída quando:

- Executar como aplicação desktop no Windows.
- Dispor de interface compacta, bandeja do sistema e temas claro/escuro.
- Autenticar com segurança por meio da integração escolhida.
- Descobrir ou selecionar o ar-condicionado real.
- Consultar e exibir o estado confirmado do dispositivo.
- Executar com sucesso os controles essenciais realmente suportados.
- Tratar desconexões, erros e estados pendentes sem travar a interface.
- Persistir preferências e proteger credenciais.
- Passar nos testes pertinentes e ter funcionamento validado com o equipamento real.
- Possuir executável e instruções de instalação/uso.

**Nota:** a viabilidade de recursos específicos depende do dispositivo, da região, da conta LG e da API acessível. Recursos não suportados devem ser documentados e não contam como falhas de implementação caso tenham sido explicitamente classificados como fora das capacidades disponíveis.
