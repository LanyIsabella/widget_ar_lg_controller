# LG AC Controller

Projeto em Python para um widget desktop Windows de um ar-condicionado LG ThinQ.

## Estado atual

O projeto concluiu a validação de leitura da Etapa 1 e possui uma prévia funcional da interface PySide6 da Etapa 3.

Nesta entrega, a CLI somente:

- autentica por Personal Access Token (PAT) do portal LG Smart Solution API;
- lista os dispositivos associados à conta;
- seleciona um dispositivo do tipo ar-condicionado;
- consulta o perfil de capacidades e o estado atual;
- imprime um relatório JSON sem imprimir o PAT.

A CLI permanece somente leitura por padrão. O desligamento exige as opções explícitas `--power-off --confirm-physical-action` e confirma o estado com uma nova leitura; outros comandos ainda não estão habilitados.

A base da aplicação também inclui configuração não sensível, cofre Windows via `keyring` e serviço de sincronização testado com provedor falso. A prévia visual usa janela sem moldura e translúcida, cartões arredondados, controle de temperatura com `−`/`+`, chips segmentados, switch vetorial, botão de energia com ícone e indicador de conexão. O ícone do aparelho acompanha desligado, ligado, refrigeração, aquecimento, desumidificação, ventilação e oscilação conforme o estado confirmado. A tela principal exibe somente os controles do ar; tema e preferências do sistema ficam no botão de configurações. Os nomes técnicos dos modos e velocidades são traduzidos para português, sem alterar os valores enviados à API. O PAT do `.env` não é migrado automaticamente. O botão X encerra o processo; para apenas ocultar a janela, use o menu da bandeja.
O aplicativo permite apenas uma instância por usuário; novas tentativas de abertura são encerradas sem criar outro processo.

Para armazenar um PAT digitado de forma oculta no Windows Credential Manager e permitir que o diagnóstico o use como fallback:

```powershell
python scripts\store_pat.py
```

## Pré-requisitos

- Windows com Python 3.12 ou superior;
- conta LG ThinQ com o ar-condicionado já associado ao aplicativo;
- Personal Access Token criado no portal oficial da LG Smart Solution API.

## Instalação

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Para instalar e executar a prévia do widget PySide6:

```powershell
python -m pip install -e ".[dev,desktop]"
python -m lg_ac_controller.main
```

Para gerar o executável Windows:

```powershell
.\scripts\build_windows.ps1
```

O executável será criado em `dist\LGAcController.exe`. A validação em uma instalação Windows limpa ainda é necessária.

### Checklist manual do widget

- Confirme que o ar-condicionado aparece na lista e que o estado inicial é exibido.
- Use **Atualizar** e confirme a alteração do horário de sincronização.
- Ajuste o intervalo de sincronização entre 60 e 3600 segundos; a preferência deve persistir ao reabrir.
- Use **Ocultar** na bandeja para esconder a janela e **Mostrar** para restaurá-la.
- Use o botão **X** ou **Encerrar** para terminar o processo; uma nova abertura não deve criar instâncias duplicadas.
- Execute controles físicos somente quando houver autorização e confirme o estado exibido após cada comando.

Os testes automatizados de UI também cobrem escalas Qt de 100%, 125% e 200%.

Quando o perfil do modelo declara suporte, a interface também exibe oscilação vertical das aletas e a luz do painel. No equipamento validado, a API não declarou oscilação horizontal nem posições fixas; esses controles não são simulados.

## Diagnóstico

O script carrega automaticamente um `.env` local ignorado pelo Git. Aceita `LG_THINQ_PAT` ou `PAT_LG`; se nenhum estiver definido, pede o PAT de forma oculta. O token não é salvo nem impresso pelo script. O `client_id` não secreto é mantido em `%LOCALAPPDATA%\LGAcController\client_id` para evitar registrar um cliente novo a cada execução.

```powershell
python scripts\diagnose_thinq.py --country BR
```

Para selecionar um aparelho específico:

```powershell
python scripts\diagnose_thinq.py --country BR --device-alias "Sala"
python scripts\diagnose_thinq.py --country BR --device-id "ID_DO_DISPOSITIVO"
python scripts\diagnose_thinq.py --country BR --device-index 1
```

Teste controlado de desligamento, somente quando autorizado:

```powershell
python scripts\diagnose_thinq.py --country BR --device-index 1 --power-off --confirm-physical-action
```

O código do país deve corresponder à região da conta LG. O Brasil usa `BR`.

## Testes

```powershell
python -m pytest
```

## Documentação

- [Viabilidade da integração](docs/integration-feasibility.md)
- [Arquitetura](docs/architecture.md)
- [Plano de desenvolvimento](docs/development-plan.md)

## Limitações importantes

A integração depende da internet e dos serviços LG; isso não representa comunicação LAN direta nem operação offline. A execução real confirmou descoberta, leitura de estado, desligamento e os controles de temperatura, modo, ventilação e oscilação deste equipamento, sempre com confirmação posterior e restauração dos valores originais.
