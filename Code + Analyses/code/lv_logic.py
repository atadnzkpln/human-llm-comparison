"""
lv_logic.py — Volledige spellogica voor NP-Hard Pac-Man (headless, geen pygame).

Dit bestand bevat alles wat nodig is om een level te simuleren zonder grafische
output.  Zowel de visuele game (level1.py) als de API-benchmark-runner
(api_runner.py) importeren hieruit.

Architectuur
────────────
  make_state(lvl)          →  maak een verse spelstaat voor een level
  player_blocked_edge(…)   →  controleert of de SPELER een cel-overgang mag nemen
  ghost_blocked_edge(…)    →  controleert of een GEEST een cel-overgang mag nemen
  move_ghost(…)            →  beweegt de patrouille-geest één stap
  move_ambush_ghost(…)     →  beweegt de hinderlaag-geest (BFS + zone-modus)
  apply_ghost_shared_teleport(…) → teleporteert een geest via gedeeld/ghost-portaal
  slide_meta_box(…)        →  berekent eindpositie van een schuivende meta-doos
  bfs_next_step(…)         →  BFS kortste pad voor de hinderlaag-geest

Muuropslag
──────────
Muren worden opgeslagen als frozenset van twee cel-coördinaten:
  frozenset([(col1, row1), (col2, row2)])
Dit maakt de richting irrelevant — een muur tussen A en B is dezelfde
frozenset als een muur tussen B en A.
"""

import copy
from collections import deque
from lv_constants import AMBUSH_RADIUS, AMBUSH_PAUSE_FREQ, POWER_TURNS, DELAY_PU_MOVES


# ─── Muur-checks ──────────────────────────────────────────────────────────────

def wall_between(walls, c1, r1, c2, r2):
    """Controleer of er een muur is tussen cel (c1,r1) en (c2,r2)."""
    return frozenset([(c1, r1), (c2, r2)]) in walls


def player_blocked_edge(lvl, state, c1, r1, c2, r2):
    """Geeft True als de SPELER de overgang (c1,r1)→(c2,r2) NIET mag nemen.

    Volgorde van checks (eerder = hogere prioriteit):
    1. Rode muur (lvl["walls"]) — permanent, tenzij gebroken door meta-doos
    2. Paarse muur — permanent, nooit te breken
    3. Blauwe muur (green_walls) binnen zone + meta-meta regel "green_wall_oneshot"
       → mag één keer passeren; daarna geblokkeerd
    4. Oranje one-shot gate (orange_gates) — richting-afhankelijk, eenmalig
    5. Gedeelde one-shot gate (shared_orange_gates) — idem, ook voor geest
    """
    edge   = frozenset([(c1, r1), (c2, r2)])
    broken = state.get("broken_walls", set())

    # Rode permanente muren (gebrokenen uitgesloten — meta-doos kan ze breken)
    if edge in lvl["walls"] and edge not in broken:
        return True

    # Paarse muren zijn altijd permanent voor de speler
    if edge in lvl.get("purple_walls", set()) and edge not in broken:
        return True

    # Blauwe muren: normaal passeerbaar, maar in de local rule zone met de
    # "green_wall_oneshot" meta-meta-regel mag je er slechts eenmaal door.
    if edge in lvl.get("green_walls", set()):
        lrz = lvl.get("local_rule_zone")
        if (lrz and "green_wall_oneshot" in lrz.get("meta_meta_rules", set())
                and _edge_in_local_rule_zone(lvl, c1, r1, c2, r2)):
            if edge in state.get("used_green_walls", set()):
                return True  # al een keer gebruikt → nu geblokkeerd

    # Oranje one-shot gates: check of al gebruikt en of richting klopt
    for og in state.get("orange_gates", []):
        if og["edge"] == edge:
            if og["used"]:
                return True  # gate is gesloten na gebruik
            if not og.get("bidirectional"):
                dc, dr = c2 - c1, r2 - r1
                if (dc, dr) != tuple(og["pass_dir"]):
                    return True  # verkeerde richting — eenrichtingsgate

    # Gedeelde one-shot gates (ook zichtbaar voor de geest)
    for sg in state.get("shared_orange_gates", []):
        if sg["edge"] == edge:
            if sg["used"]:
                return True
            dc, dr = c2 - c1, r2 - r1
            if (dc, dr) != tuple(sg["pass_dir"]):
                return True

    return False


