# Avaliação de advisor (Fable) — V1, V2 e roadmap — 2026-07-09

> **Status: ARQUIVADO — não incorporado.** Este relatório foi solicitado pelo João e produzido
> por um agente advisor (modelo Fable) que leu o projeto inteiro. **Decisão do João (2026-07-09):
> não levar as recomendações em consideração no rumo atual** — o documento fica só como registro.
> Nada aqui alterou `PRODUCT.md`, `ROADMAP.md` ou os ADRs.
>
> Nota posterior do João: **o problema da dobra de kit já foi corrigido** (a montante) — logo a
> premissa do relatório sobre o CMV inflado por kit está superada. Ver a sessão que tratar disso.

---

## Veredito em 3 linhas

O projeto está no rumo certo e com uma disciplina de documentação rara — a maior força é que cada versão nomeia a decisão que destrava. O maior risco não é técnico: é **comportamental** — a V2 vai pintar um número vermelho na tela quase todo dia (por construção, a convenção "100% da mídia → novos" só piora a aquisição), e um número vermelho diário cria pressão para frear a mídia **antes** de o projeto ter medido a recompra que justificaria não frear. E o segundo risco é de execução: a alavanca mais barata do projeto inteiro (encaminhar `docs/orientacao-base-itens-confiavel.md` pro time de Dados) está escrita e parada há 5 dias.

---

## V1 — o alicerce

**Veredito: firme para leitura de tendência, frouxo para leitura de sinal perto do zero.** A V1 é uma balança de banheiro boa — mostra se você engordou ou emagreceu (tendência), mas tem margem de erro de uns 2-3 quilos (nível). Para a decisão da V2 ("MC-novos é positiva ou negativa?"), o que importa é exatamente o **sinal** — e é aí que a margem de erro morde.

Os erros conhecidos, com direção:

| Erro | Direção | Tamanho (junho) | Fonte |
|---|---|---|---|
| Dobra de kit | MC **subestimada** | ~R$101k (~5-6% da MC) | ARCHITECTURE.md §6 |
| SKUs sem custo (137 zerados na 3.1, mitigados pelo fallback; resíduo sem custo em lugar nenhum) | MC **superestimada** | resíduo não quantificado | ADR 2026-07-09-fonte-custos |
| 136 pedidos em Vendas sem Itens (sem CMV) | MC **superestimada** | R$63k de venda sem custo (0,78%) | ARCHITECTURE.md §6 |
| Deduções em % médio (devolução 3,48%, frete 4,8%...) | direção **desconhecida** por segmento | — | PRODUCT-v1 §6 |

Dois pontos que podem enganar o João e que **ninguém escreveu ainda**:

1. **A dobra de kit não é neutra entre novos e recorrentes.** Kits do tipo "Compre 3 leve 4 + Carteira" são oferta clássica de **aquisição** — é o produto que o cliente novo compra. Se a dobra se concentra em pedidos com kit, ela infla o CMV **dos novos** desproporcionalmente. Ou seja: o erro de ~R$100k/mês não desconta 5% da MC-novos — pode descontar bem mais. A V2 vai medir a aquisição justamente com o termômetro mais quebrado no segmento que ela quer medir. Isso é verificável hoje com uma consulta: que % dos pedidos com SKU duplicado é `Primeira Compra`?

2. **As deduções em % médio viram premissa escondida quando você fatia.** Aplicar 3,48% de devolução sobre Vendas-novos assume que cliente novo devolve igual à média. Em moda, é o contrário do esperado: quem compra pela primeira vez erra tamanho/caimento mais do que quem recompra — a taxa de devolução do primeiro pedido tende a ser **maior** que a blended. Esse erro joga a MC-novos **para cima**, na direção oposta à dobra de kit. Dois erros grandes em direções opostas é a pior configuração possível: eles podem se cancelar ou se somar, e o João não sabe qual dos dois está acontecendo.

**Conclusão da frente A:** o alicerce sustenta a V2 **se** a MC-novos sair claramente longe do zero (digamos, mais de ±10% das Vendas-novos de distância). Se sair perto do zero, o verde/vermelho é ruído, não sinal — e a tela precisa dizer isso.

---

## V2 — as 4 escolhas

### 1. Herdar o `customer_type` da Shopify — **defensável, com dois senões não escritos**

A decisão é boa: point-in-time, histórico completo, sem viés de borda esquerda, automático no fluxo, 99,78% de cobertura. Eu faria igual. Mas o ADR vende dois benefícios que merecem desconto:

- **"Tira de nós a parte suja da chave" — não tira, terceiriza.** A Shopify identifica cliente por cadastro/e-mail. A pessoa que comprou com e-mail pessoal e recomprou com e-mail do trabalho é **dois clientes novos** para a Shopify. A sujeira da chave não sumiu; ela só passou a ser calculada pela Shopify com a mesma matéria-prima suja. Consequência: Pedidos-novos **superestimado** em taxa desconhecida (e o CAC, subestimado). Registrar como ressalva.
- **"Novo no Shopify", não "novo na Minimal"** — o PRODUCT.md registra isso. Mas a Minimal tem 4 outros canais. Um cliente do Mercado Livre que migra pro site é "Primeira Compra" — e a mídia dele pode ter sido paga meses atrás em outra conta. Ninguém mediu se a sobreposição é pequena.

