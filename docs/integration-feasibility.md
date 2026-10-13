# Viabilidade da integração LG ThinQ Connect

Data da pesquisa: 13/10/2026.

## Conclusão

Há uma rota tecnicamente plausível e alinhada ao escopo: usar a API em nuvem LG ThinQ Connect com um Personal Access Token (PAT), informando o país da conta e um `client_id` do cliente. O SDK Python `thinqconnect` expõe chamadas para listar dispositivos, consultar perfil, consultar estado e enviar controle.

O diagnóstico foi validado contra a conta real: com `PAT_LG` carregado do `.env` local e país `BR`, a API listou um `DEVICE_AIR_CONDITIONER`, retornou o perfil e retornou o estado atual. O comando `POWER_OFF` foi enviado uma única vez após validação do perfil e confirmado por nova leitura. Isso comprova a viabilidade da comunicação em nuvem para descoberta, leitura de estado e desligamento controlado deste dispositivo.

Em 13/10/2026, o executável Windows também foi testado manualmente com o PAT armazenado no Windows Credential Manager e apresentou o ar-condicionado real na interface. Essa evidência confirma o fluxo de autenticação e descoberta da UI.

Na mesma data, foram testados fisicamente, individualmente e com confirmação por nova leitura, os comandos de temperatura-alvo, modo de operação, ventilação e oscilação vertical. Cada valor foi restaurado ao estado original ao final. O aparelho começou e terminou ligado, em modo `COOL`, alvo 23 °C, ventilação `AUTO` e oscilação desligada.

## Fontes consultadas

