"""Timeline of the House of Basketball x Cergy interview edit.
All times in seconds. Voice times refer to the clean voice files (voix/*.m4a).
video_t = voice_t + OFF[who]."""

RUSH = {
    "cyril": "Cyril interview 2",
    "geoffroy": "Geoffroy interwiew",
    "marwin": "Marwin interview",
    "coach": "Coach cergy",
    "dan": "Dan",
}
OFF = {"cyril": -1.348, "geoffroy": -4.744, "marwin": -0.941, "coach": 0.222, "dan": 0.544}
# speaker position in the frame (normalized x, y of the face) for punch-ins
FACE = {
    "cyril": (0.42, 0.515),
    "geoffroy": (0.27, 0.335),
    "marwin": (0.55, 0.52),
    "coach": (0.40, 0.555),
    "dan": (0.69, 0.515),
}
# medium framings only (bottom of frame between the knees and the waist), alternating on every cut
ZOOMS = {
    "cyril": [2.35, 3.0],
    "geoffroy": [1.35, 2.1],
    "marwin": [2.4, 3.0],
    "coach": [2.6, 3.0],
    "dan": [2.15, 3.0],
}
FACE_ANCHOR = 0.33  # face at 1/3 from the top of the frame

# Sidy voice-over: (clip in, clip out) in vo/sidy.m4a -> start offset from the beginning of the Sidy shot
VO_SIDY = [
    (0.80, 4.70, 1.44),    # "Dans cette équipe, il y a un joueur à surveiller de près, c'est Sidy."
    (5.50, 10.40, 5.81),   # "Il a fini MVP de la saison dernière et il évolue avec Cergy..."
    (10.60, 12.40, 10.72), # "Et cette année, il compte bien remettre ça."
]

# Abdou voice-over: (clip in, clip out) in vo/abdou.m4a -> start offset from the beginning of the Abdou part
VO_ABDOU = [
    (0.55, 4.55, 0.70),    # "Il y a aussi un autre nom à retenir, celui d'Abdou..."
    (5.00, 7.75, 5.60),    # "C'est un profil qui monte..."
    (8.10, 10.50, 10.40),  # "C'est un poste 1-2, meneur, arrière,"
    (10.50, 13.50, 13.83), # "et l'année dernière... La Grinta."
    (13.60, 16.10, 17.40), # "Cette année, c'est un joueur à suivre sur la Winter Series,"
    (16.10, 17.80, 21.80), # "et Cergy remet son titre en jeu."
    (17.85, 20.00, 24.80), # "Rendez-vous le 20 décembre, à Groslay."
]

GOLD_WORDS = {
    "95", "GAGNER", "U21", "U18", "TREMPLIN", "SENIORS", "DÉFENSE", "SOUDÉS", "DUNKS",
    "INTENSITÉ", "PLAISIR", "MENTALITÉ", "VAL-D'OISE", "NIVEAU", "AMBIANCE", "MIEUX",
    "SEREINEMENT", "DONNER", "VISIBILITÉ", "ÎLE-DE-FRANCE", "IMPORTANTE", "CROSSES",
    "IMPORTANT", "ÉQUIPE", "MONDE", "REPRÉSENTE", "DIFFÉRENTS", "GAGNÉ",
}

# parts: each part is a list of shots. A dip-to-black (0.3 s) is placed between parts.
# shot kinds:
#   black  : dur
#   video  : src, tin, dur, speed, zoom=(z,cx,cy), kb=(z0,z1), amb (dB), delogo
#   dialog : who, vin, vout, text, [broll={src,tin,zoom,speed}], zoom index auto
#   q      : who, dur, text (question card on blurred interview), bg_t (voice time)
# graphics attached to shots: "gfx": list of dicts with relative times

