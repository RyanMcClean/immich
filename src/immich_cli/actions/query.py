from immich_cli.immich_api.dtos import AlbumResponseDto
from immich_cli.immich_api.dtos import TagResponseDto
from immich_cli.immich_api.immich_class import Immich
from argparse import Namespace
import pprint


def query(args: Namespace, config: dict):
    """
    Query immich instance, match to query type
    """
    if hasattr(args, "type"):
        match args.type:
            case "tag":
                tag(args, config)

            case "album":
                album(args, config)

            case _:
                raise ValueError


def tag(args: Namespace, config: dict):
    """
    Search for tag or return all tags
    """
    immich = Immich(config["BASE_URL"], config["API_KEY"])
    pp = pprint.PrettyPrinter(indent=4)

    tags: list[TagResponseDto] = immich.get_tags()

    if hasattr(args, "search") and args.search:
        tags = [tag for tag in tags if args.search.lower() in tag.value.lower()]

    tags.sort(key=lambda x: x.value)

    if hasattr(args, "print"):
        match args.print:

            case "less":
                for tag in tags:
                    pp.pprint(tag.value)

            case "tree":
                pass

            case _:
                for tag in tags:
                    pp.pprint(tag.__dict__)


def album(args: Namespace, config: dict):
    """
    Search for specific album or return all albums
    """

    immich = Immich(config["BASE_URL"], config["API_KEY"])
    pp = pprint.PrettyPrinter(indent=4)

    albums: list[AlbumResponseDto] = immich.get_albums()

    if hasattr(args, "search") and args.search:
        albums = [
            album for album in albums if args.search.lower() in album.albumName.lower()
        ]

    albums.sort(key=lambda x: x.albumName)

    if hasattr(args, "print"):
        match args.print:
            case "all":
                for album in albums:
                    pp.pprint(album.__dict__)

            case "less":
                for album in albums:
                    pp.pprint(album.albumName)

            case "tree":
                pass
