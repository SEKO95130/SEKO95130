"""60-second cut of the House of Basketball x Cergy interview.
Same sources, framing and graphics as the full version (timeline.py); one strong answer per speaker,
no music, voice-overs reused from the full version."""
from timeline import RUSH, OFF, FACE, ZOOMS, FACE_ANCHOR, GOLD_WORDS, QUESTION_LABEL  # noqa: F401

PARTS = [
    # 0 — logo
    [dict(kind="black", dur=2.6, id="logo", gfx=[dict(type="logo_big", t0=0.0, t1=2.6)])],
    # 1 — Maradas gym + title (intro voice-over runs over the logo and this shot)
    [dict(kind="video", src="INTERVIEW CERGY", tin=1.0, dur=5.2, kb=(1.0, 1.08), amb=-16,
          gfx=[dict(type="title", t0=0.4, t1=4.9, main="INTERVIEW · CERGY", sub="CHAMPIONS DE LA WINTER SERIES")])],
    # 2 — title holders + Sidy MVP
    [dict(kind="video", src="WIN CERGY", tin=0.6, dur=3.6, amb=-10, lowres=True,
          delogo=(20, 868, 360, 250),
          gfx=[dict(type="band", t0=0.0, t1=3.6, main="TENANTS DU TITRE", sub="WINTER SERIES · 45-23 FACE À FAST IMPACT")]),
     dict(kind="video", src="SIDY PHOTO", tin=0.0, dur=5.6, amb=None, kb=(1.0, 1.08), vo=True, id="sidy_photo",
          gfx=[dict(type="card", t0=0.2, t1=5.6, name="SIDY", info="MVP 2025")])],
    # 3 — Cyril
    [dict(kind="video", src="DUNK CYRIL", tin=0.4, dur=2.4, amb=-16, bright=0.05,
          gfx=[dict(type="card", t0=0.2, t1=2.4, name="CYRIL", info="Poste 1-2 · Cergy N2 · 2008")]),
     dict(kind="q", who="cyril", dur=1.7, bg_t=23.4, text="{TENANTS DU TITRE} : AUCUNE {APPRÉHENSION} ?"),
     dict(kind="dialog", who="cyril", vin=24.80, vout=28.70, text="Non, on va encore gagner, c'est bon. On va aller sereinement.")],
    # 4 — Geoffroy
    [dict(kind="video", src="GEOFF", tin=0.0, dur=2.6, amb=-18, zoom=(1.0, 0.5, 0.55),
          gfx=[dict(type="card", t0=0.2, t1=2.6, name="GEOFFROY", info="Poste 3-4 · Cergy U21 · 2006")]),
     dict(kind="q", who="geoffroy", dur=1.8, bg_t=0.3, text="LES {U21} MÉRITENT-ILS PLUS DE {VISIBILITÉ} ?"),
     dict(kind="dialog", who="geoffroy", vin=18.90, vout=22.35, text="Et parfois, même ceux qui sont en U18, ils ne veulent pas venir en U21, alors que c'est une très bonne catégorie.",
          broll=dict(src="GEOFF", tin=6.4, zoom=(1.0, 0.5, 0.5))),
     dict(kind="dialog", who="geoffroy", vin=22.35, vout=25.60, text="Et c'est un vrai tremplin vers les seniors. Donc en vrai, c'est top.")],
    # 5 — Marwin
    [dict(kind="video", src="3 ECH", tin=3.35, dur=2.2, amb=-20,
          gfx=[dict(type="card", t0=0.2, t1=2.2, name="MARWIN", info="Poste 1-2 · Cergy · 2008")]),
     dict(kind="q", who="marwin", dur=1.8, bg_t=0.1, text="TES {OBJECTIFS} POUR ALLER CHERCHER LA {VICTOIRE} ?"),
     dict(kind="dialog", who="marwin", vin=3.30, vout=6.55, text="Rien, mettre de l'intensité, des dunks, des crosses,"),
     dict(kind="dialog", who="marwin", vin=6.55, vout=8.40, text="taffer tout le monde et prendre du plaisir.")],
    # 6 — Coach
    [dict(kind="q", who="coach", dur=1.8, bg_t=1.0, text="DES {ATTENTES} PAR RAPPORT À TON {ÉQUIPE} ?"),
     dict(kind="dialog", who="coach", vin=7.60, vout=11.48, text="On a gagné l'année dernière, il faut qu'on gagne cette année.",
          gfx=[dict(type="card", t0=0.15, t1=3.6, name="COACH", info="Coach de Cergy")]),
     dict(kind="dialog", who="coach", vin=11.48, vout=13.30, text="Il faut qu'on prouve qu'on est la meilleure équipe du Val-d'Oise.")],
    # 7 — Dan
    [dict(kind="q", who="dan", dur=1.6, bg_t=1.0, text="LA PLUS GRANDE {FORCE} DE L'ÉQUIPE ?"),
     dict(kind="dialog", who="dan", vin=5.40, vout=7.55, text="Je pense que la plus grande force, c'est la défense.",
          gfx=[dict(type="card", t0=0.1, t1=2.15, name="DAN", info="Joueur · Cergy · 2008")])],
    # 8 — outro
    [dict(kind="black", dur=3.5, id="outro", gfx=[dict(type="logo_big", t0=0.0, t1=3.5, outro=True)])],
]

# (voice-over file in vo/, clip in, clip out, shot id, offset from that shot's start)
VOICEOVERS = [
    ("intro", 0.95, 9.30, "logo", 0.20),        # "...ça dit quoi ? ... les vainqueurs de la première édition ... C'est parti les mecs !"
    ("sidy", 5.50, 10.40, "sidy_photo", 0.35),  # "Il a fini MVP de la saison dernière et il évolue avec Cergy en Île-de-France et en N2."
    ("abdou", 17.85, 20.00, "outro", 0.45),     # "Rendez-vous le 20 décembre, à Groslay."
]
