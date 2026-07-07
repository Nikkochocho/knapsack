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
        'app_title': 'MOCHILA',
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

        'method_labels': {
            'Hill Climbing': 'Subida de Encosta',
            'Hill Climbing (Random Restart)': 'Subida de Encosta (Tentativa)',
            'Simulated Annealing': 'Têmpera Simulada',
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