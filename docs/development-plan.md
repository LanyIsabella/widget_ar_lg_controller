# Plano de desenvolvimento

## Etapa 1 — Viabilidade e integração mínima

### Concluído nesta entrega

- leitura integral dos requisitos do projeto;
- pesquisa da API oficial e do portal LG Smart Solution API;
- avaliação inicial de SDKs Python;
- configuração de `pyproject.toml` com Python >=3.12 e `thinqconnect==1.0.14`;
- CLI somente leitura para PAT, descoberta, seleção, perfil e estado;
- testes unitários de seleção e proteção de relatório;
- documentação de arquitetura, limites e procedimento de validação.

### Portão de decisão

Concluído para este equipamento quanto à descoberta, leitura de estado, desligamento controlado e validação física dos controles declarados pelo perfil. O PAT real não é registrado na documentação.

### Evidência obtida

- O diagnóstico real foi executado em 13/10/2026 com o PAT local, sem expô-lo.
- Após a correção de acesso, a API listou 1 dispositivo `DEVICE_AIR_CONDITIONER`.
- O perfil e o estado do modelo `RAC_056905_WW` foram consultados com sucesso.
- Foram observados modo `POWER_ON`, modo `COOL`, 27 °C ambiente, 23 °C alvo e ventilação `AUTO`.
- O comando autorizado `POWER_OFF` foi confirmado na primeira leitura posterior.
- A comunicação em nuvem está tecnicamente viável para descoberta, leitura de estado, desligamento e os controles adicionais avaliados individualmente.
- O perfil real declarou temperatura-alvo, modos, ventilação e oscilação graváveis; a UI só os oferece com base nessa declaração.
- Em 13/10/2026, temperatura-alvo, modo, ventilação e oscilação foram alterados individualmente, confirmados por nova leitura e restaurados aos valores originais. O aparelho começou e terminou ligado, em `COOL`, alvo 23 °C, ventilação `AUTO` e oscilação desligada.

## Etapa 2 — Base da aplicação

Concluída no ambiente de desenvolvimento; a validação física permanece restrita aos comandos autorizados e registrados na documentação de viabilidade.

### Concluído

- modelos de domínio para dispositivo, capacidades, estado e submissão de controle;
- contrato abstrato `ACProvider`;
- adaptador `ThinQProvider` para o SDK ThinQ;
- fábrica assíncrona do `ThinQProvider` com ciclo de vida da sessão HTTP;
- `ACService` com bloqueio de comandos sem autorização explícita;
- testes com provedor falso;
- `ControllerSettings` para configuração não sensível;
- `WindowsCredentialStore` baseado em `keyring`;
- `SyncService` com estado pendente, última sincronização, erro e confirmação pós-comando;
- validação de comandos contra propriedades e valores graváveis do perfil;
- utilitário `scripts/store_pat.py` para inserir o PAT no Windows Credential Manager;
- `ControllerSession` para compor o cofre, o provedor e o serviço da aplicação;
- `SettingsStore` para persistir preferências não sensíveis com gravação atômica;
- reutilização da identidade não secreta do cliente ThinQ pelo ponto de entrada desktop;
- `ApplicationController` para descoberta, seleção e coordenação com `SyncService`;
- normalização de timeout, transporte e erros de autenticação observados;
- retry limitado para leituras, com backoff configurável e sem retry de comandos físicos;
- teste de integração real opt-in, desabilitado por padrão.

### Pendente

- revisar visualmente os controles em uso cotidiano, incluindo estados de erro e bandeja do sistema.

## Etapa 3 — Widget PySide6

Implementada; a descoberta e os fluxos principais já foram exercitados em Windows interativo.

### Concluído

- janela compacta PySide6 com tema claro/escuro;
- atualização assíncrona fora da thread Qt;
- descoberta e seleção de dispositivos pela fachada de aplicação;
- exibição de estado confirmado e controles somente quando o perfil declara suporte;
- sincronização periódica conservadora usando o intervalo configurado, sem envio automático de comandos;
- ajuste e persistência do intervalo de sincronização pela interface, entre 60 e 3600 segundos;
- preferência de janela sempre no topo;
- bandeja do sistema com mostrar, ocultar e encerramento explícito; o botão X também encerra o processo, enquanto ocultar fica disponível pelo menu da bandeja;
- bloqueio de instância única para evitar processos duplicados;
- inicialização automática opcional via registro do usuário, desativada por padrão;
- comando de inicialização compatível tanto com execução Python quanto com o executável PyInstaller;
- testes Qt em modo offscreen;
- testes Qt offscreen aprovados com escalas de DPI 100%, 125%, 150% e 200%;
- validação manual do executável no Windows: autenticação pelo Credential Manager e apresentação do dispositivo real na lista.
- smoke test do executável em pasta temporária, sem venv/projeto: inicialização, janela e encerramento normal confirmados no Windows atual;
- encerramento assíncrono protegido contra corrida entre o loop HTTP e o fechamento da janela;
- redesign visual de alto nível com janela sem moldura, fundo translúcido, cartões arredondados, botões de ação modernos e barra de título arrastável;
- ícone vetorial dinâmico do ar-condicionado, com estados de desligado, ligado, refrigeração, desumidificação, ventilação e oscilação derivados do snapshot confirmado;
- tela principal simplificada, sem preferências do sistema; tema, inicialização, janela no topo e intervalo de sincronização foram movidos para um diálogo próprio;
- enums técnicos traduzidos para português na apresentação, preservando os valores originais nos comandos da API;
- ligar/desligar sem confirmação modal, mantendo confirmação posterior pela leitura real do estado;
- componentes visuais reutilizáveis para temperatura, modo, ventilação, oscilação, energia, conexão e movimentação da janela;
- animação vetorial de fluxo de ar com QTimer leve, pausada quando oculto e reduzida quando a preferência de animação do Windows estiver desativada;
- tentativa encapsulada de backdrop Acrylic-like via DWM, com fallback transparente nativo do Qt;
- testes unitários dos novos componentes visuais.
- seção compacta `Direção do ar` com oscilação vertical baseada em `windDirection.rotateUpDown`;
- controle `Luz do painel` baseado em `display.light`, com estado desconhecido desabilitado e restauração do último valor confirmado em falhas;
- investigação do perfil real: não há suporte declarado para oscilação horizontal ou posições fixas das aletas, portanto esses controles não são apresentados.

### Pendente

- revisão visual mais ampla em Windows interativo, incluindo diferentes escalas de DPI e mensagens de falha.
- teste físico autorizado da alternância `display.light` no equipamento real; a capacidade já foi confirmada no perfil e os testes automatizados confirmam a lógica de envio/estado.

## Etapas 4 e 5

Integração final e confirmação pós-comando estão cobertas pela camada de aplicação e pela prévia da UI. O empacotamento PyInstaller foi preparado e executado com sucesso no ambiente atual; permanece a validação do executável em uma instalação Windows limpa.

### Evidência de build

- `scripts/build_windows.ps1` instala o extra `build` no `.venv` e executa o spec versionado.
- `packaging/lg_ac_controller.spec` gerou `dist/LGAcController.exe` em 13/10/2026.
- O executável não foi considerado validado em Windows limpo apenas pela geração local.
- A build local atual possui aproximadamente 56,6 MB; o artefato permanece ignorado pelo Git.

## Critério de avanço

A integração foi considerada viável para este equipamento para descoberta, consulta de perfil/estado, `POWER_OFF` e os quatro controles adicionais testados. Qualquer novo controle deverá passar pelo mesmo processo de validação do perfil, envio único e confirmação por nova leitura.
