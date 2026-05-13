from ranks import get_branch_rank, get_general_rank


def main() -> None:
    assert get_general_rank(0) == "Ashbound"
    assert get_general_rank(40) == "Hearthmarked"
    assert get_general_rank(120) == "Waysworn"
    assert get_branch_rank("voice", 8) == "Street Crier"
    assert get_branch_rank("voice", 30) == "Ash Caller"
    assert get_branch_rank("atelier", 0) is None

    print("Rank checks passed.")


if __name__ == "__main__":
    main()
