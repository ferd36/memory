"""Manual check: show which TwoBackRecall rounds are scored."""

from problems import TwoBackRecall


def main():
    for round_num in range(1, 5):
        problem = TwoBackRecall.create(round_num=round_num)
        print(f"R{round_num}: is_scored={getattr(problem, 'is_scored', None)}")


if __name__ == '__main__':
    main()
