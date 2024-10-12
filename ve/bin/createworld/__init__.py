from argparse import ArgumentParser

from ve.world import World


def main():
    parser = ArgumentParser(description="Create a world")
    parser.add_argument(
        "-o",
        "--output",
        default="world.json",
        type=str,
        help="Output file name (default: world.json)",
    )
    parser.add_argument(
        "-s",
        "--size",
        default=16,
        type=int,
        help="World size (default: 16)",
    )
    args = parser.parse_args()

    world = World.create(args.size)
    world.save(args.output)