**O que eu exigiria na spec:** um teste de aceite que valide que o carimbo é mesmo o campo nativo e não algo recalculado na camada de extração. Teste barato: pegar o total de "first-time customers" de junho no relatório nativo da Shopify Analytics e conferir contra os 19.513 da base. Se bater, confiança comprada; se não, a premissa central da V2 cai.

### 2. Convenção "100% da mídia → novos" — **defensável como conta, arriscada como semáforo**

Como convenção declarada, é honesta e melhor do que ratear por um critério inventado. Mas cria uma **assimetria de leitura** não explicitada:

- **Verde é sinal forte.** Se a MC-novos é positiva mesmo carregando a mídia inteira (inclusive remarketing que serve à recompra), a aquisição real é ainda melhor. Verde = pode confiar.
- **Vermelho é sinal ambíguo.** Pode ser aquisição ruim, ou só o remarketing sendo cobrado da conta errada. Vermelho = **investigar**, não frear.

Essa regra ("verde aja, vermelho investigue") deveria estar na tela ou no PRODUCT.md.

**O que eu faria diferente:** separar mídia de aquisição × remarketing **por nome de campanha** (prospecting vs. RMKT) é duas colunas a mais no export do BigQuery — 10% do esforço da V4, remove 80% da ambiguidade. Se a nomenclatura permitir, é uma V2.1 barata, não V4.

### 3. Régua "MC positiva na 1ª compra" — **defensável como piso de segurança, errada se virar pedal**

Como régua provisória de quem ainda não mediu a recompra, é certa — a True Classic só empata no 1º pedido porque **conhece** as coortes; a Minimal não. O erro possível está no uso: num negócio onde 48% dos pedidos de junho são recompra (17.996 de 37.593), decidir mídia por lucro-na-1ª-compra **sub-investe sistematicamente**. Três meses "segurando porque está vermelho" têm custo real e invisível se a V4 mostrar que o cliente se paga no mês 2.

**O que eu faria diferente:** enquadrar a V2 como **instrumento de observação, não de decisão de freio**. A única decisão que a V2 autoriza sozinha é a positiva ("verde → posso acelerar"). Frear exige V4.

### 4. Estreitar para só aquisição, adiando a recompra — **defensável, com desconto de R$0**

Escopo pequeno foi correto. Mas o critério de aceite exige a amarração `novos + recompra + sem-classificação = total` — o código **já vai calcular** MC-recompra pra conferir a soma, só não vai mostrar. Esconder um número já calculado que responde "quanto do meu Lucro Bruto vem de recompra?" é rigor de escopo virando desperdício.

**O que eu faria diferente:** uma **linha de rodapé**: "Recompra no período: X% das Vendas, Y% do Lucro Bruto". Não é coluna, é uma frase.

---

## Roadmap — a sequência

**A ordem V2→V3→V4 está conceitualmente certa**, e o ponto de parada na V4 é **sabedoria, não procrastinação** — os três gates (margem bruta real, recompra real, mandato) são os certos. Três problemas:

1. **A dependência escondida da V4 precisa ser disparada agora.** V4 exige e-mail/`customer_id` — que **não existe** em nenhuma aba hoje. Pedido a montante demora. Os três pedidos ao time de Dados (base de itens sem dobra, custos da 3.1, coluna de e-mail/customer_id) deveriam ir **num pacote só, esta semana**.
2. **A V3 é dois projetos com riscos opostos.** "Consertar a dobra de kit" depende do time de Dados; "os 4 custos que vazam" depende do Financeiro entregar número que não existe. **Partir em V3a (kit + custos reais que já existem) e V3b (os 4 vazamentos como % provisório).**
3. **A separação aquisição × remarketing está na versão errada.** Não depende de e-mail nem de coorte — depende de duas colunas na aba `Midia`. Mover para logo depois da V2.

---

## Os 3 movimentos que eu faria

1. **Hoje, antes de qualquer spec: mandar o pacote a montante** (orientação da base de itens + 137 SKUs + pedido de coluna e-mail/`customer_id`), num e-mail só. Maior alavancagem por minuto do projeto; destrava V3 e V4 em paralelo.
2. **Na spec da V2, três itens de aceite que faltam:** (a) validar o carimbo contra a Shopify Analytics (19.513 devem bater); (b) medir que % dos pedidos com dobra de kit é `Primeira Compra`; (c) o rodapé de recompra + a regra de leitura ("verde acelera, vermelho investiga").
3. **Promover a separação prospecting × remarketing para V2.1** — recalcular CAC/aROAS com a mídia de aquisição de verdade. A diferença entre um CAC "por convenção" e um que aguenta reunião de diretoria.

---

## A pergunta desconfortável

**"Se a MC-novos aparecer vermelha amanhã, quem tem autoridade para mexer no orçamento de mídia — e o que exatamente vai ser feito?"** A V2 vai colocar um verde/vermelho na tela em semanas. Sem mandato para agir, o projeto está construindo um velocímetro no banco do carona. Com mandato mas sem a regra de leitura, o risco é pior: agir errado com convicção. Responder por escrito, antes da spec da V2, custa um parágrafo.
