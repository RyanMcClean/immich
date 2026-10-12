#!/home/ryan_mcc/Projects/immich-app-cli/.venv/bin/python
# PYTHON_ARGCOMPLETE_OK
# region Imports
from argparse import ArgumentParser
from logging import Logger

import argparse
import argcomplete
from datetime import datetime
import json
import logging
import os

from immich_cli.actions.download import download
from immich_cli.actions.create import create
from immich_cli.actions.query import query
from immich_cli.actions.move import move

# endregion


def main():
    # region Base parsing options

    parser = argparse.ArgumentParser(
        prog="Immich API CLI",
        description="A small CLI tool written in python" + " to interface with the immich API",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument(
        "-d",
        "--delay",
        action="store",
        help="Add a delay between each action " + "(helpful on slower servers)",
        default=0,
        type=int,
    )

    #### Sub parsers
    subparsers = parser.add_subparsers(
        dest="action",
        help="Action to take:",
        required=True,
        description="User defined action for tool to take",
    )

    # endregion
    # region Create subparser

    create_subparser: ArgumentParser = subparsers.add_parser(
        "create", help="Create object on Immich"
    )
    create_object_subparser = create_subparser.add_subparsers(
        dest="object",
        help="Object to create",
        description="Object name to create on Immich",
        required=True,
    )

    ### Create Object Subparser
    ## Asset
    create_asset_subparser: ArgumentParser = create_object_subparser.add_parser(
        "asset", help="Upload an asset to Immich"
    )
    create_asset_subparser.add_argument("file_path", help="Path to file or directory to upload")
    create_asset_subparser.add_argument(
        "--delete",
        action="store_true",
        help="Delete asset file(s) after being uploaded to Immich",
        default=False,
    )
    create_asset_subparser.add_argument(
        "-a",
        "--album",
        action="store",
        type=str,
        default=None,
        help="Add asset(s) to album after upload",
    )
    create_asset_subparser.add_argument(
        "-tb",
        "--tag-blurry",
        action="store_true",
        help="TODO: Use MSDU-Net and Facial detection "
        + "to categorise images based on blurriness",
    )
    create_asset_subparser.add_argument(
        "-ca",
        "--convert-audio",
        action="store_true",
        help="Convert audio to mp4 containers, will look weird,"
        + " but will store the audio files on immich",
    )
    create_asset_subparser.add_argument(
        "-t",
        "--tag",
        action="append",
        help="Apply specified tag to uploaded assets,"
        + " can be used multiple times in one command to apply multiple tags",
    )

    ## Album
    create_album_subparser: ArgumentParser = create_object_subparser.add_parser(
        "album", help="Create an album on Immich"
    )
    create_album_subparser.add_argument("album_name", help="Name of the album to create")

    ## Tag
    create_tag_subparser: ArgumentParser = create_object_subparser.add_parser(
        "tag", help="Create a tag on Immich"
    )
    create_tag_subparser.add_argument("tag_name", help="Name of the tag to create")

    # endregion
    # region Download subparser

    download_subparser: ArgumentParser = subparsers.add_parser(
        "download", help="Download asset from Immich"
    )
    download_object_subparser = download_subparser.add_subparsers(
        dest="object",
        help="Object to download",
        description="Object name to download",
        required=True,
    )

    ### Download Object Subparser
    ## Asset
    download_asset_parser: ArgumentParser = download_object_subparser.add_parser(
        "asset", help="Download an asset from Immich"
    )
    asset_type_parser = download_asset_parser.add_subparsers(
        dest="type", help="Type of download", description="Type of asset to download"
    )

    ## Single
    asset_single_parser: ArgumentParser = asset_type_parser.add_parser(
        "single", help="Download a single asset"
    )
    asset_single_parser.add_argument("-i", "--id", action="store", help="Asset UUID to download")
    asset_single_parser.add_argument(
        "-s",
        "--search",
        action="store",
        help="TODO: Provide search term to search for asset to download",
    )

    ## Album
    asset_album_parser: ArgumentParser = asset_type_parser.add_parser(
        "album", help="Download all assets in specified album"
    )
    asset_album_parser.add_argument(
        "-n", "--name", action="store", help="Name of album to download"
    )
    asset_album_parser.add_argument(
        "-s",
        "--search",
        action="store",
        help="TODO: Provide search term for asset to download",
    )
    asset_album_parser.add_argument(
        "-o",
        "--output",
        action="store",
        help="Output location to save downloads",
        required=True,
    )
    asset_album_parser.add_argument(
        "-i",
        "--include",
        action="store",
        help="TODO: Include deleted files, exif data, people, and stacks",
    )

    # endregion
    # region Delete subparser

    delete_subparser: ArgumentParser = subparsers.add_parser(
        "delete", help="Delete object from Immich"
    )

    # endregion
    # region Query subparser

    query_subparser: ArgumentParser = subparsers.add_parser(
        "query",
        help="Query immich instance for information. E.g. what tags/albums exist",
    )
    query_type_parser = query_subparser.add_subparsers(
        dest="type",
        help="Immich information to query",
        description="What you are querying to get information about from Immich, e.g. tags, albums, etc",
    )

    ## Tags
    query_tags_parser: ArgumentParser = query_type_parser.add_parser("tag", help="Query tags")
    query_tags_parser.add_argument("--all", action="store_true", help="Get all tags")
    query_tags_parser.add_argument(
        "-s",
        "--search",
        action="store",
        help="Search query for tags, returns all that match. "
        + "(Searching for a parent returns all child tags too)",
    )
    query_tags_parser.add_argument(
        "-p",
        "--print",
        action="store",
        help="Change print mode",
        choices=["all", "less", "tree"],
    )

    ## Album
    query_album_parser: ArgumentParser = query_type_parser.add_parser("album", help="Query albums")
    query_album_parser.add_argument("--all", action="store_true", help="Get all tags")
    query_album_parser.add_argument(
        "-s",
        "--search",
        action="store",
        help="Search query for tags, returns all that match. "
        + "(Searching for a parent returns all child tags too)",
    )
    query_album_parser.add_argument(
        "-p",
        "--print",
        action="store",
        help="Change print mode",
        choices=["all", "less", "tree"],
    )

    # endregion
    # region Move subparser

    move_subparser: ArgumentParser = subparsers.add_parser(
        "move",
        help="Move assets, e.g. copy assets from one tag to another, one album to another, etc.",
    )
    move_object_subparser = move_subparser.add_subparsers(
        dest="object",
        description="Object to move, if selecting a tag, or album, "
        + "will include every asset under that object",
        help="Object to move",
        required=True,
    )

    ## Tag
    move_tag_parser: ArgumentParser = move_object_subparser.add_parser(
        "tag", help="Move assets under a tag"
    )

    move_tag_parser.add_argument(
        "origin", action="store", help="Name of the tag to move assets from"
    )
    move_tag_parser.add_argument("to", action="store", help="Name of the object to move assets to")
    move_tag_parser.add_argument(
        "-t",
        "--type",
        choices=["tag", "album"],
        help="Type of object to move to",
        required=True,
    )
    mode = move_tag_parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-c",
        "--copy",
        action="store_true",
        help="Copy instead of move",
    )
    mode.add_argument(
        "-m",
        "--move",
        action="store_true",
        help="Move instead of copy",
    )

    # endregion
    # region Load Config

    argcomplete.autocomplete(parser)
    args: argparse.Namespace = parser.parse_args()

    with open("config.json") as f:
        config = json.load(f)

    os.makedirs("./log", exist_ok=True)

    # endregion
    # region Setup Logger

    logging.basicConfig(
        level=(
            logging.INFO
            if not args.verbose and not args.quiet
            else logging.DEBUG if args.verbose else logging.ERROR
        ),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"./log/{datetime.today().strftime('%Y-%m-%d-%H-%M')}.log"),
        ],
    )
    logger: Logger = logging.getLogger(__name__)
    logger.debug(f"Args: {args}")

    # endregion
    # region Select action to take

    if hasattr(args, "delete") and args.delete:
        check: str = ""
        while len(check) < 1 or (check.lower()[0] != "y" and check.lower()[0] != "n"):
            check = input(
                "Delete was selected\nBefore proceeding confirm the file path is correct:"
                + f"\n{args.file_path}\n(yes/no)\n"
            )
            if check.lower()[0] == "n":
                exit(0)

    match args.action:
        case "download":
            download(args, config)

        case "create":
            create(args, config)

        case "delete":
            raise NotImplementedError("This function has not yet been implemented")

        case "query":
            query(args, config)

        case "move":
            move(args, config)

        case _:
            logger.error("You are in uncharted territory here, beware, there be monsters")
            raise ValueError("Selected action does not exist")
    # endregion


if __name__ == "__main__":
    main()
