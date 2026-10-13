# Arquitetura das Etapas 1 a 5

A prova de conceito CLI continua separada da aplicação desktop. Os contratos, serviços e a prévia PySide6 usam o mesmo provedor, com chamadas de rede fora da thread principal do Qt.

```text
scripts/diagnose_thinq.py
        |
        +-- ThinQApi (SDK thinqconnect)
        |       +-- GET devices
        |       +-- GET devices/{id}/profile
        |       +-- GET devices/{id}/state
        |
        +-- lg_ac_controller.diagnostic
                +-- normalização e seleção segura
                +-- redação de credenciais
                +-- extração não presumida de atributos

Camadas de aplicação:

ACService --> ACProvider <-- ThinQProvider --> ThinQApi
    |
    +-- domain.models

ControllerSettings --> WindowsCredentialStore --> Windows Credential Manager
SettingsStore --> settings.json
main.py --> ClientIdentity
SyncService --> ACService
ControllerSession --> WindowsCredentialStore
ControllerSession --> ThinQProvider
ApplicationController --> ControllerSession
ApplicationController --> SyncService
StartupManager --> WindowsRunKey
main.py --> AsyncExecutor
AsyncExecutor --> AirConditionerWidget
SystemTrayController --> AirConditionerWidget
```

## Responsabilidades

- `scripts/diagnose_thinq.py`: fronteira CLI, entrada do PAT, ciclo assíncrono e relatório JSON. Não contém senha nem persiste segredo.
- `lg_ac_controller.diagnostic`: funções puras para seleção, normalização, redação e testes sem rede.
- `thinqconnect.ThinQApi`: transporte e contrato do SDK escolhido. A prova de conceito não duplica endpoints nem cabeçalhos da LG.
- `domain.models`: tipos de dispositivo, capacidades, estado e submissão de controle. `ControlSubmission.confirmed` começa como `False` para impedir que uma resposta de envio seja tratada como confirmação.
- `integrations.base.ACProvider`: contrato substituível para uma futura integração simulada ou outro provedor.
- `integrations.thinq_provider.ThinQProvider`: adapta o SDK ThinQ, inclusive o formato de resposta aninhado `deviceInfo` observado no dispositivo real. A fábrica assíncrona `create()` cria o cliente autenticado com PAT, país e `client_id`, e o contexto assíncrono encerra a sessão HTTP.
- `integrations.errors`: classifica timeout, transporte, autenticação observada e falhas desconhecidas sem propagar mensagens brutas do SDK para a UI.
- `services.ac_service.ACService`: coordena leitura, bloqueia controle físico sem `authorized=True` explícito e valida cada recurso/valor contra o perfil gravável do modelo.
- `services.controller_session.ControllerSession`: compõe credencial, provedor e `ACService`, além de controlar o fechamento da sessão HTTP.
- `services.application_controller.ApplicationController`: fachada para descoberta, seleção persistida, atualização e confirmação de comandos; a UI depende somente desta camada.
- `ui.async_executor.AsyncExecutor`: mantém um loop asyncio dedicado para impedir bloqueio da thread Qt e preservar o ciclo de vida do cliente HTTP.
- `ui.widget.AirConditionerWidget`: conecta os sinais do executor uma única vez, evitando avisos Qt e handlers duplicados durante operações sucessivas.
- `ui.widget.AirConditionerWidget`: apresenta apenas snapshots confirmados, temas e preferência de janela; não importa `ThinQApi`. A janela usa composição sem moldura e fundo translúcido, com cartões arredondados e barra arrastável. A tela principal mantém somente controles do ar; preferências do sistema ficam em diálogo separado.
- `ui.widget.AirConditionerWidget`: traduz enums técnicos do provedor apenas na apresentação; os valores originais permanecem nos `userData` dos campos e nos payloads enviados à API.
- `ui.components`: reúne `TemperatureControl`, `SegmentedSelector`, `ModernSwitch`, `PowerButton`, `ConnectionIndicator`, `DragBar` e `AirConditionerGlyph`, sem chamadas de rede ou conhecimento do SDK.
- `ui.components.AirConditionerGlyph`: ilustração vetorial nativa do Qt; altera cor, fluxo de ar, oscilação e aparência de desligado conforme os atributos confirmados. Usa timer leve somente enquanto o equipamento está ligado e visível.
- `ui.windows_effects`: tenta aplicar o backdrop Acrylic-like do DWM no Windows 10/11 e mantém o painel translúcido Qt como fallback; também consulta a preferência de animações da área de trabalho.
- `ui.tray.SystemTrayController`: controla mostrar/ocultar pela bandeja; o item `Encerrar` e o botão X encerram o processo explicitamente.
- `main.py`: inicializa Qt, o executor e a sessão real usando o Credential Manager.
- `config.settings.ControllerSettings`: mantém país, dispositivo, intervalo de sincronização e retry de leitura sem segredos; rejeita polling agressivo e limites de retry excessivos.
- `config.preferences.SettingsStore`: persiste somente campos permitidos em JSON local, usando gravação atômica; nunca serializa o PAT.
- `config.identity`: reutiliza ou cria o `client_id` UUID não secreto em `%LOCALAPPDATA%\LGAcController\client_id`.
- `config.startup.StartupManager`: altera somente a chave `HKCU` de inicialização do usuário, usa o comando correto para Python ou PyInstaller e apenas após a opção ser ativada.
- `config.instance.SingleInstanceGuard`: mantém um lock por usuário para impedir múltiplos processos do widget e arquivos executáveis bloqueados por instâncias duplicadas.
- `config.credentials.WindowsCredentialStore`: usa `keyring` para delegar o PAT ao cofre do Windows. O `.env` continua aceito para diagnóstico, mas não é migrado automaticamente.
- `services.sync_service.SyncService`: registra estado, última sincronização, comando pendente e erro; envia no máximo uma vez por operação, confirma por nova leitura e encerra a pendência quando a confirmação expira.
- `ui.widget.AirConditionerWidget`: agenda leituras periódicas no intervalo configurado, com limite mínimo de 60 segundos; o timer nunca envia comandos. A interface permite alterar e persistir esse intervalo.
- `ui.widget.AirConditionerWidget`: deriva os controles de aletas e painel do perfil confirmado: exibe `windDirection.rotateUpDown` e `display.light` somente quando graváveis, preserva o valor confirmado em falhas e mantém estados desconhecidos desabilitados.

## Decisões

- As chamadas de rede são assíncronas e usam timeout por chamada.
- Leituras podem repetir até três vezes com backoff configurável; comandos físicos nunca são repetidos automaticamente.
- Erros de integração são normalizados na fronteira; somente causas conhecidas são classificadas, e falhas desconhecidas permanecem genéricas.
- A seleção só aceita `DEVICE_AIR_CONDITIONER` e falha de modo explícito em caso ambíguo.
- Perfil e estado são preservados como payloads retornados, pois a capacidade precisa vir do modelo e não de uma lista inventada pelo aplicativo.
- A UI depende de contratos de domínio próprios e não importa `ThinQApi` diretamente.
- O cofre, a sessão de aplicação, a validação de capacidades e a confirmação pós-comando estão conectados à UI por meio da fachada de aplicação.
- A UI só exibe controles declarados como graváveis pelo perfil retornado para o dispositivo; isso não substitui a validação física individual de cada comando.
