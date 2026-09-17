# Feature Specification: Plataforma Pessoal de Gestão de Mídias (Amontoa V3.0)

**Feature Branch**: `002-amotoa-v3-core`  
**Created**: 2026-09-15  
**Status**: Draft  
**Input**: User description: "Plataforma pessoal centralizada para catalogar, acompanhar o progresso diário e conectar o consumo de animes, mangás e light novels em um único ambiente local."

---

## Clarifications

### Session 2026-09-15

- Q: Como cada sub-página de tipo (Animes/Mangás/LN) se relaciona com a estrutura geral da plataforma? → A: A Dashboard em `localhost:3000/` já existe e possui 3 botões de navegação (Animes, Mangás, Light Novels). Ao clicar em um botão, o administrador é direcionado para a **Vitrine tipo-específica** daquele conteúdo (ex.: `/animes`). A Página de Detalhes e o Módulo de Progresso são **sub-páginas da Vitrine**, não da Dashboard.
- Q: As 3 Vitrines (Animes/Mangás/LN) compartilham a mesma implementação ou são separadas? → A: **Implementação híbrida**: base de componentes compartilhada, com variações deliberadas por tipo — Light Novels rastreiam apenas capítulos (sem episódios); Mangás podem ter fontes de dados distintas; Animes seguem o modelo base com episódios e temporadas.
- Q: Qual o critério de agrupamento dos carrosséis nas Vitrines de Mangás e Light Novels? → A: Carrosséis agrupados por **status de acompanhamento** (ex.: “Em andamento”, “Favoritos”, “Pausados”) — o mesmo critério se aplica aos 3 tipos de mídia, variando apenas o rótulo conforme o tipo.
- Q: Para Mangás e Light Novels, como funciona a atualização de novos conteúdos e a importação histórica? → A: **Novos Mangás/LN**: verificação periódica automática (semanal ou mensal), configurável via variável de ambiente, sem vínculo com temporadas. **Históricos (antigos)**: importação em lote por ano, fracionada em batches semanais/mensais para distribuição da carga, com suporte a pausa e retomada — mesmo mecanismo de lote já previsto para Animes.
- Q: O bloco de Filmes da Franquia deve aparecer para Mangás e Light Novels? → A: **Exclusivo de Animes** — o bloco de Filmes da Franquia é ocultado automaticamente na Página de Detalhes de Mangás e Light Novels.

### Session 2026-09-17

- Q: Qual a hierarquia visual dos títulos na Vitrine tipo-específica e sub-páginas? → A: O **título japonês** é o título principal (exibido em destaque/maior); o **título em inglês** é secundário, exibido abaixo do japonês em tamanho menor — padrão uniforme nas Vitrines (Animes, Mangás, Light Novels) e em todas as suas sub-páginas (Página de Detalhes, Módulo de Progresso).
- Q: Qual o critério de identidade e unicidade para detecção de duplicatas de uma Obra? → A: O **ID da Jikan API (`mal_id`)** é a chave de identidade canônica da Obra.
- Q: Como é determinado o escopo de obras ativas no Módulo de Progresso para Mangás e Light Novels (sem temporadas)? → A: Utiliza o status de publicação oficial retornado pela Jikan API (`status: "Publishing"`), indicando obras em publicação contínua ativa, combinado ao status pessoal "Em andamento" (equivalente ao filtro de temporada atual usado em Animes).
- Q: Como as temporadas distintas de uma mesma obra são unificadas na Página de Detalhes? → A: Agrupamento automático através do endpoint de relações da Jikan API (`/relations` com tipos Sequel/Prequel), vinculando as temporadas sob uma obra-raiz/franquia comum para exibição em bloco contínuo.
- Q: Qual a estratégia de armazenamento para capas e imagens oficiais? → A: **Apenas URLs remotas** — não armazena arquivos de imagem em disco local; o navegador carrega diretamente a partir das URLs fornecidas pela CDN externa, com suporte a placeholder visual para links indisponíveis.
- Q: Qual o alcance e funcionamento da barra de busca superior? → A: **Catálogo local com busca externa opcional** — pesquisa prioritariamente as obras já salvas no banco de dados local e disponibiliza a opção de consultar a Jikan API externamente para encontrar e importar obras avulsas ao catálogo com um clique.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Vitrine e Navegação em Carrossel (Priority: P1)