1. [LG Smart Solution API Developer](https://smartsolution.developer.lge.com/en/cloud/landing): portal oficial para a API ThinQ.
2. [LG ThinQ API - Device Profile](https://smartsolution.developer.lge.com/en/apiManage/device_profile): referência oficial de perfis e propriedades de dispositivos.
3. [Comunicado da LG sobre a abertura da API ThinQ](https://www.lg.com/es/acerca-de-lg/comunicados-de-prensa/lg-abre-la-api-de-lg-thinq-para-fomentar-la-innovacion-y-conecti/): confirma a abertura da API para monitoramento e controle de dispositivos registrados no app LG ThinQ.
4. [Repositório `thinq-connect/pythinqconnect`](https://github.com/thinq-connect/pythinqconnect): código-fonte do SDK, com copyright LG Electronics, licença Apache-2.0 e métodos da API.
5. [Pacote `thinqconnect` no PyPI](https://pypi.org/project/thinqconnect/): metadados, versão publicada e dependências.

## Autenticação e região

- O fluxo suportado pelo SDK é PAT criado no portal de desenvolvedor. A CLI não solicita senha LG e não tenta reproduzir o login do aplicativo.
- O PAT é obtido pela variável `LG_THINQ_PAT`, por `PAT_LG` em um `.env` local ignorado pelo Git, pelo Windows Credential Manager ou por prompt oculto. Ele nunca é gravado pela CLI; o utilitário separado `scripts/store_pat.py` grava-o somente no cofre do sistema.
- O `client_id` é um UUID persistente e não secreto, salvo em `%LOCALAPPDATA%\LGAcController\client_id` pela CLI e reutilizado pela aplicação desktop. O SDK recomenda um identificador único por cliente e alerta contra criação excessiva de clientes.
- O código de país deve corresponder à conta. A implementação oficial do SDK inclui `BR` e o associa ao domínio regional da América Latina (`AIC`). A CLI usa `BR` por padrão, mas permite alterar com `--country`.
- A chamada de listagem de dispositivos é usada como confirmação operacional da autenticação. Não há uma etapa separada de login no SDK.

## Cobertura relevante para ar-condicionado

O perfil publicado pelo SDK para `DEVICE_AIR_CONDITIONER` mapeia, entre outras, propriedades de:

- modo de operação e modo de trabalho;
- temperatura atual e temperatura-alvo, em Celsius/Fahrenheit quando presentes;
- limites de temperatura;
- velocidade e passo do fluxo de ar;
- oscilação/direção das aletas quando o perfil do modelo expõe essas propriedades;
- iluminação do display quando o perfil do modelo expõe `display.light`;
- temporizadores, economia de energia, qualidade do ar, filtro e luz do display quando disponíveis.

Essa lista é cobertura de tipos/propriedades da API, não garantia para o modelo do usuário. A CLI preserva o perfil retornado pela API e extrai alguns atributos conhecidos apenas como conveniência, sem inventar capacidades ausentes.

## Avaliação dos SDKs Python

| Opção | Situação observada | Decisão |
|---|---|---|
| `thinqconnect` 1.0.14 | SDK publicado no PyPI sob Apache-2.0; repositório `thinq-connect/pythinqconnect`; Python >=3.10; depende de `aiohttp`, `awsiotsdk` e `cryptography`; implementa PAT, lista, perfil, estado e controle. | Escolhido para a prova de conceito. Fixado em `pyproject.toml` para tornar a primeira execução reproduzível. |
| `wideq` | Cliente reverso para uma versão antiga da API SmartThinQ; a própria documentação alerta que novos usuários podem não funcionar com a API v1. | Não usar como integração principal. |
| `pythinq2` e ferramentas semelhantes | Projetos de terceiros com manutenção/cobertura menor e sem evidência de serem a API oficial atual. | Não usar nesta etapa. |
| Clientes locais/reversos | Dependem de protocolos não documentados, captura ou substituição de serviços da nuvem; não comprovam operação LAN para este modelo. | Fora do escopo atual e não autorizados sem nova decisão. |

O nome e a organização do SDK não substituem a validação do hardware. A escolha é baseada na aderência ao portal/API oficiais, licença e cobertura técnica observável; ainda depende da execução contra a conta real.

## Prova de conceito implementada

Arquivo: [`scripts/diagnose_thinq.py`](../scripts/diagnose_thinq.py)

Fluxo:

1. Lê o país e o PAT sem persistência.
2. Cria um `client_id` UUID.
3. Executa a listagem de dispositivos.
4. Filtra exclusivamente `DEVICE_AIR_CONDITIONER`.
5. Exige seletor quando há mais de um aparelho, evitando uma escolha arbitrária.
6. Consulta perfil e estado do dispositivo selecionado.
7. Emite JSON com dispositivos, perfil, estado e atributos observados.
8. Opcionalmente, com autorização explícita, testa um desligamento único e aguarda a confirmação do estado.
9. Redige campos com aparência de token/credencial e não imprime exceções contendo cabeçalhos HTTP.

O modo é explicitamente `read_only`: não existe comando de controle na CLI desta etapa.

## Como validar com o aparelho real

Depois de criar o PAT no portal oficial, a consulta somente leitura pode ser executada com:

```powershell
python scripts\diagnose_thinq.py --country BR --device-index 1 --hide-device-id > diagnostico.json
```

O arquivo `diagnostico.json` pode ser inspecionado localmente. Antes de compartilhar qualquer resultado, revisar alias, modelo, IDs e medições. Não compartilhar o PAT.

Para migrar o PAT digitado ao cofre do Windows, sem exibi-lo:

```powershell
python scripts\store_pat.py
```

O diagnóstico real já confirmou para este equipamento que a lista é obtida, o dispositivo correto aparece como `DEVICE_AIR_CONDITIONER`, perfil e estado são retornados e `POWER_OFF` é confirmado após o comando. O perfil também declara como graváveis: temperatura-alvo de 18 a 30 °C em passos de 0,5; modos `AIR_DRY`, `COOL` e `FAN`; ventilação `LOW`, `MID`, `HIGH` e `AUTO`; oscilação vertical booleana (`windDirection.rotateUpDown`); e luz do painel (`display.light`, `ON`/`OFF`). Não foram declaradas propriedades de oscilação horizontal nem posições fixas das aletas. Os controles de temperatura, modo, ventilação e oscilação já foram testados pela aplicação desktop e confirmados por novas leituras; a luz do painel foi confirmada como capacidade do perfil e permanece sujeita a teste físico autorizado.

## Limites e riscos conhecidos

- A integração depende da internet e dos serviços LG; não é comunicação direta LAN.
- PAT, região/país, permissões da conta e disponibilidade do serviço podem impedir a listagem.
- O modelo pode aparecer, mas não oferecer todas as propriedades desejadas.
- O estado pode ser atrasado; uma resposta HTTP bem-sucedida não é tratada como confirmação de mudança sem nova leitura apropriada.
- A API pode impor limites de requisições e retornar erros de dispositivo offline, recurso não suportado, expiração/invalidade do token ou controle não autorizado.
- A execução da Etapa 1 não valida sincronização periódica, UI ou empacotamento; essas camadas possuem implementação separada, testes locais e validação interativa parcial, mas ainda dependem de uma instalação Windows limpa para a validação final de distribuição.

## Resultado da execução real de 13/10/2026

- O `.env` foi lido sem imprimir o PAT.
- A primeira tentativa retornou `1309 / NOT_ALLOWED_API_AGAIN`; depois da correção do acesso, a consulta foi aceita.
- Foram encontrados 1 dispositivo e 1 ar-condicionado.
- Modelo retornado: `RAC_056905_WW`.
- Alias retornado: `Ar-condicionado`.
- Perfil e estado foram retornados com sucesso.
- Estado observado: modo de operação `POWER_ON`, modo de trabalho `COOL`, temperatura ambiente `27 °C`, temperatura-alvo `23 °C`, ventilação `AUTO`.
- O comando `POWER_OFF` foi enviado uma única vez após validação do perfil e confirmado na primeira leitura posterior.
- Após o desligamento, o estado retornou `airConOperationMode=POWER_OFF`; a temperatura-alvo permaneceu em 23 °C.
- O perfil consultado declarou temperatura-alvo, modo, ventilação e oscilação como graváveis, com limites e enumerações preservados no relatório.
- O perfil consultado também declarou `display.light` como leitura e escrita, com valores `ON` e `OFF`; não declarou controle horizontal nem posições fixas das aletas.
- Temperatura-alvo, modo, ventilação e oscilação foram enviados individualmente, confirmados por leitura posterior e restaurados.

Os valores acima são evidência da API. O desligamento e os quatro comandos adicionais foram autorizados, confirmados via nova leitura e restaurados; não há validação física de outros recursos não testados.
