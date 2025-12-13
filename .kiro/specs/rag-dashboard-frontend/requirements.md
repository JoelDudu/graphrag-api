# Requirements Document - RAG Dashboard Frontend

## Introduction

O RAG Dashboard Frontend é uma aplicação web moderna que consome a API GraphRAG v3, fornecendo uma interface intuitiva para gerenciamento e consulta de documentos com IA. O sistema permite que usuários façam upload de documentos, acompanhem o processamento em tempo real, realizem buscas semânticas/por grafo, e interajam com um chatbot especializado. A interface segue o design apresentado com 6 módulos principais: Vetorização, Busca Inteligente, IA Especialista, Gestão Completa, Upload de Documentos e Busca Semântica.

## Requirements

### Requirement 1: Dashboard Principal com Navegação de Módulos

**User Story:** Como usuário, quero visualizar um dashboard principal que me mostre todos os módulos disponíveis do sistema, para que eu possa acessar facilmente as funcionalidades que preciso.

#### Acceptance Criteria

1. WHEN o usuário acessa a aplicação THEN o sistema SHALL exibir um dashboard com 6 cards principais (Vetorização, Busca Inteligente, IA Especialista, Gestão Completa, Upload de Documentos, Busca Semântica)
2. WHEN o usuário clica em um card THEN o sistema SHALL navegar para o módulo correspondente
3. WHEN o dashboard carrega THEN o sistema SHALL exibir o header com logo "RAG - Sistema de Documentos IA" e descrição "Retrieval-Augmented Generation"
4. WHEN o usuário está em qualquer módulo THEN o sistema SHALL permitir retornar ao dashboard através de um botão ou menu de navegação
5. WHEN o dashboard carrega THEN o sistema SHALL fazer uma chamada GET /health para verificar a disponibilidade da API

### Requirement 2: Módulo de Upload de Documentos

**User Story:** Como usuário, quero fazer upload de arquivos PDF para o sistema, para que eles sejam processados e indexados.

#### Acceptance Criteria

1. WHEN o usuário acessa o módulo de upload THEN o sistema SHALL exibir uma área de drag-and-drop para arquivos
2. WHEN o usuário arrasta um arquivo PDF sobre a área THEN o sistema SHALL destacar visualmente a área (feedback visual)
3. WHEN o usuário solta um arquivo PDF THEN o sistema SHALL fazer upload via POST /upload e exibir o document_id retornado
4. WHEN o upload é bem-sucedido THEN o sistema SHALL exibir uma mensagem de sucesso com o document_id
5. WHEN o upload falha THEN o sistema SHALL exibir uma mensagem de erro clara
6. WHEN o arquivo é enviado THEN o sistema SHALL permitir que o usuário inicie o processamento imediatamente ou navegue para outro módulo
7. WHEN o usuário faz upload THEN o sistema SHALL validar que o arquivo é PDF antes de enviar

### Requirement 3: Módulo de Processamento de Documentos (Vetorização)

**User Story:** Como usuário, quero processar documentos enviados escolhendo um modelo de IA e tipo de documento, para que o sistema extraia entidades e relacionamentos.

#### Acceptance Criteria

1. WHEN o usuário acessa o módulo de vetorização THEN o sistema SHALL exibir um formulário com campos para document_id, modelo (claude/openai/kimi) e tipo de documento
2. WHEN o usuário clica em "Processar" THEN o sistema SHALL fazer POST /process com os parâmetros selecionados
3. WHEN o processamento inicia THEN o sistema SHALL exibir status "Processing" e desabilitar o botão de processar
4. WHEN o processamento está em andamento THEN o sistema SHALL fazer polling em GET /status/{document_id} a cada 5 segundos
5. WHEN o status retorna "Completed" THEN o sistema SHALL exibir um resumo com número de chunks, entidades e relacionamentos extraídos
6. WHEN o processamento falha THEN o sistema SHALL exibir a mensagem de erro retornada pela API
7. WHEN o usuário está processando um documento THEN o sistema SHALL exibir uma barra de progresso visual baseada no campo "progress"

### Requirement 4: Módulo de Gestão de Documentos