O administrador acessa a Dashboard (`/`) e clica em um dos três botões de tipo (Animes, Mangás ou Light Novels). Isso o direciona para a **Vitrine tipo-específica** (ex.: `/animes`), que exibe exclusivamente as obras daquele tipo, organizadas em carrosséis contínuos agrupados por **status de acompanhamento** (ex.: “Em andamento”, “Favoritos”, “Pausados”). Cada carrossel é navegável horizontalmente, exibindo capas das obras. Em cada obra, o **título japonês** é exibido em destaque como título principal e o **título em inglês** aparece abaixo, em tamanho menor — padrão uniforme em toda a Vitrine e suas sub-páginas. Ao passar o mouse sobre uma capa, um popup com informações rápidas é exibido. Ao clicar na capa ou no título de uma categoria, o usuário é levado à **Página de Detalhes** (sub-página da Vitrine) ou à listagem filtrada do grupo. O **Módulo de Progresso** também é acessado como sub-página da Vitrine tipo-específica ativa.

**Why this priority**: É o ponto de entrada principal da plataforma e a interface mais utilizada no dia a dia. Sem ela, nenhum outro módulo é acessível.

**Independent Test**: Pode ser testado completamente populando o banco com obras fictícias e verificando a renderização dos carrosséis, o popup ao hover e os cliques de navegação.

**Acceptance Scenarios**:

1. **Given** que o catálogo local possui obras cadastradas, **When** o administrador clica em um botão de tipo na Dashboard e acessa a Vitrine tipo-específica, **Then** o sistema exibe somente as obras daquele tipo agrupadas em carrosséis por categoria no Tema Escuro nativo.
2. **Given** que o administrador passa o mouse sobre uma capa, **When** o hover é detectado, **Then** o sistema exibe um popup com informações rápidas da obra (título, tipo, status, nota pública).
3. **Given** que o administrador clica na capa de uma obra, **When** o clique é registrado, **Then** o sistema redireciona para a Página de Detalhes correspondente.

---

### User Story 2 — Pesquisa, Filtros e Ordenação do Catálogo (Priority: P2)

O administrador utiliza a barra de busca superior para encontrar obras pelo nome (inglês ou japonês), por detalhes ou por tags no catálogo local. Caso a obra procurada não esteja salva no banco local, a barra disponibiliza a opção de consultar a Jikan API externamente para localizar e importar a obra avulsa diretamente. Além disso, pode filtrar o catálogo por tags específicas, temporada de lançamento ou letra inicial, e ordenar a exibição por critérios como ordem alfabética, data de lançamento, nota pública ou nota pessoal.

**Why this priority**: Conforme o catálogo cresce com importações em lote de anos anteriores, localizar obras específicas rapidamente torna-se essencial para a usabilidade.

**Independent Test**: Pode ser testado cadastrando obras com atributos variados e verificando que a busca, os filtros e as ordenações retornam os subconjuntos corretos.

**Acceptance Scenarios**:

1. **Given** que o catálogo possui obras cadastradas, **When** o administrador digita um nome parcial na barra de busca, **Then** o sistema exibe apenas as obras cujo título (inglês ou japonês) ou tags contenham o termo buscado.
2. **Given** que o administrador aplica um filtro de temporada ou letra inicial, **When** o filtro é selecionado, **Then** a vitrine exibe apenas as obras que correspondem ao critério aplicado.
3. **Given** que o administrador escolhe uma ordenação (ex.: por nota pessoal), **When** a seleção é confirmada, **Then** os carrosséis são reordenados segundo o critério escolhido.
4. **Given** que uma obra não foi encontrada no catálogo local, **When** o administrador seleciona a opção de buscar na Jikan API, **Then** o sistema pesquisa a fonte externa, apresenta os resultados e permite importar a obra avulsa com um clique para o catálogo local.

---

### User Story 3 — Sincronização Automática de Novos Lançamentos (Priority: P1)

O sistema detecta e importa novos lançamentos de forma automática, com estratégia diferenciada por tipo:
- **Animes**: No início de cada nova temporada (ou acionamento manual), o sistema busca os lançamentos da temporada na fonte externa.
- **Mangás e Light Novels**: Verificação periódica automática (semanal ou mensal), configurável via variável de ambiente, sem vínculo com temporadas.

