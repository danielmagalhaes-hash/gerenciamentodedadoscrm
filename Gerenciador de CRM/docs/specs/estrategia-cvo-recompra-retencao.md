# Estratégia CVO — Recompra e Retenção (Minimal Club)

> Documento vivo. Atualizado a cada fase aprovada pelo Daniel. Não avança de fase sem aprovação explícita.

**Status:** Fase 1 concluída · Fase 2 aprovada pelo Daniel (2026-07-23) · Fase 3 (Matriz de Comunicação) construída, aguardando aprovação final.

**North Star:** Receita last-click gerada pelos canais de CRM.
**Métricas de apoio:** LTV 180 dias · Taxa de Repetição · Taxa de Churn · Taxa de Reativação.

---

## Fase 1 — Fontes de dados

| Fonte                      | O que é                                                                                                               | Volume                                  |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| Pesquisa VIP               | Entrevistas qualitativas com clientes de alto valor, abr–mai/2026                                                     | 88 entrevistas                          |
| Pós-Compra                 | Pesquisa aplicada logo após a compra, no site                                                                         | 738 respostas                           |
| Jornada de Produto         | Comportamento sequencial de compra (produto 1 → 2 → 3...), `mc-growth/docs/sessions/2026-07-23-jornada-de-produto.md` | 233.157 clientes, 20 entradas elegíveis |
| Contexto de ofertas ativas | Fornecido pelo Daniel, 2026-07-23 (ver seção 4)                                                                       | —                                       |

### 1.1 Pesquisa VIP — achados-chave