**User Story:** Como usuário, quero visualizar todos os documentos enviados, seus status e metadados, para que eu possa gerenciar minha biblioteca de documentos.

#### Acceptance Criteria

1. WHEN o usuário acessa o módulo de gestão THEN o sistema SHALL fazer GET /documents e exibir uma tabela/lista com todos os documentos
2. WHEN a lista carrega THEN o sistema SHALL exibir colunas: Nome, Status, Progresso, Modelo, Data de Criação
3. WHEN o usuário clica em um documento THEN o sistema SHALL exibir detalhes completos via GET /status/{document_id}
4. WHEN o usuário clica em "Deletar" THEN o sistema SHALL fazer DELETE /documents/{document_id} e remover da lista
5. WHEN o usuário confirma deleção THEN o sistema SHALL exibir uma confirmação antes de executar
6. WHEN a lista está vazia THEN o sistema SHALL exibir uma mensagem "Nenhum documento encontrado"
7. WHEN o status de um documento muda THEN o sistema SHALL atualizar a tabela em tempo real (polling ou WebSocket)

### Requirement 5: Módulo de Busca Semântica

**User Story:** Como usuário, quero fazer perguntas aos documentos processados usando busca semântica, para que o sistema retorne respostas baseadas no conteúdo.

#### Acceptance Criteria

1. WHEN o usuário acessa o módulo de busca semântica THEN o sistema SHALL exibir um campo de input para query e seletor de documento
2. WHEN o usuário digita uma pergunta e clica "Buscar" THEN o sistema SHALL fazer POST /query com search_type="semantic"
3. WHEN a busca retorna THEN o sistema SHALL exibir a resposta (answer) em destaque
4. WHEN a busca retorna THEN o sistema SHALL exibir as fontes (sources) com trechos de texto relevantes
5. WHEN o usuário não seleciona um documento THEN o sistema SHALL buscar em todos os documentos processados
6. WHEN a busca está em andamento THEN o sistema SHALL exibir um indicador de carregamento
7. WHEN a busca falha THEN o sistema SHALL exibir mensagem de erro clara

### Requirement 6: Módulo de Busca por Grafo

**User Story:** Como usuário, quero buscar informações navegando pelo grafo de conhecimento (entidades e relacionamentos), para que eu possa explorar conexões entre conceitos.

#### Acceptance Criteria

1. WHEN o usuário acessa o módulo de busca por grafo THEN o sistema SHALL exibir um campo de input para query
2. WHEN o usuário digita uma pergunta e clica "Buscar" THEN o sistema SHALL fazer POST /query com search_type="graph"
3. WHEN a busca retorna THEN o sistema SHALL exibir a resposta gerada pelo LLM
4. WHEN a busca retorna THEN o sistema SHALL exibir as entidades encontradas com seus tipos e descrições
5. WHEN a busca retorna THEN o sistema SHALL exibir os relacionamentos entre entidades
6. WHEN o usuário clica em uma entidade THEN o sistema SHALL destacar seus relacionamentos
7. WHEN a busca está em andamento THEN o sistema SHALL exibir um indicador de carregamento

### Requirement 7: Módulo de Busca Híbrida

**User Story:** Como usuário, quero fazer buscas que combinam semântica e grafo, para que eu obtenha resultados mais completos e contextualizados.

#### Acceptance Criteria

1. WHEN o usuário acessa o módulo de busca híbrida THEN o sistema SHALL exibir um campo de input para query
2. WHEN o usuário digita uma pergunta e clica "Buscar" THEN o sistema SHALL fazer POST /query com search_type="hybrid"
3. WHEN a busca retorna THEN o sistema SHALL exibir a resposta em destaque
4. WHEN a busca retorna THEN o sistema SHALL exibir resultados semânticos e resultados do grafo em abas separadas
5. WHEN o usuário clica na aba "Semântica" THEN o sistema SHALL exibir trechos de texto com scores de similaridade
6. WHEN o usuário clica na aba "Grafo" THEN o sistema SHALL exibir entidades e relacionamentos
7. WHEN a busca está em andamento THEN o sistema SHALL exibir um indicador de carregamento

