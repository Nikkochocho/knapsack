"""
ui/graph_canvas.py
==================
Widget de canvas responsável exclusivamente pela renderização do mapa em grid.
Renderiza um grid 15x15 com células livres e paredes, conforme mostrado nos tilesets.
"""


from    __future__  import annotations
from    pathlib     import Path
import  tkinter     as tk
import  config
from    config      import COLORS
from    PIL         import Image, ImageTk
from    algorithms.BuscaLocal import BuscaLocal

# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de nó
# ─────────────────────────────────────────────────────────────────────────────

def _node_to_rc(node: str) -> tuple[int, int]:
    if ':' in node:
        node = node.split(':', 1)[1]
    inner = node.strip('()')
    r, c = inner.split(',')
    return int(r), int(c)


def _node_map_id(node: str) -> int | None:
    if node.startswith('M') and ':' in node:
        try:
            return int(node.split(':')[0][1:])
        except ValueError:
            pass
    return None


_TERRAIN_TILE: dict[str, str] = {
    'plains':   'plains',
    'forest':   'forest',
    'swamp':    'swamp',
    'mountain': 'mountain',
}

_TERRAIN_COLOR: dict[str, str] = {
    'plains':   'tile_free',
    'forest':   'tile_w2',
    'swamp':    'tile_w3',
    'mountain': 'tile_w5',
}

# ─────────────────────────────────────────────────────────────────────────────
# Widget principal
# ─────────────────────────────────────────────────────────────────────────────

