import sys
import heapq
import yaml


class Gerador:
    # Congruente linear: X = (a*X + c) mod M
    def __init__(self, semente=None, quantidade=0, lista=None):
        self.a = 1664525
        self.c = 1013904223
        self.M = 2 ** 32
        self.x = semente
        self.lista = lista
        self.limite = len(lista) if lista else quantidade
        self.usados = 0

    def acabou(self):
        return self.usados >= self.limite

    def proximo(self):
        if self.lista:
            r = self.lista[self.usados]
        else:
            self.x = (self.a * self.x + self.c) % self.M
            r = self.x / self.M
        self.usados += 1
        return r

    def uniforme(self, a, b):
        return a + (b - a) * self.proximo()


class Fila:
    def __init__(self, nome, cfg):
        self.nome = nome
        self.servidores = cfg["servers"]
        self.capacidade = cfg.get("capacity")
        self.min_chegada = cfg.get("minArrival")
        self.max_chegada = cfg.get("maxArrival")
        self.min_servico = cfg["minService"]
        self.max_servico = cfg["maxService"]
        self.estado = 0
        self.perdas = 0
        self.tempos = {}
        self.destinos = []

    def cabe(self):
        return self.capacidade is None or self.estado < self.capacidade

    def kendall(self):
        k = f"/{self.capacidade}" if self.capacidade is not None else ""
        return f"G/G/{self.servidores}{k}"


class Simulador:
    def __init__(self, modelo, gerador):
        self.gerador = gerador
        self.filas = {n: Fila(n, c) for n, c in modelo["queues"].items()}
        for rota in modelo.get("network") or []:
            self.filas[rota["source"]].destinos.append((rota["target"], rota["probability"]))
        self.tempo = 0.0
        self.escalonador = []
        self.seq = 0
        for nome, t in modelo["arrivals"].items():
            self.agenda(t, "CHEGADA", nome)

    def agenda(self, t, tipo, origem, destino=None):
        self.seq += 1
        heapq.heappush(self.escalonador, (t, self.seq, tipo, origem, destino))

    def acumula(self, t):
        for f in self.filas.values():
            f.tempos[f.estado] = f.tempos.get(f.estado, 0.0) + (t - self.tempo)
        self.tempo = t

    def roteia(self, fila):
        if not fila.destinos:
            return None
        if len(fila.destinos) == 1 and fila.destinos[0][1] >= 1.0:
            return fila.destinos[0][0]
        r = self.gerador.proximo()
        soma = 0.0
        for destino, p in fila.destinos:
            soma += p
            if r < soma:
                return destino
        return None

    def agenda_atendimento(self, fila):
        if self.gerador.acabou():
            return
        destino = self.roteia(fila)
        if self.gerador.acabou():
            return
        t = self.tempo + self.gerador.uniforme(fila.min_servico, fila.max_servico)
        if destino is None:
            self.agenda(t, "SAIDA", fila.nome)
        else:
            self.agenda(t, "PASSAGEM", fila.nome, destino)

    def entra(self, fila):
        if fila.cabe():
            fila.estado += 1
            if fila.estado <= fila.servidores:
                self.agenda_atendimento(fila)
        else:
            fila.perdas += 1

    def sai(self, fila):
        fila.estado -= 1
        if fila.estado >= fila.servidores:
            self.agenda_atendimento(fila)

    def chegada(self, fila):
        self.entra(fila)
        if not self.gerador.acabou():
            t = self.tempo + self.gerador.uniforme(fila.min_chegada, fila.max_chegada)
            self.agenda(t, "CHEGADA", fila.nome)

    def executa(self):
        while self.escalonador and not self.gerador.acabou():
            t, _, tipo, origem, destino = heapq.heappop(self.escalonador)
            self.acumula(t)
            if tipo == "CHEGADA":
                self.chegada(self.filas[origem])
            elif tipo == "SAIDA":
                self.sai(self.filas[origem])
            else:
                self.sai(self.filas[origem])
                self.entra(self.filas[destino])

    def relatorio(self):
        for f in self.filas.values():
            print("=" * 55)
            print(f"Fila: {f.nome} ({f.kendall()})")
            if f.min_chegada is not None:
                print(f"Chegada: {f.min_chegada} ... {f.max_chegada}")
            print(f"Atendimento: {f.min_servico} ... {f.max_servico}")
            print("-" * 55)
            print(f"{'Estado':>8}{'Tempo':>20}{'Probabilidade':>20}")
            maximo = f.capacidade if f.capacidade is not None else max(f.tempos)
            for e in range(maximo + 1):
                tempo = f.tempos.get(e, 0.0)
                print(f"{e:>8}{tempo:>20.4f}{100 * tempo / self.tempo:>19.2f}%")
            print(f"\nPerdas: {f.perdas}\n")
        print("=" * 55)
        print(f"Tempo global da simulacao: {self.tempo:.4f}")
        print(f"Aleatorios utilizados: {self.gerador.usados}")
        print("=" * 55)


def carrega_modelo(arquivo):
    with open(arquivo, encoding="utf-8") as f:
        texto = f.read()
    if "!PARAMETERS" in texto:
        texto = texto.split("!PARAMETERS", 1)[1]
    return yaml.safe_load(texto)


def main():
    if len(sys.argv) < 2:
        print("uso: python simulador.py <modelo.yml>")
        return
    modelo = carrega_modelo(sys.argv[1])
    sementes = modelo.get("seeds")
    if sementes:
        geradores = [(s, Gerador(semente=s, quantidade=modelo["rndnumbersPerSeed"])) for s in sementes]
    else:
        geradores = [(None, Gerador(lista=modelo["rndnumbers"]))]
    for semente, gerador in geradores:
        if semente is not None:
            print(f"\n##### Simulacao com semente {semente} #####")
        sim = Simulador(modelo, gerador)
        sim.executa()
        sim.relatorio()


if __name__ == "__main__":
    main()
