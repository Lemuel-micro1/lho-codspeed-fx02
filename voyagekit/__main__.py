import argparse
import sys

from voyagekit import core


def main(argv=None):
    parser = argparse.ArgumentParser(prog="voyagekit")
    parser.add_argument("command", choices=["summary", "alerts"])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--synthetic", type=int, metavar="N_LINES")
    parser.add_argument("--max-knots", type=float, default=30.0)
    args = parser.parse_args(argv)

    if args.file:
        records = core.load_log(args.file)
    else:
        records = core.parse_log(core.synthetic_log(args.synthetic))

    if args.command == "summary":
        totals = core.track_distance(records)
        print(f"{len(records)} fixes, {len(totals)} vessels, "
              f"{sum(totals.values()):.1f} nm total")
    else:
        alerts = core.speed_alerts(records, args.max_knots)
        print(f"{len(alerts)} speed alerts above {args.max_knots} kn")
    return 0


if __name__ == "__main__":
    sys.exit(main())