PARTS = [
    # 0 — logo intro
    [dict(kind="black", dur=2.6, gfx=[dict(type="logo_big", t0=0.0, t1=2.6)], music="intro")],
    # 1 — Interview Cergy (Maradas gym)
    [dict(kind="video", src="INTERVIEW CERGY", tin=1.0, dur=5.6, kb=(1.0, 1.08), amb=-16,
          gfx=[dict(type="title", t0=0.5, t1=5.2, main="INTERVIEW · CERGY", sub="CHAMPIONS DE LA WINTER SERIES")])],
    # 2 — Win Cergy + Sidy Tomar
    [dict(kind="video", src="WIN CERGY", tin=0.2, dur=7.6, amb=-9, lowres=True,
          delogo=(20, 868, 360, 250),
          gfx=[dict(type="band", t0=0.0, t1=7.6, main="TENANTS DU TITRE", sub="WINTER SERIES · 45-23 FACE À FAST IMPACT")]),
     dict(kind="video", src="SIDY TOMAR", tin=0.0, dur=6.4, amb=-20, lowres=True, kb=(1.0, 1.12), vo=True,
          delogo=(170, 988, 382, 100),
          gfx=[dict(type="card", t0=0.0, t1=6.4, name="SIDY", info="MVP 2025", instant=True)]),
     dict(kind="video", src="SIDY PHOTO", tin=0.0, dur=6.3, amb=None, kb=(1.0, 1.10), vo=True,
          gfx=[dict(type="title_top", t0=0.25, t1=6.1, main="MVP DE LA SAISON PASSÉE", sub="", y=1560)])],
    # 3 — Cyril
    [dict(kind="video", src="3 ECH", tin=0.0, dur=1.5, amb=-20),
     dict(kind="video", src="DUNK CYRIL", tin=0.0, dur=3.3, amb=-16, bright=0.05),
     dict(kind="video", src="CYRIL RUSH", tin=0.3, dur=3.6, amb=-24, kb=(1.0, 1.06), zoom=(1.15, 0.5, 0.45),
          gfx=[dict(type="card", t0=0.25, t1=3.6, name="CYRIL", info="Poste 1-2 · Cergy N2 · 2008")]),
     dict(kind="q", who="cyril", dur=2.4, bg_t=0.2,
          text="UNE ATTENTE POUR CE {TOURNOI}, EN TANT QUE {TENANTS DU TITRE} ?"),
     dict(kind="dialog", who="cyril", vin=6.50, vout=8.45, text="Moi, pas forcément d'attente."),
     dict(kind="dialog", who="cyril", vin=8.45, vout=10.60, text="Du coup, l'année dernière, c'était bien."),
     dict(kind="dialog", who="cyril", vin=10.60, vout=14.60, text="J'ai juste envie que ce soit la même chose que l'année dernière. Il y avait beaucoup de monde, il y avait beaucoup d'ambiance, il y avait du niveau."),
     dict(kind="dialog", who="cyril", vin=14.60, vout=16.85, text="Et franchement, ça fait plaisir les tournois comme ça.",
          broll=dict(src="3 ECH", tin=3.0, zoom=(1.4, 0.5, 0.55))),
     dict(kind="dialog", who="cyril", vin=16.85, vout=20.92, text="Surtout, c'est dans le 95, donc ça représente. Et franchement, c'était bien. Franchement, c'était cool."),
     dict(kind="dialog", who="cyril", vin=20.92, vout=23.20, text="J'ai envie que ça refasse la même chose, même voire mieux."),
     dict(kind="q", who="cyril", dur=1.7, bg_t=23.4, text="AUCUNE {APPRÉHENSION} ?"),
     dict(kind="dialog", who="cyril", vin=24.80, vout=28.70, text="Non, on va encore gagner, c'est bon. On va aller sereinement.")],
    # 4 — Geoffroy
    [dict(kind="video", src="GEOFFROY B", tin=0.0, dur=2.8, amb=-20, band=(0, 263, 360, 250)),
     dict(kind="video", src="GEOFF", tin=0.0, dur=4.2, amb=-18, zoom=(1.0, 0.5, 0.55),
          gfx=[dict(type="card", t0=0.25, t1=4.2, name="GEOFFROY", info="Poste 3-4 · Cergy U21 · 2006")]),
     dict(kind="q", who="geoffroy", dur=2.4, bg_t=0.3,
          text="LES {U21} MÉRITENT-ILS PLUS DE {VISIBILITÉ} ?"),
     dict(kind="dialog", who="geoffroy", vin=3.72, vout=7.46, text="Oui, totalement, parce que je trouve que c'est une catégorie assez importante.",
          broll=dict(src="GEOFFROY A", tin=0.0, band=(0, 354, 444, 250))),
     dict(kind="dialog", who="geoffroy", vin=7.46, vout=10.40, text="Je trouve qu'il y a du niveau, notamment dans la région, en Île-de-France."),
     dict(kind="dialog", who="geoffroy", vin=10.40, vout=13.60, text="Donc ouais, je trouve que c'est une catégorie qui doit être mise plus en avant."),
     dict(kind="dialog", who="geoffroy", vin=13.60, vout=16.40, text="Et voilà, tout simplement. Ouais, malheureusement, elle est mise de côté."),
     dict(kind="dialog", who="geoffroy", vin=17.60, vout=18.90, text="Elle est mise trop de côté."),
     dict(kind="dialog", who="geoffroy", vin=18.90, vout=22.35, text="Et parfois, même ceux qui sont en U18, ils ne veulent pas venir en U21, alors que c'est une très bonne catégorie.",
          broll=dict(src="GEOFF", tin=6.4, zoom=(1.0, 0.5, 0.5))),
     dict(kind="dialog", who="geoffroy", vin=22.35, vout=25.60, text="Et c'est un vrai tremplin vers les seniors. Donc en vrai, c'est top.")],
    # 5 — Marwin
    [dict(kind="video", src="3 ECH", tin=3.35, dur=3.0, amb=-20,
          gfx=[dict(type="card", t0=0.3, t1=3.0, name="MARWIN", info="Poste 1-2 · Cergy · 2008")]),
     dict(kind="q", who="marwin", dur=2.2, bg_t=0.1, text="TES {OBJECTIFS} POUR ALLER CHERCHER LA {VICTOIRE} ?"),
     dict(kind="dialog", who="marwin", vin=3.30, vout=6.55, text="Rien, mettre de l'intensité, des dunks, des crosses,"),
     dict(kind="dialog", who="marwin", vin=6.55, vout=8.40, text="taffer tout le monde et prendre du plaisir.")],
    # 6 — Coach
    [dict(kind="q", who="coach", dur=2.4, bg_t=1.0, text="DES {ATTENTES} PAR RAPPORT À TON {ÉQUIPE} ?"),
     dict(kind="dialog", who="coach", vin=3.70, vout=7.45, text="Oui, tout simplement qu'ils aient une bonne mentalité, la mentalité de gagner.",
          gfx=[dict(type="card", t0=0.15, t1=3.4, name="COACH", info="Coach de Cergy")]),
     dict(kind="dialog", who="coach", vin=7.60, vout=11.48, text="On a gagné l'année dernière, il faut qu'on gagne cette année."),
     dict(kind="dialog", who="coach", vin=11.48, vout=13.30, text="Il faut qu'on prouve qu'on est la meilleure équipe du Val-d'Oise."),
     dict(kind="q", who="coach", dur=2.0, bg_t=13.8, text="DES {APPRÉHENSIONS}, APRÈS LE {TITRE} ?"),
     dict(kind="dialog", who="coach", vin=17.35, vout=19.85, text="Je pense qu'au vu du niveau de l'année dernière,"),
     dict(kind="dialog", who="coach", vin=19.85, vout=21.88, text="je pense qu'il va y avoir du niveau cette année.",
          broll=dict(src="Cergy dunk", tin=0.7, zoom=(1.22, 0.55, 0.3))),
     dict(kind="dialog", who="coach", vin=23.85, vout=25.70, text="Oui, ça va s'élever. Maintenant, j'ai des joueurs différents aussi."),
     dict(kind="dialog", who="coach", vin=26.40, vout=28.55, text="Voilà, à nous de tout donner.")],
    # 7 — Dan + Dan Tir
    [dict(kind="q", who="dan", dur=2.2, bg_t=1.0, text="LA PLUS GRANDE {FORCE} DE L'ÉQUIPE ?"),
     dict(kind="dialog", who="dan", vin=5.40, vout=7.55, text="Je pense que la plus grande force, c'est la défense.",
          gfx=[dict(type="card", t0=0.15, t1=4.0, name="DAN", info="Joueur · Cergy · 2008")]),
     dict(kind="dialog", who="dan", vin=7.55, vout=11.20, text="On est soudés en défense. Je pense que pour moi, c'est le plus important aussi."),
     dict(kind="video", src="DAN TIR", tin=0.2, dur=5.35, amb=-14)],
    # 8 — Abdou (voice-over zone)
    [dict(kind="video", src="Abou live", tin=1.6, dur=5.0, amb=-20, vo=True,
          gfx=[dict(type="sentence", t0=1.0, t1=4.6, text="ABDOU, JOUEUR DE {CERGY}")]),
     dict(kind="video", src="Abou live 2", tin=0.0, dur=5.0, amb=-20, vo=True,
          gfx=[dict(type="title", t0=0.3, t1=4.8, main="À SUIVRE · WINTER SERIES", sub="")]),
     dict(kind="video", src="Abou live 2", tin=5.0, dur=3.9, amb=-20, vo=True,
          gfx=[dict(type="card", t0=0.0, t1=3.9, name="ABDOU", info="Poste 1-2 · Cergy", extra="Demi-finaliste 2025 avec La Grinta"),
               dict(type="sentence", t0=0.5, t1=3.7, text="{POSTE 1-2}")]),
     dict(kind="video", src="Abou 1", tin=3.0, dur=3.4, amb=-20, vo=True,
          gfx=[dict(type="sentence", t0=0.2, t1=3.4, text="L'AN DERNIER, IL A ATTEINT LES {DEMI-FINALES} AVEC {LA GRINTA}")]),
     dict(kind="video", src="Abou 1", tin=14.8, dur=4.4, amb=-20, vo=True,
          gfx=[dict(type="sentence", t0=0.4, t1=4.2, text="CETTE ANNÉE, C'EST UN {JOUEUR À SUIVRE} SUR LA WINTER SERIES")]),
     dict(kind="video", src="Abou 2", tin=0.8, dur=4.2, amb=-20, vo=True),
     dict(kind="video", src="Abou 2", tin=5.0, dur=2.3, amb=-20, vo=True, kb=(1.0, 1.12),
          gfx=[dict(type="sentence", t0=-1.0, t1=2.3, text="RENDEZ-VOUS LE {20 DÉCEMBRE}")])],
    # 9 — outro
    [dict(kind="black", dur=4.6, gfx=[dict(type="logo_big", t0=0.0, t1=4.6, outro=True)], music="outro")],
]

QUESTION_LABEL = "LA QUESTION"
