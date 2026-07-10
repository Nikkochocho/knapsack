"""
ui/result_panel.py
==================
Right panel of the interface: cost display, path found, and status bar.
"""

import  tkinter         as tk
from    tkinter         import font as tkfont
from    config           import COLORS
from    search_result   import SearchResult
import  i18n


class ResultPanel(tk.Frame):
    """Right-side panel with cost, path found, and status bar."""

    def __init__(self, parent, fonts: dict, **kwargs):
        """Initialize the panel and build the result widgets."""
        super().__init__(parent, bg=COLORS['panel'], width=230,
                         highlightbackground=COLORS['panel_border'],
                         highlightthickness=1, **kwargs)
        self.pack_propagate(False)
        self._fonts = fonts

        # Registry of (widget, i18n_key) pairs refreshed on language change.
        self._i18n_widgets: list[tuple[tk.Widget, str]] = []
        # Last SearchResult rendered, so the path panel can be re-rendered
        # in the new language when the user switches languages.
        self._last_result: SearchResult | None = None

        self._build()

    # ── i18n helpers ─────────────────────────────────────────────────────────

    def _register(self, widget: tk.Widget, key: str) -> None:
        """Register a widget's `text` option for translation and set it now."""
        self._i18n_widgets.append((widget, key))
        widget.config(text=i18n.t(key))

    def refresh_language(self) -> None:
        """Re-apply translated text to every registered widget, and re-render
        the path panel if a result is currently displayed. Called by the
        main window whenever the active language changes."""
        for widget, key in self._i18n_widgets:
            if widget.winfo_exists():
                widget.config(text=i18n.t(key))
        if self._last_result is not None:
            self._render_path(self._last_result)

    # ── construction ─────────────────────────────────────────────────────────

    def _build(self):
        """Build the cost, stats, path, and status widgets."""
        self._section('rp_section_result')

        # ── total cost ──
        cost_box = tk.Frame(self, bg=COLORS['node_default'],
                            highlightbackground=COLORS['panel_border'],
                            highlightthickness=1)
        cost_box.pack(padx=14, pady=(4, 8), fill='x')
        time_lbl = tk.Label(cost_box,
                             font=self._fonts['section'],
                             bg=COLORS['node_default'],
                             fg=COLORS['text_dim'])
        self._register(time_lbl, 'rp_time_reached')
        time_lbl.pack(pady=(8, 0))
        self._cost_lbl = tk.Label(cost_box, text='—',
                                  font=self._fonts['big'],
                                  bg=COLORS['node_default'],
                                  fg=COLORS['warning'])
        self._cost_lbl.pack(pady=(0, 8))

        # ── stats ──
        stats = tk.Frame(self, bg=COLORS['panel'])
        stats.pack(padx=14, fill='x')
        self._depth_lbl = self._stat_box(stats, 'rp_stat_depth')

        self._profit_lbl = self._stat_box(stats, 'rp_stat_profit')

        # ── path ──
        self._divider()
        self._section('rp_section_path')

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
        self._status_lbl = tk.Label(self,
                                    font=self._fonts['section'],
                                    bg=COLORS['panel'],
                                    fg=COLORS['text_dim'],
                                    anchor='w', wraplength=200, justify='left')
        self._register(self._status_lbl, 'rp_status_waiting')
        self._status_lbl.pack(padx=14, pady=(4, 10), anchor='w')

    # ── public API ───────────────────────────────────────────────────────────

    def update_result(self, result: SearchResult):
        """Update all widgets with the data from a SearchResult."""
        self._last_result = result

        cost  = result.cost
        depth = result.depth
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

        self._render_path(result)

    def clear(self):
        """Reset the panel to its initial state."""
        self._last_result = None
        self._cost_lbl.config(text='—', fg=COLORS['warning'])
        self._depth_lbl.config(text='—')
        self._profit_lbl.config(text='—')
        self._path_text.config(state='normal')
        self._path_text.delete('1.0', 'end')
        self._path_text.config(state='disabled')
        self.set_status(i18n.t('rp_status_waiting'), COLORS['text_dim'])

    def set_status(self, message: str, color: str = None):
        """Display a message in the status bar with the given color."""
        color = color or COLORS['text_dim']
        self._status_lbl.config(text=message, fg=color)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _render_path(self, result: SearchResult) -> None:
        """Render the found path (or a not-found message) into the text box,
        in the currently active language."""
        path  = result.path
        cost  = result.cost
        depth = result.depth
        profit = result.profit

        self._path_text.config(state='normal')
        self._path_text.delete('1.0', 'end')
        if result.found:
            self._path_text.insert('end', ' → '.join(path) + '\n\n')
            self._path_text.insert('end', i18n.t('rp_path_total_cost', cost=cost))
            self._path_text.insert('end', i18n.t('rp_path_depth', depth=depth))
            self._path_text.insert('end', i18n.t('rp_path_gain', profit=profit))
        else:
            self._path_text.insert('end', i18n.t('rp_path_none_found'))
        self._path_text.config(state='disabled')

    def _stat_box(self, parent, label_key: str) -> tk.Label:
        """Create and return a stat box with a translated label and a value."""
        box = tk.Frame(parent, bg=COLORS['node_default'],
                       highlightbackground=COLORS['panel_border'],
                       highlightthickness=1)
        box.pack(side='left', expand=True, fill='both', padx=2)
        lbl = tk.Label(box, font=self._fonts['section'],
                        bg=COLORS['node_default'],
                        fg=COLORS['text_dim'])
        self._register(lbl, label_key)
        lbl.pack(pady=(6, 0))
        val_lbl = tk.Label(box, text='—',
                           font=tkfont.Font(family='Courier', size=14, weight='bold'),
                           bg=COLORS['node_default'],
                           fg=COLORS['accent'])
        val_lbl.pack(pady=(0, 6))
        return val_lbl

    def _section(self, key: str):
        """Render a section header label with the standard heading style."""
        lbl = tk.Label(self, font=self._fonts['section'],
                       bg=COLORS['panel'], fg=COLORS['accent2'],
                       anchor='w')
        self._register(lbl, key)
        lbl.pack(padx=16, pady=(10, 2), fill='x')

    def _divider(self):
        """Insert a horizontal divider line between sections."""
        tk.Frame(self, bg=COLORS['panel_border'], height=1).pack(
            fill='x', padx=12, pady=6)