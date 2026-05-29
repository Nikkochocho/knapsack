"""
ui/result_panel.py
==================
Painel direito da interface: exibição de custo, caminho encontrado e barra de status.
"""

import  tkinter         as tk
from    tkinter         import font as tkfont
from    config          import COLORS
from    search_result   import SearchResult


class ResultPanel(tk.Frame):
    """Painel lateral direito com custo, caminho encontrado e barra de status."""

    def __init__(self, parent, fonts: dict, **kwargs):
        """Inicializa o painel e constrói os widgets de resultado."""
        super().__init__(parent, bg=COLORS['panel'], width=230,
                         highlightbackground=COLORS['panel_border'],
                         highlightthickness=1, **kwargs)
        self.pack_propagate(False)
        self._fonts = fonts
        self._build()

    # ── construção ──────────────────────────────────────────────────────────

    def _build(self):
        """Constrói os widgets de custo, estatísticas, caminho e status."""
        self._section('▸ RESULTADO')

        # ── custo total ──
        cost_box = tk.Frame(self, bg=COLORS['node_default'],
                            highlightbackground=COLORS['panel_border'],
                            highlightthickness=1)
        cost_box.pack(padx=14, pady=(4, 8), fill='x')
        tk.Label(cost_box, text='TEMPO ALCANÇADO',
                 font=self._fonts['section'],
                 bg=COLORS['node_default'],
                 fg=COLORS['text_dim']).pack(pady=(8, 0))
        self._cost_lbl = tk.Label(cost_box, text='—',
                                  font=self._fonts['big'],
                                  bg=COLORS['node_default'],
                                  fg=COLORS['warning'])
        self._cost_lbl.pack(pady=(0, 8))

        # ── estatísticas ──
        stats = tk.Frame(self, bg=COLORS['panel'])
        stats.pack(padx=14, fill='x')
        self._depth_lbl = self._stat_box(stats, 'PROF.\nSOLUÇÃO')

        self._profit_lbl = self._stat_box(stats, 'GANHO\nSOLUÇÃO')

        # ── caminho ──
        self._divider()
        self._section('▸ CAMINHO ENCONTRADO')

        path_frame = tk.Frame(self, bg=COLORS['node_default'],
                              highlightbackground=COLORS['panel_border'],
                              highlightthickness=1)
        path_frame.pack(padx=14, pady=4, fill='both', expand=True)

        scrollbar = tk.Scrollbar(path_frame, orient='vertical',
                                 bg=COLORS['panel_border'])
        self._path_text = tk.Text(path_frame,
                                  font=self._fonts['mono'],
                                  bg=COLORS['node_default'],
                                  fg=COLORS['text'],
                                  relief='flat', wrap='word',
                                  state='disabled',
                                  insertbackground=COLORS['text'],
                                  yscrollcommand=scrollbar.set,
                                  padx=8, pady=8)
        scrollbar.config(command=self._path_text.yview)
        scrollbar.pack(side='right', fill='y')
        self._path_text.pack(side='left', fill='both', expand=True)

        # ── status ──
        self._divider()
        self._status_lbl = tk.Label(self, text='Aguardando execução...',
                                    font=self._fonts['section'],
                                    bg=COLORS['panel'],
                                    fg=COLORS['text_dim'],
                                    anchor='w', wraplength=200, justify='left')
        self._status_lbl.pack(padx=14, pady=(4, 10), anchor='w')

    # ── API pública ──────────────────────────────────────────────────────────

    def update_result(self, result: SearchResult):
        """Atualiza todos os widgets com os dados do SearchResult."""
        path     = result.path
        cost     = result.cost
        depth    = result.depth

        self._cost_lbl.config(
            text=str(cost) if result.found else '∞',
            fg=COLORS['warning'] if result.found else COLORS['danger'],
        )
        self._depth_lbl.config(text=str(depth))

        profit = result.profit
        self._profit_lbl.config(
            text=f'+{profit}' if profit and profit > 0 else (str(profit) if profit is not None else '—'),
            fg=COLORS['accent'] if profit and profit > 0 else (COLORS['danger'] if profit is not None else COLORS['text_dim']),
        )

        self._path_text.config(state='normal')
        self._path_text.delete('1.0', 'end')
        if result.found:
            self._path_text.insert('end', ' → '.join(path) + '\n\n')
            self._path_text.insert('end', f'Custo total: {cost}\n')
            self._path_text.insert('end', f'Profundidade: {depth}\n')
            self._path_text.insert('end', f'Ganho: {profit} %\n')
        else:
            self._path_text.insert('end', 'Nenhum caminho encontrado.')
        self._path_text.config(state='disabled')

    def clear(self):
        """Restaura o painel ao estado inicial."""
        self._cost_lbl.config(text='—', fg=COLORS['warning'])
        self._depth_lbl.config(text='—')
        self._profit_lbl.config(text='—')
        self._path_text.config(state='normal')
        self._path_text.delete('1.0', 'end')
        self._path_text.config(state='disabled')
        self.set_status('Aguardando execução...', COLORS['text_dim'])

    def set_status(self, message: str, color: str = None):
        """Exibe uma mensagem na barra de status com a cor indicada."""
        color = color or COLORS['text_dim']
        self._status_lbl.config(text=message, fg=color)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _stat_box(self, parent, label_text: str) -> tk.Label:
        """Cria e retorna um box de estatística com rótulo e valor."""
        box = tk.Frame(parent, bg=COLORS['node_default'],
                       highlightbackground=COLORS['panel_border'],
                       highlightthickness=1)
        box.pack(side='left', expand=True, fill='both', padx=2)
        tk.Label(box, text=label_text, font=self._fonts['section'],
                 bg=COLORS['node_default'],
                 fg=COLORS['text_dim']).pack(pady=(6, 0))
        val_lbl = tk.Label(box, text='—',
                           font=tkfont.Font(family='Courier', size=14, weight='bold'),
                           bg=COLORS['node_default'],
                           fg=COLORS['accent'])
        val_lbl.pack(pady=(0, 6))
        return val_lbl

    def _section(self, text: str):
        """Renderiza um rótulo de seção com estilo de cabeçalho."""
        tk.Label(self, text=text, font=self._fonts['section'],
                 bg=COLORS['panel'], fg=COLORS['accent2'],
                 anchor='w').pack(padx=16, pady=(10, 2), fill='x')

    def _divider(self):
        """Insere uma linha horizontal separadora entre seções."""
        tk.Frame(self, bg=COLORS['panel_border'], height=1).pack(
            fill='x', padx=12, pady=6)