- **JTBD central declarado:** *"O cliente da Minimal Club não compra roupa. Ele resolve um problema: ter um guarda-roupa funcional, básico e confiável sem gastar tempo ou energia com isso."*
- **Produto âncora:** camiseta de algodão egípcio — vetor de entrada e pilar de confiança.
- **3 pilares da fidelidade:** praticidade, durabilidade, caimento. Qualquer falha aqui = risco real de perda silenciosa.
- **Churn é silencioso:** o cliente que sai não reclama — simplesmente para de comprar. Não aparece em NPS, suporte ou Reclame Aqui.
(daniel) rever isso com a entrada das respostas de nps
  → **Claude:** revisado na seção 1.4. A frase acima ("não aparece em NPS") está desatualizada — o NPS existe e é coletado, mas depois de tirar assinatura do corte, ele NÃO antecipa claramente o churn (achado #7 revisado). O churn segue comportamentalmente silencioso; o NPS geral não preenche essa lacuna sozinho ainda.
- **Gatilhos de abandono:** queda de qualidade percebida, cobrança não comunicada, atendimento que não resolve (chatbot ineficaz), inconsistência de tamanho entre lotes/cores, excesso de comunicação (spam).
- **O que NÃO gera fidelidade sozinho:** desconto/promoção agressiva — *"a marca não pode fazer promoção o tempo todo se quer se posicionar como premium. 
- **2 arquétipos:**
  - **Executor Prático** — zero fricção, decide rápido, quer resolver o guarda-roupa de uma vez. Risco: qualquer atrito (site lento, chatbot, tamanho inconsistente).
(daniel) como eu consigo facilitar a jornada de compra desse cliente
  → **Claude:** direção pra Fase 3 (fica tático lá): atalho "comprar de novo" direto do e-mail/WhatsApp pro checkout com tamanho/cor já salvos (sem navegar o site), aviso automático de back-in-stock no tamanho certo, e resolver as fricções que a própria pesquisa já nomeou — chatbot ineficaz e demora até humano são, pra esse arquétipo, o que mais quebra a promessa de "zero atrito".
  - **Construtor Consistente** — pesquisa antes de comprar, mas quando decide é leal por entrega consistente ao longo do tempo. Risco: qualquer queda perceptível de qualidade.
(daniel) como eu consigo mostrar que meus produtos são os melhores do mercado? e fazer cross sell de produtos
  → **Claude:** prova específica por categoria, não genérica — atacar de frente o que a própria pesquisa levantou como crítica a OUTRAS marcas (desbota, encolhe, tamanho inconsistente) dizendo explicitamente "isso não acontece aqui", não deixando implícito. Sobre cross-sell: ver achado #2 revisado mais abaixo — o mecanismo certo não é bundle, é comunicação dedicada à categoria nova.
- **Oportunidades de produto citadas espontaneamente:** calça de alfaiataria de alta qualidade e blazer leve/versátil — produtos mais pedidos pra completar looks, ainda sub-explorados.
- **Fidelização:** 26 de 86 entrevistas elogiaram o modelo de clube de assinatura (hoje encerrado) — mencionado com frustração pela ausência.
(Daniel) como eu consigo desenvolver um produto de assinatura de forma diferente para a base?
  → **Claude:** pergunta boa, mas é decisão de PRODUTO/modelo de negócio, não de comunicação de CRM — sugiro parquear como workstream separado, fora do escopo da Matriz de Comunicação, pra não travar a Fase 3. Posso ajudar a pensar nisso depois, à parte.

### 1.2 Pós-Compra — achados-chave (738 respostas)

| Pergunta | Resultado |
|---|---|
| Primeira compra? | 59,3% sim / 40,7% não (já eram clientes) |
| **O que trouxe de volta** (recompra) | **59,8% "gostei das peças e quis comprar mais"** · 14,5% "recebi promoção/cupom" · 8,4% "vi lançamento novo" · 7,9% indicação |
| Motivo da compra | 24,7% "queria conhecer a marca" · 12,6% qualidade · 9,3% modelagem/caimento |
| Percepção de preço | 76,0% "justo" · 22,2% "caro" |
| Preferência por loja física | 49,8% "pra alguns produtos sim" · 24,5% "sim, gostaria" → **74,3% quer física pra algo** |
| Compra feita para quem | 80,8% pra mim · 12,3% pra outra pessoa · 6,9% pra mim e outra pessoa |
| Frequência de compra (Minimal) | 59,2% primeira compra · 22,1% 2-3x/ano · 14,1% 1x/ano |
| Outras marcas consideradas | 29,1% nenhuma · 17,2% Insider · 5,1% Reserva |
| **Sugestão de próximo produto (texto livre)** | **"Calça" domina disparado** (42 menções vs. 8 de camiseta) |

**Achado crítico #1:** a recompra é motivada por **confiança no produto (59,8%)**, não por incentivo financeiro (14,5%). Desconto pesado não é o motor principal de retenção — é a prova de qualidade repetida.
(daniel) - como eu faço os clientes acreditarem nos meus outros produtos. o que vejo é que quem compra camiseta compra camiseta de novo e com outros produtos é assim também. precisamos fazé-los confiar nos outros produtos.
  → **Claude:** confirmado com dado — ver achado #2 revisado na seção "Achados críticos consolidados".
**Achado crítico #2:** "calça" é o produto mais desejado como próxima compra — bate exatamente com o que a Jornada de Produto mede quantitativamente (ver 1.3).

### 1.3 Jornada de Produto — achados-chave

Fonte: `mc-growth/docs/sessions/2026-07-23-jornada-de-produto.md` (ver lá o dado completo, entrada por entrada).

- Camiseta Minimal domina a entrada: ~183 mil dos 233 mil clientes elegíveis (78%), em 4 buckets de quantidade (1/4/6/10 un + outras).
- **Retenção do produto de entrada (2ª compra) varia MUITO por tipo de entrada:**
  - Camiseta sozinha: 23-27% recompram a mesma família, em 92-139 dias de mediana.
  - **Combos voltam mais rápido, mas raramente repetem o MESMO combo**: Camiseta+Carteira volta em 34 dias (o mais rápido de todos), mas só 0,9% repete o combo exato — o produto que eles compram de novo, na maioria, é a Camiseta Minimal sozinha.
  - Calça Jeans 1.0 como entrada: retorno em 49 dias, 11,8% de retenção — 2º melhor tempo de retorno da base.
- **LTV 180 dias** varia de R$147 (Camiseta 1un, mediana) até R$880 (Camiseta+Social, mediana) — a entrada por combo tende a ter LTV mais alto que a entrada solo por camiseta unitária.
- **Taxa de reativação mais alta:** Camiseta+Cueca (18,1%) e Cueca solo (19,9%) — hipótese a validar: cueca como categoria "sempre precisa repor" pode ser um gatilho natural de reativação.
- **Achado a confirmar:** Polo 2.0 e Calça Comfort têm 0% de "inativo hoje" — possivelmente linhas lançadas recentemente (não deram tempo de gerar inativos ainda).
- Maioria não volta: 57-92% dos que entram, dependendo da entrada, nunca fazem 2ª compra — a maior alavanca de receita está aí, não na otimização de quem já repete.

### 1.4 NPS — cruzado com status do cliente e produto de entrada *(adicionado 2026-07-23, revisado após comentário do Daniel: assinatura excluída)*

Fonte: `Análises - Base de Dados Extras/Respostas de NPS - Minimal.xlsx`, filtrado a **`Tipo == "NPS Geral"`** (9.825 das 10.926 respostas — os 1.101 de "NPS Assinatura" foram descartados por decisão do Daniel, 2026-07-23), cruzado com `Todos os negócios - Minimal - BQ. v2.csv` pela data de cada resposta, mesma régua oficial de 6/11 meses. Script `Análises - Base de Dados Extras/analise_nps_cvo.py`.

**⚠️ Correção de dado (2026-07-23):** a 1ª versão desta seção misturava NPS Geral com NPS Assinatura e mostrava uma queda monotônica de nota (Ativo→Recente→Inativo) que eu apresentei como "achado crítico #7". **Ao excluir assinatura como o Daniel pediu, esse padrão desaparece.** Isso não invalida a existência de um achado — mostra que ele estava sendo puxado pelas respostas de assinatura (que provavelmente disparam justamente em momentos de cancelamento, um viés óbvio). Versão corrigida abaixo.

| Status na data da resposta | Nota média | % Promotor | % Detrator | Respostas |
|---|---:|---:|---:|---:|
| Ativo | 8,29 | 70,1% | 17,9% | 2.286 |
| Recente | **7,91** | 62,9% | 22,4% | 6.330 |
| Inativo | 8,32 | 65,6% | 17,6% | **125** |

**Achado crítico #7 (revisado): a leitura correta é o OPOSTO da versão original.** Clientes **recém-chegados dão nota mais baixa (7,91)** que clientes **ativos estabelecidos (8,29)** — a confiança sobe com o relacionamento, não cai (coerente com a Pesquisa VIP: "depois que acertei o tamanho, virou automático"). O grupo Inativo tem só 125 respostas — **amostra pequena demais e com viés de sobrevivência** (só quem ainda se dispõe a responder um NPS estando inativo; o detrator mais bravo provavelmente nem responde) — **não dá pra usar isso como gatilho preditivo de churn ainda**. Recomendação: não construir nenhum fluxo em cima da hipótese "NPS antecipa churn" até termos mais volume de resposta de clientes inativos, ou confirmarmos que o NPS Geral é disparado também pra quem não compra há tempos (não só pós-compra).

**NPS por produto de entrada** (7.501 respostas casadas com a Jornada de Produto, NPS Geral, mín. 10 respostas):

| Melhor NPS | Nota | Pior NPS | Nota |
|---|---:|---|---:|
| Overshirt | 8,59 | Polo 2.0 | 7,42 |
| Camiseta + Perfume | 8,56 | Camiseta + Camiseta Fitness | 7,45 |
| Camiseta Manga Longa | 8,55 | Camiseta + Jeans | 7,55 |
| Camiseta + Social | 8,50 | Cueca | 7,79 |

**Camiseta + Camiseta Fitness com nota baixa (7,45) continua batendo com a Pesquisa VIP** (durabilidade/odor). **Polo 2.0 segue a pior nota (7,42)** — candidato a revisão de qualidade antes de investir mídia nessa linha. Esses dois achados sobrevivem à correção acima (são por entrada, não por status de churn).

*Ressalva de dado: 1.393 respostas de NPS Geral não casaram com nenhuma compra na base (provavelmente diferença de e-mail entre sistemas) — não interpretar como "cliente sem compra".*

---

### 1.5 Contexto de ofertas ativas hoje (fornecido pelo Daniel, 2026-07-23)

| Régua | Público | Oferta |
|---|---|---|
| Welcome | Lead (nunca comprou) | 12% de desconto |
| Welcome | Cliente | **nenhuma** |
| Carrinho abandonado | Lead | 12% de desconto, oferecido direto/automático |
| Carrinho abandonado | Cliente | Até 7%, **só se o cliente pedir** (não automático) |
| Ofertas diversas | **Só lead** | Compre 3 leve 4 + carteira OU perfume de brinde · Comfort 14% off · Jeans + cueca (bundle) · "vários outros, só pra lead" |
| Outlet | Cliente | Não é desconto — produtos de ponta de estoque, preço já menor |
| Reativação (frios) | Cliente inativo | Kit 4 + cueca · Jeans + carteira — **"nada é muito bem desenhado"** (palavras do Daniel) |

**Achado crítico #3 (o gap estrutural):** o arsenal de incentivo hoje é quase 100% desenhado pra **aquisição** (lead). A base de clientes — onde mora toda a receita de recompra, LTV e a North Star deste projeto — não tem régua de oferta estruturada, só duas combinações soltas de reativação mal desenhadas e um outlet que não é bem uma "oferta" no sentido de CRM.

Isso cria uma tensão direta com o Achado crítico #1: se a recompra é motivada por confiança de produto (não desconto), a resposta certa **não é copiar a agressividade de desconto do lead pro cliente** — é desenhar incentivos e comunicação que reforcem PROVA e EXPANSÃO GUIADA (a calça, o próximo produto mais desejado) em vez de descontos genéricos. A Fase 3 vai propor isso.

---

## Fase 2 — Síntese

### 2.1 Jobs to be Done (JTBD)

Três JTBD distintos — um por momento do ciclo de vida (entrada, expansão, reativação). Cruzam o "porquê" da pesquisa com o "quando/o quê" da Jornada de Produto.

**JTBD 1 — Entrada (1ª compra)**
> Quando eu preciso renovar meu guarda-roupa básico mas não tenho tempo nem paciência pra testar várias marcas e arriscar dinheiro com caimento ou qualidade incertos, me ajude a comprar uma peça que eu **sei** que vai caber bem e durar — com risco baixo (preço acessível, devolução fácil, prova social real) — para que eu possa parar de pensar em roupa básica e voltar a focar no que importa (trabalho, treino, família).

**JTBD 2 — Expansão / Recompra (a maioria das compras seguintes)**
> Quando uma peça da Minimal já provou que entrega o prometido (não desbotou, não encolheu, o caimento se manteve), me ajude a expandir meu guarda-roupa com mais peças da mesma linha de confiança — sem precisar testar tudo de novo do zero — para que eu possa ter o guarda-roupa inteiro resolvido, em piloto automático, sem gastar energia decidindo.
> (daniel) - como eu consigo mostrar os produtos para o cliente. aqui está o grande centro, mixx de produto, cross sell
> → **Claude:** concordo — isso vira o EIXO PRINCIPAL da Matriz da Fase 3, não mais um loop entre outros. Ver achado #2 revisado.

**JTBD 3 — Reativação (cliente frio, >11 meses sem comprar)**
> Quando eu já esqueci a marca ou simplesmente não tive um motivo novo pra voltar, me ajude a lembrar por que eu confiava nela — com uma prova concreta (peça nova, melhoria real) e não um desconto genérico que me faça sentir "vendido" — para que eu possa voltar a ter meu guarda-roupa resolvido sem sentir que a marca perdeu o posicionamento premium.
> (daniel) como eu consigo agregar peça nova melhoria com incentivo
> → **Claude:** ver Loop 4 revisado abaixo — combinei sua correção (tratar como 1ª compra + countdown) com a ideia original (prova antes do desconto).

### 2.2 Use Case Map (mapa situacional)

Situações que efetivamente disparam compra ou recompra, cruzando pesquisa + dado transacional:

| Situação | Gatilho | Produto associado | Evidência |
|---|---|---|---|
| **Reposição de uniforme diário** | A peça do dia a dia está gasta ou o guarda-roupa "ficou sem opção" | Camiseta (kit 4/6/10) | VIP: "uso como uniforme diário" · Jornada: kit 4un é a maior entrada (84k clientes) |
| **Teste de baixo risco** | Viu anúncio/indicação, quer experimentar sem comprometimento | Camiseta 1un | Pós-Compra: 24,7% "queria conhecer a marca" · Jornada: entrada 1un tem o retorno mais rápido entre as solo (92 dias) |
| **Completar o look / expandir categoria** | Já confia na camiseta, quer resolver o resto do guarda-roupa | Calça (Jeans, Comfort, Alfaiataria) | Pós-Compra: "calça" domina sugestão de próximo produto (42 menções) · VIP: pede calça de alfaiataria e blazer · Jornada: Camiseta+Jeans e Calça Jeans 1.0 têm os melhores tempos de retorno |
| **Ocasião específica** | Evento, viagem, reunião — precisa de algo além do básico do dia a dia | Camisa social, Overshirt, Blazer (ainda não existe) | VIP: Overshirt "destaque positivo em eventos e reuniões" |
| **Presentear** | Compra não é (só) pra si | Combos, kits | Pós-Compra: 19,2% envolve "outra pessoa" |
| **Reposição de básico invisível** | Item que "sempre precisa repor" sem pensar muito | Cueca | Jornada: Cueca tem a maior taxa de reativação da base (19,9%) — hipótese: é o produto certo pra puxar quem sumiu |
| **Loja física como resolução de incerteza** | Insegurança sobre caimento de calça/peça estruturada | Calça, Alfaiataria | VIP + Pós-Compra: 74,3% quer física pra "alguns produtos" — calça é o caso mais citado |

### 2.3 Ficha de Diagnóstico Reforge

**Loop de Hábito Orgânico** (o que já acontece, sem CRM empurrar)

```
Gatilho interno                Ação                          Recompensa
(peça desgasta OU               Cliente entra direto           Confirmação, a cada lavagem/
guarda-roupa "sem opção",  →     no site "sem pensar"     →     uso, de que o produto entrega
rotina corrida gera a                                          o prometido (não desbota,
necessidade)                                                   não encolhe, caimento igual)
```
- Evidência: 59,8% dos que recompraram citaram só "gostei e quis comprar mais" — SEM estímulo de CRM.
- **Limitação real:** o loop orgânico é fraco em FREQUÊNCIA. Roupa básica não tem cadência viciante (não é feed social, é reposição). 57-92% dos que entram nunca voltam sozinhos — o loop orgânico sozinho não sustenta a North Star.

**Loops Manufaturados** (o que o CRM precisa construir pra simular/acelerar o loop)

1. **Loop de Consistência (pós-1ª compra → 2ª compra)** — reforçar a prova de qualidade no timing certo (92-139 dias pra camiseta solo; 34-64 dias pra quem entrou por combo/jeans). Gatilho artificial: lembrete + prova social, não desconto — coerente com o achado de que cupom não é o motor.
2. **Loop de Expansão Guiada (2ª/3ª compra → calça)** — em vez de cross-sell genérico ou bundle, fazer o cliente EXPERIMENTAR calça como compra própria (sozinha, não em combo — é assim que a categoria vira hábito, ver achado #2 revisado). Calça é o produto nº1 pedido espontaneamente e o que tem melhor tempo de retorno entre as categorias não-camiseta.
(daniel) em quanto tempo?
  → **Claude:** a concentração de cross-sell de calça pica na **2ª compra** e cai a cada compra seguinte (2,1% na 2ª → 1,2% na 3ª → 0,7% na 4ª, pra quem entrou por Camiseta 4un). A mediana de dias até a 2ª compra desse grupo é **139 dias**. Disparar o convite pra calça em torno de **90-140 dias após a entrada**, ANTES da 2ª compra acontecer — depois disso, o cliente já decidiu sozinho (voltar pra camiseta, na maioria) e fica mais difícil mudar o hábito.
3. **Loop de Reposição Invisível (Cueca como APOIO, não produto-fim)** — cueca tem a maior taxa de reativação medida (19,9%), mas o Daniel está certo: cueca sozinha tem ticket baixo (LTV 180d mediana R$351 solo) contra R$568 quando vem JUNTO com camiseta (Camiseta+Cueca). **Dado confirma a correção:** cueca funciona como elemento de apoio que PUXA o ticket pra cima dentro de uma oferta com camiseta como produto-foco (ex.: "leve uma cueca junto" dentro do fluxo de reativação de camiseta), nunca como headline sozinha.
(Daniel) - Entendo isso, mas na minha visão faz sentido eu trazer a cueca de forma mais importante do que só apenas ganhe, mas o produto foco não pode ser cueca, ele pode ser apoio. penso assim pois se não vamos ter tickets médio abaixo do normal para recompra.
  → **Claude:** exatamente essa correção que fiz acima, com o LTV comprovando. Cueca = apoio de alta conversão dentro de uma oferta ancorada em camiseta, não oferta própria.
4. **Loop de Prova + Incentivo com Urgência (reativação de frios) — revisado com a correção do Daniel.** Tratar o inativo como se fosse uma 1ª compra de novo (reset da régua), MAS a copy não parte de zero como um lead genuíno — ele já teve prova de qualidade antes, então a mensagem ancora em "lembra por que você confiava" + o que ele perdeu (lançamentos, melhorias de produto) + um incentivo real com **countdown/urgência** (não um desconto qualquer, oferta com prazo). É a fusão dos dois pontos: prova (o que mudou) E incentivo com peso de lead (porque ele "saiu" da base ativa e precisa do mesmo empurrão que traria um lead nunca-comprou), só que com a mensagem certa pra quem já confiou antes.

(daniel) - eu discordo em partes. acredito que deveríamos olhar para inativos como se fosse primeira compra. Eu preciso fazer ele a voltar. acredito que não pode ser toma esse desconto, mas sim uma comunicação onde eu eu mostro o que ele esqueceu e o que tem de novo e dou um incentivo com countdonw em oferta. 
  → **Claude:** incorporado acima. Concordo com a correção — é mais preciso que a versão original.

**Loops Suplementares** (reforço lateral, não centrais hoje)

- **Indicação/boca a boca** — ~10% do discovery vem de indicação, mas não existe programa formal de indicação. Oportunidade não explorada.
(daniel) isso precisa entrar em algum momento no modelo
  → **Claude:** confirmado — entra na Matriz da Fase 3 como loop suplementar formal (programa de indicação, provavelmente ativado a partir de clientes Ativos/promotores de NPS).
- **Presentear** — ~19% das compras envolvem outra pessoa; não há loop de "compre pra você, leve algo pra indicar/presentear".
- **Loja física como loop de confiança** — 74,3% quer física pra categorias de risco de fit (calça); a expansão de lojas (BH, e planos pra RJ/BSB/SP) é, na prática, um loop suplementar de confiança pra destravar a categoria nº1 de expansão.

---

## Achados críticos consolidados (pra decisão na Fase 3)

1. **Recompra é motivada por confiança no produto (59,8%), não por desconto (14,5%).** A comunicação de recompra deve liderar com prova, não com cupom.
2. **Cross-sell é estruturalmente fraco — confirmado com dado, o Daniel está certo.** Rodei a 2ª compra de TODAS as 20 entradas: em produtos-combo (Camiseta+X), a Camiseta Minimal vence o "X" como recompra em 100% dos casos (ex.: Camiseta+Jeans → 16,1% recompram Camiseta vs. 10,6% Jeans; Camiseta+Cueca → 29,4% vs. 12,2%). Em entradas SOLO de categoria própria (Jeans, Social, Henley, Overshirt, Polo, Comfort), a autorrepetição vence — quem entra por Calça Jeans 1.0 sozinha recompra Calça Jeans 1.0 (11,8%) mais que Camiseta (7,8%). **Conclusão revisada:** o problema não é "qual produto empurrar" — é que categorias fora da camiseta só criam hábito quando o cliente entra NELAS sozinho, não quando vêm de brinde/combo. Calça continua sendo o alvo certo (é onde a autorrepetição funciona e o retorno é rápido) — mas o mecanismo tem que ser fazer o cliente EXPERIMENTAR a calça como compra própria, não só incluir numa oferta combinada com camiseta.
3. **O arsenal de ofertas hoje é 100% viesado pra aquisição.** A base de clientes (recompra, LTV, North Star) não tem régua de incentivo estruturada — só 2 combos soltos de reativação "mal desenhados" e um outlet que não é bem oferta.
4. **Churn continua silencioso** — a hipótese de que o NPS antecipa esse silêncio NÃO se confirmou depois de excluir assinatura (achado #7 revisado, amostra de inativo pequena demais). A régua de Antigos Ativos (180-360D) segue dependendo do tempo desde a última compra como sinal principal, sem um proxy de sentimento validado ainda.
5. **Cueca tem a maior taxa de reativação medida (19,9%), mas como APOIO — não produto-foco** (ver Loop 3 revisado; ticket cai se cueca virar a oferta principal).
(daniel) como falei anteriormente. Dá para trabalhar melhor essa comunicação
  → **Claude:** de acordo, já revisado acima.
6. **Combos (Camiseta+Carteira, Camiseta+Jeans) trazem o cliente de volta mais rápido, mas ele raramente repete o combo exato** — o que ele repete é a camiseta. A comunicação de 2ª compra pra quem entrou por combo deve focar na camiseta (produto-âncora), não tentar vender o mesmo combo de novo.
7. **NPS por status: achado revisado, mais fraco do que eu disse.** Sem assinatura, Ativo (8,29) e Inativo (8,32) ficam praticamente empatados — a amostra de inativo (125) é pequena e tem viés (só detrator complacente responde). O achado que sobrevive é outro: Recente (7,91) é mais crítico que Ativo (8,29) — a confiança sobe com o tempo, não cai. Não usar "nota baixa" como gatilho de churn ainda.
8. **Camiseta + Camiseta Fitness e Polo 2.0 têm o pior NPS por entrada (7,44 e 7,43)** — a Pesquisa VIP já explica o motivo da Fitness (durabilidade/odor); vale resolver o produto antes de qualquer fluxo de expansão pra esses dois.

---

## Fase 3 — Matriz de Comunicação (O QUE, QUANDO, COMO)

> Fase 2 aprovada pelo Daniel em 2026-07-23. Eixo central desta matriz: o achado #2 revisado — cross-sell só gruda quando a categoria nova é vivida SOZINHA, não em bundle. Toda a lógica de "expansão" abaixo parte disso.

### 3.1 Fluxos Horizontais (Ciclo de Vida)

#### F=1 · Pós-Compra / Upsell Imediato (0–30D) — REVISADO após o Daniel trazer o dado de cohort

**Correção de fundo (2026-07-23, 3ª rodada):** eu estava tratando 0-30D como fase "sem oferta ainda". O Daniel apontou — e o dado confirma com força — que existe uma concentração real de recompra nos primeiros 30 dias, maior que deixar essa janela vazia. Medido na base inteira (233.157 clientes): **7,7% de TODA a entrada recompra em até 30 dias** — quase o dobro da janela seguinte de mesmo tamanho (30-60d = 3,5%). Por entrada, varia de 3,9% (Camiseta+Carteira) a **13,3% (Calça Comfort)** e 12,4% (Camiseta+Social). E o ritmo dentro do mês CRESCE (ex. Camiseta+Social: 2,8% na 1ª semana → 3,4% → 4,9% na 3ª/4ª semana) — não é um impulso de dia 1, é uma janela que esquenta até o dia 30.

**Isso muda o desenho:** 0-30D deixa de ser só conteúdo e ganha uma **oferta real, com prazo**, desenhada pra capturar essa recompra que o dado mostra que JÁ ia acontecer — não é o mesmo tipo de desconto genérico que o Achado #1 desaconselha (esse é constante, sem prazo, erode posicionamento). Aqui é o oposto: uma janela curta e cirúrgica, sobre uma demanda comprovada.

| Entrada | O QUE (ângulo) | QUANDO | COMO / oferta |
|---|---|---|---|
| Todas as entradas | Confirma que a escolha foi certa (prova de durabilidade) + oferece o combo **produto de entrada + 1 categoria nova**, com desconto, como o "passo 2" natural — não é upsell genérico, é convite a completar o guarda-roupa enquanto a decisão de compra ainda está "quente" | D+3 a D+5 (prova/cuidados, sem oferta ainda) → **D+10 abre a oferta de combo com desconto e prazo até D+30** (o crescimento da curva mostra que vale manter ativa a janela toda, com lembrete em D+20) | E-mail + WhatsApp. **Desconto real, mas com prazo definido** (não recorrente) — trata a demanda que já existe, não tenta criar uma nova |
| Camiseta+X (já veio de combo) | Mesma lógica, mas o combo da oferta pode reforçar a categoria "X" que já apareceu na entrada (em vez de introduzir uma 3ª categoria) | mesma janela D+10–D+30 | idem |
| Categoria solo (Jeans, Social, Henley, Overshirt, Polo, Comfort) | Mesma mecânica — Calça Comfort e Camiseta+Social são justamente as entradas com MAIOR recompra em 30d (13,3% e 12,4%), então essa régua vale ainda mais aqui | idem | idem |

*Nota: esta oferta some do desenho depois do D+30 — quem não converter aqui entra no fluxo "Recentes" (30-180D) abaixo, que já não usa mais desconto como motor principal (achado #1 volta a valer fora dessa janela específica).*

(daniel) pelo que eu entendi, aqui nós vamos tentar vender a camiseta com um produto novo dentro de um combo, certo? 
  → **Claude:** sim, isso mesmo — e essa versão revisada confirma exatamente o que você descreveu (combo entrada + categoria nova + desconto, dentro dos 30 dias). Minha primeira resposta pra você (abaixo, riscada) estava desatualizada; corrigida depois que você trouxe o dado de cohort.
#### Recentes (30–180D) — o fluxo mais importante da matriz

É aqui que mora o achado central: fazer a categoria nova ser **experimentada sozinha**, no timing certo de cada entrada.

**Revisado após o comentário do Daniel (linha abaixo) — o dado dá razão a ele:** LTV 180d de combo é sistematicamente MAIOR que solo (Camiseta+Social R$880 mediana, Camiseta+Jeans R$753 vs. Calça Jeans 1.0 solo R$369, Cueca solo R$351). Eu confundi duas coisas diferentes: "combo não gera HÁBITO de recompra da categoria X depois" (achado #2, isso é real) ≠ "combo é ruim pra ticket/LTV agora" (é o oposto — combo é melhor). Não são a mesma decisão.

**Recomendação corrigida:** manter o combo NA OFERTA (captura o ticket maior, comprovado), mas **testar como A/B** se acompanhar isso de conteúdo dedicado só à categoria nova (não a oferta — a COMUNICAÇÃO de reforço pós-combo) muda a taxa de recompra dela depois. Não sabemos ainda se o problema é a estrutura da oferta (combo) ou o fato de o cliente nunca ter recebido comunicação tratando "X" como categoria própria — só um teste real resolve isso.

| Entrada                                   | Janela de pico (dado real)                                            | O QUE                                                                                                                 | COMO / oferta                                                                                                                                                                    |
| ----------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Camiseta 1un / Camiseta+Carteira          | 34–92 dias                                                            | JTBD2: "você já confia, agora resolve o resto" — oferecer categoria nova, **testar A/B: solo vs. combo com camiseta** | Grupo A: incentivo só na categoria nova · Grupo B: combo camiseta+categoria (ticket maior, comprovado) — medir LTV 180d e recompra da categoria X no ciclo seguinte nos 2 grupos |
| Camiseta 4un/6un/outras                   | 90–140 dias (mediana 139d)                                            | Mesmo teste A/B, disparo concentrado nessa janela — reforço a cada 30-40 dias até a 2ª compra acontecer               | idem                                                                                                                                                                             |
| Combo (Camiseta+Jeans, +Social, +Fitness) | 64–84 dias                                                            | Aqui o "X" já apareceu no combo de entrada — reforçar ELE com conteúdo dedicado (não confundir com nova oferta)       | Convite pra levar mais 1 peça da linha "X" — pode vir em combo de novo (ticket) OU sozinha (teste), com conteúdo específico da categoria nos dois casos                          |
| Categoria solo (Jeans, Social, Henley...) | autorrepetição natural — não precisa empurrar, precisa não atrapalhar | Reforço de prova + sugestão de 2ª categoria (mesmo teste A/B combo x solo)                                            | Baixo volume, sem pressão comercial                                                                                                                                              |
(daniel) - porque aqui eu vou oferecer só a categoria nova, não faz sentido o combo? digo porque eu aumento o ticket médio aumentando o ltv 180 dias se eu "empurrar o segundo produto" 
  → **Claude:** você está certo, corrigido acima — combo tem LTV 180d maior em TODOS os casos que medi. Minha recomendação original ("nunca em combo") foi longe demais; o dado só prova que combo não gera repetição da categoria X depois, não que combo seja ruim pra ticket agora. Virou teste A/B, não uma regra fechada.
#### Antigos Ativos (180–360D) — revisado após discordância do Daniel (2026-07-23, 5ª rodada)

**Tamanho real da base:** 56.329 clientes (24,2% dos elegíveis) — o Daniel está certo em chamar de "o cluster mais importante do modelo": é o maior grupo ainda RECUPERÁVEL sem esforço pesado (Churn, >360D, é maior em volume — 126.023 — mas custa muito mais caro reativar, ver seção seguinte).

**Correção pedida pelo Daniel: essa base não é homogênea.** Segmentei os 26.962 eventos de retorno na janela 180-360D por quantas compras o cliente já tinha feito ANTES do intervalo:

| Segmento | Clientes | Camiseta Minimal | Calça Jeans 1.0 | Camiseta Fitness | Cueca |
|---|---:|---:|---:|---:|---:|
| **A — 1ª recompra pendente** (só tinha 1 compra antes) | 13.024 | 77,3% | 6,6% | 4,6% | 4,3% |
| **B — já recorrente** (2+ compras antes) | 11.281 | 73,8% | 10,5% | 8,9% | 6,7% |

**O Daniel está parcialmente certo:** clientes já recorrentes (Segmento B) têm de 40% a 60% mais chance relativa de recomprar categoria diferente de camiseta (Jeans 10,5% vs. 6,6%; Fitness 8,9% vs. 4,6%; Cueca 6,7% vs. 4,3%). **Mas camiseta ainda domina mesmo no Segmento B (73,8%)** — não é uma inversão, é um gradiente. A conclusão não é "só camiseta" nem "cross-sell domina" — é **liderar com camiseta para todos, mas dar peso real ao cross-sell especificamente pro Segmento B**, que já provou fidelidade e está mais aberto a experimentar.

**Por que essa base é o cluster mais importante — e por que a comunicação NÃO deve soar como "resgate":** a Pós-Compra mostra que, entre quem já é cliente, 89% compra só 1-3x por ano (22,1% "2-3x/ano" + 14,1% "1x/ano" de 40,8% que não são 1ª compra). **Um intervalo de 180-360 dias sem comprar é o ritmo NORMAL da maioria da base, não um sinal de alerta.** Tratar esse cliente como "sumiu, precisa ser resgatado" contraria o próprio dado — e a Pesquisa VIP avisa que excesso de comunicação/tom errado é gatilho de abandono. O tom certo é de continuidade natural ("faz um tempo que você não passa por aqui, olha o que tem de novo"), não de emergência.

**Ligando com o JTBD e os arquétipos (Fase 2):**
- **Segmento A** ainda está resolvendo o JTBD1→JTBD2 (provando a marca, decidindo se confia pra expandir) — perfil mais próximo do **Executor Prático**: liderar com camiseta (o que ele já testou e aprovou), prova de consistência, zero fricção pra recomprar (1-clique, tamanho salvo).
- **Segmento B** já está no JTBD2 pleno (expansão) e se aproxima do **Construtor Consistente** — já validou a marca em 2+ compras, é o cliente certo pra responder à pergunta que o próprio Daniel fez na Fase 2 ("como eu mostro que meus outros produtos são os melhores do mercado?"). Aqui a comunicação pode e deve mostrar categoria nova com prova específica (não desconto — achado #1 vale com força total aqui, ele já confia, não precisa ser comprado com cupom).

**O QUE (por segmento):**
- **Segmento A:** "a camiseta que você aprovou está esperando" — prova de consistência (mesma cor, mesmo caimento), sem desconto ainda.
- **Segmento B:** camiseta em 1º plano (ainda o produto mais seguro de vender) + **1 categoria específica em destaque com prova dedicada** (ex.: depoimento real da Pesquisa VIP sobre Calça de Alfaiataria ou Camisa Social — "não precisa passar, é respirável") — tratando o produto 2 como decisão própria, não bônus.

**QUANDO — ajustado por segmento, não só por dia:**
- Segmento A: reforço mensal, camiseta-first do dia 180 ao 360 inteiro — ele ainda não demonstrou abertura a outra categoria, não vale queimar o cartucho de cross-sell aqui ainda.
- Segmento B: pode iniciar o convite de cross-sell mais cedo (dia 180-220), já que o dado mostra mais receptividade — reforço quinzenal a partir do dia 220, escalando pra oferta com prazo (não desconto raso) nos últimos 60 dias antes de virar Inativo.

**COMO:** e-mail + WhatsApp nos dois segmentos; **sem desconto até os últimos ~60-90 dias da janela** (achado #1 — este cliente confia, não precisa de cupom pra voltar); quando a oferta entrar, ela é sobre a CATEGORIA em destaque (Segmento B) ou sobre camiseta (Segmento A), nunca genérica "olha nossos produtos".

**⚠️ Limite do dado — por que isso vira A/B, não uma regra fechada (pedido do Daniel, 2026-07-23, 6ª rodada):** tudo acima (camiseta domina) é dado HISTÓRICO — descreve o que aconteceu quando a marca nunca empurrou cross-sell de verdade pra esse segmento. Não prova que é o que o cliente PREFERE; pode só provar que camiseta é o caminho de menor resistência quando nada mais é oferecido com força. O Daniel aposta que, olhando pra frente, vale jogar o jogo de diversificação mesmo assim. Só um teste real resolve essa dúvida — não dá pra decidir isso só com dado histórico observacional.

**Desenho do teste A/B (Antigos Ativos, os 2 segmentos):**
- **Grupo Controle:** régua camiseta-first como desenhada acima.
- **Grupo Teste:** régua cross-sell-first — categoria nova em destaque desde o início da janela (dia 180), com a mesma prova dedicada por categoria, mesmo pro Segmento A.
- **Métrica de decisão:** taxa de repetição (achado #1 do North Star) + se quem converte no Teste também repete a categoria nova na compra seguinte (validaria se cross-sell cria hábito de verdade, não só uma venda pontual — liga direto ao achado #2).
- **Tamanho de amostra:** sobra volume (56.329 clientes) pra um teste estatisticamente válido rodando os 2 segmentos em paralelo.
- **Decisão após o teste:** se Teste bater Controle em taxa de repetição SEM perder LTV, camiseta-first deixa de ser a regra padrão pro Segmento B (e possivelmente A).

#### Churn / Inativo (>360D) — aprofundado a pedido do Daniel (2026-07-23, 4ª rodada)

**É a MAIOR base da empresa: 126.023 clientes (54,1% dos elegíveis).** Qualquer ganho percentual pequeno aqui move mais receita absoluta que em qualquer outro segmento — justifica o nível de agressividade de oferta que o Daniel já havia defendido.

**O mesmo achado de Antigos Ativos se repete aqui, ainda mais forte:** nos 24.047 eventos de retorno depois de 360+ dias parado, a compra de reativação também é dominada por Camiseta Minimal — inclusive pra quem nunca tinha entrado por ela (ex.: Camisa Social Tech Classics solo volta 39,1% Camiseta Minimal vs. 19,1% a própria categoria; Camiseta Fitness solo volta 45,7% Camiseta vs. 33,6% Fitness). **Conclusão: o produto que reativa quase sempre é a Camiseta Minimal — a comunicação de reativação deve vender CAMISETA, com cueca como apoio (achado já validado), não "o que há de novo" de forma genérica.**

- **O QUE:** aplica a correção do Daniel (tratar como 1ª compra + prova + incentivo com countdown), mas agora com o produto certo: **Camiseta Minimal como herói da oferta** (kit com desconto real, cueca como apoio dentro do kit) + copy "lembra por que você confiava" + o que mudou desde que ele sumiu.
- **QUANDO:** dispara no D+360 exato (o momento em que sai de Antigos Ativos); intenso nos primeiros 30-60 dias de inatividade oficial, depois esporádico (trimestral) — mantém o Efeito Plinko ativo mesmo sem conversão imediata.
- **COMO:** e-mail agressivo (nível-lead: kit Camiseta com desconto real, cueca de apoio) + WhatsApp direto. Countdown real (48-72h), não decorativo. Dado o tamanho da base (126 mil), *vale segmentar por LTV histórico do cliente antes de decidir a profundidade do desconto — quem tinha LTV alto antes de sumir merece uma oferta mais forte que quem comprou uma vez só*.

### 3.2 Fluxos Verticais (Apoio ao Funil)

| Régua | Situação hoje | Recomendação Fase 3 |
|---|---|---|
| Welcome (F=0) | 12% lead / 0% cliente | Manter — funciona pra aquisição (preço "justo" pra 76% da base) |
| Abandono de Site / Navegação / Categoria | Sem oferta pra cliente | Manter sem oferta pra cliente recorrente (confiança > desconto) — só reforço de prova |
| Carrinho/Checkout | Lead: 12% automático · Cliente: até 7% só se pedir | **Testar automatizar um nível leve pra cliente** (não os 7% manuais — algo tipo frete grátis SE for a 1ª peça de uma categoria nova), pra medir se destrava cross-sell |
~~Back in Stock, Funnel Flusher e Traffic Cop~~ — **removidos do escopo desta rodada por decisão do Daniel (2026-07-23).**
### 3.3 Campanhas

- Segmentação: 4 estágios CXL × engajamento ativo/inativo, cruzando com produto de entrada quando fizer sentido tático (ex.: campanha de lançamento de calça mirando quem está na janela de pico de expansão).
- **Campanha de prova social:** usar os depoimentos reais da Pesquisa VIP como copy (ex.: "não desbota, não encolhe, não cria bolinha" — linguagem do próprio cliente, não da marca).
- **Campanha de indicação (piloto):** mirar clientes Ativos e Promotores de NPS — loop suplementar confirmado no Fase 2.
- **Atenção de produto antes de campanha:** não investir mídia/campanha em Camiseta+Fitness ou Polo 2.0 até revisar a queda de NPS nessas linhas (achado #8) — campanha amplificaria um problema de produto, não de comunicação.
  (daniel) - vamos deixar essa por último, mas aqui eu vejo outra estratégia
  → **Claude:** ok, despriorizado — fica em aberto pra você trazer sua estratégia alternativa quando fizer sentido, não bloqueia o resto da Fase 3.

---

## Próximo passo

**Fase 3 construída — aguardando leitura e aprovação final do Daniel.** Pontos que dependem de teste/validação antes de virar régua definitiva: automação do desconto de carrinho pra cliente (3.2), e a nova cadência de Antigos Ativos em degrau (3.1).
