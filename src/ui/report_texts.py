"""
ui/report_texts.py
==================
Textos fixos do relatório PDF de Análise Comparativa.
Edite este arquivo para personalizar o conteúdo do relatório.
"""

# ── Capa ──────────────────────────────────────────────────────────────────────

TITULO    = "RELATÓRIO DE INTELIGÊNCIA ARTIFICIAL I"
SUBTITULO = "Algoritmos de Busca Local e AG no Problema da Mochila"

INTEGRANTES = [
    "Guilherme Carvalho Alvarenga",
    "Lara Hydalgo Ferreira",
]

INSTITUICAO = " Universidade de Taubaté - Engenharia da Computação"   
ANO         = "2026"   

# ── Seção 1 — Introdução ──────────────────────────────────────────────────────

SEC1_TITULO = "1. INTRODUÇÃO"

SEC1_TEXTO = (
    "Este relatório apresenta os resultados de experimentos realizados com algoritmos "
    "de busca local e algoritmo genético aplicados ao Problema da Mochila com restrição "
    "de tempo de deslocamento. O problema consiste em determinar o melhor caminho entre "
    "dois pontos em um mapa gerado proceduralmente, composto por diferentes tipos de "
    "terreno — planície, floresta, pântano e montanha — cada qual com um fator de "
    "modificação da velocidade de deslocamento do agente."
    "\n\n"
    "O objetivo principal é maximizar o aproveitamento do tempo disponível (capacidade "
    "da mochila), encontrando caminhos que permitam ao agente percorrer a maior distância "
    "possível sem ultrapassar o limite de tempo estipulado. O ganho de cada solução é "
    "calculado em relação à solução inicial gerada por busca em largura (BFS), servindo "
    "como linha de base para a comparação entre os métodos."
)

# ── Seção 2 — Metodologia ─────────────────────────────────────────────────────

SEC2_TITULO = "2. METODOLOGIA"

SEC2_TEXTO = (
    "Foram implementados e avaliados quatro algoritmos de busca local, cada um com "
    "características distintas quanto à exploração do espaço de soluções:"
    "\n\n"
    "Subida de Encosta (SE): algoritmo guloso que aceita apenas movimentos que melhorem "
    "o valor da solução corrente. Tende a convergir rapidamente, mas pode ficar preso "
    "em ótimos locais."
    "\n\n"
    "Subida de Encosta com Tentativa (SET): variante que tolera um número máximo de "
    "iterações sem melhora (parâmetro TMAX) antes de encerrar, conferindo maior "
    "resistência a platôs."
    "\n\n"
    "Têmpera Simulada (TS): inspirada no processo físico de resfriamento de metais, "
    "aceita soluções piores com uma probabilidade que decresce com a temperatura. "
    "Os parâmetros controlam a temperatura inicial (TI), a temperatura final (TF) e "
    "o fator de resfriamento (FR)."
    "\n\n"
    "Algoritmo Genético (AG): baseado em mecanismos da evolução biológica, opera sobre "
    "uma população de soluções por meio de operadores de seleção, cruzamento e mutação. "
    "Os parâmetros incluem tamanho da população (TP), número de gerações (NG), taxa de "
    "cruzamento (TC), taxa de mutação (TM) e fração de elitismo (IG)."
    "\n\n"
    "A solução inicial de cada execução é gerada por busca em largura (BFS), garantindo "
    "um caminho válido entre os estados inicial e objetivo. O fitness de cada solução é "
    "calculado como o tempo total de deslocamento dentro do limite estabelecido, e o "
    "ganho percentual é obtido pela razão entre a melhoria alcançada e o tempo limite."
    "\n\n"
    "A coleta de dados foi realizada por meio da ferramenta de Análise Comparativa "
    "integrada à aplicação, que permite configurar individualmente os parâmetros de "
    "cada algoritmo e definir o número de execuções por método. O custo final reportado "
    "corresponde à média aritmética das execuções realizadas, assim como o ganho médio "
    "percentual em relação à solução inicial."
)

# ── Seção 3 — Resultados (texto base — o restante é gerado dinamicamente) ────

SEC3_TITULO = "3. RESULTADOS OBTIDOS"

SEC3_INTRO = (
    "A seguir são apresentados os resultados obtidos nos experimentos, incluindo a "
    "tabela comparativa com os principais indicadores de desempenho de cada configuração "
    "testada e o gráfico de barras com os ganhos percentuais alcançados."
)

# Texto de conclusão — use {method}, {config}, {time}, {limit} e {gain}
# como marcadores; eles serão substituídos automaticamente pelo melhor resultado.
SEC3_CONCLUSAO_TEMPLATE = (
    "Nos testes realizados, o algoritmo que apresentou o melhor resultado foi {method}, "
    "utilizando a configuração {config}, com tempo de {time}s para um limite de {limit}s "
    "e ganho de {gain}% em relação à solução inicial gerada por BFS."
)