from immich_cli.immich_api.dtos import TagResponseDto
from immich_cli.immich_api.immich_class import Immich
from argparse import Namespace


def move(args: Namespace, config: dict) -> None:
    """Pick a create action based on the user-selected object."""
    if hasattr(args, "object"):
        match args.object:
            case "asset":
                raise NotImplementedError()

            case "album":
                raise NotImplementedError()

            case "tag":
                print(args)
                raise NotImplementedError()

            case _:
                raise ValueError()


def tag(args: Namespace, config: dict):

    origin: str = args.origin
    to: str = args.to
    type: str = args.type
    mode: str = (
        "move"
        if hasattr(args, "move") and args.move
        else ("copy" if hasattr(args, "copy") and args.copy else "None")
    )

    immich: Immich = Immich(apiKey=config["apiKey"], baseURL=config["baseURL"])

    current_tags: list[TagResponseDto] = immich.get_tags()
