# Implementação de funcionalidades — LG AC Controller

## 1. Objetivo

Implementar duas novas funcionalidades no projeto LG AC Controller, desenvolvido em Python com PySide6 e integração com o ar-condicionado LG Split Hi Wall Dual Inverter Voice pela rede.

As funcionalidades são:

1. Controle da direção do fluxo de ar por meio do posicionamento das aletas.
2. Controle de ativação e desativação do LED/display presente na unidade interna do ar-condicionado.

A implementação deverá preservar a arquitetura atual, a comunicação existente com LG ThinQ e a identidade visual moderna do widget.

**Não reescreva o projeto nem substitua componentes que já estejam funcionando corretamente.**

---

## 2. Análise inicial obrigatória

Antes de implementar qualquer funcionalidade:

1. Leia integralmente o AGENTS.md.
2. Analise a estrutura atual do projeto.
3. Identifique o módulo responsável pela comunicação com LG ThinQ.
4. Identifique o SDK, biblioteca ou cliente HTTP utilizado.
5. Verifique como os comandos são enviados ao equipamento.
6. Analise como as capacidades disponíveis do dispositivo são obtidas.
7. Consulte a documentação técnica da integração utilizada.

Investigue especificamente o suporte às seguintes operações:

- Controle de oscilação vertical.
- Controle de oscilação horizontal.
- Posicionamento fixo das aletas.
- Seleção da direção do fluxo de ar.
- Ativação e desativação da iluminação do display.
- Consulta do estado atual dessas configurações.

Não presuma que essas funcionalidades estão disponíveis apenas porque existem no controle remoto físico.

Documente quais operações são efetivamente suportadas pela API e pelo aparelho.

---

## 3. Controle de direção das aletas

### Objetivo

Permitir que o usuário ajuste a direção do ar emitido pelo equipamento diretamente pelo widget.

### Funcionalidades desejadas

**3.1. Oscilação vertical**

Implementar controle para:

- Ativar oscilação vertical.
- Desativar oscilação vertical.
- Consultar o estado atual da oscilação.

**3.2. Posicionamento vertical**

Caso a integração permita selecionar posições específicas, implementar o ajuste da direção vertical do fluxo de ar.

Exemplos conceituais:

- Direcionado para cima.
- Posição intermediária.
- Direcionado para baixo.
- Oscilação automática.

Essas opções são apenas referências de interface. Utilize exclusivamente as posições realmente disponibilizadas pelo equipamento.

**3.3. Oscilação horizontal**

Verificar a disponibilidade de controle horizontal.

Caso seja suportado:

- Permitir ativar e desativar a oscilação.
- Implementar seleção de direção horizontal, se disponível.
- Exibir o estado atual.

Caso não seja suportado, não apresentar controles funcionais fictícios.

### Interface

Criar uma seção compacta chamada "Direção do ar".

Utilizar componentes modernos que estejam alinhados ao design atual do widget.

Priorizar:

- Botões segmentados.
- Ícones representando direções.
- Indicadores visuais de seleção.
- Transições suaves.
- Feedback de processamento.

Evitar QComboBox e controles nativos com aparência antiga quando houver alternativa visual adequada.

Se possível, utilizar uma representação visual simplificada do fluxo de ar para indicar a direção selecionada.

### Requisitos de comportamento

- Atualizar os controles conforme o estado confirmado do dispositivo.
- Não assumir que um comando foi executado antes da confirmação.
- Respeitar as capacidades retornadas pela integração.
- Desabilitar controles não disponíveis.
- Evitar comandos simultâneos conflitantes.
- Tratar falhas de comunicação.
- Preservar a última configuração confirmada quando uma operação falhar.

Se o comando for aceito sem retornar o novo estado, realizar uma nova consulta antes de considerar a operação confirmada.

---

## 4. Controle de LED/display

### Objetivo

Permitir ativar ou desativar a iluminação do display localizado na unidade interna do ar-condicionado.

O controle deverá afetar somente a iluminação ou os indicadores do painel do equipamento, conforme o suporte da API.

Não deve desligar o aparelho nem alterar seu modo de funcionamento.

### Funcionalidades

Implementar:

- Ligar o LED/display.
- Desligar o LED/display.
- Consultar o estado atual, quando suportado.
- Preservar a configuração durante a sincronização.

### Interface

Adicionar um controle chamado "Luz do painel" ou "LED do display".

Utilizar um switch moderno, consistente com os demais controles da aplicação.

Comportamento esperado:

**LED ligado:**
- Indicador visual ativo.
- Ícone representando iluminação habilitada.

**LED desligado:**
- Indicador visual inativo.
- Ícone representando iluminação desabilitada.

**Estado desconhecido:**
- Exibir estado indeterminado ou indisponível.
- Não assumir automaticamente que o LED está ligado ou desligado.

### Requisitos técnicos

Identificar o comando equivalente na API LG ThinQ utilizada.

A funcionalidade pode aparecer na integração com nomenclaturas diferentes. Investigue a documentação e as capacidades retornadas pelo dispositivo, sem presumir nomes de endpoints ou parâmetros.