Em ambos os casos, obras já cadastradas são ignoradas, preservando notas, tags e progresso do administrador. Novas obras são adicionadas ao catálogo automaticamente.

**Why this priority**: Garante que o catálogo esteja sempre atualizado sem esforço manual do administrador, que é o principal benefício da plataforma frente a anotações externas.

**Independent Test**: Pode ser testado simulando uma chamada de atualização (sazonal para Anime e periódica para Mangá/LN) e verificando que apenas itens novos foram inseridos, enquanto os existentes permanecem intocados.

**Acceptance Scenarios**:

1. **Given** que o sistema detecta o início de uma nova temporada (Anime) ou o intervalo periódico é atingido (Mangá/LN), **When** a sincronização automática é disparada, **Then** o sistema adiciona apenas obras novas ao catálogo local, ignorando as já existentes.
2. **Given** que uma obra já cadastrada possui nota pessoal e progresso registrados, **When** a sincronização é executada, **Then** esses dados permanecem intactos após a atualização.
3. **Given** que a fonte de dados externa está instável ou aplica limite de requisições, **When** um erro é detectado, **Then** o sistema aciona a fila com auto-retry, pausando temporariamente e retomando as tentativas automaticamente.

---

### User Story 4 — Importação em Lote de Anos Anteriores (Priority: P2)

O administrador define um intervalo de anos (ex.: 2005 a 2007) para importar conteúdo histórico em segundo plano. Para **Animes**, o lote segue a granularidade de temporadas. Para **Mangás e Light Novels**, o lote é organizado por ano e fracionado em batches semanais ou mensais para distribuição controlada da carga. O processo exibe notificações discretas no menu superior e um painel detalhado com progresso e logs de falhas. Caso haja interrupção, o sistema salva o ponto de parada e permite retomar de onde parou.

**Why this priority**: Permite ao administrador resgatar o histórico completo de sua coleção de forma controlada, sendo fundamental para a proposta de centralização da plataforma.

**Independent Test**: Pode ser testado iniciando uma importação de 2 anos, interrompendo o processo manualmente, e verificando a retomada a partir do ponto correto.

**Acceptance Scenarios**:

1. **Given** que o administrador define um intervalo de anos e inicia a importação em lote, **When** o processo é executado em segundo plano, **Then** o sistema exibe notificações discretas no menu superior e disponibiliza um painel com progresso e logs detalhados.
2. **Given** que a importação em lote é interrompida (ex.: encerramento do sistema), **When** o administrador retorna e acessa o painel de lote, **Then** o sistema permite retomar o processo exatamente do ponto onde parou.
3. **Given** que um item do lote falha após esgotar todas as tentativas de retry, **When** o erro é registrado, **Then** o sistema prossegue para o próximo item da fila e registra a falha isoladamente no log detalhado.

---

### User Story 5 — Página de Detalhes Unificada (Priority: P1)

O administrador acessa a Página de Detalhes de uma obra e visualiza sinopse, datas, número de episódios/capítulos, tags e todas as temporadas do mesmo título unificadas em um único bloco (agrupadas automaticamente pelas relações `Sequel`/`Prequel` obtidas na Jikan API sob uma franquia comum). Pode navegar por imagens oficiais em carrossel horizontal, ampliando qualquer imagem em modal de tela cheia. Setas laterais permitem navegar para o título anterior ou seguinte do mesmo grupo, com desativação visual nos limites da lista.

**Why this priority**: É o hub central de informação e gestão de cada obra; sem ela, as demais funções de gerenciamento de progresso e filmes ficam inacessíveis.

**Independent Test**: Pode ser testado acessando a página de uma obra com múltiplas temporadas e verificando a unificação de dados, a navegação no carrossel de imagens e o comportamento das setas de navegação nos extremos da lista.

**Acceptance Scenarios**:

