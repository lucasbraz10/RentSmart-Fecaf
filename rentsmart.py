import csv
from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP

CENTAVOS = Decimal("0.01")
MESES_PROJECAO = 12


# --------------------------------------------------------------------------
# Utilitários
# --------------------------------------------------------------------------
def arredondar(valor):
    """Arredonda para 2 casas decimais (centavos)."""
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def moeda(valor):
    """Formata como moeda brasileira: R$ 1.234,56."""
    texto = f"{arredondar(valor):,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def numero_csv(valor):
    """Formata número para o CSV com vírgula decimal (padrão do Excel BR)."""
    return f"{arredondar(valor):.2f}".replace(".", ",")


# --------------------------------------------------------------------------
# Imóveis
# --------------------------------------------------------------------------
class Imovel(ABC):
    """Classe base: define o contrato comum a todos os tipos de imóvel."""

    TIPO = ""
    ALUGUEL_BASE = Decimal("0")

    def __init__(self, quartos, vagas):
        self.quartos = quartos
        self.vagas = vagas
        self._validar()

    @abstractmethod
    def _validar(self):
        """Valida os atributos conforme as regras do tipo de imóvel."""

    @abstractmethod
    def adicionais(self):
        """Retorna lista de tuplas (descrição, valor) dos adicionais."""

    def desconto(self):
        """Desconto aplicado sobre o aluguel. Por padrão, não há desconto."""
        return Decimal("0"), ""

    def total_adicionais(self):
        return sum((valor for _, valor in self.adicionais()), Decimal("0"))

    def aluguel_bruto(self):
        """Aluguel-base + adicionais (antes do desconto)."""
        return self.ALUGUEL_BASE + self.total_adicionais()

    def descricao(self):
        return f"{self.TIPO} de {self.quartos} quarto(s)"


class _ImovelComVagaUnica(Imovel):
    """Comportamento comum a casas e apartamentos (1 ou 2 quartos, 0/1 vaga)."""

    ADICIONAL_2_QUARTOS = Decimal("0")
    ADICIONAL_GARAGEM = Decimal("300.00")

    def _validar(self):
        if self.quartos not in (1, 2):
            raise ValueError("Escolha 1 ou 2 quartos.")
        if self.vagas not in (0, 1):
            raise ValueError("Casas e apartamentos aceitam no máximo 1 vaga.")

    def adicionais(self):
        itens = []
        if self.quartos == 2:
            itens.append(("Adicional de 2 quartos", self.ADICIONAL_2_QUARTOS))
        if self.vagas == 1:
            itens.append(("Vaga de garagem", self.ADICIONAL_GARAGEM))
        return itens


class Apartamento(_ImovelComVagaUnica):
    TIPO = "Apartamento"
    ALUGUEL_BASE = Decimal("700.00")
    ADICIONAL_2_QUARTOS = Decimal("200.00")
    PERCENTUAL_DESCONTO = Decimal("0.05")

    def __init__(self, quartos, vagas, possui_criancas):
        self.possui_criancas = possui_criancas
        super().__init__(quartos, vagas)

    def desconto(self):
        """5% sobre o aluguel após aplicar os adicionais, se não houver crianças."""
        if not self.possui_criancas:
            valor = arredondar(self.aluguel_bruto() * self.PERCENTUAL_DESCONTO)
            return valor, "Desconto de 5% (sem crianças)"
        return Decimal("0"), ""


class Casa(_ImovelComVagaUnica):
    TIPO = "Casa"
    ALUGUEL_BASE = Decimal("900.00")
    ADICIONAL_2_QUARTOS = Decimal("250.00")


class Estudio(Imovel):
    TIPO = "Estúdio"
    ALUGUEL_BASE = Decimal("1200.00")
    PACOTE_INICIAL_VAGAS = 2
    VALOR_PACOTE_INICIAL = Decimal("250.00")
    VALOR_VAGA_EXTRA = Decimal("60.00")

    def __init__(self, vagas):
        super().__init__(quartos=1, vagas=vagas)

    def _validar(self):
        if self.vagas < 0:
            raise ValueError("O número de vagas não pode ser negativo.")

    def adicionais(self):
        itens = []
        if self.vagas > 0:
            itens.append((f"Pacote inicial de {self.PACOTE_INICIAL_VAGAS} vagas",
                          self.VALOR_PACOTE_INICIAL))
            extras = max(0, self.vagas - self.PACOTE_INICIAL_VAGAS)
            if extras:
                itens.append((f"{extras} vaga(s) adicional(is) x {moeda(self.VALOR_VAGA_EXTRA)}",
                              self.VALOR_VAGA_EXTRA * extras))
        return itens

    def descricao(self):
        return "Estúdio"


# --------------------------------------------------------------------------
# Taxa contratual
# --------------------------------------------------------------------------
class TaxaContratual:
    """Taxa de contrato (R$ 2.000,00), parcelável em até 5 vezes.

    É tratada separadamente do aluguel mensal.
    """

    VALOR = Decimal("2000.00")
    MAX_PARCELAS = 5

    def __init__(self, parcelas):
        if not 1 <= parcelas <= self.MAX_PARCELAS:
            raise ValueError(f"Parcelas devem estar entre 1 e {self.MAX_PARCELAS}.")
        self.parcelas = parcelas

    def valor_parcela(self, numero):
        """Valor da parcela `numero` (1..n). A última absorve a diferença de centavos."""
        if not 1 <= numero <= self.parcelas:
            return Decimal("0")
        base = arredondar(self.VALOR / self.parcelas)
        if numero == self.parcelas:
            return self.VALOR - base * (self.parcelas - 1)
        return base


