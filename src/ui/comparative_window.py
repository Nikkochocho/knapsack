"""
ui/comparative_window.py
==================================================================
Janela de Análise Comparativa dos algoritmos de busca.
Permite configurar grafo, parâmetros por método, executar todos e
exibir tabela + gráfico de barras comparativo.
"""

import tkinter as tk
from tkinter import ttk
import time
import config
from config import COLORS
from algorithms import run_search
from multiverse import generate_multiverse
from ui.report_exporter import export_report


# ── paleta de cores para as barras do gráfico ─────────────────────────────────
BAR_COLORS = ['#4A9EFF', '#F5A623', '#7ED321', '#D0021B',
              '#9B59B6', '#1ABC9C', '#E67E22', '#2ECC71']

METHOD_ABBR = {
    'Subida de Encosta':             'SE',
    'Subida de Encosta (Tentativa)': 'SET',
    'Têmpera Simulada':              'TS',
    'Algoritmo Genético':            'AG',
}

TMAX_METHODS    = {'Subida de Encosta (Tentativa)'}
TEMPERA_METHODS = {'Têmpera Simulada'}
AG_METHODS      = {'Algoritmo Genético'}


class ComparativeWindow(tk.Toplevel):
    """Janela principal da análise comparativa."""

    def __init__(self, parent, fonts: dict):
        super().__init__(parent)
        self.withdraw() 
        self.title('Análise Comparativa')
        self.configure(bg=COLORS['bg'])
        self.resizable(True, True)
        self.minsize(400, 800)

        self._fonts  = fonts
        self._results: list[dict] = []
        self._param_widgets: dict = {}   # method_name -> dict of vars
        self._build()
        self._center(parent)
        self.deiconify()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self._build_header()

        # scrollable body
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill='both', expand=True)

        canvas = tk.Canvas(outer, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=COLORS['bg'])

        self._scroll_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self._scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), 'units'))

        body = self._scroll_frame

        self._build_params_section(body)
        self._divider(body)
        self._build_run_button(body)

    def _build_header(self):
        h = tk.Frame(self, bg=COLORS['panel'], height=48)
        h.pack(fill='x')
        h.pack_propagate(False)
        tk.Label(h, text='◈  ANÁLISE COMPARATIVA',
                 font=self._fonts['title'],
                 bg=COLORS['panel'], fg=COLORS['accent'],
                 ).pack(side='left', padx=20, pady=10)
        tk.Button(h, text='✕  Fechar',
                  font=self._fonts['label'],
                  bg=COLORS['panel'], fg=COLORS['text_dim'],
                  activebackground='#c0392b', activeforeground='#ffffff',
                  relief='flat', cursor='hand2', padx=14, pady=4,
                  command=self.destroy,
                  ).pack(side='right', padx=(4, 16), pady=8)

    # ── seção parâmetros ──────────────────────────────────────────────────────

    def _build_params_section(self, parent):
        self._section(parent, '▸ PARÂMETROS POR MÉTODO')

        runs_frame = tk.Frame(parent, bg=COLORS['bg'])
        runs_frame.pack(pady=(0, 8))
        tk.Label(runs_frame, text='Execuções por método:',
                font=self._fonts['label'],
                bg=COLORS['bg'], fg=COLORS['text_dim']).pack(side='left', padx=(0, 8))
        self._n_runs_var = tk.IntVar(value=1)
        tk.Spinbox(runs_frame, from_=1, to=10,
                textvariable=self._n_runs_var, width=4,
                font=self._fonts['mono'],
                bg=COLORS['node_default'], fg=COLORS['text'],
                buttonbackground=COLORS['panel_border'],
                relief='flat', insertbackground=COLORS['text'],
                ).pack(side='left')

        # _param_widgets[method] = lista de dicts de vars (um por bloco)
        self._param_widgets  = {}
        # _method_containers[method] = frame que contém todos os blocos
        self._method_containers = {}

        # ── Subida de Encosta (sem parâmetros, bloco fixo) ───────────────────
        se_outer = tk.Frame(parent, bg=COLORS['bg'])
        se_outer.pack(padx=20, pady=4, fill='x')

        title_row = tk.Frame(se_outer, bg=COLORS['bg'])
        title_row.pack(fill='x', pady=(0, 4))
        tk.Label(title_row, text='SE  —  Subida de Encosta',
                font=self._fonts['section'],
                bg=COLORS['bg'], fg=COLORS['accent2'],
                ).pack(side='left')

        se_block = tk.Frame(se_outer, bg=COLORS['panel'],
                            highlightbackground=COLORS['panel_border'],
                            highlightthickness=1)
        se_block.pack(fill='x', pady=3)

        se_header = tk.Frame(se_block, bg=COLORS['panel'])
        se_header.pack(fill='x', padx=12, pady=(6, 6))

        self._se_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(se_header, text='#1',
                    variable=self._se_enabled,
                    font=self._fonts['section'],
                    bg=COLORS['panel'], fg=COLORS['accent'],
                    activebackground=COLORS['panel'],
                    selectcolor=COLORS['node_default'],
                    relief='flat', cursor='hand2',
                    ).pack(side='left')
        tk.Label(se_header, text='(sem parâmetros adicionais)',
                font=self._fonts['label'],
                bg=COLORS['panel'], fg=COLORS['text_dim'],
                ).pack(side='left', padx=(12, 0))

        methods = [
            'Subida de Encosta (Tentativa)',
            'Têmpera Simulada',
            'Algoritmo Genético',
        ]
        for method in methods:
            self._param_widgets[method]     = []
            self._build_method_section(parent, method)

    def _build_method_section(self, parent, method: str):
        """Cria o frame-mãe de um método com seus blocos e botão '+'."""
        abbr = METHOD_ABBR.get(method, method)

        outer = tk.Frame(parent, bg=COLORS['bg'])
        outer.pack(padx=20, pady=4, fill='x')

        # título do método
        title_row = tk.Frame(outer, bg=COLORS['bg'])
        title_row.pack(fill='x', pady=(0, 4))
        tk.Label(title_row, text=f'{abbr}  —  {method}',
                font=self._fonts['section'],
                bg=COLORS['bg'], fg=COLORS['accent2'],
                ).pack(side='left')

        # container dos blocos
        container = tk.Frame(outer, bg=COLORS['bg'])
        container.pack(fill='x')
        self._method_containers[method] = container

        # botão '+'
        tk.Button(outer, text='＋  adicionar configuração',
                font=self._fonts['label'],
                bg=COLORS['bg'], fg=COLORS['accent'],
                activebackground=COLORS['node_default'],
                activeforeground=COLORS['accent'],
                relief='flat', cursor='hand2',
                command=lambda m=method: self._add_block(m),
                ).pack(anchor='center', pady=(4, 0))

        # primeiro bloco já criado por padrão
        self._add_block(method)

    def _build_method_block(self, parent, method: str):
        abbr = METHOD_ABBR.get(method, method)

        frame = tk.Frame(parent, bg=COLORS['panel'],
                         highlightbackground=COLORS['panel_border'],
                         highlightthickness=1)
        frame.pack(padx=20, pady=6, fill='x')
        frame.pack_propagate(True)

        # cabeçalho do bloco
        header = tk.Frame(frame, bg=COLORS['panel'])
        header.pack(fill='x', padx=12, pady=(8, 4))

        self._param_widgets[method] = {}

        enabled_var = tk.BooleanVar(value=True)
        self._param_widgets[method]['_enabled'] = enabled_var
        tk.Checkbutton(header, text=f'{abbr}  —  {method}',
                       variable=enabled_var,
                       font=self._fonts['section'],
                       bg=COLORS['panel'], fg=COLORS['accent'],
                       activebackground=COLORS['panel'],
                       selectcolor=COLORS['node_default'],
                       relief='flat', cursor='hand2',
                       ).pack(side='left')

        inner = tk.Frame(frame, bg=COLORS['panel'])
        inner.pack(expand=True, anchor='center', pady=(0, 10))

        if method in TMAX_METHODS:
            self._add_spinbox(inner, method, 'tmax', 'Tentativas (tmax):',
                              20, 1, 500, 1, '%d', 'int')

        elif method in TEMPERA_METHODS:
            self._add_spinbox(inner, method, 't1', 'Temperatura inicial (t1):',
                              100.0, 1.0, 1000.0, 10.0, '%.1f', 'float')
            self._add_spinbox(inner, method, 'tf', 'Temperatura final (tf):',
                              0.1, 0.01, 10.0, 0.1, '%.2f', 'float')
            self._add_spinbox(inner, method, 'fr', 'Fator de resfriamento (fr):',
                              0.95, 0.01, 0.99, 0.01, '%.2f', 'float')

        elif method in AG_METHODS:
            self._add_spinbox(inner, method, 'tp', 'População (tp):',
                              10, 2, 100, 1, '%d', 'int')
            self._add_spinbox(inner, method, 'ng', 'Gerações (ng):',
                              20, 1, 500, 1, '%d', 'int')
            self._add_spinbox(inner, method, 'tc', 'Taxa cruzamento (tc):',
                              0.8, 0.0, 1.0, 0.05, '%.2f', 'float')
            self._add_spinbox(inner, method, 'tm', 'Taxa mutação (tm):',
                              0.1, 0.0, 1.0, 0.01, '%.2f', 'float')
            self._add_spinbox(inner, method, 'ig', 'Elitismo (ig):',
                              0.2, 0.0, 1.0, 0.05, '%.2f', 'float')

        else:
            tk.Label(inner, text='(sem parâmetros adicionais)',
                     font=self._fonts['label'],
                     bg=COLORS['panel'], fg=COLORS['text_dim']).pack(anchor='w')

    def _add_block(self, method: str):
        """Adiciona um novo bloco de parâmetros para o método."""
        container = self._method_containers[method]
        idx       = len(self._param_widgets[method])
        pw        = {}
        self._param_widgets[method].append(pw)

        block = tk.Frame(container, bg=COLORS['panel'],
                        highlightbackground=COLORS['panel_border'],
                        highlightthickness=1)
        block.pack(fill='x', pady=3)

        # cabeçalho do bloco com checkbox e botão X
        header = tk.Frame(block, bg=COLORS['panel'])
        header.pack(fill='x', padx=12, pady=(6, 2))

        enabled_var = tk.BooleanVar(value=True)
        pw['_enabled'] = enabled_var
        abbr = METHOD_ABBR.get(method, method)
        tk.Checkbutton(header,
                    text=f'#{idx + 1}',
                    variable=enabled_var,
                    font=self._fonts['section'],
                    bg=COLORS['panel'], fg=COLORS['accent'],
                    activebackground=COLORS['panel'],
                    selectcolor=COLORS['node_default'],
                    relief='flat', cursor='hand2',
                    ).pack(side='left')

        # botão X (só aparece se não for o primeiro bloco)
        if idx > 0:
            tk.Button(header, text='✕',
                    font=self._fonts['label'],
                    bg=COLORS['panel'], fg=COLORS['text_dim'],
                    activebackground='#c0392b', activeforeground='#ffffff',
                    relief='flat', cursor='hand2', padx=4,
                    command=lambda b=block, m=method, p=pw: self._remove_block(b, m, p),
                    ).pack(side='right')

        inner = tk.Frame(block, bg=COLORS['panel'])
        inner.pack(anchor='center', pady=(0, 8))

        if method in TMAX_METHODS:
            self._add_spinbox(inner, pw, 'tmax', 'Tentativas (tmax):',
                            20, 1, 500, 1, '%d', 'int')
        elif method in TEMPERA_METHODS:
            self._add_spinbox(inner, pw, 't1', 'Temperatura inicial (t1):',
                            100.0, 1.0, 1000.0, 10.0, '%.1f', 'float')
            self._add_spinbox(inner, pw, 'tf', 'Temperatura final (tf):',
                            0.1, 0.01, 10.0, 0.1, '%.2f', 'float')
            self._add_spinbox(inner, pw, 'fr', 'Fator de resfriamento (fr):',
                            0.95, 0.01, 0.99, 0.01, '%.2f', 'float')
        elif method in AG_METHODS:
            self._add_spinbox(inner, pw, 'tp', 'População (tp):',
                            10, 2, 100, 1, '%d', 'int')
            self._add_spinbox(inner, pw, 'ng', 'Gerações (ng):',
                            20, 1, 500, 1, '%d', 'int')
            self._add_spinbox(inner, pw, 'tc', 'Taxa cruzamento (tc):',
                            0.8, 0.0, 1.0, 0.05, '%.2f', 'float')
            self._add_spinbox(inner, pw, 'tm', 'Taxa mutação (tm):',
                            0.1, 0.0, 1.0, 0.01, '%.2f', 'float')
            self._add_spinbox(inner, pw, 'ig', 'Elitismo (ig):',
                            0.2, 0.0, 1.0, 0.05, '%.2f', 'float')

    def _remove_block(self, block: tk.Frame, method: str, pw: dict):
        """Remove um bloco de parâmetros."""
        self._param_widgets[method].remove(pw)
        block.destroy()

    def _add_spinbox(self, parent, pw: dict, key, label,
                 default, mn, mx, inc, fmt, tipo):
        row = tk.Frame(parent, bg=COLORS['panel'])
        row.pack(pady=2)
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)
        tk.Label(row, text=label, font=self._fonts['label'],
                bg=COLORS['panel'], fg=COLORS['text_dim'],
                anchor='e').grid(row=0, column=0, sticky='e', padx=(0, 8))
        var = (tk.IntVar(value=int(default))
            if tipo == 'int' else tk.DoubleVar(value=default))
        pw[key] = var
        tk.Spinbox(row, from_=mn, to=mx, increment=inc,
                textvariable=var, width=8,
                format=fmt if tipo == 'float' else None,
                font=self._fonts['mono'],
                bg=COLORS['node_default'], fg=COLORS['text'],
                buttonbackground=COLORS['panel_border'],
                relief='flat', insertbackground=COLORS['text'],
                ).grid(row=0, column=1, sticky='w')
    
    # ── botão executar ────────────────────────────────────────────────────────

    def _build_run_button(self, parent):
        self._status_var = tk.StringVar(value='')
        tk.Label(parent, textvariable=self._status_var,
                 font=self._fonts['label'],
                 bg=COLORS['bg'], fg=COLORS['accent'],
                 ).pack(padx=20, pady=(4, 0), anchor='w')

        tk.Button(parent, text='▶  EXECUTAR COMPARAÇÃO',
                  font=self._fonts['section'],
                  bg=COLORS['accent'], fg='#ffffff',
                  activebackground='#6AAAF8', activeforeground='#ffffff',
                  relief='flat', cursor='hand2',
                  command=self._run_all, pady=10,
                  ).pack(padx=20, pady=(4, 20), fill='x')

    # ── execução ──────────────────────────────────────────────────────────────

    def _run_all(self):
        start_node = config.START_NODE
        goal_node  = config.GOAL_NODE
        graph      = config.SUPER_GRAPH if config.MULTIVERSE_MODE else config.GRAPH

        if start_node == goal_node:
            self._status_var.set('⚠ Início igual ao objetivo.')
            return

        methods_order = [
            'Subida de Encosta',
            'Subida de Encosta (Tentativa)',
            'Têmpera Simulada',
            'Algoritmo Genético',
        ]

        self._results = []
        n_runs = self._n_runs_var.get()

        # conta total de blocos habilitados
        total = 0
        for method in methods_order:
            if method == 'Subida de Encosta':
                total += 1
            else:
                total += sum(1 for pw in self._param_widgets[method]
                            if pw['_enabled'].get())
        done = 0

        for method in methods_order:
            abbr   = METHOD_ABBR[method]

            # SE não tem blocos — trata separado
            if method == 'Subida de Encosta':
                done += 1
                costs, gains, path_lens, founds = [], [], [], []
                for run in range(n_runs):
                    self._status_var.set(
                        f'Executando {abbr} ({done}/{total}) — tentativa {run+1}/{n_runs}…')
                    self.update()
                    result = run_search(method=method, start=start_node,
                                        goal=goal_node, graph=graph,
                                        tempo_limite=config.TEMPO_LIMITE,
                                        tmax=20, t1=100.0, tf=0.1, fr=0.95,
                                        tp=10, ng=20, tc=0.8, tm=0.1, ig=0.2)
                    costs.append(result.cost)
                    gains.append(result.profit / 100 if result.profit is not None else None)
                    path_lens.append(len(result.path))
                    founds.append(result.found)

                self._results.append(self._build_result_dict(
                    abbr, method, '—', n_runs, costs, gains, path_lens, founds))
                continue

            # métodos com blocos
            for block_idx, pw in enumerate(self._param_widgets[method]):
                if not pw['_enabled'].get():
                    continue
                done += 1
                label = f'{abbr} #{block_idx+1}' if len(self._param_widgets[method]) > 1 else abbr
                costs, gains, path_lens, founds = [], [], [], []

                for run in range(n_runs):
                    self._status_var.set(
                        f'Executando {label} ({done}/{total}) — tentativa {run+1}/{n_runs}…')
                    self.update()
                    kwargs = dict(
                        method=method, start=start_node, goal=goal_node,
                        graph=graph, tempo_limite=config.TEMPO_LIMITE,
                        tmax=pw.get('tmax', tk.IntVar(value=20)).get(),
                        t1=pw.get('t1',  tk.DoubleVar(value=100.0)).get(),
                        tf=pw.get('tf',  tk.DoubleVar(value=0.1)).get(),
                        fr=pw.get('fr',  tk.DoubleVar(value=0.95)).get(),
                        tp=pw.get('tp',  tk.IntVar(value=10)).get(),
                        ng=pw.get('ng',  tk.IntVar(value=20)).get(),
                        tc=pw.get('tc',  tk.DoubleVar(value=0.8)).get(),
                        tm=pw.get('tm',  tk.DoubleVar(value=0.1)).get(),
                        ig=pw.get('ig',  tk.DoubleVar(value=0.2)).get(),
                    )
                    result = run_search(**kwargs)
                    costs.append(result.cost)
                    gains.append(result.profit / 100 if result.profit is not None else None)
                    path_lens.append(len(result.path))
                    founds.append(result.found)

                cfg_str = _build_config_str(method, pw)
                cfg_str += f'  ×{n_runs}' if n_runs > 1 else ''
                self._results.append(self._build_result_dict(
                    label, method, cfg_str, n_runs, costs, gains, path_lens, founds))
        
        self._status_var.set(f'✓ Concluído — {len(self._results)} método(s) executado(s).')
        self._open_results()

    # ── janela de resultados ──────────────────────────────────────────────────

    def _open_results(self):
        ResultsWindow(self, self._results, self._fonts)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _section(self, parent, text: str):
        tk.Label(parent, text=text, font=self._fonts['section'],
                 bg=COLORS['bg'], fg=COLORS['accent2'],
                 anchor='w').pack(padx=20, pady=(12, 2), fill='x')

    def _divider(self, parent):
        tk.Frame(parent, bg=COLORS['panel_border'], height=1).pack(
            fill='x', padx=16, pady=6)

    def _center(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = 400, 800
        self.geometry(f'{w}x{h}+{px + (pw-w)//2}+{py + (ph-h)//2}')

    def _build_result_dict(self, label, method, cfg_str, n_runs,
                       costs, gains, path_lens, founds) -> dict:
        avg_cost  = sum(costs) / len(costs)
        avg_gain  = (sum(g for g in gains if g is not None) /
                    len([g for g in gains if g is not None])
                    if any(g is not None for g in gains) else None)
        avg_nodes = round(sum(path_lens) / len(path_lens))
        return {
            'method':   label,
            'full':     method,
            'config':   cfg_str,
            'time':     avg_cost,
            'gain':     avg_gain,
            'found':    any(founds),
            'path_len': avg_nodes,
        }

# ── janela de resultados ───────────────────────────────────────────────────────

class ResultsWindow(tk.Toplevel):

    def __init__(self, parent, results: list[dict],
                 fonts: dict):
        super().__init__(parent)
        self.withdraw() 
        self.title('Resultados — Análise Comparativa')
        self.configure(bg=COLORS['bg'])
        self.resizable(True, True)
        self.minsize(820, 540)

        self._fonts  = fonts
        self._results = results
        self._build()
        self._center(parent)
        self.deiconify()

    def _build(self):
        # cabeçalho
        h = tk.Frame(self, bg=COLORS['panel'], height=48)
        h.pack(fill='x')
        h.pack_propagate(False)
        tk.Label(h, text=f'◈  COMPARATIVA DOS ALGORITMOS  —  LIMITE {config.TEMPO_LIMITE:.0f}s',
                font=self._fonts['title'],
                bg=COLORS['panel'], fg=COLORS['accent'],
                ).pack(side='left', padx=20, pady=10)
        tk.Button(h, text='✕  Fechar',
                font=self._fonts['label'],
                bg=COLORS['panel'], fg=COLORS['text_dim'],
                activebackground='#c0392b', activeforeground='#ffffff',
                relief='flat', cursor='hand2', padx=14, pady=4,
                command=self.destroy,
                ).pack(side='right', padx=(4, 16), pady=8)
        tk.Button(h, text='⬇  EXPORTAR PDF',
                font=self._fonts['label'],
                bg=COLORS['panel'], fg=COLORS['accent'],
                activebackground=COLORS['accent'], activeforeground='#ffffff',
                relief='flat', cursor='hand2', padx=14, pady=4,
                command=self._export_pdf,
                ).pack(side='right', padx=(4, 4), pady=8)

        # ── scrollable body ───────────────────────────────────────────────
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill='both', expand=True)

        canvas = tk.Canvas(outer, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLORS['bg'])

        scroll_frame.bind('<Configure>',
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(
                            -1 * (e.delta // 120), 'units'))
        # ─────────────────────────────────────────────────────────────────

        body = tk.Frame(scroll_frame, bg=COLORS['bg'])
        body.pack(fill='both', expand=True, padx=16, pady=12)

        self._build_table(body)
        tk.Frame(body, bg=COLORS['panel_border'], height=1).pack(
            fill='x', pady=10)
        self._build_chart(body)

    # ── tabela ────────────────────────────────────────────────────────────────

    def _build_table(self, parent):
        tk.Label(parent, text='▸ TABELA COMPARATIVA',
                font=self._fonts['section'],
                bg=COLORS['bg'], fg=COLORS['accent2'],
                anchor='w').pack(fill='x', pady=(0, 6))

        wrapper = tk.Frame(parent, bg=COLORS['panel'],
                        highlightbackground=COLORS['panel_border'],
                        highlightthickness=1)
        wrapper.pack(fill='x')

        cols      = ('MÉTODO', 'CONFIGURAÇÃO', 'TEMPO (s)', 'GANHO', 'NÓS')
        col_widths = (8, 0, 10, 8, 6)   # 0 = coluna CONFIGURAÇÃO estica livre

        # configura as colunas do grid
        for i, w in enumerate(col_widths):
            wrapper.grid_columnconfigure(i, weight=1 if w == 0 else 0,
                                        minsize=w * 8)

        # cabeçalho
        for col_idx, col in enumerate(cols):
            tk.Label(wrapper, text=col, font=self._fonts['section'],
                    bg=COLORS['panel_border'], fg=COLORS['text'],
                    anchor='w', padx=6, pady=6,
                    ).grid(row=0, column=col_idx, sticky='ew')

        # linhas de dados
        for row_idx, r in enumerate(self._results, start=1):
            bg = COLORS['panel'] if row_idx % 2 == 0 else COLORS['node_default']

            gain_str = f"{r['gain']*100:.1f}%" if r['gain'] is not None else '—'
            cost_str = f"{r['time']:.3f}"      if r['time'] is not None else '—'
            nodes_str = str(r['path_len'])     if r['found'] else '—'
            fg_gain = (COLORS['success'] if r['gain'] and r['gain'] > 0
                    else COLORS['danger'] if r['gain'] is not None
                    else COLORS['text_dim'])

            cells = [
                (r['method'],  COLORS['accent'],  col_widths[0]),
                (r['config'],  COLORS['text'],    0),
                (cost_str,     COLORS['text_dim'],col_widths[2]),
                (gain_str,     fg_gain,           col_widths[3]),
                (nodes_str,    COLORS['text_dim'],col_widths[4]),
            ]
            for col_idx, (text, fg, w) in enumerate(cells):
                tk.Label(wrapper, text=text, font=self._fonts['label'],
                        bg=bg, fg=fg,
                        anchor='w', padx=6, pady=5,
                        ).grid(row=row_idx, column=col_idx, sticky='ew')

    # ── gráfico de barras ─────────────────────────────────────────────────────

    def _build_chart(self, parent):
        tk.Label(parent, text='▸ GANHO POR MÉTODO (%)',
                 font=self._fonts['section'],
                 bg=COLORS['bg'], fg=COLORS['accent2'],
                 anchor='w').pack(fill='x', pady=(0, 6))

        # filtra apenas resultados com ganho mensurável
        data = [(r['method'], r['gain'] * 100)
                for r in self._results
                if r['gain'] is not None]

        if not data:
            tk.Label(parent, text='Nenhum dado de ganho disponível.',
                     font=self._fonts['label'],
                     bg=COLORS['bg'], fg=COLORS['text_dim']).pack()
            return

        CHART_W, CHART_H = 760, 220
        PAD_L, PAD_R = 60, 20
        PAD_T, PAD_B = 20, 48
        BAR_GAP = 0.3

        cv = tk.Canvas(parent, width=CHART_W, height=CHART_H,
                       bg=COLORS['panel'],
                       highlightbackground=COLORS['panel_border'],
                       highlightthickness=1)
        cv.pack(fill='x', pady=(0, 8))
        self._chart_canvas = cv 

        max_val = max(v for _, v in data) if data else 1
        max_val = max(max_val, 1)                 # evita divisão por zero

        n       = len(data)
        plot_w  = CHART_W - PAD_L - PAD_R
        plot_h  = CHART_H - PAD_T - PAD_B
        bar_w   = plot_w / n * (1 - BAR_GAP)
        slot_w  = plot_w / n

        # eixo Y: linhas de grade
        for pct in [0, 25, 50, 75, 100]:
            if pct > max_val + 5:
                continue
            y = PAD_T + plot_h - (pct / max_val) * plot_h
            cv.create_line(PAD_L, y, CHART_W - PAD_R, y,
                           fill=COLORS['panel_border'], dash=(4, 4))
            cv.create_text(PAD_L - 6, y,
                           text=f'{pct}%', anchor='e',
                           font=self._fonts['label'],
                           fill=COLORS['text_dim'])

        # barras
        for idx, (label, value) in enumerate(data):
            x0 = PAD_L + idx * slot_w + slot_w * BAR_GAP / 2
            x1 = x0 + bar_w
            bar_h = max((value / max_val) * plot_h, 2)
            y0 = PAD_T + plot_h - bar_h
            y1 = PAD_T + plot_h

            color = BAR_COLORS[idx % len(BAR_COLORS)]

            # sombra
            cv.create_rectangle(x0 + 3, y0 + 3, x1 + 3, y1 + 3,
                                 fill='#111111', outline='')
            # barra principal
            cv.create_rectangle(x0, y0, x1, y1,
                                 fill=color, outline='')
            # brilho superior
            cv.create_rectangle(x0, y0, x1, y0 + 4,
                                 fill=_lighten(color), outline='')

            # valor em cima
            cv.create_text((x0 + x1) / 2, y0 - 8,
                            text=f'{value:.1f}%',
                            font=self._fonts['label'],
                            fill=COLORS['text'])

            # rótulo abaixo
            cv.create_text((x0 + x1) / 2, y1 + 14,
                            text=label,
                            font=self._fonts['section'],
                            fill=color)

        # eixo X
        cv.create_line(PAD_L, PAD_T + plot_h,
                       CHART_W - PAD_R, PAD_T + plot_h,
                       fill=COLORS['panel_border'], width=1)
        # eixo Y
        cv.create_line(PAD_L, PAD_T,
                       PAD_L, PAD_T + plot_h,
                       fill=COLORS['panel_border'], width=1)
        
    def _export_pdf(self):
        export_report(self._results)

    # ── center ────────────────────────────────────────────────────────────────

    def _center(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = 860, 600
        self.geometry(f'{w}x{h}+{px + (pw-w)//2 + 40}+{py + (ph-h)//2 + 40}')


# ── utilitários ───────────────────────────────────────────────────────────────

def _build_config_str(method: str, pw: dict) -> str:
    """Monta a string de configuração exibida na tabela."""
    if method == 'Subida de Encosta':
        return '—'
    if method == 'Subida de Encosta (Tentativa)':
        return f"TMAX={pw['tmax'].get()}"
    if method == 'Têmpera Simulada':
        return (f"TI={pw['t1'].get():.1f}; "
                f"TF={pw['tf'].get():.2f}; "
                f"FR={pw['fr'].get():.2f}")
    if method == 'Algoritmo Genético':
        return (f"TP={pw['tp'].get()}; "
                f"NG={pw['ng'].get()}; "
                f"TC={pw['tc'].get():.2f}; "
                f"TM={pw['tm'].get():.2f}; "
                f"IG={pw['ig'].get():.2f}")
    return ''


def _lighten(hex_color: str, amount: int = 40) -> str:
    """Clareia uma cor hex para o brilho da barra."""
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, r + amount)
    g = min(255, g + amount)
    b = min(255, b + amount)
    return f'#{r:02X}{g:02X}{b:02X}'