# LG AC Controller

Widget desktop para Windows que permite monitorar e controlar ar-condicionados LG compatíveis com a conta LG ThinQ. A comunicação utiliza a API em nuvem LG ThinQ Connect; não é uma integração LAN e não funciona sem internet.

## Recursos

- Descoberta dos ar-condicionados associados à conta LG ThinQ.
- Exibição do estado confirmado, temperatura ambiente e temperatura-alvo.
- Controle de energia, temperatura, modo e ventilação quando o perfil do aparelho os disponibilizar.
- Oscilação vertical das aletas e luz do painel quando declaradas como suportadas pela API.
- Interface compacta com tema claro/escuro, fundo translúcido e ícone visual dinâmico.
- Bandeja do sistema, janela sempre no topo e inicialização opcional com o Windows.
- Preferências persistidas e PAT armazenado no Windows Credential Manager.

Os controles são habilitados dinamicamente pelo perfil do modelo. O aplicativo não apresenta opções que a API não declarou como disponíveis.

## Compatibilidade

- Windows 10 ou Windows 11.
- Python 3.12 ou superior para executar a partir do código-fonte.
- Conta LG ThinQ com o ar-condicionado já configurado no aplicativo oficial.
- PAT (Personal Access Token) criado no portal [LG Smart Solution API](https://smartsolution.developer.lge.com/en/cloud/landing).
- A conta, o país informado e as permissões do PAT precisam estar habilitados para a API.

O equipamento validado neste projeto é um LG Split Hi Wall Dual Inverter Voice identificado pela API como `RAC_056905_WW`. Outros modelos podem oferecer menos recursos.

## Opção recomendada: executável Windows

Se houver um executável publicado nas Releases do projeto:

1. Baixe o arquivo `LGAcController.exe` em uma pasta local.
2. Abra o PowerShell nessa pasta.
3. Armazene o PAT no cofre do Windows seguindo a seção [Credencial](#credencial).
4. Execute `LGAcController.exe`.

O executável não solicita nem grava a senha da conta LG. Na primeira execução, ele consulta os dispositivos associados ao PAT e apresenta o ar-condicionado na lista.

> Este repositório também permite gerar o executável localmente. O arquivo em `dist/` é um artefato de build e pode não estar incluído em todos os pacotes publicados.

## Executar a partir do código-fonte

Abra o PowerShell na pasta do projeto e execute:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop]"
python -m lg_ac_controller.main
```

Se o PowerShell bloquear a ativação do ambiente virtual, é possível executar diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[desktop]"
.\.venv\Scripts\python.exe -m lg_ac_controller.main
```

## Credencial

O aplicativo desktop lê o PAT do Windows Credential Manager. Para armazená-lo sem exibir o valor na tela:

```powershell
.\.venv\Scripts\python.exe scripts\store_pat.py
```

O script solicita o PAT de forma oculta e confirma apenas que o armazenamento foi concluído. Nunca coloque o token no README, em issues, capturas de tela ou logs.

Para remover a credencial, abra o **Gerenciador de Credenciais** do Windows e remova a entrada correspondente ao LG AC Controller.

### Uso do `.env`

O arquivo `.env` é aceito pelo diagnóstico e é útil apenas para desenvolvimento local. Copie `.env.example` para `.env`, preencha o PAT e mantenha o arquivo fora do Git:

```powershell
Copy-Item .env.example .env
notepad .env
```

Não é necessário criar `.env` para usar o executável ou a aplicação desktop; prefira o Windows Credential Manager.

## Primeiro uso

1. Confirme que o ar-condicionado está online no aplicativo LG ThinQ.
2. Inicie o widget.
3. Selecione o ar-condicionado na lista de dispositivos.
4. Aguarde o indicador ficar **Online** e confira o estado exibido.
5. Use **Atualizar** para uma consulta manual.
6. Para somente ocultar a janela, escolha **Ocultar** no menu da bandeja. Use **Encerrar** ou o botão X para finalizar o processo.

Após um comando, a interface aguarda uma nova leitura antes de apresentar a alteração como confirmada.

## Gerar o executável

Para criar uma build Windows local:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[desktop,build]"
.\scripts\build_windows.ps1
```

O resultado será criado em:

```text
dist\LGAcController.exe
```

Copie esse arquivo para outro computador Windows e repita o procedimento de armazenamento do PAT nesse computador. O token não é incorporado ao executável.

## Diagnóstico da integração

O diagnóstico é somente leitura por padrão, lista os dispositivos, consulta o perfil e mostra o estado sem imprimir o PAT:

```powershell
.\.venv\Scripts\python.exe scripts\diagnose_thinq.py --country BR
```

Para selecionar um dispositivo específico:

```powershell
python scripts\diagnose_thinq.py --country BR --device-index 1
python scripts\diagnose_thinq.py --country BR --device-alias "Ar-condicionado"
```

O teste de desligamento exige autorização explícita e envia uma única ação física:

```powershell
python scripts\diagnose_thinq.py --country BR --device-index 1 --power-off --confirm-physical-action
```

Não execute esse comando se não quiser desligar o aparelho.

## Preferências e bandeja

O botão de configurações permite alterar tema, intervalo de sincronização, inicialização com o Windows e comportamento sempre no topo. O intervalo mínimo de atualização é de 60 segundos para evitar consultas excessivas à API.

Na bandeja do sistema:

- **Mostrar** restaura a janela.
- **Ocultar** deixa o aplicativo em segundo plano.
- **Encerrar** para o processo e fecha a sessão de comunicação.

## Solução de problemas

### Nenhum dispositivo aparece

- Verifique se o ar-condicionado está associado à mesma conta LG usada para criar o PAT.
- Confirme o país com `--country` no diagnóstico; para uma conta brasileira, use `BR`.
- Verifique se o PAT está ativo e autorizado para a API ThinQ Connect.
- Execute o diagnóstico em modo somente leitura e confira a mensagem apresentada.

### O estado não atualiza

- Confirme a conexão do computador com a internet.
- Verifique se o aparelho está online no aplicativo LG ThinQ.
- Use **Atualizar** e aguarde a confirmação.
- Evite reduzir o intervalo de sincronização abaixo do limite permitido.

### O controle não aparece

Os controles dependem do perfil retornado para o modelo e a região. Um recurso disponível no controle remoto físico pode não estar exposto pela API. Nesse caso, a opção é ocultada intencionalmente.

## Desenvolvimento e testes

Para instalar as dependências de desenvolvimento:

```powershell
python -m pip install -e ".[dev,desktop,build]"
python -m pytest
```

O teste de integração real é opt-in e não é executado por padrão.

Documentação técnica:

- [Viabilidade da integração](docs/integration-feasibility.md)
- [Arquitetura](docs/architecture.md)
- [Plano de desenvolvimento](docs/development-plan.md)
- [AGENTS.md](AGENTS.md)
- [FEATS.md](FEATS.md)

## Segurança e limitações

- A integração depende da internet e dos serviços LG.
- O aplicativo não controla o aparelho diretamente pela rede local.
- O PAT não deve ser versionado nem compartilhado.
- Uma resposta de envio não é tratada como sucesso definitivo sem nova leitura do estado.
- A execução real confirmou descoberta, leitura, desligamento, temperatura, modo, ventilação e oscilação vertical no equipamento validado.
- A capacidade de luz do painel foi confirmada no perfil da API; o teste físico desse recurso deve ser realizado pelo usuário somente quando autorizado.
- A validação em uma instalação Windows limpa ainda depende do ambiente de distribuição utilizado.
