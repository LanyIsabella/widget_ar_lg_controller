# Redesign da interface — LG AC Controller

## 1. Objetivo

Realize uma refatoração visual e de experiência do usuário (UI/UX) na interface atual do projeto LG AC Controller.

A aplicação é um widget desktop desenvolvido em Python com PySide6, destinado ao controle de um ar-condicionado LG Dual Inverter Voice por meio da rede.

A interface atual está funcional, mas possui uma aparência de aplicação desktop convencional, com botões, campos numéricos e seletores que remetem a componentes antigos do Windows.

Quero transformar essa interface em um **widget moderno, minimalista, elegante e interativo**, com aparência de aplicação desktop premium.

Utilize a imagem de referência da interface atual fornecida como ponto de partida.

**Importante:** o trabalho consiste principalmente na modernização da interface. Preserve integralmente a lógica de integração, comunicação, autenticação, sincronização e controle do equipamento.

---

## 2. Identidade visual

### Direção de design

Adotar uma linguagem visual inspirada em:

- Glassmorphism.
- Widgets modernos do Windows 11.
- Interfaces de dispositivos inteligentes (Smart Home).
- Painéis de controle minimalistas.
- Aplicações com microinterações e animações suaves.

A interface deve transmitir modernidade, simplicidade e sofisticação, sem excesso de elementos visuais.

### Transparência

Implementar uma janela com fundo transparente e cantos arredondados.

Requisitos:

- Remover o fundo cinza opaco atual.
- Utilizar transparência real na janela.
- Implementar um painel principal translúcido, com aparência de vidro fosco.
- Aplicar bordas discretas e sombras suaves.
- Permitir visualizar parcialmente o conteúdo da área de trabalho através do widget.
- Preservar a legibilidade dos componentes sobre diferentes papéis de parede.

Investigar o suporte do Windows 10/11 a efeitos nativos como Acrylic ou Mica, priorizando soluções compatíveis com PySide6.

Caso seja necessário utilizar APIs nativas do Windows, encapsular essa implementação em um módulo independente.

Não utilizar apenas um fundo com cor sólida simulando transparência.

### Paleta

Utilizar uma identidade visual baseada em:

- Azul pastel.
- Branco translúcido.
- Cinza-azulado.
- Azul-ciano para estados ativos.
- Tons suaves e discretos para estados inativos.

Evitar cores excessivamente saturadas.

Preparar suporte para temas claro e escuro, mantendo transparência e contraste adequados em ambos.

---

## 3. Redesenho da estrutura

A interface deve deixar de parecer um formulário e passar a apresentar uma composição visual típica de um widget inteligente.

### Cabeçalho

Implementar um cabeçalho compacto contendo:

- Nome da aplicação.
- Identificação do ar-condicionado selecionado.
- Indicador de conexão.
- Acesso às configurações.
- Controles discretos para minimizar e fechar.

A janela deverá permitir movimentação pelo cabeçalho, inclusive caso não utilize a barra de título nativa.

Reduzir elementos decorativos desnecessários.

### Área principal

Criar uma área visual de destaque contendo:

- Ilustração dinâmica do ar-condicionado.
- Temperatura configurada em tamanho maior.
- Estado atual do equipamento.
- Modo de operação.
- Indicador visual de atividade.

A temperatura deve ser o elemento informativo de maior destaque.

### Área de controles

Organizar os controles em uma estrutura compacta, intuitiva e visualmente equilibrada.

Evitar excesso de divisórias, caixas e formulários.

Utilizar espaçamentos consistentes, alinhamento adequado e hierarquia visual clara.

---

## 4. Ícone dinâmico do ar-condicionado

Atualmente, a aplicação já altera a representação do equipamento conforme seu estado.

Essa funcionalidade deve ser preservada e aprimorada.

### Animação

Implementar uma animação dinâmica e discreta na ilustração do ar-condicionado.

Comportamento esperado:

**Equipamento desligado:**
- Ilustração estática.
- Coloração neutra.
- Ausência de partículas ou animações de ventilação.

**Equipamento ligado:**
- Transição suave para estado ativo.
- Representação visual discreta do fluxo de ar.
- Movimento contínuo e leve enquanto o equipamento estiver funcionando.