def _edge_in_local_rule_zone(lvl, c1, r1, c2, r2):
    """Geeft True als BEIDE cellen van de overgang binnen de local rule zone liggen.

    Wordt gebruikt om te bepalen of een muur-interactie onder de zone-regels valt.
    Een muur op de grens (één cel binnen, één cel buiten) telt NIET als een zone-muur.
    """
    lrz = lvl.get("local_rule_zone")
    if not lrz:
        return False
    c_min, r_min, c_max, r_max = lrz["rect"]
    return (c_min <= c1 <= c_max and r_min <= r1 <= r_max
            and c_min <= c2 <= c_max and r_min <= r2 <= r_max)


def ghost_blocked_edge(lvl, c1, r1, c2, r2, shared_gates=None, broken_walls=None):
    """Geeft True als een GEEST de overgang (c1,r1)→(c2,r2) NIET mag nemen.

    Geesten hebben andere muurregels dan de speler:
    - Rode muren: geblokkeerd (tenzij gebroken)
    - Blauwe muren BUITEN zone: geblokkeerd (geesten kunnen er niet door)
    - Blauwe muren BINNEN zone: doorgangbaar (zone-effect verhindert dit niet)
    - Paarse muren: worden bewust NIET gecheckt — geesten negeren paarse muren
    - Oranje gates: altijd geblokkeerd voor gewone patrouille-geesten
    - Gedeelde gates: geblokkeerd als al gebruikt of verkeerde richting
    """
    edge   = frozenset([(c1, r1), (c2, r2)])
    broken = broken_walls or set()

    if edge in lvl["walls"] and edge not in broken:
        return True

    # Blauwe muren zijn passeerbaar voor geesten ALLEEN binnen de local rule zone.
    # Buiten de zone zijn ze een obstakel voor geesten (niet voor spelers).
    in_zone = _edge_in_local_rule_zone(lvl, c1, r1, c2, r2)
    if edge in lvl.get("green_walls", set()) and not in_zone and edge not in broken:
        return True

    # Gewone oranje gates blokkeren geesten altijd (speler-only mechanic)
    for og in lvl.get("orange_gates", []):
        if og["edge"] == edge:
            return True

    # Gedeelde gates: geest mag er door in de juiste richting, tot ze gebruikt zijn
    if shared_gates:
        for sg in shared_gates:
            if sg["edge"] == edge:
                if sg["used"]:
                    return True
                dc, dr = c2 - c1, r2 - r1
                if (dc, dr) != tuple(sg["pass_dir"]):
                    return True

    return False


# ─── State aanmaken ───────────────────────────────────────────────────────────

def make_state(lvl):
    """Maak een verse, onafhankelijke spelstaat op basis van een level-definitie.

    De state is een dict met alle veranderlijke spelgegevens.  De level-definitie
    (lvl) bevat de vaste opzet (muren, doelen, startpositie); de state bevat wat
    er tijdens het spelen verandert (positie, verbruikte zetten, etc.).

    Geeft een diep-gekopieerde state terug zodat meerdere simulations onafhankelijk
    van elkaar kunnen draaien (relevant voor de multi-run API-benchmark).
    """
    return {
        # Huidige positie van de speler (col = x-as, row = y-as, 0-geïndexeerd)
        "col":                  lvl["start"][0],
        "row":                  lvl["start"][1],

        # Resterende zetten; als dit 0 bereikt → game_over
        "moves_left":           lvl["max_moves"],

        # Richting voor de animatie van Pac-Man (niet voor spellogica)
        "direction":            "RIGHT",

        # "playing" | "level_complete" | "game_over"
        "status":               "playing",
        "reason":               "",  # reden van game_over voor weergave

        # Lijst van doel-dicts; elk doel krijgt "collected": True als bereikt
        "goals":                [dict(g) for g in lvl["goals"]],

        # Gate-staat (None als level geen gate heeft)
        "gate":                 dict(lvl["gate"]) if lvl["gate"] else None,

        # Diep-gekopieerde geest-dicts zodat de state volledig onafhankelijk is
        "ghost":                copy.deepcopy(lvl["ghost"])        if lvl["ghost"]               else None,
        "ambush_ghost":         copy.deepcopy(lvl["ambush_ghost"]) if lvl.get("ambush_ghost")    else None,

        # Powerup-tracking (ondersteunt meerdere powerups via lijst)
        "powerups_taken":       set(),   # set van indices van al opgepakte powerups
        "powered_turns":        0,       # aflopende teller; > 0 → speler kan geesten eten
        "ghost_eaten":          False,   # True zodra de patrouille-geest gegeten is

        # Vertraagde powerup — activeert pas DELAY_PU_MOVES zetten ná oppakken
        "delayed_pu_taken":     False,
        "delayed_pu_countdown": 0,       # resterende zetten tot activering
        "delayed_pu_in_zone":   False,   # True → countdown is gepauzeerd (meta-meta regel)

        # Blauwe muren die de speler al eenmaal is doorgegaan (one-shot in zone)
        "used_green_walls":     set(),

        # Muren die gebroken zijn door een schuivende meta-doos (meta-meta "meta_block_breaks")
        "broken_walls":         set(),

        # Duwbare dozen — lijst van [col, row] (veranderlijk, dus list, niet tuple)
        "boxes":                [list(b) for b in lvl["pushable_blocks"]],

        # Meta-dozen — schuiven door tot een obstakel in plaats van één stap
        "meta_boxes":           [list(b) for b in lvl.get("meta_blocks", [])],

        # One-shot gates: eenmalig passeerbaar in één richting
        "orange_gates": [
            {"edge": og["edge"], "pass_dir": og["pass_dir"], "used": False,
             "bidirectional": og.get("bidirectional", False)}
            for og in lvl.get("orange_gates", [])
        ],

        # Gedeelde one-shot gates: werken voor zowel speler als geest
        "shared_orange_gates": [
            {"edge": sg["edge"], "pass_dir": sg["pass_dir"], "used": False}
            for sg in lvl.get("shared_orange_gates", [])
        ],
    }


