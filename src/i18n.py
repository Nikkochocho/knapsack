"""
i18n.py
==============================================================
Lightweight internal translation (i18n) system for the app's UI.
Supports English (default) and Portuguese.

Usage:
    import i18n
    i18n.t('btn_about')                       -> translated string
    i18n.t('status_running', method='A*')     -> formatted + translated
    i18n.set_language('pt')                   -> switch active language
    i18n.get_language()                       -> 'en' or 'pt'
"""

DEFAULT_LANGUAGE = 'en'
_current_lang = DEFAULT_LANGUAGE

_STRINGS = {
    'en': {
        'app_title': 'KNAPSACK',
        'btn_exit': '✕  Exit',
        'btn_about': 'ℹ  About',
        'btn_settings': '⚙  Settings',
        'generated_map': 'GENERATED MAP',

        'status_start_eq_goal': '⚠ Initial state = goal.',
        'status_running': 'Running {method}...',
        'status_no_path': '✗ No path found.',
        'status_time_limit': ('⚠ Time limit reached at {cost:.2f}s of '
                               '{limit:.1f}s — destination not reached.'),
        'status_path_found': '✓ Path found! {n} nodes.',
        'status_generating_multiverse': 'Generating multiverse...',
        'status_multiverse_generated': ('✓ Multiverse generated: {n_maps} maps, '
                                         '{n_portals} portals.'),

        'status_generating_initial_solution': 'Generating initial solution...',
        'status_initial_solution_done': '⬡ Initial solution: {n} nodes, cost {cost:.3f}s.',

        'about_title': 'About',
        'about_header': '◈  About  ◈',
        'about_developed_by': 'DEVELOPED BY',
        'about_desc': (
            'Interactive visualizer for local search algorithms and genetic '
            'algorithms in artificial intelligence. The grid is procedurally '
            'generated and traversed by solution optimization strategies for '
            'real-time comparison of cost, depth and gain. This project also '
            'includes a comparative analysis, showing the performance '
            'differences between the different optimization algorithms.'
        ),
        'about_assets': ('\n\nPIXEL ART ASSETS AND TILESETS SHOWN WERE CREATED '
                          'BY THE DEVELOPERS'),
        'about_repo': '\n\nFor more information visit the repository: ',
        'about_close': 'Close',

        'settings_title': 'Settings',
        'settings_language_label': 'Language / Idioma',
        'settings_close': 'Close',

        # ── control panel (ui/control_panel.py) ─────────────────────────────
        'cp_section_method':             '▸ SEARCH METHOD',
        'cp_section_capacity':           '▸ CAPACITY',
        'cp_section_start_state':        '▸ INITIAL STATE',
        'cp_section_goal_state':         '▸ GOAL STATE',
        'cp_section_multiverse':         '▸ MULTIVERSE',
        'cp_section_states_transitions': '▸ STATES & TRANSITIONS',
        'cp_section_terrains':           '▸ TERRAINS',

        'cp_label_tmax':         'Attempts (tmax):',
        'cp_label_t1':           'Initial temperature (t1):',
        'cp_label_tf':           'Final temperature (tf):',
        'cp_label_fr':           'Cooling factor (fr):',
        'cp_label_tp':           'Population (tp):',
        'cp_label_ng':           'Generations (ng):',
        'cp_label_tc':           'Crossover rate (tc):',
        'cp_label_tm':           'Mutation rate (tm):',
        'cp_label_ig':           'Elitism (ig):',
        'cp_label_time_limit':   'Time limit (s):',
        'cp_label_n_maps':       'Number of maps:',
        'cp_label_portal_cost':  'Portal cost:',

        'cp_btn_initial_solution':    '⬡  INITIAL SOLUTION',
        'cp_btn_run_search':          '▶  RUN SEARCH',
        'cp_btn_clear':                '↺  CLEAR',
        'cp_btn_new_map':              '⟳  NEW MAP',
        'cp_btn_generate_multiverse': '🌀  GENERATE MULTIVERSE',
        'cp_btn_exit_multiverse':     '✕  EXIT MULTIVERSE',
        'cp_btn_comparative':         '◈  COMPARATIVE ANALYSIS',
        'cp_btn_legend':              '◈  LEGEND / TERRAINS',
        'cp_checkbox_animate':        'Path animation',

        # ── legend window ────────────────────────────────────────────────────
        'legend_title':       'Legend',
        'legend_start_state': 'Initial state',
        'legend_goal_state':  'Goal state',
        'legend_path_found':  'Path found',
        'legend_map_portal':  'Map portal',
        'legend_plains':      'Plains  (20% speed increase)',
        'legend_forest':      'Forest  (speed unchanged)',
        'legend_swamp':       'Swamp   (30% speed decrease)',
        'legend_mountain':    'Mountain  (50% speed decrease)',
        'legend_close':       'Close',

        # ── graph canvas (ui/graph_canvas.py) ───────────────────────────────
        'gc_map_start':   '◈  Map {id}  —  START',
        'gc_map_goal':    '◈  Map {id}  —  REAL EXIT',
        'gc_map_default': '◈  Map {id}',

        # ── result panel (ui/result_panel.py) ───────────────────────────────
        'rp_section_result':   '▸ RESULT',
        'rp_time_reached':     'TIME REACHED',
        'rp_stat_depth':       'SOL.\nDEPTH',
        'rp_stat_profit':      'SOL.\nGAIN',
        'rp_section_path':     '▸ PATH FOUND',
        'rp_status_waiting':   'Waiting for execution...',
        'rp_path_total_cost':  'Total cost: {cost}\n',
        'rp_path_depth':       'Depth: {depth}\n',
        'rp_path_gain':        'Gain: {profit}%\n',
        'rp_path_none_found':  'No path found.',

        # ── comparative window (ui/comparative_window.py) ───────────────────
        'cw_title':              'Comparative Analysis',
        'cw_header':              '◈  COMPARATIVE ANALYSIS',
        'cw_close':                '✕  Close',
        'cw_section_params':      '▸ PARAMETERS PER METHOD',
        'cw_runs_per_method':     'Runs per method:',
        'cw_no_extra_params':     '(no additional parameters)',
        'cw_add_config':          '＋  add configuration',
        'cw_btn_run_comparison':  '▶  RUN COMPARISON',
        'cw_status_start_eq_goal':'⚠ Start equals goal.',
        'cw_status_running':      'Running {label} ({done}/{total}) — attempt {run}/{n_runs}…',
        'cw_status_done':         '✓ Done — {n} method(s) executed.',

        'cw_results_title':   'Results — Comparative Analysis',
        'cw_results_header':  '◈  ALGORITHM COMPARISON  —  LIMIT {limit:.0f}s',
        'cw_export_pdf':       '⬇  EXPORT PDF',
        'cw_section_table':    '▸ COMPARISON TABLE',
        'cw_col_method':        'METHOD',
        'cw_col_config':        'CONFIGURATION',
        'cw_col_time':          'TIME (s)',
        'cw_col_gain':          'GAIN',
        'cw_col_nodes':         'NODES',
        'cw_section_chart':    '▸ GAIN BY METHOD (%)',
        'cw_no_gain_data':      'No gain data available.',

        # Abbreviations shown for each canonical method key.
        'method_abbr': {
            'Hill Climbing':                  'HC',
            'Hill Climbing (Random Restart)': 'HCR',
            'Simulated Annealing':            'SA',
            'Genetic Algorithm':              'GA',
        },

        # Display labels for the internal (English) search-method keys used
        # in config.SEARCH_METHODS. The key is the canonical identifier used
        # for algorithm dispatch; the value is what the UI shows.
        'method_labels': {
            'Hill Climbing': 'Hill Climbing',
            'Hill Climbing (Random Restart)': 'Hill Climbing (Random Restart)',
            'Simulated Annealing': 'Simulated Annealing',
            'Genetic Algorithm': 'Genetic Algorithm',
        },
    },
    'pt': {
        'app_title': 'KNAPSACK',
        'btn_exit': '✕  Sair',
        'btn_about': 'ℹ  Sobre',
        'btn_settings': '⚙  Configurações',
        'generated_map': 'MAPA GERADO',

        'status_start_eq_goal': '⚠ Estado inicial = objetivo.',
        'status_running': 'Executando {method}...',
        'status_no_path': '✗ Sem caminho encontrado.',
        'status_time_limit': ('⚠ Limite atingido em {cost:.2f}s de '
                               '{limit:.1f}s — destino não alcançado.'),
        'status_path_found': '✓ Caminho encontrado! {n} nós.',
        'status_generating_multiverse': 'Gerando multiverso...',
        'status_multiverse_generated': ('✓ Multiverso gerado: {n_maps} mapas, '
                                         '{n_portals} portais.'),

        'status_generating_initial_solution': 'Gerando solução inicial...',
        'status_initial_solution_done': '⬡ Solução inicial: {n} nós, custo {cost:.3f}s.',

        'about_title': 'Sobre',
        'about_header': '◈  Sobre  ◈',
        'about_developed_by': 'DESENVOLVIDO POR',
        'about_desc': (
            'Visualizador interativo de algoritmos de busca local e AGs em '
            'inteligência artificial. O grid é gerado proceduralmente e '
            'percorrido por estratégias de otimização de solução para '
            'comparação de custo, profundidade e ganho em tempo real. Este '
            'projeto contém também uma análise comparativa, mostrando '
            'diferenças de ganho entre os diferentes algoritmos de otimização.'
        ),
        'about_assets': ('\n\nASSETS E TILESETS EM PIXEL ART APRESENTADOS SÃO '
                          'DA AUTORIA DOS DESENVOLVEDORES'),
        'about_repo': '\n\nPara mais informações acesse o repositório: ',
        'about_close': 'Fechar',

        'settings_title': 'Configurações',
        'settings_language_label': 'Idioma / Language',
        'settings_close': 'Fechar',

        # ── control panel (ui/control_panel.py) ─────────────────────────────
        'cp_section_method':             '▸ MÉTODO DE BUSCA',
        'cp_section_capacity':           '▸ CAPACIDADE',
        'cp_section_start_state':        '▸ ESTADO INICIAL',
        'cp_section_goal_state':         '▸ ESTADO OBJETIVO',
        'cp_section_multiverse':         '▸ MULTIVERSO',
        'cp_section_states_transitions': '▸ ESTADOS E TRANSIÇÕES',
        'cp_section_terrains':           '▸ TERRENOS',

        'cp_label_tmax':         'Tentativas (tmax):',
        'cp_label_t1':           'Temperatura inicial (t1):',
        'cp_label_tf':           'Temperatura final (tf):',
        'cp_label_fr':           'Fator de resfriamento (fr):',
        'cp_label_tp':           'População (tp):',
        'cp_label_ng':           'Gerações (ng):',
        'cp_label_tc':           'Taxa cruzamento (tc):',
        'cp_label_tm':           'Taxa mutação (tm):',
        'cp_label_ig':           'Elitismo (ig):',
        'cp_label_time_limit':   'Tempo limite (s):',
        'cp_label_n_maps':       'Nº de mapas:',
        'cp_label_portal_cost':  'Custo do portal:',

        'cp_btn_initial_solution':    '⬡  SOLUÇÃO INICIAL',
        'cp_btn_run_search':          '▶  EXECUTAR BUSCA',
        'cp_btn_clear':                '↺  LIMPAR',
        'cp_btn_new_map':              '⟳  NOVO MAPA',
        'cp_btn_generate_multiverse': '🌀  GERAR MULTIVERSO',
        'cp_btn_exit_multiverse':     '✕  SAIR DO MULTIVERSO',
        'cp_btn_comparative':         '◈  ANÁLISE COMPARATIVA',
        'cp_btn_legend':              '◈  LEGENDA / TERRENOS',
        'cp_checkbox_animate':        'Animação do caminho',

        # ── legend window ────────────────────────────────────────────────────
        'legend_title':       'Legenda',
        'legend_start_state': 'Estado inicial',
        'legend_goal_state':  'Estado objetivo',
        'legend_path_found':  'Caminho encontrado',
        'legend_map_portal':  'Portal de mapa',
        'legend_plains':      'Planície  (aumento de 20% da velocidade)',
        'legend_forest':      'Floresta  (velocidade se mantém)',
        'legend_swamp':       'Pântano   (redução de 30% da velocidade)',
        'legend_mountain':    'Montanha  (redução de 50% da velocidade)',
        'legend_close':       'Fechar',

        # ── graph canvas (ui/graph_canvas.py) ───────────────────────────────
        'gc_map_start':   '◈  Mapa {id}  —  INÍCIO',
        'gc_map_goal':    '◈  Mapa {id}  —  SAÍDA REAL',
        'gc_map_default': '◈  Mapa {id}',

        # ── result panel (ui/result_panel.py) ───────────────────────────────
        'rp_section_result':   '▸ RESULTADO',
        'rp_time_reached':     'TEMPO ALCANÇADO',
        'rp_stat_depth':       'PROF.\nSOLUÇÃO',
        'rp_stat_profit':      'GANHO\nSOLUÇÃO',
        'rp_section_path':     '▸ CAMINHO ENCONTRADO',
        'rp_status_waiting':   'Aguardando execução...',
        'rp_path_total_cost':  'Custo total: {cost}\n',
        'rp_path_depth':       'Profundidade: {depth}\n',
        'rp_path_gain':        'Ganho: {profit} %\n',
        'rp_path_none_found':  'Nenhum caminho encontrado.',

        # ── comparative window (ui/comparative_window.py) ───────────────────
        'cw_title':              'Análise Comparativa',
        'cw_header':              '◈  ANÁLISE COMPARATIVA',
        'cw_close':                '✕  Fechar',
        'cw_section_params':      '▸ PARÂMETROS POR MÉTODO',
        'cw_runs_per_method':     'Execuções por método:',
        'cw_no_extra_params':     '(sem parâmetros adicionais)',
        'cw_add_config':          '＋  adicionar configuração',
        'cw_btn_run_comparison':  '▶  EXECUTAR COMPARAÇÃO',
        'cw_status_start_eq_goal':'⚠ Início igual ao objetivo.',
        'cw_status_running':      'Executando {label} ({done}/{total}) — tentativa {run}/{n_runs}…',
        'cw_status_done':         '✓ Concluído — {n} método(s) executado(s).',

        'cw_results_title':   'Resultados — Análise Comparativa',
        'cw_results_header':  '◈  COMPARATIVA DOS ALGORITMOS  —  LIMITE {limit:.0f}s',
        'cw_export_pdf':       '⬇  EXPORTAR PDF',
        'cw_section_table':    '▸ TABELA COMPARATIVA',
        'cw_col_method':        'MÉTODO',
        'cw_col_config':        'CONFIGURAÇÃO',
        'cw_col_time':          'TEMPO (s)',
        'cw_col_gain':          'GANHO',
        'cw_col_nodes':         'NÓS',
        'cw_section_chart':    '▸ GANHO POR MÉTODO (%)',
        'cw_no_gain_data':      'Nenhum dado de ganho disponível.',

        'method_abbr': {
            'Hill Climbing':                  'SE',
            'Hill Climbing (Random Restart)': 'SET',
            'Simulated Annealing':            'TS',
            'Genetic Algorithm':              'AG',
        },

        'method_labels': {
            'Hill Climbing': 'Subida de Encosta',
            'Hill Climbing (Random Restart)': 'Subida de Encosta (Tentativa)',
            'Simulated Annealing': 'Têmpera Simulada',
            'Genetic Algorithm': 'Algoritmo Genético',
        },
    },
    'es': {
        'app_title': 'KNAPSACK',
        'btn_exit': '✕  Salir',
        'btn_about': 'ℹ  Acerca de',
        'btn_settings': '⚙  Configuración',
        'generated_map': 'MAPA GENERADO',

        'status_start_eq_goal': '⚠ Estado inicial = objetivo.',
        'status_running': 'Ejecutando {method}...',
        'status_no_path': '✗ No se encontró un camino.',
        'status_time_limit': ('⚠ Límite de tiempo alcanzado en {cost:.2f}s de '
                               '{limit:.1f}s — destino no alcanzado.'),
        'status_path_found': '✓ ¡Camino encontrado! {n} nodos.',
        'status_generating_multiverse': 'Generando multiverso...',
        'status_multiverse_generated': ('✓ Multiverso generado: {n_maps} mapas, '
                                         '{n_portals} portales.'),

        'status_generating_initial_solution': 'Generando solución inicial...',
        'status_initial_solution_done': '⬡ Solución inicial: {n} nodos, costo {cost:.3f}s.',

        'about_title': 'Acerca de',
        'about_header': '◈  Acerca de  ◈',
        'about_developed_by': 'DESARROLLADO POR',
        'about_desc': (
            'Visualizador interactivo de algoritmos de búsqueda local y AG en '
            'inteligencia artificial. La cuadrícula se genera de forma procedural '
            'y es recorrida por estrategias de optimización de soluciones para '
            'la comparación en tiempo real de costo, profundidad y ganancia. '
            'Este proyecto también incluye un análisis comparativo, que muestra '
            'las diferencias de rendimiento entre los distintos algoritmos de '
            'optimización.'
        ),
        'about_assets': ('\n\nLOS ASSETS Y TILESETS EN PIXEL ART MOSTRADOS '
                          'FUERON CREADOS POR LOS DESARROLLADORES'),
        'about_repo': '\n\nPara más información visita el repositorio: ',
        'about_close': 'Cerrar',

        'settings_title': 'Configuración',
        'settings_language_label': 'Idioma / Language',
        'settings_close': 'Cerrar',

        # ── control panel (ui/control_panel.py) ─────────────────────────────
        'cp_section_method':             '▸ MÉTODO DE BÚSQUEDA',
        'cp_section_capacity':           '▸ CAPACIDAD',
        'cp_section_start_state':        '▸ ESTADO INICIAL',
        'cp_section_goal_state':         '▸ ESTADO OBJETIVO',
        'cp_section_multiverse':         '▸ MULTIVERSO',
        'cp_section_states_transitions': '▸ ESTADOS Y TRANSICIONES',
        'cp_section_terrains':           '▸ TERRENOS',

        'cp_label_tmax':         'Intentos (tmax):',
        'cp_label_t1':           'Temperatura inicial (t1):',
        'cp_label_tf':           'Temperatura final (tf):',
        'cp_label_fr':           'Factor de enfriamiento (fr):',
        'cp_label_tp':           'Población (tp):',
        'cp_label_ng':           'Generaciones (ng):',
        'cp_label_tc':           'Tasa de cruce (tc):',
        'cp_label_tm':           'Tasa de mutación (tm):',
        'cp_label_ig':           'Elitismo (ig):',
        'cp_label_time_limit':   'Límite de tiempo (s):',
        'cp_label_n_maps':       'N.º de mapas:',
        'cp_label_portal_cost':  'Costo del portal:',

        'cp_btn_initial_solution':    '⬡  SOLUCIÓN INICIAL',
        'cp_btn_run_search':          '▶  EJECUTAR BÚSQUEDA',
        'cp_btn_clear':                '↺  LIMPIAR',
        'cp_btn_new_map':              '⟳  NUEVO MAPA',
        'cp_btn_generate_multiverse': '🌀  GENERAR MULTIVERSO',
        'cp_btn_exit_multiverse':     '✕  SALIR DEL MULTIVERSO',
        'cp_btn_comparative':         '◈  ANÁLISIS COMPARATIVO',
        'cp_btn_legend':              '◈  LEYENDA / TERRENOS',
        'cp_checkbox_animate':        'Animación del camino',

        # ── legend window ────────────────────────────────────────────────────
        'legend_title':       'Leyenda',
        'legend_start_state': 'Estado inicial',
        'legend_goal_state':  'Estado objetivo',
        'legend_path_found':  'Camino encontrado',
        'legend_map_portal':  'Portal de mapa',
        'legend_plains':      'Llanura  (aumento del 20% de velocidad)',
        'legend_forest':      'Bosque  (la velocidad se mantiene)',
        'legend_swamp':       'Pantano   (reducción del 30% de velocidad)',
        'legend_mountain':    'Montaña  (reducción del 50% de velocidad)',
        'legend_close':       'Cerrar',

        # ── graph canvas (ui/graph_canvas.py) ───────────────────────────────
        'gc_map_start':   '◈  Mapa {id}  —  INICIO',
        'gc_map_goal':    '◈  Mapa {id}  —  SALIDA REAL',
        'gc_map_default': '◈  Mapa {id}',

        # ── result panel (ui/result_panel.py) ───────────────────────────────
        'rp_section_result':   '▸ RESULTADO',
        'rp_time_reached':     'TIEMPO ALCANZADO',
        'rp_stat_depth':       'PROF.\nSOLUCIÓN',
        'rp_stat_profit':      'GANANCIA\nSOLUCIÓN',
        'rp_section_path':     '▸ CAMINO ENCONTRADO',
        'rp_status_waiting':   'Esperando ejecución...',
        'rp_path_total_cost':  'Costo total: {cost}\n',
        'rp_path_depth':       'Profundidad: {depth}\n',
        'rp_path_gain':        'Ganancia: {profit}%\n',
        'rp_path_none_found':  'No se encontró ningún camino.',

        # ── comparative window (ui/comparative_window.py) ───────────────────
        'cw_title':              'Análisis Comparativo',
        'cw_header':              '◈  ANÁLISIS COMPARATIVO',
        'cw_close':                '✕  Cerrar',
        'cw_section_params':      '▸ PARÁMETROS POR MÉTODO',
        'cw_runs_per_method':     'Ejecuciones por método:',
        'cw_no_extra_params':     '(sin parámetros adicionales)',
        'cw_add_config':          '＋  agregar configuración',
        'cw_btn_run_comparison':  '▶  EJECUTAR COMPARACIÓN',
        'cw_status_start_eq_goal':'⚠ El inicio es igual al objetivo.',
        'cw_status_running':      'Ejecutando {label} ({done}/{total}) — intento {run}/{n_runs}…',
        'cw_status_done':         '✓ Completado — {n} método(s) ejecutado(s).',

        'cw_results_title':   'Resultados — Análisis Comparativo',
        'cw_results_header':  '◈  COMPARACIÓN DE ALGORITMOS  —  LÍMITE {limit:.0f}s',
        'cw_export_pdf':       '⬇  EXPORTAR PDF',
        'cw_section_table':    '▸ TABLA COMPARATIVA',
        'cw_col_method':        'MÉTODO',
        'cw_col_config':        'CONFIGURACIÓN',
        'cw_col_time':          'TIEMPO (s)',
        'cw_col_gain':          'GANANCIA',
        'cw_col_nodes':         'NODOS',
        'cw_section_chart':    '▸ GANANCIA POR MÉTODO (%)',
        'cw_no_gain_data':      'No hay datos de ganancia disponibles.',

        'method_abbr': {
            'Hill Climbing':                  'AC',
            'Hill Climbing (Random Restart)': 'ACR',
            'Simulated Annealing':            'RS',
            'Genetic Algorithm':              'AG',
        },

        'method_labels': {
            'Hill Climbing': 'Ascenso de Colinas',
            'Hill Climbing (Random Restart)': 'Ascenso de Colinas (Intento)',
            'Simulated Annealing': 'Recocido Simulado',
            'Genetic Algorithm': 'Algoritmo Genético',
        },
    },
}


def set_language(lang: str) -> None:
    """Set the active UI language ('en' or 'pt'). Ignored if unknown."""
    global _current_lang
    if lang in _STRINGS:
        _current_lang = lang


def get_language() -> str:
    """Return the current active language code."""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """Translate `key` into the active language, formatting with kwargs."""
    template = _STRINGS.get(_current_lang, _STRINGS[DEFAULT_LANGUAGE]).get(key, key)
    return template.format(**kwargs) if kwargs else template


def method_label(method_key: str) -> str:
    """Translate a canonical search-method key (see config.SEARCH_METHODS)
    into the display label for the active language. Falls back to the key
    itself if no translation is registered."""
    labels = _STRINGS.get(_current_lang, _STRINGS[DEFAULT_LANGUAGE]).get('method_labels', {})
    return labels.get(method_key, method_key)


def method_abbr(method_key: str) -> str:
    """Translate a canonical search-method key into its short display
    abbreviation (e.g. 'HC', 'SA') for the active language. Falls back to
    the key itself if no abbreviation is registered."""
    abbrs = _STRINGS.get(_current_lang, _STRINGS[DEFAULT_LANGUAGE]).get('method_abbr', {})
    return abbrs.get(method_key, method_key)