"""
ui/control_panel.py
==================================================================
Left panel of the interface: method selection, states and buttons.
"""

from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import config
import i18n
from config import COLORS, SEARCH_METHODS
from ui.comparative_window import ComparativeWindow


# Methods that show tmax (canonical English keys — see config.SEARCH_METHODS)
TMAX_METHODS  = {'Hill Climbing (Random Restart)'}
# Methods that show t1, tf, fr
TEMPERA_METHODS = {'Simulated Annealing'}
AG_METHODS      = {'Genetic Algorithm'}


class ControlPanel(tk.Frame):

    def __init__(self, parent, on_search, on_reset, fonts: dict,
                 on_regenerate=None, on_clear_path=None, on_clear_result=None,
                 on_pick_start=None, on_pick_goal=None,
                 on_regenerate_multiverse=None,
                 on_exit_multiverse=None,
                 on_comparative=None,
                 on_initial_solution=None,**kwargs):

        super().__init__(parent, bg=COLORS['panel'], width=240,
                     highlightbackground=COLORS['panel_border'],
                     highlightthickness=1, **kwargs)
        self.pack_propagate(False)

        # ── scrollable inner frame ────────────────────────────────────────
        canvas = tk.Canvas(self, bg=COLORS['panel'],
                        highlightthickness=0, width=224)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        self._inner = tk.Frame(canvas, bg=COLORS['panel'])

        self._inner.bind('<Configure>',
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self._inner, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(
                            -1 * (e.delta // 120), 'units'))
        # ─────────────────────────────────────────────────────────────────

        self._on_search                = on_search
        self._on_reset                 = on_reset
        self._fonts                    = fonts
        self._on_regenerate            = on_regenerate
        self._on_clear_path            = on_clear_path
        self._on_clear_result          = on_clear_result
        self._on_pick_start            = on_pick_start
        self._on_pick_goal             = on_pick_goal
        self._on_regenerate_multiverse = on_regenerate_multiverse
        self._on_exit_multiverse       = on_exit_multiverse
        self._on_comparative           = on_comparative
        self._on_initial_solution      = on_initial_solution
        self._pick_btns: dict[str, tk.Button] = {}
        self._legend_imgs = []

        # Registry of (widget, i18n_key) pairs refreshed on language change.
        self._i18n_widgets: list[tuple[tk.Widget, str]] = []
        # Canonical (English) search-method key currently selected, kept
        # separate from the translated label shown in the combobox.
        self._selected_method_key = SEARCH_METHODS[0]

        self._build()
        self._apply_combobox_style()

    # ── i18n helpers ─────────────────────────────────────────────────────────

    def _register(self, widget: tk.Widget, key: str) -> None:
        """Register a widget's `text` option for translation and set it now."""
        self._i18n_widgets.append((widget, key))
        widget.config(text=i18n.t(key))

    def _label(self, parent, key: str, **extra) -> tk.Label:
        """Create a translated section/field label and register it."""
        lbl = tk.Label(parent, font=self._fonts['section'],
                        bg=COLORS['panel'], fg=COLORS['text_dim'])
        self._register(lbl, key)
        return lbl

    def refresh_language(self) -> None:
        """Re-apply translated text to every registered widget. Called by
        the main window whenever the active language changes."""
        for widget, key in self._i18n_widgets:
            if widget.winfo_exists():
                widget.config(text=i18n.t(key))
        self._refresh_method_combobox()

    def _refresh_method_combobox(self) -> None:
        """Update the method dropdown's displayed labels and keep the
        currently selected canonical method in sync with the new language."""
        labels = [i18n.method_label(k) for k in SEARCH_METHODS]
        self._method_cb['values'] = labels
        self.method_var.set(i18n.method_label(self._selected_method_key))

    # ── construction ─────────────────────────────────────────────────────────

    def _build(self):
        pad = {'padx': 16, 'pady': 4}

        # ── search method ────────────────────────────────────────────────────
        self._section(self._label(self._inner, 'cp_section_method',
                                   anchor='w'))
        self.method_var = tk.StringVar(value=i18n.method_label(self._selected_method_key))
        self._method_cb = ttk.Combobox(
            self._inner, textvariable=self.method_var,
            values=[i18n.method_label(k) for k in SEARCH_METHODS],
            state='readonly', width=26, font=self._fonts['mono'])
        self._method_cb.pack(**pad, fill='x')
        self._method_cb.bind('<<ComboboxSelected>>', self._on_method_change)

        # ── tmax parameter (Hill Climbing w/ Random Restart) ────────────────
        self._tmax_frame = tk.Frame(self._inner, bg=COLORS['panel'])
        self._tmax_frame.pack(**pad, fill='x')
        self._label(self._tmax_frame, 'cp_label_tmax').pack(anchor='w')
        self.tmax_var = tk.IntVar(value=20)
        tk.Spinbox(self._tmax_frame, from_=1, to=500,
                   textvariable=self.tmax_var, width=8,
                   font=self._fonts['mono'],
                   bg=COLORS['node_default'], fg=COLORS['text'],
                   buttonbackground=COLORS['panel_border'],
                   relief='flat', insertbackground=COLORS['text'],
                   ).pack(anchor='w')
        self._tmax_frame.pack_forget()

        # ── simulated annealing parameters ───────────────────────────────────
        self._tempera_frame = tk.Frame(self._inner, bg=COLORS['panel'])
        self._tempera_frame.pack(**pad, fill='x')

        for key, var_name, default, mn, mx, inc, fmt in [
            ('cp_label_t1', '_t1_var',  100.0, 1.0,  1000.0, 10.0,  '%.1f'),
            ('cp_label_tf', '_tf_var',    0.1, 0.01,   10.0,  0.1,  '%.2f'),
            ('cp_label_fr', '_fr_var',   0.95, 0.01,    0.99, 0.01, '%.2f'),
        ]:
            self._label(self._tempera_frame, key).pack(anchor='w')
            var = tk.DoubleVar(value=default)
            setattr(self, var_name, var)
            tk.Spinbox(self._tempera_frame, from_=mn, to=mx, increment=inc,
                       textvariable=var, width=8, format=fmt,
                       font=self._fonts['mono'],
                       bg=COLORS['node_default'], fg=COLORS['text'],
                       buttonbackground=COLORS['panel_border'],
                       relief='flat', insertbackground=COLORS['text'],
                       ).pack(anchor='w', pady=(0, 6))
        self._tempera_frame.pack_forget()

        # ── genetic algorithm parameters ─────────────────────────────────────
        self._ag_frame = tk.Frame(self._inner, bg=COLORS['panel'])
        self._ag_frame.pack(**pad, fill='x')

        for key, var_name, default, mn, mx, inc, fmt, tipo in [
            ('cp_label_tp', '_tp_var',  10,  2,  100,  1,    '%d',    'int'),
            ('cp_label_ng', '_ng_var',  20,  1,  500,  1,    '%d',    'int'),
            ('cp_label_tc', '_tc_var',  0.8, 0.0, 1.0, 0.05, '%.2f', 'float'),
            ('cp_label_tm', '_tm_var',  0.1, 0.0, 1.0, 0.01, '%.2f', 'float'),
            ('cp_label_ig', '_ig_var',  0.2, 0.0, 1.0, 0.05, '%.2f', 'float'),
        ]:
            self._label(self._ag_frame, key).pack(anchor='w')
            var = tk.IntVar(value=int(default)) if tipo == 'int' else tk.DoubleVar(value=default)
            setattr(self, var_name, var)
            tk.Spinbox(self._ag_frame,
                       from_=mn, to=mx, increment=inc,
                       textvariable=var, width=8,
                       format=fmt if tipo == 'float' else None,
                       font=self._fonts['mono'],
                       bg=COLORS['node_default'], fg=COLORS['text'],
                       buttonbackground=COLORS['panel_border'],
                       relief='flat', insertbackground=COLORS['text'],
                       ).pack(anchor='w', pady=(0, 6))

        self._ag_frame.pack_forget()

        # ── capacity (time limit) ────────────────────────────────────────────
        self._divider()
        self._label(self._inner, 'cp_section_capacity', anchor='w',
                    fg=COLORS['accent2']).pack(padx=16, pady=(10, 2), fill='x')
        cap_frame = tk.Frame(self._inner, bg=COLORS['panel'])
        cap_frame.pack(padx=16, pady=(0, 4), fill='x')
        self._label(cap_frame, 'cp_label_time_limit').pack(anchor='w')
        self.tempo_limite_var = tk.DoubleVar(value=10.0)
        tk.Spinbox(cap_frame, from_=0.1, to=9999.0, increment=0.5,
                   textvariable=self.tempo_limite_var, width=8, format='%.1f',
                   font=self._fonts['mono'],
                   bg=COLORS['node_default'], fg=COLORS['text'],
                   buttonbackground=COLORS['panel_border'],
                   relief='flat', insertbackground=COLORS['text'],
                   ).pack(anchor='w')

        # ── initial state ────────────────────────────────────────────────────
        self._divider()
        self._label(self._inner, 'cp_section_start_state', anchor='w',
                    fg=COLORS['accent2']).pack(padx=16, pady=(10, 2), fill='x')
        start_row = tk.Frame(self._inner, bg=COLORS['panel'])
        start_row.pack(padx=16, pady=(0, 4), fill='x')
        self.start_var = tk.StringVar(value=config.STATES[0])
        self.start_var.trace_add('write', self._on_state_change)
        self._start_cb = ttk.Combobox(start_row, textvariable=self.start_var,
                                      values=config.STATES, state='readonly',
                                      width=10, font=self._fonts['mono'])
        self._start_cb.bind('<<ComboboxSelected>>', self._clear)
        self._start_cb.pack(side='left')
        pick_start_btn = tk.Button(
            start_row, text='📍', font=self._fonts['mono'],
            bg=COLORS['node_default'], fg=COLORS['accent'],
            activebackground=COLORS['accent'], activeforeground='#ffffff',
            relief='flat', cursor='hand2', padx=6,
            command=self._fire_pick_start)
        pick_start_btn.pack(side='left', padx=(6, 0))
        self._pick_btns['start'] = pick_start_btn

        # ── goal state ───────────────────────────────────────────────────────
        self._label(self._inner, 'cp_section_goal_state', anchor='w',
                    fg=COLORS['accent2']).pack(padx=16, pady=(10, 2), fill='x')
        goal_row = tk.Frame(self._inner, bg=COLORS['panel'])
        goal_row.pack(padx=16, pady=(0, 4), fill='x')
        self.goal_var = tk.StringVar(value=config.STATES[-1])
        self.goal_var.trace_add('write', self._on_state_change)
        self._goal_cb = ttk.Combobox(goal_row, textvariable=self.goal_var,
                                     values=config.STATES, state='readonly',
                                     width=10, font=self._fonts['mono'])
        self._goal_cb.bind('<<ComboboxSelected>>', self._clear)
        self._goal_cb.pack(side='left')
        pick_goal_btn = tk.Button(
            goal_row, text='🎯', font=self._fonts['mono'],
            bg=COLORS['node_default'], fg=COLORS['success'],
            activebackground=COLORS['success'], activeforeground='#ffffff',
            relief='flat', cursor='hand2', padx=6,
            command=self._fire_pick_goal)
        pick_goal_btn.pack(side='left', padx=(6, 0))
        self._pick_btns['goal'] = pick_goal_btn

        # ── action buttons ───────────────────────────────────────────────────
        self._divider()

        initial_btn = tk.Button(
            self._inner,
            font=self._fonts['section'],
            bg=COLORS['panel_border'], fg=COLORS['text_dim'],
            activebackground=COLORS['node_default'],
            activeforeground=COLORS['text'],
            relief='flat', cursor='hand2',
            command=self._fire_initial_solution, pady=6)
        self._register(initial_btn, 'cp_btn_initial_solution')
        initial_btn.pack(padx=16, pady=(0, 4), fill='x')

        run_btn = tk.Button(
            self._inner,
            font=self._fonts['section'],
            bg=COLORS['accent'], fg='#ffffff',
            activebackground='#6AAAF8', activeforeground='#ffffff',
            relief='flat', cursor='hand2',
            command=self._fire_search, pady=8)
        self._register(run_btn, 'cp_btn_run_search')
        run_btn.pack(padx=16, pady=(8, 4), fill='x')

        clear_btn = tk.Button(
            self._inner,
            font=self._fonts['section'],
            bg=COLORS['node_default'], fg=COLORS['text_dim'],
            activebackground=COLORS['panel_border'],
            activeforeground=COLORS['text'],
            relief='flat', cursor='hand2',
            command=self._on_reset, pady=6)
        self._register(clear_btn, 'cp_btn_clear')
        clear_btn.pack(padx=16, pady=(0, 4), fill='x')

        if self._on_regenerate:
            new_map_btn = tk.Button(
                self._inner,
                font=self._fonts['section'],
                bg=COLORS['panel_border'], fg=COLORS['warning'],
                activebackground=COLORS['node_default'],
                activeforeground=COLORS['warning'],
                relief='flat', cursor='hand2',
                command=self._on_regenerate, pady=6)
            self._register(new_map_btn, 'cp_btn_new_map')
            new_map_btn.pack(padx=16, pady=(0, 4), fill='x')

        # ── animation ─────────────────────────────────────────────────────────
        self._divider()
        self.animate_var = tk.BooleanVar(value=True)
        animate_chk = tk.Checkbutton(
            self._inner, variable=self.animate_var,
            font=self._fonts['section'],
            bg=COLORS['panel'], fg=COLORS['text_dim'],
            activebackground=COLORS['panel'],
            selectcolor=COLORS['node_default'],
            relief='flat', cursor='hand2')
        self._register(animate_chk, 'cp_checkbox_animate')
        animate_chk.pack(padx=16, pady=(0, 4), anchor='center')

        # ── comparative analysis ─────────────────────────────────────────────
        self._divider()
        comparative_btn = tk.Button(
            self._inner,
            font=self._fonts['section'],
            bg=COLORS['panel_border'], fg=COLORS['accent'],
            activebackground=COLORS['node_default'],
            activeforeground=COLORS['accent'],
            relief='flat', cursor='hand2',
            command=self._fire_comparative, pady=6)
        self._register(comparative_btn, 'cp_btn_comparative')
        comparative_btn.pack(padx=16, pady=(0, 4), fill='x')

        # ── multiverse section ───────────────────────────────────────────────
        if self._on_regenerate_multiverse:
            self._divider()
            self._label(self._inner, 'cp_section_multiverse', anchor='w',
                        fg=COLORS['accent2']).pack(padx=16, pady=(10, 2), fill='x')

            mv_grid = tk.Frame(self._inner, bg=COLORS['panel'])
            mv_grid.pack(padx=16, pady=(0, 4), fill='x')

            self._label(mv_grid, 'cp_label_n_maps'
                        ).grid(row=0, column=0, sticky='w', pady=2)
            self._n_maps_var = tk.IntVar(value=4)
            tk.Spinbox(mv_grid, from_=2, to=12,
                       textvariable=self._n_maps_var, width=5,
                       font=self._fonts['mono'],
                       bg=COLORS['node_default'], fg=COLORS['text'],
                       buttonbackground=COLORS['panel_border'],
                       relief='flat', insertbackground=COLORS['text'],
                       ).grid(row=0, column=1, sticky='w', padx=(8, 0), pady=2)

            self._label(mv_grid, 'cp_label_portal_cost'
                        ).grid(row=1, column=0, sticky='w', pady=2)
            self._portal_cost_var = tk.DoubleVar(value=1.0)
            tk.Spinbox(mv_grid, from_=0.1, to=10.0, increment=0.5,
                       textvariable=self._portal_cost_var, width=5,
                       format='%.1f',
                       font=self._fonts['mono'],
                       bg=COLORS['node_default'], fg=COLORS['text'],
                       buttonbackground=COLORS['panel_border'],
                       relief='flat', insertbackground=COLORS['text'],
                       ).grid(row=1, column=1, sticky='w', padx=(8, 0), pady=2)

            self._gen_mv_btn = tk.Button(
                self._inner,
                font=self._fonts['section'],
                bg=COLORS['accent2'], fg='#ffffff',
                activebackground='#FAAB50', activeforeground='#ffffff',
                relief='flat', cursor='hand2',
                command=self._fire_regenerate_multiverse, pady=6,
            )
            self._register(self._gen_mv_btn, 'cp_btn_generate_multiverse')
            self._gen_mv_btn.pack(padx=16, pady=(4, 4), fill='x')

            self._exit_mv_btn = tk.Button(
                self,
                font=self._fonts['section'],
                bg=COLORS['node_default'], fg=COLORS['warning'],
                activebackground=COLORS['panel_border'],
                activeforeground=COLORS['warning'],
                relief='flat', cursor='hand2',
                command=self._fire_exit_multiverse, pady=6,
            )
            self._register(self._exit_mv_btn, 'cp_btn_exit_multiverse')

            self._divider()
            legend_btn = tk.Button(
                self._inner,
                font=self._fonts['section'],
                bg=COLORS['panel_border'], fg=COLORS['text_dim'],
                activebackground=COLORS['node_default'],
                activeforeground=COLORS['text'],
                relief='flat', cursor='hand2',
                command=self._open_legend, pady=6)
            self._register(legend_btn, 'cp_btn_legend')
            legend_btn.pack(padx=16, pady=(0, 4), fill='x')

    # ── public API ───────────────────────────────────────────────────────────

    def refresh_states(self, states: list[str], start: str, goal: str):
        self._start_cb['values'] = states
        self._goal_cb['values']  = states
        self.start_var.set(start)
        self.goal_var.set(goal)

    def set_pick_active(self, role: str | None):
        styles   = {'start': (COLORS['accent'],  '#ffffff'),
                    'goal':  (COLORS['success'], '#ffffff')}
        defaults = {'start': (COLORS['node_default'], COLORS['accent']),
                    'goal':  (COLORS['node_default'], COLORS['success'])}
        for key, btn in self._pick_btns.items():
            bg, fg = styles[key] if key == role else defaults[key]
            btn.config(bg=bg, fg=fg)

    # ── events ───────────────────────────────────────────────────────────────

    def _fire_pick_start(self):
        self.set_pick_active('start')
        if self._on_pick_start:
            self._on_pick_start()

    def _fire_pick_goal(self):
        self.set_pick_active('goal')
        if self._on_pick_goal:
            self._on_pick_goal()

    def _fire_search(self):
        # Use the canonical (English) key for dispatch, not the translated
        # label currently shown in the combobox.
        method = self._selected_method_key
        self._on_search(
            method=method,
            start=self.start_var.get(),
            goal=self.goal_var.get(),
            tmax=self.tmax_var.get(),
            t1=self._t1_var.get(),
            tf=self._tf_var.get(),
            fr=self._fr_var.get(),
            tempo_limite=self.tempo_limite_var.get(),
            # ── GA ──────────────────────────────
            tp=self._tp_var.get(),
            ng=self._ng_var.get(),
            tc=self._tc_var.get(),
            tm=self._tm_var.get(),
            ig=self._ig_var.get(),
        )

    def _fire_regenerate_multiverse(self):
        if self._on_regenerate_multiverse:
            self._on_regenerate_multiverse(
                n_maps=self._n_maps_var.get(),
                portal_cost=self._portal_cost_var.get(),
            )
            self._exit_mv_btn.pack(padx=16, pady=(0, 4), fill='x',
                                   after=self._gen_mv_btn)

    def _fire_exit_multiverse(self):
        self._exit_mv_btn.pack_forget()
        if self._on_exit_multiverse:
            self._on_exit_multiverse()

    def _fire_comparative(self):
        if self._on_comparative:
            self._on_comparative()
        else:
            ComparativeWindow(self.winfo_toplevel(), self._fonts)

    def _fire_initial_solution(self):
        if self._on_initial_solution:
            self._on_initial_solution()

    def _on_state_change(self, *_):
        config.START_NODE = self.start_var.get()
        config.GOAL_NODE  = self.goal_var.get()
        self._clear()

    def _on_method_change(self, _event=None):
        self._clear()

        # Map the selected (translated) label back to its canonical key.
        labels = [i18n.method_label(k) for k in SEARCH_METHODS]
        selected_label = self.method_var.get()
        if selected_label in labels:
            self._selected_method_key = SEARCH_METHODS[labels.index(selected_label)]
        method = self._selected_method_key

        self._tmax_frame.pack_forget()
        self._tempera_frame.pack_forget()
        self._ag_frame.pack_forget()

        if method in TMAX_METHODS:
            self._tmax_frame.pack(padx=16, pady=4, fill='x')
        elif method in TEMPERA_METHODS:
            self._tempera_frame.pack(padx=16, pady=4, fill='x')
        elif method in AG_METHODS:
            self._ag_frame.pack(padx=16, pady=4, fill='x')

    # ── helpers ──────────────────────────────────────────────────────────────

    def _section(self, label_widget: tk.Label):
        """Apply the standard accent styling to a section header label."""
        label_widget.config(fg=COLORS['accent2'])
        label_widget.pack(padx=16, pady=(10, 2), fill='x')

    def _divider(self):
        tk.Frame(self._inner, bg=COLORS['panel_border'], height=1).pack(
            fill='x', padx=12, pady=6)

    def _clear(self, _event=None):
        if self._on_clear_path:
            self._on_clear_path()
        if self._on_clear_result:
            self._on_clear_result()

    @staticmethod
    def _apply_combobox_style():
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TCombobox',
                        fieldbackground=COLORS['node_default'],
                        background=COLORS['node_default'],
                        foreground=COLORS['text'],
                        selectbackground=COLORS['accent'],
                        selectforeground='#ffffff',
                        arrowcolor=COLORS['accent'],
                        bordercolor=COLORS['panel_border'],
                        lightcolor=COLORS['panel_border'],
                        darkcolor=COLORS['panel_border'])
        style.map('TCombobox',
                  fieldbackground=[('readonly', COLORS['node_default'])],
                  foreground=[('readonly', COLORS['text'])],
                  selectbackground=[('readonly', COLORS['accent'])],
                  selectforeground=[('readonly', '#ffffff')])

    def _open_legend(self):
        win = tk.Toplevel(self)
        win.title(i18n.t('legend_title'))
        win.configure(bg=COLORS['panel'])
        win.resizable(False, False)

        _ROOT = Path(__file__).parent.parent

        def _load_tileset(filename):
            path = _ROOT / 'assets' / 'tilesets' / filename
            try:
                img = Image.open(path).resize((32, 32), Image.NEAREST)
                tk_img = ImageTk.PhotoImage(img)
                self._legend_imgs.append(tk_img)
                return tk_img
            except Exception:
                return None

        def _section(text):
            tk.Label(win, text=text, font=self._fonts['section'],
                     bg=COLORS['panel'], fg=COLORS['accent2'],
                     anchor='w').pack(padx=16, pady=(10, 2), fill='x')

        def _divider():
            tk.Frame(win, bg=COLORS['panel_border'], height=1).pack(
                fill='x', padx=12, pady=6)

        _section(i18n.t('cp_section_states_transitions'))
        for filename, label in [
            ('start.png',  i18n.t('legend_start_state')),
            ('goal.png',   i18n.t('legend_goal_state')),
            ('path.png',   i18n.t('legend_path_found')),
            ('portal.png', i18n.t('legend_map_portal')),
        ]:
            row = tk.Frame(win, bg=COLORS['panel'])
            row.pack(anchor='w', padx=16, pady=2)
            tk_img = _load_tileset(filename)
            if tk_img:
                tk.Label(row, image=tk_img, bg=COLORS['panel']).pack(side='left')
            else:
                tk.Label(row, text='●', font=self._fonts['label'],
                         fg=COLORS['text_dim'], bg=COLORS['panel']).pack(side='left')
            tk.Label(row, text=label, font=self._fonts['label'],
                     fg=COLORS['text_dim'], bg=COLORS['panel'],
                     ).pack(side='left', padx=8)

        _divider()
        _section(i18n.t('cp_section_terrains'))
        for filename, label in [
            ('plains.png',   i18n.t('legend_plains')),
            ('forest.png',   i18n.t('legend_forest')),
            ('swamp.png',    i18n.t('legend_swamp')),
            ('mountain.png', i18n.t('legend_mountain')),
        ]:
            row = tk.Frame(win, bg=COLORS['panel'])
            row.pack(anchor='w', padx=16, pady=2)
            tk_img = _load_tileset(filename)
            if tk_img:
                tk.Label(row, image=tk_img, bg=COLORS['panel']).pack(side='left')
            else:
                tk.Label(row, text='■', font=self._fonts['label'],
                         fg=COLORS['text_dim'], bg=COLORS['panel']).pack(side='left')
            tk.Label(row, text=label, font=self._fonts['label'],
                     fg=COLORS['text_dim'], bg=COLORS['panel'],
                     ).pack(side='left', padx=8)

        _divider()
        tk.Button(win, text=i18n.t('legend_close'),
                  font=self._fonts['section'],
                  bg=COLORS['node_default'], fg=COLORS['text_dim'],
                  activebackground=COLORS['panel_border'],
                  relief='flat', cursor='hand2',
                  command=win.destroy, pady=6,
                  ).pack(padx=16, pady=(0, 12), fill='x')

        win.withdraw()
        win.update_idletasks()
        root = self.winfo_toplevel()
        w = win.winfo_reqwidth() + 80
        h = win.winfo_reqheight()
        x = root.winfo_rootx() + (root.winfo_width()  - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
        win.geometry(f'{w}x{h}+{x}+{y}')
        win.deiconify()