# ─── Geest-beweging ───────────────────────────────────────────────────────────

def move_ghost(ghost, lvl, blocked_cells, broken_walls=None):
    """Beweegt de patrouille-geest één stap.

    Twee gedragstypen:
    1. "patrol" (waypoint-based): volgt een vaste lijst van coördinaten in een
       cyclische lus.  Wordt gebruikt voor complexe routes (bv. level 1F).
    2. Stuiterende patrouille (standaard): beweegt langs één as (h of v) tot
       een grens of muur, keert dan om.  Eenvoudiger te voorspellen.

    blocked_cells: set van cellen die de geest niet mag betreden (bv. gesloten gate).
    broken_walls:  muren die door een meta-doos gebroken zijn (geest kan er door).
    """
    if ghost.get("type") == "patrol":
        # Waypoint-patrouille: simpelweg de volgende waypoint pakken in de lijst
        ghost["wp_idx"] = (ghost["wp_idx"] + 1) % len(ghost["waypoints"])
        wp = ghost["waypoints"][ghost["wp_idx"]]
        ghost["col"] = wp[0]
        ghost["row"] = wp[1]
        return

    bw = broken_walls or set()

    if ghost["axis"] == "h":
        # Horizontale stuitering
        nxt = ghost["col"] + ghost["dir"]
        if (nxt < ghost["min_col"] or nxt > ghost["max_col"]
                or ghost_blocked_edge(lvl, ghost["col"], ghost["row"], nxt, ghost["row"], broken_walls=bw)
                or (nxt, ghost["row"]) in blocked_cells):
            ghost["dir"] *= -1  # keer om
            nxt = ghost["col"] + ghost["dir"]
        if (ghost["min_col"] <= nxt <= ghost["max_col"]
                and not ghost_blocked_edge(lvl, ghost["col"], ghost["row"], nxt, ghost["row"], broken_walls=bw)
                and (nxt, ghost["row"]) not in blocked_cells):
            ghost["col"] = nxt
    else:
        # Verticale stuitering
        nxt = ghost["row"] + ghost["dir"]
        if (nxt < ghost["min_row"] or nxt > ghost["max_row"]
                or ghost_blocked_edge(lvl, ghost["col"], ghost["row"], ghost["col"], nxt, broken_walls=bw)
                or (ghost["col"], nxt) in blocked_cells):
            ghost["dir"] *= -1
            nxt = ghost["row"] + ghost["dir"]
        if (ghost["min_row"] <= nxt <= ghost["max_row"]
                and not ghost_blocked_edge(lvl, ghost["col"], ghost["row"], ghost["col"], nxt, broken_walls=bw)
                and (ghost["col"], nxt) not in blocked_cells):
            ghost["row"] = nxt


