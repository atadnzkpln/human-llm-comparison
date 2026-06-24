"""
lv_constants.py — Gedeelde constanten voor het NP-Hard Pac-Man project.

Geïmporteerd door zowel de visuele game (level1.py) als de headless API-runner
(api_runner.py) en de gamelogica (lv_logic.py).  Door alle magic numbers hier
te centraliseren hoeft een waarde maar op één plek aangepast te worden.
"""

import os

# Pad naar het pixel-font dat in de visuele game gebruikt wordt.
# Als het bestand ontbreekt, valt level1.py terug op een systeem-font.
FONT_PATH = os.path.join(os.path.dirname(__file__), "PressStart2P-Regular.ttf")

# Pixels tussen de rand van het venster en de eerste cel van het grid.
# Groter = meer ruimte voor kolom-/rij-labels en de rand.
PADDING   = 65


# ─── Kleurenpalet (RGB-tuples) ────────────────────────────────────────────────
# Gebaseerd op Paul Tol's Muted colorblind-safe palette:
#   navy(46,37,133)  green(51,117,56)  teal(93,168,153)  light-blue(148,203,236)
#   sand(220,205,125)  rose(194,106,119)  purple(159,74,150)  dark-purple(126,41,84)

C_BG           = ( 10,   8,  25)  # achtergrondkleur venster (diep marineblauw)
C_GRID         = ( 38,  32,  90)  # celrand-kleur in het grid
C_CELL         = ( 18,  16,  45)  # celvulling
C_LABEL        = (148, 203, 236)  # kolom-/rij-labels — Tol light-blue
C_PAC          = (255, 220,   0)  # Pac-Man (geel, iconisch)
C_PAC_POWERED  = (255, 140,   0)  # Pac-Man tijdens powerup (oranje)
C_EYE          = (255, 255, 255)  # oogwit
C_EYE_PUP     = (  0,   0,   0)  # pupil
C_FOOD         = (220, 205, 125)  # voedsel-pellet — Tol sand
C_FOOD_IN      = (240, 230, 170)  # voedsel-pellet binnenrand
C_BANANA       = (220, 205, 125)  # banaan (doel) — Tol sand
C_BANANA_D     = (130, 115,  45)  # banaan donkere omtrek
C_WALL_LINE    = (194, 106, 119)  # permanente muur — Tol rose
C_GHOST        = (148, 203, 236)  # patrouille-geest — Tol light-blue
C_GHOST_SCARED = ( 46,  37, 133)  # geest scared — Tol navy
C_GHOST_EYE    = (  0,  50, 160)  # pupil van normale geest
C_GHOST_EYE_SC = (220, 205, 125)  # pupil van scared geest — Tol sand
C_AMBUSH_GHOST     = (126,  41,  84)  # hinderlaag-geest — Tol dark-purple (goed zichtbaar)
C_AMBUSH_GHOST_EYE = (220, 205, 125)  # oog van hinderlaag-geest — Tol sand
C_GATE_OPEN    = ( 51, 117,  56)  # open gate — Tol green
C_GATE_SHUT    = (126,  41,  84)  # gesloten gate — Tol dark-purple
C_GATE_FRAME   = (220, 205, 125)  # omlijsting van de gate — Tol sand
C_TP_A         = ( 46,  37, 133)  # teleporter eindpunt A — Tol navy
C_TP_B         = (148, 203, 236)  # teleporter eindpunt B — Tol light-blue
C_TP_SHARED_A  = ( 51, 117,  56)  # gedeeld teleportaal A — Tol green (visueel duidelijk anders dan TP_A/B)
C_TP_SHARED_B  = (220, 205, 125)  # gedeeld teleportaal B — Tol sand (warm, onderscheidend van TP_SHARED_A)
C_LIGHTNING    = (220, 205, 125)  # powerup bliksem — Tol sand
C_LIGHTNING_D  = (130, 115,  45)  # powerup bliksem omtrek
C_DELAY_PU     = ( 46,  37, 133)  # vertraagde powerup — Tol navy
C_DELAY_PU_D   = ( 93, 168, 153)  # vertraagde powerup omtrek — Tol teal
C_BOX          = (160, 100,  40)  # duwbare doos (bruin)
C_BOX_EDGE     = (100,  60,  20)  # doos-rand
C_BOX_CROSS    = (120,  75,  30)  # kruis op de doos
C_META_BOX     = ( 93, 168, 153)  # meta-doos — Tol teal
C_META_BOX_EDG = (148, 203, 236)  # meta-doos rand — Tol light-blue
C_META_BOX_CRS = (120, 185, 170)  # meta-doos kruis
C_MOVE_OK      = ( 51, 117,  56)  # resterende zetten — voldoende — Tol green
C_MOVE_WARN    = (220, 205, 125)  # resterende zetten — bijna op — Tol sand
C_MOVE_NO      = ( 38,  32,  80)  # verbruikte zetten in de balk
C_MOVE_BAR     = ( 18,  16,  45)  # achtergrond van de zettenbalk
C_POWER_BAR    = (220, 205, 125)  # powerup-duur indicator — Tol sand
C_WIN          = ( 51, 117,  56)  # groene tekst bij winst — Tol green
C_LOSE         = (194, 106, 119)  # rode tekst bij verlies — Tol rose
C_WHITE        = (255, 255, 255)
C_BORDER       = ( 46,  37, 133)  # gridborder — Tol navy
C_NEXT         = (148, 203, 236)  # "volgende level"-kleur — Tol light-blue
C_GREEN_WALL      = ( 93, 168, 153)  # one-shot muur — visueel TEAL (Tol teal); variabelenaam "GREEN" is historisch
C_GREEN_WALL_USED = ( 28,  60,  55)  # one-shot muur na gebruik — donker teal, geblokkeerd
C_PURPLE_WALL  = (159,  74, 150)  # permanente muur (visueel: PAARS) — Tol purple
C_ORANGE_WALL  = (220, 205, 125)  # one-shot gate open (visueel: ZANDGEEL) — Tol sand
C_ORANGE_USED  = ( 75,  65,  30)  # one-shot gate na gebruik (donker zandgeel, gesloten)
C_FRIEND_GHOST     = ( 51, 117,  56)  # vriendelijke geest — Tol green
C_FRIEND_GHOST_EYE = ( 15,  55,  20)  # oog vriendelijke geest


# ─── Spelconstanten ───────────────────────────────────────────────────────────

# Aantal zetten dat de speler ghosts kan opeten na het pakken van een powerup.
# Na POWER_TURNS zetten worden geesten weer gevaarlijk.
POWER_TURNS       = 6

# Aantal zetten dat de vertraagde powerup wacht NADAT de speler de zone verlaat
# voordat hij activeert.  Lager = minder uitdagend.
DELAY_PU_MOVES    = 3

# Chebyshev-afstand waarbij een slapende hinderlaag-geest wakker wordt.
# Chebyshev = max(|Δcol|, |Δrij|) — maakt diagonale nadering even gevaarlijk.
AMBUSH_RADIUS     = 2

# De hinderlaag-geest pauzeert elke AMBUSH_PAUSE_FREQ zetten tijdens de achtervolging.
# Dit geeft de speler een korte ademruimte en maakt de timing voorspelbaar.
AMBUSH_PAUSE_FREQ = 5