# --------------------------------------------------------------------------
# Orçamento
# --------------------------------------------------------------------------
class Orcamento:
    """Reúne imóvel e taxa contratual, calcula valores e gera saídas."""

    def __init__(self, imovel, taxa):
        self.imovel = imovel
        self.taxa = taxa

    def aluguel_mensal(self):
        desconto, _ = self.imovel.desconto()
        return self.imovel.aluguel_bruto() - desconto

    def projecao(self):
        """Lista de dicts com os pagamentos de cada um dos 12 primeiros meses."""
        linhas, acumulado = [], Decimal("0")
        for mes in range(1, MESES_PROJECAO + 1):
            aluguel = self.aluguel_mensal()
            parcela = self.taxa.valor_parcela(mes)
            total = aluguel + parcela
            acumulado += total
            linhas.append({"mes": mes, "aluguel": aluguel, "taxa": parcela,
                           "total": total, "acumulado": acumulado})
        return linhas

    def total_primeiro_ano(self):
        return self.projecao()[-1]["acumulado"]

    def resumo(self):
        im = self.imovel
        desconto, desc_txt = im.desconto()
        larg = 52
        linhas = ["", "=" * larg, "ORÇAMENTO DE LOCAÇÃO - R.M IMÓVEIS".center(larg),
                  "=" * larg, f"Imóvel: {im.descricao()}", "",
                  f"{'Aluguel-base':<34}{moeda(im.ALUGUEL_BASE):>18}"]
        for nome, valor in im.adicionais():
            linhas.append(f"{'+ ' + nome:<34}{moeda(valor):>18}")
        linhas.append(f"{'Subtotal':<34}{moeda(im.aluguel_bruto()):>18}")
        if desconto > 0:
            linhas.append(f"{'- ' + desc_txt:<34}{moeda(desconto):>18}")
        linhas += ["-" * larg,
                   f"{'ALUGUEL MENSAL':<34}{moeda(self.aluguel_mensal()):>18}",
                   "", "TAXA CONTRATUAL (cobrada à parte do aluguel)",
                   f"{'Valor total':<34}{moeda(self.taxa.VALOR):>18}",
                   f"{'Parcelamento':<34}{str(self.taxa.parcelas) + 'x':>18}"]
        for n in range(1, self.taxa.parcelas + 1):
            linhas.append(f"{'  Parcela ' + str(n):<34}{moeda(self.taxa.valor_parcela(n)):>18}")
        linhas += ["-" * larg,
                   f"{'Total no 1º ano (12 meses)':<34}{moeda(self.total_primeiro_ano()):>18}",
                   "=" * larg]
        return "\n".join(linhas)

    def exportar_csv(self, caminho="projecao_12_meses.csv"):
        """Gera o CSV (separador ';', compatível com Excel em português)."""
        cabecalho = ["Mês", "Aluguel mensal (R$)", "Parcela taxa contratual (R$)",
                     "Total do mês (R$)", "Total acumulado (R$)"]
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arq:
            escritor = csv.writer(arq, delimiter=";")
            escritor.writerow(cabecalho)
            for l in self.projecao():
                escritor.writerow([l["mes"], numero_csv(l["aluguel"]), numero_csv(l["taxa"]),
                                   numero_csv(l["total"]), numero_csv(l["acumulado"])])
        return caminho


# --------------------------------------------------------------------------
# Interface de terminal (com validação de entradas)
# --------------------------------------------------------------------------
def ler_opcao(pergunta, opcoes):
    """Pede um valor até que esteja entre as opções válidas (dict texto->valor)."""
    while True:
        resposta = input(pergunta).strip().lower()
        if resposta in opcoes:
            return opcoes[resposta]
        print(f"  Entrada inválida. Opções: {', '.join(opcoes)}.")


def ler_inteiro(pergunta, minimo, maximo=None):
    while True:
        try:
            valor = int(input(pergunta).strip())
            if valor >= minimo and (maximo is None or valor <= maximo):
                return valor
        except ValueError:
            pass
        faixa = f"entre {minimo} e {maximo}" if maximo is not None else f"maior ou igual a {minimo}"
        print(f"  Entrada inválida. Digite um número inteiro {faixa}.")


def montar_imovel():
    tipo = ler_opcao("Tipo de imóvel [1] Apartamento  [2] Casa  [3] Estúdio: ",
                     {"1": "apartamento", "2": "casa", "3": "estudio"})
    sim_nao = {"s": True, "n": False}

    if tipo == "estudio":
        print("(Estúdio: pacote inicial de 2 vagas = R$ 250,00; extras = R$ 60,00 cada)")
        vagas = ler_inteiro("Quantidade de vagas (0 se não deseja): ", 0)
        return Estudio(vagas)

    quartos = ler_inteiro("Número de quartos (1 ou 2): ", 1, 2)
    vagas = 1 if ler_opcao("Deseja vaga de garagem? (s/n): ", sim_nao) else 0
    if tipo == "casa":
        return Casa(quartos, vagas)
    criancas = ler_opcao("Haverá crianças no imóvel? (s/n): ", sim_nao)
    return Apartamento(quartos, vagas, criancas)


def main():
    print("=== RentSmart - R.M Imóveis ===\n")
    imovel = montar_imovel()
    parcelas = ler_inteiro(f"Parcelas da taxa contratual (1 a {TaxaContratual.MAX_PARCELAS}): ",
                           1, TaxaContratual.MAX_PARCELAS)
    orcamento = Orcamento(imovel, TaxaContratual(parcelas))
    print(orcamento.resumo())
    caminho = orcamento.exportar_csv()
    print(f"\nProjeção dos 12 meses salva em: {caminho}")


if __name__ == "__main__":
    main()