def move_friendly_ghost(ghost, lvl, blocked_cells):
    """Vriendelijke geest — zelfde bewegingslogica als de gewone geest.
    Gereserveerd voor toekomstige level-types; momenteel niet in gebruik.
    """
    move_ghost(ghost, lvl, blocked_cells)


# ─── BFS: kortste pad voor hinderlaag-geest ───────────────────────────────────

def bfs_next_step(ghost_col, ghost_row, target_col, target_row, lvl,
                  blocked_cells, shared_gates=None, skip_tp_at_start=False,
                  broken_walls=None):
    """Geeft (dc, dr) voor de eerste stap op het kortste pad via BFS.

    De hinderlaag-geest gebruikt dit om de speler te achtervolgen.
    BFS garandeert het kortste pad; het houdt rekening met:
    - ghost_blocked_edge: alle muurtypes die relevant zijn voor geesten
    - shared_teleporters en ghost_teleporters: geesten mogen deze gebruiken
    - skip_tp_at_start=True: voorkomt ping-pong direct na een teleporter-sprong
      (de geest zou anders onmiddellijk terugspringen via het portaal)

    Geeft (0, 0) als er geen pad bestaat (ingesloten geest).
    """
    start  = (ghost_col, ghost_row)
    target = (target_col, target_row)
    if start == target:
        return (0, 0)

    # Bouw een kaart van teleporter-verbindingen (gedeeld + ghost-only)
    tp_map = {}
    stps = lvl.get("shared_teleporters")
    if stps:
        tp_map[tuple(stps[0])] = tuple(stps[1])
        tp_map[tuple(stps[1])] = tuple(stps[0])
    gtps = lvl.get("ghost_teleporters")
    if gtps:
        tp_map[tuple(gtps[0])] = tuple(gtps[1])
        tp_map[tuple(gtps[1])] = tuple(gtps[0])

    queue   = deque([(start, None)])  # (positie, eerste_stap)
    visited = {start}

    while queue:
        (c, r), first = queue.popleft()

        # Probeer alle vier richtingen
        for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nc, nr = c + dc, r + dr
            if (nc, nr) in visited:
                continue
            if not (0 <= nc < lvl["cols"] and 0 <= nr < lvl["rows"]):
                continue
            if ghost_blocked_edge(lvl, c, r, nc, nr, shared_gates, broken_walls=broken_walls or set()):
                continue
            if (nc, nr) in blocked_cells:
                continue

            # Onthoud de allereerste stap — dat is wat we teruggeven
            step = first if first is not None else (dc, dr)
            if (nc, nr) == target:
                return step
            visited.add((nc, nr))
            queue.append(((nc, nr), step))

        # Teleporter-sprong vanuit huidige positie
        if (c, r) in tp_map:
            if (c, r) == start and skip_tp_at_start:
                continue  # sla teleporter over als startpositie (anti-pingpong)
            nc, nr = tp_map[(c, r)]
            if (nc, nr) not in visited:
                step = first if first is not None else (nc - c, nr - r)
                if (nc, nr) == target:
                    return step
                visited.add((nc, nr))
                queue.append(((nc, nr), step))

    return (0, 0)  # geen pad gevonden


# ─── Local rule zone: perimeterberekening ─────────────────────────────────────

def compute_zone_perimeter(rect):
    """Geeft de randcellen van een rechthoekige zone in KLOKSGEWIJZE volgorde.

    rect = (col_min, row_min, col_max, row_max)
    Volgorde: bovenkant →  rechterkant ↓  onderkant ←  linkerkant ↑

    Gebruikt door de hinderlaag-geest wanneer hij de zone betreedt en overschakelt
    naar perimeterpatrouille (meta-meta-regel "perimeter_patrol").
    Hoeken worden maar één keer opgenomen (geen duplicaten).
    """
    c_min, r_min, c_max, r_max = rect
    p = []
    for c in range(c_min, c_max + 1):          # bovenkant →
        p.append((c, r_min))
    for r in range(r_min + 1, r_max + 1):       # rechterkant ↓
        p.append((c_max, r))
    for c in range(c_max - 1, c_min - 1, -1):  # onderkant ←
        p.append((c, r_max))
    for r in range(r_max - 1, r_min, -1):       # linkerkant ↑
        p.append((c_min, r))
    return p