### Requirement 8: Chatbot Especialista

**User Story:** Como usuário, quero conversar com um chatbot especializado que mantém contexto da conversa, para que eu possa fazer perguntas de acompanhamento.

#### Acceptance Criteria

1. WHEN o usuário acessa o módulo de chatbot THEN o sistema SHALL exibir uma interface de chat com histórico de mensagens
2. WHEN o usuário digita uma mensagem e pressiona Enter THEN o sistema SHALL fazer POST /query com a mensagem
3. WHEN a resposta retorna THEN o sistema SHALL exibir a mensagem do assistente no chat
4. WHEN o usuário faz uma pergunta de acompanhamento THEN o sistema SHALL manter o contexto da conversa anterior
5. WHEN o chat está em andamento THEN o sistema SHALL exibir um indicador de digitação
6. WHEN o usuário clica em uma fonte THEN o sistema SHALL exibir o trecho completo em um modal
7. WHEN o usuário clica "Limpar Chat" THEN o sistema SHALL resetar o histórico de mensagens

### Requirement 9: Seleção de Tipos de Documentos

**User Story:** Como usuário, quero selecionar o tipo de documento antes de processar, para que o sistema use prompts otimizados para cada domínio.

#### Acceptance Criteria

1. WHEN o usuário acessa o formulário de processamento THEN o sistema SHALL fazer GET /doc-types para obter tipos disponíveis
2. WHEN os tipos carregam THEN o sistema SHALL exibir um dropdown com opções: generic, legal, medical, technical, financial, aesthetics, health, it
3. WHEN o usuário seleciona um tipo THEN o sistema SHALL exibir a descrição do tipo
4. WHEN o usuário não seleciona um tipo THEN o sistema SHALL usar "generic" como padrão
5. WHEN o usuário processa um documento THEN o sistema SHALL enviar o tipo selecionado no campo doc_type

### Requirement 10: Autenticação e Login

**User Story:** Como usuário, quero fazer login na aplicação com credenciais, para que apenas usuários autorizados possam acessar o sistema.

#### Acceptance Criteria

1. WHEN o usuário acessa a aplicação sem estar autenticado THEN o sistema SHALL redirecionar para a tela de login
2. WHEN o usuário está na tela de login THEN o sistema SHALL exibir campos para email/usuário e senha
3. WHEN o usuário preenche as credenciais e clica "Entrar" THEN o sistema SHALL validar as credenciais
4. WHEN as credenciais são válidas THEN o sistema SHALL armazenar um token de autenticação (JWT ou similar)
5. WHEN as credenciais são inválidas THEN o sistema SHALL exibir mensagem de erro clara
6. WHEN o usuário está autenticado THEN o sistema SHALL incluir o token em todas as requisições à API
7. WHEN o token expira THEN o sistema SHALL redirecionar para a tela de login
8. WHEN o usuário clica "Sair" THEN o sistema SHALL limpar o token e redirecionar para login
9. WHEN o usuário acessa com token válido THEN o sistema SHALL permitir acesso ao dashboard

### Requirement 11: Responsividade e Acessibilidade

**User Story:** Como usuário em diferentes dispositivos, quero que a interface seja responsiva e acessível, para que eu possa usar o sistema em desktop, tablet e mobile.

#### Acceptance Criteria

1. WHEN o usuário acessa em desktop THEN o sistema SHALL exibir layout otimizado para telas grandes
2. WHEN o usuário acessa em tablet THEN o sistema SHALL exibir layout adaptado para telas médias
3. WHEN o usuário acessa em mobile THEN o sistema SHALL exibir layout adaptado para telas pequenas
4. WHEN o usuário usa leitor de tela THEN o sistema SHALL ter labels, ARIA attributes e navegação por teclado
5. WHEN o usuário navega por teclado THEN o sistema SHALL permitir acesso a todos os elementos interativos
6. WHEN o usuário interage com elementos THEN o sistema SHALL exibir feedback visual claro (focus states, hover states)
7. WHEN o usuário usa a aplicação THEN o sistema SHALL ter contraste de cores adequado (WCAG AA mínimo)