1. **Given** que o administrador clica em uma obra no catálogo, **When** a Página de Detalhes é carregada, **Then** o sistema exibe todas as temporadas daquele título unificadas em um bloco contínuo, junto com sinopse, metadados e tags.
2. **Given** que a obra possui imagens oficiais cadastradas, **When** o administrador interage com o carrossel de setas, **Then** as imagens são alternadas; ao clicar em uma, abre-se uma janela modal em tela cheia.
3. **Given** que o administrador utiliza as setas laterais de navegação entre títulos, **When** ele tenta avançar no último título do grupo, **Then** a seta direita fica desativada visualmente, impedindo transição inválida.
4. **Given** que uma obra não possui imagens ou filmes cadastrados, **When** a Página de Detalhes é renderizada, **Then** os blocos correspondentes são ocultados automaticamente, sem espaços vazios.

---

### User Story 6 — Gestão de Progresso, Links Externos, Notas e Tags (Priority: P1)

Na Página de Detalhes, o administrador pode: atualizar o marcador de progresso (episódio para Animes ou capítulo para Mangás/LN); editar a nota pessoal; adicionar ou remover tags; clicar em links externos que abrem o conteúdo em nova aba. Para obras do tipo **Anime**, também pode gerenciar filmes da franquia (adicionar e marcar como assistido/não assistido) — este bloco é ocultado automaticamente para Mangás e Light Novels. Todas as alterações são persistidas imediatamente.

**Why this priority**: É a funcionalidade central de gestão que diferencia a plataforma de qualquer lista estática externa; resolve diretamente o problema de "onde parei".

**Independent Test**: Pode ser testado alterando progresso, nota e tags de uma obra e verificando que os valores são preservados após recarregar a página.

**Acceptance Scenarios**:

1. **Given** que o administrador está na Página de Detalhes, **When** ele altera o marcador de episódio/capítulo, **Then** o novo valor é salvo imediatamente e refletido na interface.
2. **Given** que o administrador clica em um link externo de redirecionamento, **When** o clique é registrado, **Then** o conteúdo abre em uma nova aba do navegador, mantendo a plataforma aberta.
3. **Given** que o administrador está na Página de Detalhes de um **Anime** e marca um filme da franquia como assistido, **When** a ação é confirmada, **Then** o status do filme é atualizado e persistido imediatamente. Para Mangás e Light Novels, o bloco de filmes não é exibido.

---

### User Story 7 — Acompanhamento de Progresso Diário (Priority: P1)

O administrador acessa o Módulo de Progresso e visualiza uma listagem enxuta somente com obras em andamento ativas: para **Animes**, aquelas em andamento na temporada atual; para **Mangás e Light Novels**, aquelas em andamento com status oficial de publicação `Publishing` (em lançamento contínuo retornado pela Jikan API). Cada item exibe um botão de incremento rápido (+1) e um menu dropdown para selecionar o episódio/capítulo exato. Um link de redirecionamento rápido abre o conteúdo em nova aba. Ao marcar o último episódio/capítulo lançado (manual ou automaticamente), a obra é finalizada e removida da listagem. Se não houver obras em andamento, um estado vazio amigável é exibido com atalho para a Vitrine.

**Why this priority**: É a rotina diária do administrador; um módulo de progresso ágil e sem fricção é o núcleo da proposta de valor da plataforma.

**Independent Test**: Pode ser testado com obras em andamento e verificando os fluxos de incremento (+1), dropdown, finalização e estado vazio.

**Acceptance Scenarios**:

1. **Given** que existem obras com status pessoal de andamento ativas (temporada atual para Animes; status oficial `Publishing` para Mangás e Light Novels), **When** o administrador acessa o Módulo de Progresso, **Then** o sistema exibe uma listagem limpa contendo apenas essas obras, em Tema Escuro nativo.
2. **Given** que o administrador clica no botão "+1" de uma obra, **When** o clique é registrado, **Then** o contador de progresso é incrementado imediatamente e a alteração é persistida.
3. **Given** que o administrador seleciona um número específico no dropdown, **When** tenta selecionar um valor acima do total oficial catalogado, **Then** o sistema exibe um aviso discreto de restrição e bloqueia a seleção inválida.
4. **Given** que o administrador marca o último episódio de uma obra, **When** a ação é confirmada, **Then** o status é alterado para finalizado e o item é removido da listagem de andamento.
5. **Given** que não há obras em andamento na temporada atual, **When** o administrador acessa o Módulo de Progresso, **Then** o sistema exibe uma mensagem de incentivo com botão de atalho para a Vitrine.