# ─── Hinderlaag-geest beweging ────────────────────────────────────────────────

def move_ambush_ghost(ghost, lvl, player_col, player_row, blocked_cells,
                      shared_gates=None, broken_walls=None):
    """Beweegt de hinderlaag-geest één stap.

    Gedragsautomaat met drie modi:

    1. DORMANT — geest staat stil totdat de speler binnen Chebyshev-afstand
       ghost["radius"] komt.  Chebyshev = max(|Δcol|, |Δrij|).

    2. ACTIEF (achtervolging) — volgt de speler via BFS.  Pauzeert elke
       AMBUSH_PAUSE_FREQ zetten (geeft de speler een ademruimte).

    3. ZONE-MODUS — zodra de geest een local_rule_zone binnenstapt met effect
       "perimeter_patrol", schakelt hij over naar kloksgewijze randpatrouille.
       Hij loopt de rand van de zone rond totdat hij die verlaat.
       Deze modus heeft prioriteit boven achtervolging.
    """
    lrz = lvl.get("local_rule_zone")

    # ── Modus 3: zone-patrouille (hoogste prioriteit) ─────────────────────────
    if lrz and lrz.get("ghost_effect") == "perimeter_patrol":
        c_min, r_min, c_max, r_max = lrz["rect"]
        in_zone = (c_min <= ghost["col"] <= c_max
                   and r_min <= ghost["row"] <= r_max)

        if in_zone:
            if not ghost.get("zone_mode", False):
                # Eerste keer in de zone: bouw de perimeterlijst en zoek de
                # startindex op (het dichtste randpunt bij de huidige positie)
                ghost["activated"] = True
                perimeter = compute_zone_perimeter(lrz["rect"])
                entry = (ghost["col"], ghost["row"])
                if entry in perimeter:
                    start_idx = perimeter.index(entry)
                else:
                    # Binnenste cel (onverwacht): kies dichtstbijzijnde randcel
                    start_idx = min(range(len(perimeter)),
                                    key=lambda i: (abs(perimeter[i][0] - entry[0])
                                                   + abs(perimeter[i][1] - entry[1])))
                ghost["zone_mode"]      = True
                ghost["zone_perimeter"] = perimeter
                ghost["zone_wp_idx"]    = start_idx

            # Één stap kloksgewijs langs de rand
            perimeter = ghost["zone_perimeter"]
            next_idx  = (ghost["zone_wp_idx"] + 1) % len(perimeter)
            ghost["zone_wp_idx"]        = next_idx
            ghost["col"], ghost["row"] = perimeter[next_idx]
            ghost["paused"]            = False
            return

        elif ghost.get("zone_mode"):
            # Geest heeft de zone verlaten → reset naar normale achtervolgingsmodus
            ghost["zone_mode"]      = False
            ghost["zone_perimeter"] = None
            ghost["zone_wp_idx"]    = 0

    # ── Modus 1: controle of de geest wakker wordt ────────────────────────────
    if not ghost["activated"]:
        chebyshev = max(abs(ghost["col"] - player_col),
                        abs(ghost["row"] - player_row))
        if chebyshev <= ghost.get("radius", AMBUSH_RADIUS):
            ghost["activated"] = True

    if not ghost["activated"]:
        ghost["paused"] = False
        return

    # ── Modus 2: achtervolging met periodieke pauze ───────────────────────────
    ghost["move_count"] += 1
    if ghost["move_count"] % AMBUSH_PAUSE_FREQ == 0:
        # Elke AMBUSH_PAUSE_FREQ zetten staat de geest één beurt stil
        ghost["paused"] = True
        return

    ghost["paused"] = False
    prev_col, prev_row = ghost["col"], ghost["row"]

    # Teleporter-cooldown: voorkomt dat de geest onmiddellijk terugspringt
    # via hetzelfde portaal nadat hij er net doorheen gegaan is
    tp_cd = ghost.get("tp_cooldown", 0)
    if tp_cd > 0:
        ghost["tp_cooldown"] = tp_cd - 1
        skip_tp = True
    else:
        skip_tp = False

    dc, dr = bfs_next_step(ghost["col"], ghost["row"],
                           player_col, player_row,
                           lvl, blocked_cells, shared_gates,
                           skip_tp_at_start=skip_tp,
                           broken_walls=broken_walls)

    # Alleen één stap bewegen (teleporter-sprongen worden afgehandeld door
    # apply_ghost_shared_teleport ná deze functie)
    if abs(dc) <= 1 and abs(dr) <= 1:
        ghost["col"] += dc
        ghost["row"] += dr

    # Als de geest door een gedeelde one-shot gate is gegaan: markeer als gebruikt
    if shared_gates and (dc != 0 or dr != 0):
        edge_moved = frozenset([(prev_col, prev_row), (ghost["col"], ghost["row"])])
        for sg in shared_gates:
            if sg["edge"] == edge_moved and not sg["used"]:
                if (dc, dr) == tuple(sg["pass_dir"]):
                    sg["used"] = True


