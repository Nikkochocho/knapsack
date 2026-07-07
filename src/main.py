"""
main.py
==============================================================
Main application orchestrator.
"""

import  webbrowser
import  tkinter     as tk
from    tkinter     import font
from    PIL         import Image, ImageTk
from    pathlib     import Path

import  config
import  i18n
from    config                      import COLORS, WINDOW
from    algorithms                  import run_search
from    multiverse                  import generate_multiverse
from    ui.graph_canvas             import GraphCanvas
from    ui.control_panel            import ControlPanel
from    ui.result_panel             import ResultPanel
from    algorithms.initial_solution import handle_initial_solution


class SearchApp(tk.Tk):
    """Main application window; orchestrates the canvas, panels and callbacks."""

    def __init__(self):
        """Initialize the window, fonts, internal state and build the UI."""
        super().__init__()
        i18n.set_language(i18n.DEFAULT_LANGUAGE)

        self.title(WINDOW['title'])
        self.configure(bg=COLORS['bg'])
        self.resizable(True, True)
        self.minsize(WINDOW['min_width'], WINDOW['min_height'])

        self._fonts = self._create_fonts()
        self._last_path:  list[str] = []
        self._last_start: str = config.START_NODE
        self._last_goal:  str = config.GOAL_NODE
        self._i18n_refresh: list[tuple[tk.Widget, callable]] = []
        self._build_ui()
        self._center_window()

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _create_fonts(self) -> dict:
        """Create and return the dictionary of fonts used across the interface."""
        return {
            'title':   font.Font(family='Courier', size=13, weight='bold'),
            'label':   font.Font(family='Courier', size=9),
            'section': font.Font(family='Courier', size=8,  weight='bold'),
            'mono':    font.Font(family='Courier', size=9),
            'big':     font.Font(family='Courier', size=22, weight='bold'),
            'node':    font.Font(family='Courier', size=11, weight='bold'),
        }

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        """Assemble the main layout: header, control panel, canvas and results."""
        self._build_header()
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(fill='both', expand=True)

        self.control = ControlPanel(
            body,
            on_search=self._handle_search,
            on_reset=self._handle_reset,
            on_regenerate=self._handle_regenerate,
            on_clear_path=lambda: self.graph_canvas.clear_path(),
            on_clear_result=lambda: self.result.clear(),
            on_pick_start=lambda: self.graph_canvas.set_pick_mode('start'),
            on_pick_goal=lambda: self.graph_canvas.set_pick_mode('goal'),
            on_regenerate_multiverse=self._handle_regenerate_multiverse,
            on_exit_multiverse=self._exit_multiverse,
            on_comparative=self._open_comparative,
            on_initial_solution=self._handle_initial_solution,
            fonts=self._fonts,
        )
        self.control.pack(side='left', fill='y', padx=(8, 4), pady=8)

        canvas_wrapper = tk.Frame(body, bg=COLORS['bg'])
        canvas_wrapper.pack(side='left', fill='both', expand=True, padx=4, pady=8)
        map_label = tk.Label(canvas_wrapper,
                              font=self._fonts['section'],
                              bg=COLORS['bg'], fg=COLORS['text_dim'],
                              anchor='w')
        map_label.pack(padx=4, pady=(4, 0))
        self._register_i18n(map_label, lambda w: w.config(text=i18n.t('generated_map')))

        self.graph_canvas = GraphCanvas(
            canvas_wrapper,
            on_node_picked=self._handle_node_picked,
            on_map_nav=self._handle_map_nav,
            on_map_switch=self._handle_map_switch,
            animation_on=True,
        )
        self.graph_canvas.set_fonts(self._fonts)
        self.graph_canvas.pack(fill='both', expand=True)

        self.control.animate_var.trace_add(
            'write', lambda *_: self.graph_canvas.set_animate(
                self.control.animate_var.get()))
        self.control.tempo_limite_var.trace_add(
            'write', lambda *_: setattr(config, 'TEMPO_LIMITE',
                                        self.control.tempo_limite_var.get()))

        self.result = ResultPanel(body, fonts=self._fonts)
        self.result.pack(side='right', fill='y', padx=(4, 8), pady=8)

    def _build_header(self):
        """Build the top bar with the title and global action buttons."""
        header = tk.Frame(self, bg=COLORS['panel'], height=48)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)

        title_label = tk.Label(header,
                                font=self._fonts['title'],
                                bg=COLORS['panel'], fg=COLORS['accent'])
        title_label.pack(side='left', padx=20, pady=10)
        self._register_i18n(
            title_label, lambda w: w.config(text=f"◈  {i18n.t('app_title')}  ◈"))

        btn_style = dict(font=self._fonts['label'], relief='flat',
                         cursor='hand2', padx=14, pady=4)

        btn_exit = tk.Button(header,
                              bg=COLORS['panel'], fg=COLORS['text_dim'],
                              activebackground='#c0392b', activeforeground='#ffffff',
                              command=self.destroy, **btn_style)
        btn_exit.pack(side='right', padx=(4, 16), pady=8)
        self._register_i18n(btn_exit, lambda w: w.config(text=i18n.t('btn_exit')))

        btn_about = tk.Button(header,
                               bg=COLORS['panel'], fg=COLORS['text_dim'],
                               activebackground=COLORS['accent'], activeforeground='#ffffff',
                               command=self._show_about, **btn_style)
        btn_about.pack(side='right', padx=4, pady=8)
        self._register_i18n(btn_about, lambda w: w.config(text=i18n.t('btn_about')))

        btn_settings = tk.Button(header,
                                  bg=COLORS['panel'], fg=COLORS['text_dim'],
                                  activebackground=COLORS['accent'], activeforeground='#ffffff',
                                  command=self._open_settings, **btn_style)
        btn_settings.pack(side='right', padx=4, pady=8)
        self._register_i18n(btn_settings, lambda w: w.config(text=i18n.t('btn_settings')))

    def _center_window(self):
        """Center the window on the screen at startup."""
        self.update_idletasks()
        w, h = WINDOW['width'], WINDOW['height']
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f'{w}x{h}+{x}+{y}')

    # ── i18n ──────────────────────────────────────────────────────────────────

    def _register_i18n(self, widget: tk.Widget, updater) -> None:
        """Register a widget updater so its text refreshes on language change.

        `updater` is a callable that receives the widget and applies the
        translated text to it. It is invoked immediately (to set the initial
        text) and again every time the language changes.
        """
        self._i18n_refresh.append((widget, updater))
        updater(widget)

    def _apply_language(self, lang: str) -> None:
        """Switch the active language and refresh all registered widgets."""
        i18n.set_language(lang)
        for widget, updater in self._i18n_refresh:
            if widget.winfo_exists():
                updater(widget)

        # Propagate to child panels, if they expose a refresh hook.
        for panel in (getattr(self, 'control', None), getattr(self, 'result', None)):
            if panel is not None and hasattr(panel, 'refresh_language'):
                panel.refresh_language()

    def _open_settings(self):
        """Open the settings window to switch the interface language."""
        win = tk.Toplevel(self)
        win.title(i18n.t('settings_title'))
        win.resizable(False, False)
        win.configure(bg=COLORS['panel'])
        win.grab_set()

        w, h = 320, 190
        win.withdraw()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        win.geometry(f'{w}x{h}+{x}+{y}')
        win.deiconify()

        tk.Label(win, text=i18n.t('settings_title'),
                 font=self._fonts['title'],
                 bg=COLORS['panel'], fg=COLORS['accent']).pack(pady=(18, 8))

        tk.Label(win, text=i18n.t('settings_language_label'),
                 font=self._fonts['label'],
                 bg=COLORS['panel'], fg=COLORS['text']).pack(pady=(0, 12))

        btn_row = tk.Frame(win, bg=COLORS['panel'])
        btn_row.pack(pady=4)

        def _select(lang: str):
            self._apply_language(lang)
            win.destroy()

        def _lang_button(parent, label: str, lang_code: str):
            active = i18n.get_language() == lang_code
            return tk.Button(
                parent, text=label, font=self._fonts['label'],
                bg=COLORS['accent'] if active else COLORS['panel'],
                fg='#ffffff' if active else COLORS['text'],
                activebackground=COLORS['accent'], activeforeground='#ffffff',
                relief='flat', cursor='hand2', padx=16, pady=6,
                command=lambda: _select(lang_code))

        _lang_button(btn_row, 'English', 'en').pack(side='left', padx=6)
        _lang_button(btn_row, 'Português', 'pt').pack(side='left', padx=6)

        tk.Button(win, text=i18n.t('settings_close'),
                  font=self._fonts['label'],
                  bg=COLORS['panel'], fg=COLORS['text_dim'],
                  relief='flat', cursor='hand2',
                  command=win.destroy).pack(pady=14)

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _handle_search(self, method: str, start: str, goal: str,
                   tmax: int = 20,
                   t1: float = 100.0, tf: float = 0.1, fr: float = 0.95,
                   tempo_limite: float = 10.0,
                   tp=10, ng=20, tc=0.8, tm=0.1, ig=0.2):

        config.ACTIVE_METHOD = method

        if start == goal:
            self.result.set_status(i18n.t('status_start_eq_goal'), COLORS['warning'])
            return

        self.result.set_status(i18n.t('status_running', method=method), COLORS['accent'])
        self.update()

        graph = config.SUPER_GRAPH if config.MULTIVERSE_MODE else config.GRAPH

        result = run_search(
            method=method,
            start=start,
            goal=goal,
            graph=graph,
            tmax=tmax,
            t1=t1,
            tf=tf,
            fr=fr,
            tempo_limite=tempo_limite,
            tp=tp, ng=ng, tc=tc, tm=tm, ig=ig,
        )

        config.GOAL_REACHED = result.path[-1] == goal if result.path else False
        config.TEMPO_LIMITE = self.control.tempo_limite_var.get()
        self.graph_canvas.reset_visited()
        self.graph_canvas.render(path=result.path, start=start, goal=goal)
        self.result.update_result(result)

        self._last_path  = result.path
        self._last_start = start
        self._last_goal  = goal

        if not result.found:
            self.result.set_status(i18n.t('status_no_path'), COLORS['danger'])
        elif result.path[-1] != goal:
            self.result.set_status(
                i18n.t('status_time_limit', cost=result.cost, limit=config.TEMPO_LIMITE),
                COLORS['warning'])
        else:
            self.result.set_status(
                i18n.t('status_path_found', n=len(result.path)), COLORS['success'])

    def _on_body_resize(self, event):
        """Resize the background image when the window is resized."""
        if not hasattr(self, '_bg_pil_orig'):
            return
        from PIL import ImageTk
        self._bg_image = ImageTk.PhotoImage(
            self._bg_pil_orig.resize((event.width, event.height), Image.NEAREST))
        self._bg_label.config(image=self._bg_image)

    def _handle_regenerate(self):
        """Regenerate the simple grid or the multiverse, per the active mode."""
        if config.MULTIVERSE_MODE and config.MULTIVERSE is not None:
            self._handle_regenerate_multiverse(
                n_maps = config.MULTIVERSE.n_maps,
                portal_cost = config.PORTAL_COST,
            )
        else:
            config.regenerate_maze()
            self.graph_canvas.reset_visited()
            self.control.refresh_states(
                config.STATES, config.START_NODE, config.GOAL_NODE)
            self.graph_canvas.render()
            self.result.clear()

    def _handle_regenerate_multiverse(self, n_maps: int, portal_cost: float):
        """Generate a new multiverse and update global state and the interface."""
        config.PORTAL_COST = portal_cost
        self.result.set_status(i18n.t('status_generating_multiverse'), COLORS['accent'])
        self.update()

        mv = generate_multiverse(
            n_maps=n_maps,
            rows=config.MAZE_LOGICAL_ROWS,
            cols=config.MAZE_LOGICAL_COLS,
            portal_cost=portal_cost,
        )
        config.apply_multiverse(mv)

        self._last_path  = []
        self._last_start = config.START_NODE
        self._last_goal  = config.GOAL_NODE
        self.graph_canvas.reset_visited()

        self.control.refresh_states(
            [config.START_NODE, config.GOAL_NODE],
            config.START_NODE,
            config.GOAL_NODE,
        )
        self.graph_canvas.render()
        self.result.clear()
        self.result.set_status(
            i18n.t('status_multiverse_generated',
                   n_maps=n_maps, n_portals=len(mv.portals) // 2),
            COLORS['success'],
        )

    def _exit_multiverse(self):
        """Exit multiverse mode and regenerate a simple grid."""
        self.graph_canvas.reset_visited()
        config.MULTIVERSE_MODE = False
        config.MULTIVERSE = None
        self._handle_regenerate()

    def _handle_map_switch(self, new_map_id: int):
        """Update the active map when a portal is crossed during animation."""
        if not config.MULTIVERSE_MODE or config.MULTIVERSE is None:
            return
        if 0 <= new_map_id < config.MULTIVERSE.n_maps:
            config._apply_active_map(new_map_id)

    def _handle_map_nav(self, delta: int):
        """Manually navigate between multiverse maps via the side arrows."""
        if not config.MULTIVERSE_MODE or config.MULTIVERSE is None:
            return
        new_id = config.ACTIVE_MAP_ID + delta
        if 0 <= new_id < config.MULTIVERSE.n_maps:
            config._apply_active_map(new_id)
            self.graph_canvas.render(
                path=self._last_path,
                start=self._last_start,
                goal=self._last_goal,
                static=True,            # ← keep trail fixed, no re-animation
            )

    def _handle_reset(self):
        """Redraw the map without a path, keeping the current start and goal."""
        start = self.control.start_var.get()
        goal  = self.control.goal_var.get()
        self.graph_canvas.render(start=start, goal=goal)
        self.result.clear()

    def _handle_node_picked(self, role: str, node: str):
        """Register the clicked node as start or goal and redraw the map."""
        self.control.set_pick_active(None)
        if role == 'start':
            self.control.start_var.set(node)
            config.START_NODE = node
        else:
            self.control.goal_var.set(node)
            config.GOAL_NODE = node
        self.graph_canvas.clear_path()
        self.result.clear()
        start = self.control.start_var.get()
        goal  = self.control.goal_var.get()
        self.graph_canvas.render(start=start, goal=goal)

    def _open_comparative(self):
        from ui.comparative_window import ComparativeWindow
        ComparativeWindow(self, self._fonts)

    def _handle_initial_solution(self):
        handle_initial_solution(self)

    # ── About ─────────────────────────────────────────────────────────────────

    def _show_about(self):
        """Open the window with project information."""
        win = tk.Toplevel(self)
        win.title(i18n.t('about_title'))
        win.resizable(False, False)
        win.configure(bg=COLORS['panel'])
        win.grab_set()

        w, h = 630, 480
        win.withdraw()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        win.geometry(f'{w}x{h}+{x}+{y}')
        win.deiconify()

        font_family = self._fonts['label'].actual()['family']
        base_size   = self._fonts['label'].actual()['size']

        main_frame = tk.Frame(win, bg=COLORS['panel'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=10)

        tk.Label(main_frame, text=i18n.t('about_header'),
                 font=self._fonts['title'],
                 bg=COLORS['panel'], fg=COLORS['accent']
                 ).pack(pady=(10, 15))

        tk.Label(main_frame, text=i18n.t('about_developed_by'),
                 font=(font_family, base_size, 'bold'),
                 bg=COLORS['panel'], fg=COLORS['accent']).pack()

        tk.Label(main_frame,
                 text='Guilherme Carvalho Alvarenga & Lara Hydalgo Ferreira',
                 font=(self._fonts['label'], base_size + 2, 'bold'),
                 bg=COLORS['panel'], fg=COLORS['text']).pack(pady=(0, 20))

        tk.Label(main_frame, text=i18n.t('about_desc'),
                 font=self._fonts['label'],
                 bg=COLORS['panel'], fg=COLORS['text'],
                 justify='left', wraplength=550
                 ).pack(pady=10)

        tk.Label(main_frame, text=i18n.t('about_assets'),
                 font=(font_family, base_size, 'bold'),
                 bg=COLORS['panel'], fg=COLORS['accent']).pack()

        tk.Label(main_frame, text=i18n.t('about_repo'),
                 font=(font_family, base_size + 2, 'bold'),
                 bg=COLORS['panel'], fg=COLORS['accent']
                 ).pack(pady=(15, 0))

        repo_url = 'https://github.com/Nikkochocho/knapsack'
        link_label = tk.Label(main_frame, text=repo_url,
                              font=(font_family, base_size, 'underline'),
                              bg=COLORS['panel'], fg='#58a6ff',
                              cursor='hand2')
        link_label.pack(pady=15)
        link_label.bind('<Button-1>', lambda e: webbrowser.open_new(repo_url))

        tk.Button(main_frame, text=i18n.t('about_close'),
                  font=self._fonts['label'],
                  bg=COLORS['accent'], fg='#ffffff',
                  activebackground=COLORS['node_glow_start'],
                  relief='flat', cursor='hand2',
                  padx=30, pady=8,
                  command=win.destroy
                  ).pack(side='bottom', pady=20)


if __name__ == '__main__':
    app = SearchApp()
    app.mainloop()