---

### Edge Cases

- **Instabilidade ou Rate Limit da fonte de dados externa**: Se a chamada externa falhar ou for bloqueada por excesso de requisições, o sistema aciona a fila com auto-retry, pausando temporariamente sem interromper o ambiente local.
- **Interrupção da importação em lote**: O ponteiro do lote é salvo localmente; o administrador pode retomar exatamente do ponto de parada através do painel de logs.
- **Conflito de dados existentes durante sincronização**: O sistema aplica a regra "Ignorar e Pular", preservando integralmente notas, tags e progresso manual do administrador.
- **ID de obra obsoleto na fonte externa**: Após esgotar as tentativas de retry, o erro é registrado isoladamente no log do lote e o próximo item da fila é processado.
- **Tentativa de seleção de episódio acima do máximo**: O sistema valida o limite e exibe um aviso discreto, bloqueando a seleção inválida.
- **Ausência de imagens ou filmes relacionados**: Os blocos correspondentes são ocultados automaticamente na Página de Detalhes, sem espaços vazios.
- **Navegação lateral nos limites da lista**: A seta correspondente ao início ou fim é desativada visualmente, impedindo transições inválidas.
- **Falha de persistência local**: O sistema exibe uma notificação rápida de erro, permitindo que o administrador tente novamente.
- **Link externo inválido ou quebrado**: A plataforma local permanece intacta e funcional em segundo plano.
- **Indisponibilidade ou falha no carregamento de URL de imagem remota**: O sistema exibe um placeholder neutro estilizado no Tema Escuro sem quebrar o layout do carrossel ou da página de detalhes.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE exibir a Vitrine tipo-específica com obras agrupadas em carrosséis de navegação horizontal contínua, ordenados por **status de acompanhamento** (ex.: “Em andamento”, “Favoritos”, “Pausados”) — critério uniforme para Animes, Mangás e Light Novels.
- **FR-026**: O sistema DEVE exibir o **título japonês** como título principal (em destaque/maior) e o **título em inglês** como título secundário (abaixo, em tamanho menor) em todas as telas da Vitrine tipo-específica e suas sub-páginas (Página de Detalhes e Módulo de Progresso).
- **FR-002**: O sistema DEVE exibir um popup com informações rápidas ao passar o mouse sobre a capa de uma obra.
- **FR-003**: O sistema DEVE permitir pesquisar obras por nome (inglês/japonês), detalhes ou tags no catálogo local através de uma barra de busca superior, disponibilizando a opção de consultar a Jikan API externamente para localizar e importar obras avulsas ao catálogo com um clique.
- **FR-004**: O sistema DEVE permitir filtrar o catálogo por tags, temporada de lançamento ou letra inicial, e ordenar por diferentes critérios (alfabética, data, nota pública, nota pessoal).
- **FR-005**: O sistema DEVE conectar-se a uma fonte de dados externa para buscar informações de animes, mangás e light novels.
- **FR-006**: O sistema DEVE sincronizar novos lançamentos de forma automática com estratégia por tipo: **Animes** — gatilho sazonal (início de temporada) com opção de acionamento manual; **Mangás e Light Novels** — verificação periódica automática (intervalo configurável via variável de ambiente, sem vínculo com temporadas), também com acionamento manual.
- **FR-007**: O sistema DEVE implementar uma fila de importação com auto-retry para contornar instabilidades ou limites de requisição da fonte externa.
- **FR-008**: O sistema DEVE aplicar a política "Ignorar e Pular" durante sincronizações usando o `mal_id` da Jikan API como identificador único canônico, preservando notas, tags e progresso do administrador em obras já cadastradas.
- **FR-009**: O sistema DEVE suportar importações em lote de conteúdo histórico por intervalo de anos, executadas em segundo plano com suporte a pausa e retomada. Para Mangás e Light Novels, o lote é fracionado em batches semanais ou mensais (configuráveis) para distribuição controlada da carga de requisições.
- **FR-025**: O sistema DEVE permitir configurar, via variável de ambiente, o intervalo de verificação periódica automática de novos Mangás e Light Novels (ex.: `MANGA_LN_SYNC_INTERVAL=weekly` ou `monthly`).
- **FR-010**: O sistema DEVE exibir notificações discretas no menu superior e um painel detalhado com progresso e logs para tarefas em segundo plano.
- **FR-011**: O sistema DEVE renderizar a Página de Detalhes unificando todas as temporadas de uma obra em um único bloco visual, agrupando-as automaticamente a partir das relações (`Sequel`/`Prequel`) da Jikan API (`/relations`) vinculadas sob um identificador comum de franquia.
- **FR-012**: O sistema DEVE prover um carrossel horizontal com setas para imagens oficiais, abrindo a imagem selecionada em modal de tela cheia ao clicar.
- **FR-013**: O sistema DEVE abrir links externos de redirecionamento em uma nova aba do navegador.
- **FR-014**: O sistema DEVE permitir a atualização do progresso de episódios/capítulos, notas pessoais e gerenciamento de tags com persistência imediata.
- **FR-015**: O sistema DEVE permitir adicionar filmes de franquia e alternar seu status (assistido/não assistido) **exclusivamente para obras do tipo Anime**; o bloco é ocultado automaticamente para Mangás e Light Novels.
- **FR-016**: O sistema DEVE prover navegação lateral por setas entre títulos do mesmo grupo, com desativação visual nos limites de início e fim da lista.
- **FR-017**: O sistema DEVE ocultar automaticamente blocos de conteúdo quando não houver dados cadastrados (galeria de imagens) ou quando o tipo da obra não suportar o bloco (**Filmes da Franquia** — ocultado para Mangás e Light Novels).
- **FR-018**: O sistema DEVE renderizar uma listagem enxuta no Módulo de Progresso, restrita às obras em andamento ativas — para **Animes**, restritas à temporada atual; para **Mangás e Light Novels**, restritas àquelas cujo status oficial de publicação retornado pela Jikan API seja `Publishing`.
- **FR-019**: O sistema DEVE disponibilizar em cada item da listagem de progresso um botão de incremento rápido (+1) e um menu dropdown para seleção exata da unidade de progresso correspondente ao tipo da obra — **episódio** para Animes, **capítulo** para Mangás e Light Novels —, com validação de limite máximo.
- **FR-020**: O sistema DEVE finalizar o acompanhamento de uma obra de forma manual ou automática ao atingir o último episódio/capítulo, removendo-a da listagem ativa.
- **FR-021**: O sistema DEVE exibir uma mensagem de incentivo com atalho para a Vitrine quando não houver obras em andamento no Módulo de Progresso.
- **FR-022**: O sistema DEVE operar exclusivamente em ambiente local com interface em Tema Escuro fixo.
- **FR-023**: O sistema DEVE armazenar todos os dados em banco de dados local, persistindo exclusivamente as URLs remotas de imagens (carregadas diretamente pelo navegador a partir da CDN externa, com placeholder de fallback) e links externos de redirecionamento, sem armazenar arquivos binários de imagem em disco local.
- **FR-024**: O sistema DEVE gerar backups compactados automáticos e diários do banco de dados local na pasta configurada via variável de ambiente `BACKUP_DIR` (padrão `./backups`).