class GraphCanvas(tk.Canvas):

    _MIN_CELL = 20
    _MAX_CELL = 48

    def __init__(self, parent, on_node_picked=None,
                 on_map_nav=None, on_map_switch=None,
                 animation_on=True, **kwargs):
        """Inicializa o canvas, bindings e estado interno da animação."""
        super().__init__(parent, bg=COLORS['bg'],
                         highlightthickness=0, **kwargs)

        self._fonts: dict = {}
        self._on_node_picked = on_node_picked
        self._on_map_nav     = on_map_nav      # callback(delta)   — setas manuais
        self._on_map_switch  = on_map_switch   # callback(map_id)  — troca automática
        self._animation_on   = animation_on
        self._pick_mode: str | None = None
        
        self._render_generation: int = 0

        self._tile_imgs:  dict[str, ImageTk.PhotoImage] = {}
        self._tile_pil:   dict[str, Image.Image]        = {}
        self._temp_imgs:  list[ImageTk.PhotoImage]      = []

        self._sprite_frames:    dict[str, list[ImageTk.PhotoImage]] = {}
        self._sprite_frame_idx: dict[str, int]                      = {}
        self._anim_jobs:        dict[str, str]                      = {}

        self._cached_cell: int | None = None

        # Estado da animação em curso (necessário para switch mid-animation)
        self._anim_full_path:  list[str] = []
        self._anim_full_start: str = ''
        self._anim_full_goal:  str = ''
        self._showing_sad = False   # ← nova flag

        # Rastreia até onde o personagem já chegou por mapa:
        # {map_id: [nós visitados nesse mapa, em ordem]}
        self._visited_per_map: dict[int, list[str]] = {}

        self.bind('<Configure>', lambda _e: self._reload_tiles() or self.render())
        self.bind('<Button-1>',  self._on_canvas_click)

    # ── API pública ──────────────────────────────────────────────────────────

    def set_fonts(self, fonts: dict):
        """Define o dicionário de fontes usado nos textos do canvas."""
        self._fonts = fonts

    def set_animate(self, value: bool):
        """Ativa ou desativa o modo de animação do caminho."""
        self._animation_on = value

    def clear_path(self):
        """Limpa o histórico de visitas e redesenha o mapa sem caminho."""
        self._showing_sad = False
        self._visited_per_map = {}
        self.render(path=[])

    def set_pick_mode(self, mode: str | None):
        """Ativa o modo de seleção de nó por clique, alterando o cursor."""
        self._pick_mode = mode
        self.config(cursor='crosshair' if mode else '')

    def reset_visited(self):
        """Cancela animações em curso e apaga o histórico de visitas."""
        # TODO: Fazer com que sprite retorne à posição do estado original
        # ao LIMPAR antes de animação ser finalizada
        # N° de tentativas: 5 ;-;
        self._cancel_all_anim()  
        self._visited_per_map  = {}
        self._anim_full_path   = []
        self._anim_full_start  = ''
        self._anim_full_goal   = ''

    # ── assets ───────────────────────────────────────────────────────────────

    def _reload_tiles(self):
        """Recarrega e redimensiona tiles e spritesheets conforme o tamanho atual do canvas."""
        cw = self.winfo_width()  or 600
        ch = self.winfo_height() or 480
        cell = self._cell_size(cw, ch, config.GRID_ROWS, config.GRID_COLS)
        if self._cached_cell == cell:
            return
        self._cached_cell = cell
        _ROOT = Path(__file__).parent.parent

        tile_paths = {
            'plains':   _ROOT / 'assets' / 'tilesets' / 'plains.png',
            'forest':   _ROOT / 'assets' / 'tilesets' / 'forest.png',
            'swamp':    _ROOT / 'assets' / 'tilesets' / 'swamp.png',
            'mountain': _ROOT / 'assets' / 'tilesets' / 'mountain.png',
            'wall':     _ROOT / 'assets' / 'tilesets' / 'wall.png',
            'path':     _ROOT / 'assets' / 'tilesets' / 'path.png',
            'portal':   _ROOT / 'assets' / 'tilesets' / 'portal.png',
        }
        self._tile_imgs = {}
        self._tile_pil  = {}
        for name, fp in tile_paths.items():
            try:
                img = Image.open(fp).convert('RGBA').resize((cell, cell), Image.NEAREST)
                self._tile_pil[name]  = img
                self._tile_imgs[name] = ImageTk.PhotoImage(img)
            except Exception:
                pass

        self._sprite_frames    = {}
        self._sprite_frame_idx = {}

        # USADO PRA SPRITES START E GOAL
        for sheet in ('start_down', 'start_up', 'start_left', 'start_right', 
                      'goal_down', 'goal_up', 'goal_left', 'goal_right'):
            frames = self._load_spritesheet(
                _ROOT / 'assets' / 'sprites' / f'{sheet}_sheet.png', cell)
            self._sprite_frames[sheet]    = frames
            self._sprite_frame_idx[sheet] = 0

        # ANIMAÇÃO DE START IDLE
        start_idle_frames = self._load_spritesheet(
            _ROOT / 'assets' / 'sprites' / 'start_idle_sheet.png', cell)
        self._sprite_frames['start_idle']    = start_idle_frames
        self._sprite_frame_idx['start_idle'] = 0

        goal_idle_frames = self._load_spritesheet(
            _ROOT / 'assets' / 'sprites' / 'goal_idle_sheet.png', cell)
        self._sprite_frames['goal_idle']    = goal_idle_frames
        self._sprite_frame_idx['goal_idle'] = 0

        # ANIMAÇÃO DE FINALIZAÇÃO DO CAMINHO
        end_frames = self._load_spritesheet(
            _ROOT / 'assets' / 'sprites' / 'end_sheet.png', cell)
        self._sprite_frames['end']    = end_frames
        self._sprite_frame_idx['end'] = 0

        # ANIMAÇÃO DE WARP
        warp_frames = self._load_spritesheet(
            _ROOT / 'assets' / 'sprites' / 'start_warp_sheet.png', cell)
        self._sprite_frames['start_warp']    = warp_frames
        self._sprite_frame_idx['start_warp'] = 0

        #ANIMAÇÃO DE BAD ENDING
        for sheet in ('sad_start', 'sad_goal'):
            frames = self._load_spritesheet(
                _ROOT / 'assets' / 'sprites' / f'{sheet}_sheet.png', cell)
            self._sprite_frames[sheet]    = frames
            self._sprite_frame_idx[sheet] = 0

    def _load_spritesheet(self, path: Path, cell: int,
                          frame_size: int = 32) -> list[ImageTk.PhotoImage]:
        """Fatia um spritesheet horizontal em frames individuais redimensionados."""
        try:
            sheet    = Image.open(path).convert('RGBA')
            n_frames = sheet.width // frame_size
            method   = Image.NEAREST
            frames   = []
            for i in range(n_frames):
                frame = sheet.crop((i * frame_size, 0, (i + 1) * frame_size, frame_size))
                frame = frame.resize((cell, cell), method)
                base  = Image.new('RGBA', (cell, cell), (0, 0, 0, 0))
                base.alpha_composite(frame)
                frames.append(ImageTk.PhotoImage(base))
            return frames
        except Exception:
            return []

    # ── clique ───────────────────────────────────────────────────────────────

    def _on_canvas_click(self, event):
        """Converte o clique em coordenadas de grid e notifica o nó selecionado."""
        if not self._pick_mode:
            return
        grid_map  = config.GRID_MAP
        grid_rows = config.GRID_ROWS
        grid_cols = config.GRID_COLS
        cw   = self.winfo_width()  or 600
        ch   = self.winfo_height() or 480
        cell = self._cell_size(cw, ch, grid_rows, grid_cols)
        ox, oy = self._origin(cw, ch, cell, grid_rows, grid_cols)
        c = (event.x - ox) // cell
        r = (event.y - oy) // cell
        if not (0 <= r < grid_rows and 0 <= c < grid_cols):
            return
        if grid_map[r][c] == 1:
            return
        if config.MULTIVERSE_MODE:
            node = f"M{config.ACTIVE_MAP_ID}:({r},{c})"
        else:
            node = f"({r},{c})"
        role = self._pick_mode
        self.set_pick_mode(None)
        if self._on_node_picked:
            self._on_node_picked(role, node)

    # ── cancelamento de animações ─────────────────────────────────────────────

    def _cancel_all_anim(self):
        """Cancela todos os jobs de animação pendentes."""
        self._showing_sad = False   # ← limpa ao cancelar
        self._render_generation += 1 
        for job_id in list(self._anim_jobs.values()):
            try:
                self.after_cancel(job_id)
            except Exception:
                pass
        self._anim_jobs = {}

    # ── render ───────────────────────────────────────────────────────────────

    def render(self, path: list[str] = None,
            start: str = None, goal: str = None,
            static: bool = False):
        """Redesenha o mapa ativo, iniciando animação ou renderizando de forma estática."""
        self._cancel_all_anim()
        self.delete('all')

        path  = path  if path  is not None else []
        start = start or config.START_NODE
        goal  = goal  or config.GOAL_NODE

        if config.MULTIVERSE_MODE and config.MULTIVERSE is not None and not static:
            start_map_id = _node_map_id(start)
            if start_map_id is not None:
                config._apply_active_map(start_map_id)

        # ── Se há path, sobrescreve com o mapa do primeiro nó ────────────────
        if (config.MULTIVERSE_MODE and config.MULTIVERSE is not None
                and path and not static):
            first_map_id = _node_map_id(path[0])
            if first_map_id is not None:
                config._apply_active_map(first_map_id)

        grid_map     = config.GRID_MAP
        grid_weights = config.GRID_WEIGHTS
        grid_rows    = config.GRID_ROWS
        grid_cols    = config.GRID_COLS
        terrain_map  = config.TERRAIN_MAP

        # Calcula nós do mapa ativo e posições start/goal
        if config.MULTIVERSE_MODE:
            active_id  = config.ACTIVE_MAP_ID
            local_path = [n for n in path if _node_map_id(n) == active_id]
            path_set   = {_node_to_rc(n) for n in local_path}
            start_rc   = (_node_to_rc(start)
                        if _node_map_id(start) == active_id else None)
            goal_rc    = (_node_to_rc(goal)
                        if _node_map_id(goal)  == active_id else None)
        else:
            local_path = path
            path_set   = {_node_to_rc(n) for n in path}
            start_rc   = _node_to_rc(start) if start else None
            goal_rc    = _node_to_rc(goal)  if goal  else None

        # Portais do mapa ativo
        portal_cells: set[tuple[int, int]] = set()
        if config.MULTIVERSE_MODE and config.MULTIVERSE is not None:
            from multiverse import portal_cells_of_map
            portal_cells = portal_cells_of_map(config.MULTIVERSE,
                                            config.ACTIVE_MAP_ID)

        cw = self.winfo_width()  or 600
        ch = self.winfo_height() or 480
        cell = self._cell_size(cw, ch, grid_rows, grid_cols)
        ox, oy = self._origin(cw, ch, cell, grid_rows, grid_cols)

        self._draw_background(cw, ch)
        self._temp_imgs = []

        # ── Tiles base ────────────────────────────────────────────────────────
        for r in range(grid_rows):
            for c in range(grid_cols):
                rc      = (r, c)
                wall    = grid_map[r][c] == 1
                weight  = grid_weights[r][c] or 1.0
                terrain = terrain_map[r][c] if terrain_map and not wall else None
                if config.MULTIVERSE_MODE:
                    lnode = f"M{config.ACTIVE_MAP_ID}:({r},{c})"
                else:
                    lnode = f"({r},{c})"
                idx = local_path.index(lnode) if lnode in local_path else -1
                self._draw_tile(
                    r, c, cell, ox, oy,
                    wall=wall, in_path=False,
                    is_start=(start_rc == rc), is_goal=(goal_rc == rc),
                    is_portal=(rc in portal_cells and not wall),
                    weight=weight, terrain=terrain, idx=idx, path=local_path,
                )

        # ── Decide modo de exibição ───────────────────────────────────────────
        use_animation = self._animation_on and local_path and not static

        if use_animation:
            self._anim_full_path  = path
            self._anim_full_start = start
            self._anim_full_goal  = goal
            self._animate_path(path, cell, ox, oy, start, goal, index=0)
            
        else:
            # ── Modo estático / navegação manual ─────────────────────────────
            active_id = config.ACTIVE_MAP_ID if config.MULTIVERSE_MODE else -1
            visited   = self._visited_per_map.get(active_id, local_path)

            visited_set = {_node_to_rc(n) for n in visited}

            for idx, node in enumerate(local_path):
                rc = _node_to_rc(node)
                already = rc in visited_set
                self._draw_tile(
                    rc[0], rc[1], cell, ox, oy,
                    wall=False, in_path=already,
                    is_start=(start_rc == rc),
                    is_goal=(goal_rc  == rc),
                    is_portal=False,
                    weight=1,
                    terrain=(terrain_map[rc[0]][rc[1]] if terrain_map else None),
                    idx=idx, path=local_path,
                )

            visited_local = [n for n in local_path if _node_to_rc(n) in visited_set]
            self._draw_path_indices(visited_local, cell, ox, oy)

            visited_this_map = [n for n in visited if _node_map_id(n) == (config.ACTIVE_MAP_ID if config.MULTIVERSE_MODE else None)]
            last_visited = visited_this_map[-1] if visited_this_map else None
            last_rc = _node_to_rc(last_visited) if last_visited else None

            # Não renderiza start se ele estiver sobre o goal
            if last_rc and last_rc != goal_rc:
                if self._sprite_frames.get('start_idle'):
                    self._anim_jobs['start'] = None
                    self._play_sprite_loop(last_rc[0], last_rc[1], cell, ox, oy,
                                        sheet='start_idle', tag='sprite_start',
                                        job_key='start', loop=True,
                                        generation=self._render_generation)
            elif start_rc and start_rc != goal_rc:
                if self._sprite_frames.get('start_idle'):
                    self._anim_jobs['start'] = None
                    self._play_sprite_loop(start_rc[0], start_rc[1], cell, ox, oy,
                                        sheet='start_idle', tag='sprite_start',
                                        job_key='start', loop=True,
                                        generation=self._render_generation)

            # goal sempre idle
            if goal_rc and self._sprite_frames.get('goal_idle'):
                self._anim_jobs['goal'] = None
                self._play_sprite_loop(goal_rc[0], goal_rc[1], cell, ox, oy,
                                    sheet='goal_idle', tag='sprite_goal',
                                    job_key='goal', loop=True,
                                    generation=self._render_generation)

        if config.MULTIVERSE_MODE:
            self._draw_map_banner()
            self._draw_nav_arrows(cw, ch)

    # ── Troca de mapa durante animação (sem cancelar after-jobs) ─────────────

    def _switch_map_mid_animation(self, new_map_id: int,
                                  path: list[str],
                                  start: str, goal: str):
        """Troca o mapa ativo e redesenha os tiles base sem interromper a animação."""

        if self._on_map_switch:
            self._on_map_switch(new_map_id)

        self.delete('all')
        grid_map     = config.GRID_MAP
        grid_weights = config.GRID_WEIGHTS
        grid_rows    = config.GRID_ROWS
        grid_cols    = config.GRID_COLS
        terrain_map  = config.TERRAIN_MAP

        cw = self.winfo_width()  or 600
        ch = self.winfo_height() or 480
        cell = self._cell_size(cw, ch, grid_rows, grid_cols)
        ox, oy = self._origin(cw, ch, cell, grid_rows, grid_cols)

        self._draw_background(cw, ch)
        self._temp_imgs = []

        # PORTAIS
        portal_cells: set[tuple[int, int]] = set()
        if config.MULTIVERSE is not None:
            from multiverse import portal_cells_of_map
            portal_cells = portal_cells_of_map(config.MULTIVERSE, new_map_id)

        local_path = [n for n in path if _node_map_id(n) == new_map_id]

        # start/goal globais
        start_rc = (_node_to_rc(start)
                    if _node_map_id(start) == new_map_id else None)
        goal_rc  = (_node_to_rc(goal)
                    if _node_map_id(goal)  == new_map_id else None)

        for r in range(grid_rows):
            for c in range(grid_cols):
                rc      = (r, c)
                wall    = grid_map[r][c] == 1
                weight  = grid_weights[r][c] or 1.0
                terrain = terrain_map[r][c] if terrain_map and not wall else None
                lnode   = f"M{new_map_id}:({r},{c})"
                idx     = local_path.index(lnode) if lnode in local_path else -1
                self._draw_tile(
                    r, c, cell, ox, oy,
                    wall=wall, in_path=False,
                    is_start=(start_rc == rc), is_goal=(goal_rc == rc),
                    is_portal=(rc in portal_cells and not wall),
                    weight=weight, terrain=terrain, idx=idx, path=local_path,
                )

        self._draw_background_overlay(cw, ch)   # banner e setas por cima
        self._draw_map_banner()
        self._draw_nav_arrows(cw, ch)

    def _draw_background_overlay(self, cw, ch):
        """Placeholder para sobreposição de banner e setas após redesenho mid-animation."""
        pass  # banner e setas são desenhados separadamente logo após

    # ── Engine de animação ────────────────────────────────────────────────────

    def _animate_path(self, path: list[str], cell: int, ox: int, oy: int,
              start: str, goal: str, index: int = 0, velocidade_atual: float = None,
              tempo_acumulado=0.0, generation=None):
        """Avança o sprite um nó por vez ao longo do caminho, agendando o próximo passo."""

        if velocidade_atual is None:
            velocidade_atual = getattr(config, 'LAST_VELOCITY', 1.0)

        if generation is None:
            generation = self._render_generation
        if generation != self._render_generation:
            return

        if index >= len(path):
            if path and config.GOAL_REACHED:   # ← checa flag
                self.delete('sprite_start')
                self.delete('sprite_goal')
                for name in ('start', 'goal'):
                    self._anim_jobs.pop(name, None)
                gr, gc = _node_to_rc(path[-1])
                cw = self.winfo_width()  or 600
                ch = self.winfo_height() or 480
                self._anim_jobs['end'] = None
                self._play_sprite_loop(gr, gc, cell, ox, oy,
                    sheet='end', tag='sprite_end',
                    job_key='end', loop=True, generation=self._render_generation)
            return

        node   = path[index]
        map_id = _node_map_id(node)

        # ── Detecção de mudança de mapa ───────────────────────────────────────
        current_map = config.ACTIVE_MAP_ID if config.MULTIVERSE_MODE else None
        if config.MULTIVERSE_MODE and map_id is not None and map_id != current_map:
            visited_so_far = [n for n in path[:index]
                            if _node_map_id(n) == current_map]
            self._visited_per_map[current_map] = visited_so_far
            pr, pc = _node_to_rc(path[index - 1])
            self._play_warp_then_switch(
                pr, pc, cell, ox, oy,
                path, start, goal, index,
                repeats=3,
                tempo_acumulado=tempo_acumulado   # ← propaga
            )
            return

        r, c = _node_to_rc(node)

        # ── Calcula delay e checa limite ANTES de desenhar ───────────────────
        w = config.MULTIVERSE.maps[config.ACTIVE_MAP_ID].grid_weights if config.MULTIVERSE_MODE else config.GRID_WEIGHTS
        peso = w[r][c] or 1.0
        tm = config.TERRAIN_MAP
        terreno = tm[r][c] if tm else None
        fator = config.FATORES.get(terreno.name, 1.0) if terreno else 1.0

        delay = round((peso / velocidade_atual) * 1000)
        delay = max(50, min(delay, 2000))

        tempo_acumulado += delay / 1000
        tempo_limite = getattr(config, 'TEMPO_LIMITE', 0.0)

        # ── NOVO: checa se o caminho restante vai estourar ──────────────────
        tempo_restante = 0.0
        vel_sim = velocidade_atual
        for no in path[index + 1:]:
            if config.MULTIVERSE_MODE:
                mid = _node_map_id(no)
                sr, sc = _node_to_rc(no)
                w_sim  = config.MULTIVERSE.maps[mid].grid_weights
                tm_sim = config.MULTIVERSE.maps[mid].terrain_map
            else:
                sr, sc = _node_to_rc(no)
                w_sim  = config.GRID_WEIGHTS
                tm_sim = config.TERRAIN_MAP

            peso_sim    = w_sim[sr][sc] or 1.0
            terreno_sim = tm_sim[sr][sc] if tm_sim else None
            fator_sim   = config.FATORES.get(terreno_sim.name, 1.0) if terreno_sim else 1.0

            d = round((peso_sim / vel_sim) * 1000)
            d = max(50, min(d, 2000))
            tempo_restante += d / 1000

            vel_sim = vel_sim * fator_sim
            vel_sim = max(config.VELOCIDADE_MIN, min(vel_sim, config.VELOCIDADE_MAX))

        vai_estourar = (
            tempo_limite
            and (tempo_acumulado + tempo_restante) > tempo_limite
            and not config.GOAL_REACHED
        )

        if not config.GOAL_REACHED and ( (tempo_limite and tempo_acumulado > tempo_limite) or (index == len(path) - 1) ):            
            # ── CANCELAR jobs pendentes ANTES de incrementar a geração ──
            for key, job in list(self._anim_jobs.items()):
                if job is not None:
                    self.after_cancel(job)
            self._anim_jobs.clear()

            # ── Agora invalida a geração (novos afters ignorarão) ──
            self._render_generation += 1
            new_gen = self._render_generation

            # ── Limpa TODOS os sprites de movimento ──
            self.delete('sprite_start')
            self.delete('sprite_goal')

            # ── Repinta o tile do nó atual como caminho (não deixa "buraco") ──
            tm = config.TERRAIN_MAP
            self._draw_tile(
                r, c, cell, ox, oy,
                wall=False, in_path=True,
                is_start=False, is_goal=False, is_portal=False,
                weight=1,
                terrain=(tm[r][c] if tm else None),
                idx=index, path=path,
            )

            # ── Repinta o tile anterior também, se existir ──
            if index > 0:
                prev_node = path[index - 1]
                prev_map_id = _node_map_id(prev_node)
                if prev_map_id == (config.ACTIVE_MAP_ID if config.MULTIVERSE_MODE else None):
                    pr, pc = _node_to_rc(prev_node)
                    self._draw_tile(
                        pr, pc, cell, ox, oy,
                        wall=False, in_path=True,
                        is_start=False, is_goal=False, is_portal=False,
                        weight=1,
                        terrain=(tm[pr][pc] if tm else None),
                        idx=index - 1, path=path,
                    )

            self._showing_sad = True

            self._play_sprite_loop(r, c, cell, ox, oy,
                sheet='sad_start', tag='sprite_sad_start',
                job_key='sad_start', loop=True,
                generation=new_gen)

            if goal:
                goal_map_id = _node_map_id(goal) if config.MULTIVERSE_MODE else None
                current_map = config.ACTIVE_MAP_ID if config.MULTIVERSE_MODE else None
                if not config.MULTIVERSE_MODE or goal_map_id == current_map:
                    gr, gc = _node_to_rc(goal)
                    self._play_sprite_loop(gr, gc, cell, ox, oy,
                        sheet='sad_goal', tag='sprite_sad_goal',
                        job_key='sad_goal', loop=True,
                        generation=new_gen)
            return
        # ────────────────────────────────────────────────────────────────────

        # Pinta tile "percorrido" no nó anterior (se do mesmo mapa)
        if index > 0:
            prev_node   = path[index - 1]
            prev_map_id = _node_map_id(prev_node)
            if prev_map_id == (config.ACTIVE_MAP_ID if config.MULTIVERSE_MODE else None):
                pr, pc = _node_to_rc(prev_node)
                tm = config.TERRAIN_MAP
                self._draw_tile(
                    pr, pc, cell, ox, oy,
                    wall=False, in_path=True,
                    is_start=False, is_goal=False, is_portal=False,
                    weight=1,
                    terrain=(tm[pr][pc] if tm else None),
                    idx=index - 1, path=path,
                )
            self.delete('sprite_start')

        # Registra visita ao nó atual
        active_id = config.ACTIVE_MAP_ID if config.MULTIVERSE_MODE else -1
        if active_id not in self._visited_per_map:
            self._visited_per_map[active_id] = []
        if node not in self._visited_per_map[active_id]:
            self._visited_per_map[active_id].append(node)

        # Desenha sprite do personagem na posição atual
        x1, y1     = ox + c * cell, oy + r * cell
        sheet_name = self._start_direction(index, path, 'start')
        n_frames   = max(len(self._sprite_frames.get(sheet_name, [1])), 1)
        self._sprite_frame_idx[sheet_name] = (
            self._sprite_frame_idx.get(sheet_name, 0) + 1
        ) % n_frames
        frames = self._sprite_frames.get(sheet_name, [])
        if frames:
            self.delete('sprite_start')
            self.create_image(x1, y1, anchor='nw',
                            image=frames[self._sprite_frame_idx[sheet_name]],
                            tags='sprite_start')

        self.tag_raise('nav_prev')
        self.tag_raise('nav_next')

        proxima_vel = velocidade_atual * fator
        proxima_vel = max(config.VELOCIDADE_MIN, min(proxima_vel, config.VELOCIDADE_MAX))

        job = self.after(delay, lambda g=generation: self._animate_path(
            path, cell, ox, oy, start, goal, index + 1, proxima_vel,
            tempo_acumulado, g))
        self._anim_jobs['path_walk'] = job
    
    def _play_warp_then_switch(self, r, c, cell, ox, oy,
                            path, start, goal, index,
                            repeats=3, frame_idx=0, plays_done=0,
                            generation=None, tempo_acumulado=0.0): 
        """Reproduz a animação de warp no portal e, ao término, aciona a troca de mapa."""
        if generation is None:
            generation = self._render_generation
        if generation != self._render_generation:
            return

        frames = self._sprite_frames.get('start_warp', [])
        if not frames:
            self._do_map_switch(path, start, goal, index, cell, ox, oy)
            return

        x1, y1 = ox + c * cell, oy + r * cell
        self.delete('sprite_start')
        self.create_image(x1, y1, anchor='nw',
                        image=frames[frame_idx], tags='sprite_start')

        next_frame = frame_idx + 1
        self.tag_raise('nav_prev')
        self.tag_raise('nav_next')

        if next_frame < len(frames):
            job = self.after(80, lambda: self._play_warp_then_switch(
                r, c, cell, ox, oy, path, start, goal, index,
                repeats, next_frame, plays_done, generation, tempo_acumulado))  # ← adiciona
        else:
            plays_done += 1
            if plays_done < repeats:
                job = self.after(80, lambda: self._play_warp_then_switch(
                    r, c, cell, ox, oy, path, start, goal, index,
                    repeats, 0, plays_done, generation, tempo_acumulado))       # ← adiciona
            else:
                job = self.after(80, lambda: self._do_map_switch(
                    path, start, goal, index, cell, ox, oy, generation,
                    tempo_acumulado))                                            # ← já estava

        self._anim_jobs['path_walk'] = job

    def _do_map_switch(self, path, start, goal, index, cell, ox, oy, generation=None, tempo_acumulado: float = 0.0):
        """Aplica a troca de mapa e reinicia a animação a partir do nó atual."""
        if generation is None:
            generation = self._render_generation
        if generation != self._render_generation:
            return

        map_id = _node_map_id(path[index])
        self._switch_map_mid_animation(map_id, path, start, goal)

        cw = self.winfo_width()  or 600
        ch = self.winfo_height() or 480
        cell  = self._cell_size(cw, ch, config.GRID_ROWS, config.GRID_COLS)
        ox, oy = self._origin(cw, ch, cell, config.GRID_ROWS, config.GRID_COLS)

        self._animate_path(path, cell, ox, oy, start, goal, index)

    def _play_sprite_loop(self, r, c, cell, ox, oy,
                      sheet, tag, job_key,
                      frame_idx=0, loop=True,
                      generation: int = 0):  
        """Reproduz um sprite em loop ou uma vez, agendando cada frame via after()."""
        # Descarta se a geração mudou
        if generation != self._render_generation:
            return
        
        if frame_idx == 0 and job_key in self._anim_jobs:
            job_id = self._anim_jobs.pop(job_key)
            if job_id is not None:
                self.after_cancel(job_id)

        if job_key not in self._anim_jobs and frame_idx != 0:
            print(f"[SPRITE] job '{job_key}' morreu no frame {frame_idx}")  # ← temporário
            return

        frames = self._sprite_frames.get(sheet, [])
        if not frames:
            return
        x1, y1 = ox + c * cell, oy + r * cell
        self.delete(tag)
        self.create_image(x1, y1, anchor='nw',
                        image=frames[frame_idx], tags=tag)

        next_idx = (frame_idx + 1) % len(frames)
        if not loop and next_idx == 0:
            self._anim_jobs.pop(job_key, None)
            return
        job = self.after(120, lambda: self._play_sprite_loop(
            r, c, cell, ox, oy, sheet, tag, job_key,
            next_idx, loop,
            generation))                               
        self._anim_jobs[job_key] = job

        self.tag_raise('nav_prev')
        self.tag_raise('nav_next')
        
    # ── Direção do sprite ─────────────────────────────────────────────────────

    def _start_direction(self, idx: int, path: list[str], name : str) -> str:
        """Retorna o nome do spritesheet correspondente à direção de movimento do sprite."""
        def delta(a, b):
            ra, ca = _node_to_rc(a)
            rb, cb = _node_to_rc(b)
            return rb - ra, cb - ca
        dr, dc = (delta(path[idx], path[idx + 1])
                  if idx < len(path) - 1
                  else delta(path[idx - 1], path[idx]))
        return {
            (1,  0): f'{name}_down',
            (-1, 0): f'{name}_up',
            (0, -1): f'{name}_left',
            (0,  1): f'{name}_right',
        }.get((dr, dc), f'{name}_down')

    def _path_rotation(self, idx: int, path: list[str]) -> float:
        """Retorna o ângulo de rotação do tile de caminho conforme a direção do movimento."""
        def delta(a, b):
            ra, ca = _node_to_rc(a)
            rb, cb = _node_to_rc(b)
            return rb - ra, cb - ca
        dr, dc = (delta(path[idx], path[idx + 1])
                  if idx < len(path) - 1
                  else delta(path[idx - 1], path[idx]))
        return {(1, 0): 0, (-1, 0): 180, (0, 1): 90, (0, -1): 270}.get((dr, dc), 0)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _cell_size(self, cw, ch, grid_rows, grid_cols):
        """Calcula o tamanho de célula que melhor ocupa o canvas sem ultrapassar os limites."""
        sx = (cw - 40) // grid_cols
        sy = (ch - 40) // grid_rows
        return max(self._MIN_CELL, min(self._MAX_CELL, sx, sy))

    def _origin(self, cw, ch, cell, grid_rows, grid_cols):
        """Calcula o offset de origem para centralizar o grid no canvas."""
        ox = (cw - cell * grid_cols) // 2
        oy = (ch - cell * grid_rows) // 2
        return ox, oy

    def _tile_rect(self, r, c, cell, ox, oy):
        """Retorna as coordenadas do retângulo delimitador de uma célula."""
        x1 = ox + c * cell
        y1 = oy + r * cell
        return x1, y1, x1 + cell, y1 + cell

    def _tile_center(self, r, c, cell, ox, oy):
        """Retorna o ponto central de uma célula em coordenadas de canvas."""
        x1, y1, x2, y2 = self._tile_rect(r, c, cell, ox, oy)
        return (x1 + x2) / 2, (y1 + y2) / 2

    # ── Desenho de tiles ──────────────────────────────────────────────────────

    def _draw_background(self, cw, ch):
        """Preenche o fundo do canvas com a cor de background."""
        self.create_rectangle(0, 0, cw, ch, fill=COLORS['bg'], outline='')

    def _draw_tile(self, r, c, cell, ox, oy,
                   wall, in_path, is_start, is_goal,
                   is_portal=False, weight=1.0, terrain=None,
                   idx=-1, path=None):
        """Desenha um tile completo: base, overlay de caminho, portal e sprite de start/goal."""
        x1, y1, x2, y2 = self._tile_rect(r, c, cell, ox, oy)

        if wall:
            base_key = 'wall'
        elif terrain is not None:
            base_key = _TERRAIN_TILE.get(terrain.name, 'plains')
        else:
            base_key = 'plains'

        base_img = self._tile_imgs.get(base_key)
        if base_img:
            self.create_image(x1, y1, anchor='nw', image=base_img)
        else:
            self._draw_tile_color_fallback(x1, y1, x2, y2, wall, in_path,
                                           is_start, is_goal, is_portal,
                                           weight, terrain)

        if in_path and not is_start and not is_goal and not wall:
            angle   = self._path_rotation(idx, path) if path and idx >= 0 else 0
            pil_img = self._tile_pil.get('path')
            if pil_img:
                rotated = pil_img.rotate(angle, expand=False)
                tk_img  = ImageTk.PhotoImage(rotated)
                self._temp_imgs.append(tk_img)
                self.create_image(x1, y1, anchor='nw', image=tk_img)

        if is_portal and not wall and not is_start and not is_goal:
            portal_img = self._tile_imgs.get('portal')
            if portal_img:
                self.create_image(x1, y1, anchor='nw', image=portal_img)

        for role, color, label in (
            ('start', COLORS['accent'],  'S'),
            ('goal',  COLORS['success'], 'G'),
        ):
            if (role == 'start' and is_start) or (role == 'goal' and is_goal):
                sheet_name = 'start_idle' if role == 'start' else 'goal_idle'
                frames = self._sprite_frames.get(sheet_name, [])
                if frames:
                    tag = f'sprite_{role}'
                    self.delete(tag)
                    self.create_image(
                        x1, y1, anchor='nw',
                        image=frames[self._sprite_frame_idx.get(sheet_name, 0)],
                        tags=tag)
                else:
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    self._draw_marker(cx, cy, max(4, cell // 5), color, label)
                break
        self.tag_raise('nav_prev')
        self.tag_raise('nav_next')

    def _draw_tile_color_fallback(self, x1, y1, x2, y2,
                                  wall, in_path, is_start, is_goal,
                                  is_portal, weight, terrain):
        """Renderiza o tile com cores sólidas quando os assets de imagem não estão disponíveis."""
        pad = 1
        if wall:
            self.create_rectangle(
                x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                fill=COLORS['tile_wall'],
                outline=COLORS['tile_border'], width=1)
            self.create_line(x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                             fill=COLORS['tile_border'], width=1)
            self.create_line(x2 - pad, y1 + pad, x1 + pad, y2 - pad,
                             fill=COLORS['tile_border'], width=1)
            return

        if is_start:
            fill, glow = COLORS['node_start'], COLORS['node_glow_start']
        elif is_goal:
            fill, glow = COLORS['node_goal'],  COLORS['node_glow_goal']
        elif in_path:
            fill, glow = COLORS['node_path'],  COLORS['node_glow_path']
        elif is_portal:
            fill, glow = COLORS['tile_portal'], COLORS['tile_portal_glow']
        else:
            glow = None
            if terrain is not None:
                fill = COLORS[_TERRAIN_COLOR.get(terrain.name, 'tile_free')]
            elif weight >= 5.0:
                fill = COLORS['tile_w5']
            elif weight >= 3.0:
                fill = COLORS['tile_w3']
            elif weight >= 2.0:
                fill = COLORS['tile_w2']
            else:
                fill = COLORS['tile_free']

        self.create_rectangle(
            x1 + pad, y1 + pad, x2 - pad, y2 - pad,
            fill=fill,
            outline=COLORS['tile_border'] if not glow else glow,
            width=1 if not glow else 2)

    def _draw_marker(self, cx, cy, r, color, label):
        """Desenha um marcador circular com rótulo, usado como fallback de start e goal."""
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill=color, outline='')
        f = self._fonts.get('section')
        if f:
            self.create_text(cx, cy, text=label, font=f, fill='#ffffff')

    def _draw_path_indices(self, path: list[str], cell, ox, oy):
        """Exibe o índice de cada nó intermediário do caminho sobre o tile correspondente."""
        f = self._fonts.get('section')
        if not f or cell < 28:
            return
        for idx, node in enumerate(path):
            if idx == 0 or idx == len(path) - 1:
                continue
            r, c = _node_to_rc(node)
            cx, cy = self._tile_center(r, c, cell, ox, oy)
            bx = cx + cell // 2 - 6
            by = cy - cell // 2 + 6
            dot_r = 7
            self.create_oval(bx - dot_r, by - dot_r,
                             bx + dot_r, by + dot_r,
                             fill=COLORS['index'], outline='')
            self.create_text(bx, by, text=str(idx),
                             font=f, fill='#ffffff')

    # ── Banner e setas de multiverso ──────────────────────────────────────────

    def _draw_map_banner(self):
        """Exibe o banner com o identificador e papel do mapa ativo no multiverso."""
        if config.MULTIVERSE is None:
            return
        mv  = config.MULTIVERSE
        mid = config.ACTIVE_MAP_ID
        if mid == mv.start_map:
            label = f'◈  Mapa {mid}  —  INÍCIO'
            color = COLORS['accent']
        elif mid == mv.goal_map:
            label = f'◈  Mapa {mid}  —  SAÍDA REAL'
            color = COLORS['success']
        else:
            label = f'◈  Mapa {mid}'
            color = COLORS['warning']
        f  = self._fonts.get('section')
        cw = self.winfo_width() or 600
        if f:
            self.create_text(cw // 2, 14, text=label, font=f,
                             fill=color, anchor='center')

    def _draw_nav_arrows(self, cw: int, ch: int):
        """Desenha os botões de navegação lateral entre mapas do multiverso."""
        if config.MULTIVERSE is None or not self._on_map_nav:
            return
        mv  = config.MULTIVERSE
        mid = config.ACTIVE_MAP_ID
        aw, ah = 36, 72
        margin = 6
        mid_y  = ch // 2
        y1, y2 = mid_y - ah // 2, mid_y + ah // 2
        f = self._fonts.get('title') or self._fonts.get('section')

        if mid > 0:
            lx1, lx2 = margin, margin + aw
            btn_l = self.create_rectangle(
                lx1, y1, lx2, y2,
                fill=COLORS['panel_border'],
                outline=COLORS['accent'], width=1,
                tags='nav_prev')
            self.create_text((lx1 + lx2) / 2, (y1 + y2) / 2,
                             text='◀', font=f, fill=COLORS['accent'],
                             tags='nav_prev')

            def _prev_enter(_e, b=btn_l):
                self.itemconfig(b, fill=COLORS['node_start'])
                self.config(cursor='hand2')

            def _prev_leave(_e, b=btn_l):
                self.itemconfig(b, fill=COLORS['panel_border'])
                self.config(cursor='')

            self.tag_bind('nav_prev', '<Enter>',    _prev_enter)
            self.tag_bind('nav_prev', '<Leave>',    _prev_leave)
            self.tag_bind('nav_prev', '<Button-1>',
                          lambda _e: self._on_map_nav(-1))

        if mid < mv.n_maps - 1:
            rx1, rx2 = cw - margin - aw, cw - margin
            btn_r = self.create_rectangle(
                rx1, y1, rx2, y2,
                fill=COLORS['panel_border'],
                outline=COLORS['accent'], width=1,
                tags='nav_next')
            self.create_text((rx1 + rx2) / 2, (y1 + y2) / 2,
                             text='▶', font=f, fill=COLORS['accent'],
                             tags='nav_next')

            def _next_enter(_e, b=btn_r):
                self.itemconfig(b, fill=COLORS['node_start'])
                self.config(cursor='hand2')

            def _next_leave(_e, b=btn_r):
                self.itemconfig(b, fill=COLORS['panel_border'])
                self.config(cursor='')

            self.tag_bind('nav_next', '<Enter>',    _next_enter)
            self.tag_bind('nav_next', '<Leave>',    _next_leave)
            self.tag_bind('nav_next', '<Button-1>',
                          lambda _e: self._on_map_nav(+1))
            
            self.tag_raise('nav_prev')
            self.tag_raise('nav_next')