def apply_ghost_shared_teleport(ghost, lvl):
    """Teleporteert een geest als hij op een gedeeld of ghost-only portaal staat.

    Moet ALTIJD aangeroepen worden ná move_ghost() of move_ambush_ghost().
    De cooldown van 1 beurt voorkomt ping-pong: zonder cooldown zou de geest
    direct na aankomst via het portaal terugspringen.

    Geeft True terug als de geest geteleporteerd is, anders False.
    """
    if ghost.get("tp_cooldown", 0) > 0:
        return False

    pos = (ghost["col"], ghost["row"])
    for tp_key in ("shared_teleporters", "ghost_teleporters"):
        stp = lvl.get(tp_key)
        if not stp:
            continue
        for i, tp in enumerate(stp):
            if pos == tuple(tp):
                dest = stp[1 - i]
                ghost["col"]        = dest[0]
                ghost["row"]        = dest[1]
                ghost["tp_cooldown"] = 1  # blokkeer terugsprong voor 1 beurt
                return True

    return False


# ─── Meta-box schuif ──────────────────────────────────────────────────────────

def slide_meta_box(col, row, dc, dr, lvl, state, all_box_pos):
    """Berekent de eindpositie van een schuivende meta-doos.

    Een meta-doos (M) glijdt in de opgegeven richting totdat hij stopt door:
    - Een rode, blauwe of paarse muur
    - Een oranje gate
    - Een andere doos of meta-doos
    - De gesloten gate-cel
    - De rand van het grid

    Meta-meta regel "meta_block_breaks" (alleen actief in de local rule zone):
    Als het blok BINNEN de zone een muur raakt, wordt die muur gebroken en
    schuift het blok verder.  Rode, groene en paarse muren kunnen zo gebroken
    worden.  Oranje gates en andere dozen breken nooit.

    Geeft de eindpositie (col, row) terug.
    """
    gate      = state["gate"]
    gate_cell = tuple(gate["pos"]) if gate and not gate["open"] else None
    broken    = state.get("broken_walls", set())
    lrz       = lvl.get("local_rule_zone")

    def in_zone(c, r):
        """True als cel (c, r) in de zone ligt én de meta_block_breaks regel actief is."""
        if not lrz:
            return False
        if "meta_block_breaks" not in lrz.get("meta_meta_rules", set()):
            return False
        c_min, r_min, c_max, r_max = lrz["rect"]
        return c_min <= c <= c_max and r_min <= r <= r_max

    def is_breakable_wall(edge):
        """True als de muur gebroken KAN worden (rood, groen of paars — niet oranje)."""
        return (edge in lvl["walls"]
                or edge in lvl.get("green_walls",  set())
                or edge in lvl.get("purple_walls", set()))

    while True:
        nc, nr = col + dc, row + dr

        # Stop aan de rand van het grid
        if not (0 <= nc < lvl["cols"] and 0 <= nr < lvl["rows"]):
            break

        edge = frozenset([(col, row), (nc, nr)])

        # Oranje gates en andere dozen stoppen het blok altijd
        if any(og["edge"] == edge for og in state.get("orange_gates", [])):
            break
        if (nc, nr) in all_box_pos:
            break
        if gate_cell and (nc, nr) == gate_cell:
            break

        # Muurcheck met optionele wallbreaking (meta-meta-regel)
        if is_breakable_wall(edge) and edge not in broken:
            if in_zone(col, row) and in_zone(nc, nr):
                # BEIDE cellen in zone → muur breekt, blok schuift verder
                broken.add(edge)
                state["broken_walls"] = broken
            else:
                # Buiten zone (of slechts één cel in zone) → normaal stoppen
                break

        col, row = nc, nr

    return col, row