### Key Entities *(include if feature involves data)*

- **Obra (Media)**: Representa o anime, mangá ou light novel. Identificada unicamente pelo `mal_id` (ID canônico da Jikan API). Possui título japonês (campo principal, exibido em destaque) e título em inglês (campo secundário, exibido abaixo e em tamanho menor), sinopse, URL de capa, tipo (anime/mangá/light novel), status de publicação oficial retornado pela Jikan API (ex.: `Publishing`, `Currently Airing`, `Finished`), nota pública, nota pessoal, tags, vínculo de franquia (derivado das relações `Sequel`/`Prequel` da Jikan API para unificar temporadas) e links externos de redirecionamento. O campo `tipo` determina as variações de comportamento conforme a implementação híbrida.
- **Progresso (Progress)**: Registro individual vinculado a uma obra. Contém a unidade de progresso atual — **episódio** para Animes; **capítulo** para Mangás e Light Novels —, status de acompanhamento (Em andamento, Finalizado, Pausado, Dropado) e data da última atualização. A unidade é determinada pelo `tipo` da obra vinculada.
- **Filme da Franquia (FranchiseMovie)**: Filme vinculado à franquia principal de uma obra do tipo **Anime** (exclusivo; não aplicável a Mangás ou Light Novels). Possui título, URL de capa, status de visualização (assistido/não assistido) e data de lançamento. O bloco correspondente é ocultado automaticamente na Página de Detalhes quando o `tipo` da obra não é Anime.
- **Galeria de Imagens (OfficialImageGallery)**: Coleção de URLs de imagens oficiais associadas à obra para exibição em carrossel e modal.
- **Link Externo (ExternalLink)**: Endereço web salvo apontando para a página onde o administrador consome o conteúdo (assiste ou lê).
- **Trabalho de Importação em Lote (BatchImportJob)**: Controle de execução para varreduras por intervalo de anos. Gerencia estados (Em execução, Pausado, Concluído, Falhou), ponteiro de retomada e logs de falhas isoladas.
- **Grupo de Navegação (NavigationGroup)**: Sequência ordenada de títulos pertencentes ao mesmo agrupamento na Vitrine, usada para navegação lateral via setas na Página de Detalhes.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O administrador consegue atualizar o progresso diário de uma obra (incremento ou seleção exata) em no máximo 2 interações a partir do Módulo de Progresso.
- **SC-002**: 100% das notas pessoais, tags e marcações de progresso são preservadas após qualquer sincronização automática ou importação em lote.
- **SC-003**: Importações em lote de múltiplos anos são concluídas de forma autônoma mesmo diante de falhas intermitentes da fonte externa, sem necessidade de intervenção manual do administrador.
- **SC-004**: A Vitrine e os carrosséis são renderizados a 60fps constantes com tempo de resposta da API local inferior a 50ms, independentemente do volume de obras cadastradas no catálogo local.
- **SC-005**: Em caso de interrupção de uma importação em lote, o administrador consegue retomar o processo do ponto exato de parada sem perda de progresso do lote.
- **SC-006**: A Página de Detalhes apresenta informações unificadas de todas as temporadas de uma obra sem duplicação ou inconsistência visual.
- **SC-007**: O sistema gera backups diários do banco local sem intervenção manual, garantindo recuperação dos dados em caso de falha de hardware.