**Modo resfriamento:**
- Fluxo de ar com tonalidade azul-clara.
- Animação suave simulando circulação de ar frio.

**Modo aquecimento:**
- Fluxo com tonalidade quente, quando disponível.

**Modo ventilação:**
- Fluxo de ar com coloração neutra.
- Movimento que remeta à circulação de ar.

**Modo desumidificação:**
- Utilizar representação visual discreta e coerente com a função.

### Requisitos técnicos

- Priorizar animações vetoriais desenhadas com QPainter.
- Utilizar QPropertyAnimation, QVariantAnimation ou mecanismos equivalentes do Qt.
- Evitar GIFs pesados e animações excessivamente complexas.
- Não bloquear a thread principal.
- Reduzir o consumo de CPU e memória.
- Interromper ou reduzir animações quando o widget estiver oculto.
- Respeitar, quando possível, as preferências de redução de movimento do sistema.

A animação deve estar associada ao estado real confirmado do dispositivo, e não apenas à interação do usuário.

---

## 5. Controle moderno de temperatura

Substituir completamente o campo numérico tradicional utilizado atualmente.

Não utilizar QSpinBox com aparência nativa do Windows como controle visual principal.

### Componente desejado

Implementar um controle personalizado de temperatura com:

- Temperatura central em destaque.
- Botões modernos de incremento e decremento.
- Ícones minimalistas de "+" e "−".
- Botões com formato circular ou arredondado.
- Feedback visual durante a interação.
- Transições suaves na alteração do valor.

Exemplo conceitual:

    [ − ]       23 °C       [ + ]

A temperatura central deverá ter destaque tipográfico.

### Comportamento

- Incrementar ou decrementar conforme os intervalos aceitos pelo equipamento.
- Respeitar limites reais de temperatura.
- Desabilitar ações indisponíveis.
- Apresentar feedback enquanto o comando estiver sendo executado.
- Tratar falhas de comunicação.
- Evitar o envio excessivo de comandos em cliques rápidos.
- Manter consistência entre o valor apresentado e o valor confirmado pelo ar-condicionado.

O controle deverá ser implementado como componente reutilizável.

---

## 6. Modernização dos controles

Substituir a aparência convencional dos componentes atuais.

### Botão de energia

Criar um botão principal de ligar/desligar com aparência moderna.

Requisitos:

- Ícone de energia.
- Estados visuais distintos para ligado e desligado.
- Transições suaves.
- Feedback de processamento.
- Desabilitação temporária quando necessário.

O botão de energia deve ter destaque sem dominar excessivamente a interface.

### Seleção de modo

Substituir o QComboBox tradicional por um seletor personalizado.

Utilizar uma das alternativas:

- Botões segmentados.
- Chips selecionáveis.
- Menu popover personalizado.

Preferir botões segmentados caso a quantidade de modos permita.

Representar visualmente os modos suportados, como:

- Resfriar.
- Aquecer.
- Ventilar.
- Desumidificar.
- Automático.

Não apresentar como disponíveis funcionalidades que o equipamento não suporta.

### Controle de ventilação

Substituir o seletor convencional por componentes visualmente modernos.

Permitir selecionar as velocidades disponíveis.

Utilizar:

- Chips.
- Botões segmentados.
- Ícones indicativos de ventilação.

### Oscilação

Substituir a checkbox tradicional por um switch moderno.

O componente deve possuir:

- Estado ligado/desligado.
- Animação discreta.
- Cores adequadas.
- Feedback visual.

---

## 7. Microinterações

Adicionar microinterações que tornem a aplicação mais fluida.

Exemplos:

- Transição ao ligar ou desligar.
- Animação discreta ao alterar temperatura.
- Mudança suave dos estados selecionados.
- Feedback ao passar o cursor sobre botões.
- Animação de carregamento durante sincronização.
- Transição entre estados de conexão.

Evitar animações exageradas ou constantes em elementos que não precisam delas.

Priorizar durações curtas, entre aproximadamente 150 e 300 ms para interações pontuais.

A animação de fluxo de ar pode ser contínua enquanto o equipamento estiver funcionando.

---

## 8. Informações de sincronização

Redesenhar o indicador atual de sincronização.

