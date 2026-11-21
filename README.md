# RentSmart – R.M Imóveis

Aplicação em Python que calcula o orçamento de locação da R.M Imóveis, aplica as regras comerciais
(adicionais, descontos e taxa contratual), exibe um resumo detalhado e gera um CSV com a projeção
dos 12 primeiros meses.

## Requisitos
- Python 3.8 ou superior
- Nenhuma biblioteca externa (usa apenas a biblioteca padrão)

## Como executar
```bash
python rentsmart.py
```
Responda às perguntas no terminal (tipo de imóvel, quartos, garagem, crianças e parcelas da taxa).
Ao final, o arquivo `projecao_12_meses.csv` é criado na pasta atual.

## Regras implementadas
| Item | Regra |
|---|---|
| Aluguel-base | Apartamento 1 quarto: R$ 700 · Casa 1 quarto: R$ 900 · Estúdio: R$ 1.200 |
| 2 quartos | Apartamento: +R$ 200 · Casa: +R$ 250 (estúdio possui apenas 1 quarto) |
| Garagem (casa/apto) | 1 vaga por +R$ 300/mês |
| Garagem (estúdio) | Pacote inicial de 2 vagas: R$ 250 · vagas extras: R$ 60 cada |
| Desconto | Apartamento sem crianças: 5% sobre o aluguel já com os adicionais |
| Taxa contratual | R$ 2.000, parcelável em 1 a 5 vezes, tratada separadamente do aluguel |

## Decisões e premissas
- **Estúdio:** ao pedir vagas, 1 ou 2 vagas custam o pacote inicial (R$ 250); a partir da 3ª, +R$ 60 cada. Informar 0 significa sem garagem.
- **Desconto:** os 5% incidem sobre aluguel-base + adicionais (2 quartos e garagem).
- **Taxa contratual:** dividida em parcelas iguais; a última absorve a diferença de centavos. As parcelas são cobradas nos primeiros meses, somadas ao aluguel na projeção.
- **Valores monetários:** uso de `Decimal` para evitar erros de ponto flutuante.

## Estrutura do código (POO)
- `Imovel` (classe abstrata) → `Apartamento`, `Casa`, `Estudio`: cada uma com suas regras de adicionais, validação e desconto (polimorfismo).
- `TaxaContratual`: valor e parcelamento.
- `Orcamento`: calcula o aluguel mensal, o resumo e a projeção, e exporta o CSV.
- Funções de interface validam as entradas do usuário.

## Arquivo CSV
Colunas: Mês · Aluguel mensal · Parcela da taxa contratual · Total do mês · Total acumulado.
Usa `;` como separador, vírgula decimal e codificação UTF-8 com BOM, para abrir corretamente no Excel em português.

## Exemplo de uso
Apartamento, 2 quartos, com garagem, sem crianças, taxa em 3x → aluguel mensal de **R$ 1.140,00**
(R$ 700 + R$ 200 + R$ 300 = R$ 1.200, menos 5%) e total no primeiro ano de **R$ 15.680,00**.