---

## Assumptions

- O ambiente de execução é exclusivamente local (localhost); não há requisitos de escalabilidade multi-usuário, autenticação ou exposição à internet.
- A fonte de dados externa utilizada é a Jikan API v4 (API pública não oficial do MyAnimeList), que já está referenciada nos requisitos do projeto.
- O sistema operacional hospedeiro é compatível com a stack tecnológica do projeto (conforme definido em `docker-compose.yml` e `.env`).
- A pasta de destino dos backups diários está em caminho configurável pelo administrador via variável de ambiente.
- Mangás e light novels podem ter fontes de dados distintas ou limitadas na Jikan API; o comportamento de fallback para categorias com cobertura parcial será definido na fase de planejamento.
- A implementação das 3 Vitrines é **híbrida**: base de componentes compartilhada parametrizada por `tipo`, com variações conhecidas: (1) Light Novels usam capítulos como unidade de progresso, sem episódios; (2) Mangás podem consumir fontes de dados distintas; (3) Animes seguem o modelo base com episódios e temporadas.
- A navegação lateral entre títulos do mesmo grupo é baseada na ordem de exibição dos carrosséis da Vitrine.
- O Tema Escuro é fixo e não há opção de alternância para tema claro; esta é uma decisão de produto definitiva.
- A **Dashboard** (`localhost:3000/`) é pré-existente e contém exatamente 3 botões de navegação por tipo: Animes, Mangás e Light Novels. Ela não é coberta por este spec.
- A hierarquia de navegação é: Dashboard (`/`) → Vitrine tipo-específica (`/animes`, `/manga`, `/light_novels`) → sub-páginas (Página de Detalhes, Módulo de Progresso). Cada Vitrine é isolada por tipo de mídia, com o MediaConfig mapeando a rota plural `/animes` para a entidade singular `'anime'`.
- O spec cobre as três Vitrines tipo-específicas e suas sub-páginas, não a Dashboard em si.