Em vez de apresentar apenas um texto no rodapé, implementar uma indicação visual discreta contendo:

- Ícone de conexão.
- Estado conectado, sincronizando ou desconectado.
- Informação sobre a última sincronização bem-sucedida.
- Feedback quando houver problemas de comunicação.

Distinguir claramente:

- Estado confirmado do equipamento.
- Alteração solicitada e ainda pendente.
- Falha na execução de um comando.

---

## 9. Responsividade da interface

O widget deve manter proporções compactas.

Requisitos:

- Evitar rolagem desnecessária.
- Evitar áreas vazias excessivas.
- Manter alinhamento visual.
- Suportar diferentes escalas de DPI do Windows.
- Adaptar o posicionamento dos controles quando necessário.
- Preservar a legibilidade em telas com escalonamento de 125%, 150% ou superior.

Priorizar um layout mais compacto e funcional do que o atual.

---

## 10. Arquitetura e implementação

Antes de modificar o código:

1. Inspecione a estrutura atual do projeto.
2. Leia o AGENTS.md.
3. Identifique como a interface foi construída.
4. Localize a implementação dos componentes atuais.
5. Identifique os mecanismos de atualização de estado.
6. Verifique como a interface recebe as informações da integração LG.
7. Planeje a refatoração evitando alterações desnecessárias no backend.

### Componentização

Criar componentes reutilizáveis para:

- Botão de energia.
- Controle de temperatura.
- Seletor de modo.
- Seletor de ventilação.
- Switch de oscilação.
- Ilustração animada do ar-condicionado.
- Indicador de conexão.

### Organização

Separar:

- Componentes visuais.
- Estilos e temas.
- Animações.
- Estado da interface.
- Serviços de controle.
- Integração com LG ThinQ.

Não colocar lógica de comunicação dentro dos componentes visuais.

---

## 11. Restrições importantes

- Não reescrever o projeto do zero.
- Não modificar a integração LG sem necessidade técnica comprovada.
- Não remover funcionalidades existentes.
- Não alterar contratos entre serviços sem justificativa.
- Não substituir PySide6 por outra tecnologia.
- Não utilizar navegador ou interface web.
- Não depender de recursos externos para renderizar a interface.
- Não incluir animações pesadas.
- Não utilizar componentes com aparência nativa antiga.
- Não simular sucesso em comandos não confirmados.
- Não utilizar cores que prejudiquem a leitura sobre fundos transparentes.

Caso algum recurso visual apresente limitações no Qt ou no Windows, implemente a alternativa tecnicamente mais adequada e documente a decisão.

---

## 12. Validação

Após a implementação, verificar:

- Transparência real da janela.
- Funcionamento dos cantos arredondados.
- Movimentação da janela.
- Funcionamento dos controles de janela.
- Comportamento das animações.
- Atualização dos estados do equipamento.
- Alteração de temperatura.
- Seleção de modos.
- Controle da ventilação.
- Controle da oscilação.
- Funcionamento do botão de energia.
- Sincronização de informações.
- Compatibilidade com execução pela bandeja.
- Adequação aos temas claro e escuro.
- Comportamento em diferentes escalas de DPI.

Executar testes automatizados existentes e adicionar testes para novos componentes quando pertinente.

Não afirmar que funcionalidades foram validadas no equipamento real quando apenas testes simulados tiverem sido executados.

---

## 13. Resultado esperado

Entregar uma interface significativamente mais moderna do que a atual.

O widget deverá apresentar:

- Fundo transparente com efeito de vidro.
- Aparência de widget premium para Windows.
- Ilustração dinâmica do ar-condicionado.
- Fluxo de ar animado conforme o funcionamento.
- Controle moderno de temperatura.
- Botões e seletores personalizados.
- Microinterações suaves.
- Interface compacta e organizada.
- Excelente legibilidade.
- Integração e funcionalidades existentes preservadas.

O objetivo é que a aplicação pareça um **painel inteligente de controle de climatização**, e não um formulário convencional desenvolvido com componentes padrão de desktop.

Implemente as alterações diretamente na estrutura existente do projeto, seguindo as diretrizes do AGENTS.md.

Ao finalizar, apresente os arquivos alterados, as decisões técnicas tomadas, os testes executados e possíveis limitações.