BRANCHES = {
    "voice": "The Voice of Ashfall",
    "atelier": "The Atelier of Ash",
    "merchant": "The Merchant Covenant",
    "wardens": "The Chronicle Wardens",
}


GENERAL_RANKS = {
    "Ashbound": 0,
    "Hearthmarked": 40,
    "Waysworn": 120,
    "Trusted of Ashfall": 300,
    "Keeper of the Chronicle": 700,
    "Inner Circle": 1500,
}


BRANCH_RANKS = {
    "voice": {
        "Street Crier": 8,
        "Ash Caller": 30,
        "Chapel Voice": 90,
        "Church Herald": 220,
        "High Proclaimer": 500,
    },
    "atelier": {
        "Soot Sketcher": 10,
        "Candle Painter": 35,
        "Reliquary Artisan": 85,
        "Cathedral Illuminator": 190,
        "Master of the Atelier": 380,
    },
    "merchant": {
        "Pack Trader": 12,
        "Caravan Factor": 40,
        "Guild Broker": 100,
        "Benefactor of Ash": 220,
        "High Quartermaster": 450,
    },
    "wardens": {
        "Ash Witness": 8,
        "Road Scout": 30,
        "Chronicle Scribe": 75,
        "Cartographer of Ruin": 170,
        "Archive Keeper": 360,
    },
}


def get_rank_by_marks(ranks: dict[str, int], marks: int) -> str | None:
    available_ranks = [
        rank_name
        for rank_name, required_marks in ranks.items()
        if marks >= required_marks
    ]

    if not available_ranks:
        return None

    return max(available_ranks, key=lambda rank_name: ranks[rank_name])


def get_general_rank(total_marks: int) -> str:
    rank = get_rank_by_marks(GENERAL_RANKS, total_marks)
    return rank or "Ashbound"


def get_branch_rank(branch: str, marks: int) -> str | None:
    ranks = BRANCH_RANKS.get(branch)

    if ranks is None:
        return None

    return get_rank_by_marks(ranks, marks)
