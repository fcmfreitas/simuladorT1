# Simulador de Rede de Filas

Simulador de eventos discretos para redes de filas G/G/c/K, com chegadas e atendimentos uniformes e roteamento probabilístico entre filas. O modelo é lido de um arquivo `.yml` no mesmo formato do simulador do módulo 3.

## Requisitos

- PyYAML: `pip install pyyaml`

## Como executar

```
python simulador.py modelo_t1.yml
```

## Formato do arquivo de entrada

```yaml
arrivals:          # fila que recebe chegadas externas e tempo da 1ª chegada
   Q1: 2.0

queues:
   Q1:
      servers: 1
      capacity: 5      # opcional (sem capacity = capacidade infinita)
      minArrival: 2.0  # só para filas com chegada externa
      maxArrival: 4.0
      minService: 1.0
      maxService: 2.0

network:           # roteamento; o que faltar para somar 1 é saída do sistema
-  source: Q1
   target: Q2
   probability: 0.2

# opção 1: gerador congruente linear com semente(s)
rndnumbersPerSeed: 100000
seeds:
- 1

# opção 2: lista fixa de aleatórios (usada só se não houver 'seeds')
rndnumbers:
- 0.2176
- 0.0103
```

## Funcionamento

- Gerador congruente linear: `X = (a*X + c) mod M`, com a = 1664525, c = 1013904223, M = 2^32.
- Eventos: `CHEGADA` (externa), `SAIDA` (deixa o sistema) e `PASSAGEM` (vai de uma fila para outra).
- Cada sorteio de chegada, atendimento ou roteamento consome um aleatório. A simulação termina quando todos os aleatórios são usados.
- Ao final, mostra para cada fila o tempo acumulado e a probabilidade de cada estado, o número de perdas e o tempo global da simulação.
- Com várias sementes, é feita uma simulação para cada uma.