Não confundir o LED do display com:

- Iluminação ambiente.
- Indicadores de conectividade.
- Iluminação da interface do aplicativo.
- Estado de energia do equipamento.

Caso a API não disponibilize essa operação, documente a limitação.

---

## 5. Integração e arquitetura

Preservar a separação entre:

- Interface gráfica.
- Gerenciamento de estado.
- Serviços de controle.
- Provedor de comunicação LG ThinQ.

Estender as abstrações existentes, quando necessário, para suportar:

- Consulta das capacidades de direção do ar.
- Alteração de oscilação vertical.
- Alteração de oscilação horizontal.
- Seleção de posições fixas das aletas.
- Consulta e alteração da iluminação do display.

Os nomes e assinaturas dos métodos devem seguir os padrões existentes no projeto.

Não criar métodos fictícios apenas para corresponder aos exemplos deste documento.

### Normalização de estados

Caso a API retorne códigos ou valores específicos, implemente uma camada de normalização.

A interface não deverá depender diretamente dos valores internos da API.

Separar claramente:

- Funcionalidade suportada.
- Funcionalidade indisponível.
- Estado conhecido.
- Estado desconhecido.
- Comando pendente.
- Falha de comunicação.

---

## 6. Preservação da interface atual

O projeto já possui um widget com identidade visual própria.

As novas funcionalidades deverão ser incorporadas sem comprometer sua aparência.

Requisitos:

- Manter o efeito de transparência existente.
- Preservar os temas claro e escuro.
- Utilizar os componentes visuais modernos já disponíveis.
- Preservar a organização e a hierarquia visual.
- Evitar crescimento desnecessário da janela.
- Evitar excesso de botões e informações.
- Utilizar animações discretas.

Caso os controles ocupem muito espaço, avaliar a criação de uma área expansível para funcionalidades avançadas.

A seção deve permanecer compacta quando não estiver em uso.

---

## 7. Sincronização com o equipamento

As novas funcionalidades deverão utilizar o mecanismo de sincronização existente.

Ao iniciar a aplicação:

1. Identificar o dispositivo.
2. Consultar suas capacidades.
3. Recuperar os estados disponíveis.
4. Atualizar os controles visuais.

Após executar comandos:

1. Enviar a solicitação.
2. Apresentar feedback de processamento.
3. Verificar o resultado.
4. Atualizar o estado confirmado.
5. Informar eventuais falhas.

Não atualizar permanentemente o estado da interface apenas com base no comando solicitado.

Evitar consultas excessivas e respeitar eventuais limites da API.

---

## 8. Testes

Implementar testes automatizados para:

### Direção do ar

- Ativação da oscilação vertical.
- Desativação da oscilação vertical.
- Alteração de posições fixas, quando suportadas.
- Controle horizontal, quando suportado.
- Retorno de estados desconhecidos.
- Tentativa de uso de funcionalidade indisponível.
- Falha no envio de comandos.

### LED/display

- Ativação da iluminação.
- Desativação da iluminação.
- Consulta de estado.
- Tratamento de funcionalidade não suportada.
- Tratamento de falhas de comunicação.

### Interface

- Atualização dos controles.
- Feedback visual de processamento.
- Desabilitação de operações indisponíveis.
- Preservação do estado anterior em caso de falha.
- Ausência de bloqueio da interface durante operações de rede.

Utilizar mocks para os testes automatizados.

Quando houver acesso ao equipamento real, realizar testes de integração sem considerar automaticamente que os mocks comprovam compatibilidade física.

---

## 9. Critérios de aceitação

A implementação será considerada concluída quando:

1. As capacidades reais do equipamento forem identificadas.
2. Os comandos suportados estiverem implementados.
3. O widget apresentar controles modernos.
4. A direção das aletas puder ser alterada conforme as possibilidades da API.
5. O LED/display puder ser controlado, caso a integração ofereça suporte.
6. Os estados forem sincronizados corretamente.
7. Falhas de comunicação forem tratadas.
8. Funcionalidades existentes continuarem funcionando.
9. Os testes automatizados forem executados.
10. As limitações técnicas forem documentadas.

A ausência de suporte na API não deverá ser contornada por simulações que aparentem controlar o equipamento.

---

## 10. Instrução final

Analise o projeto existente e implemente as funcionalidades descritas.

Priorize a documentação oficial da LG e os recursos reais do SDK utilizado.

Primeiro, confirme a disponibilidade dos comandos na integração. Depois, implemente os serviços e controles visuais correspondentes.

Preserve a identidade visual moderna do widget e mantenha a compatibilidade com as funcionalidades existentes.

Não altere desnecessariamente a arquitetura ou a lógica de comunicação.

Ao concluir, apresente:

- Arquivos modificados.
- Funcionalidades implementadas.
- Comandos utilizados pela integração.
- Recursos efetivamente suportados pelo equipamento.
- Testes realizados e seus resultados.
- Limitações identificadas.

Não declare uma funcionalidade como plenamente validada sem confirmação de funcionamento no equipamento real.