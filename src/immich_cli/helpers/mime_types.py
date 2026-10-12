"""
File extension constants ported from the TypeScript MIME types
https://github.com/immich-app/immich/blob/main/server/src/utils/mime-types.ts
"""

# --- Image extensions (all) ---
WEB_SUPPORTED_IMAGE_EXTENSIONS: set[str] = {
    ".avif",
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}

RAW_IMAGE_EXTENSIONS: set[str] = {
    ".3fr",
    ".ari",
    ".arw",
    ".cap",
    ".cin",
    ".cr2",
    ".cr3",
    ".crw",
    ".dcr",
    ".dng",
    ".erf",
    ".fff",
    ".iiq",
    ".k25",
    ".kdc",
    ".mrw",
    ".nef",
    ".nrw",
    ".orf",
    ".ori",
    ".pef",
    ".psd",
    ".raf",
    ".raw",
    ".rw2",
    ".rwl",
    ".sr2",
    ".srf",
    ".srw",
    ".x3f",
}

OTHER_WEB_UNSUPPORTED_IMAGE_EXTENSIONS: set[str] = {
    ".heic",
    ".heif",
    ".hif",
    ".insp",
    ".jp2",
    ".jpe",
    ".jxl",
    ".mpo",
    ".svg",
    ".tif",
    ".tiff",
}

IMAGE_EXTENSIONS: set[str] = (
    WEB_SUPPORTED_IMAGE_EXTENSIONS
    | RAW_IMAGE_EXTENSIONS
    | OTHER_WEB_UNSUPPORTED_IMAGE_EXTENSIONS
)

# --- Video extensions ---
VIDEO_EXTENSIONS: set[str] = {
    ".3gp",
    ".3gpp",
    ".avi",
    ".flv",
    ".insv",
    ".m2t",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpe",
    ".mpeg",
    ".mpg",
    ".mts",
    ".mxf",
    ".ts",
    ".vob",
    ".webm",
    ".wmv",
}

# --- Audio extensions ---
AUDIO_EXTENSIONS: set[str] = {
    ".mp3",
    ".wav",
    ".aiff",
    ".aac",
    ".flac",
    ".alac",
    ".wma",
    ".ogg",
    ".opus",
    ".m4a",
    ".m4b",
    ".m4p",
    ".m4r",
    ".amr",
    ".awb",
    ".dss",
    ".gsm",
    ".vox",
    ".pcm",
    ".dsd",
    ".dsf",
    ".wv",
    ".mpc",
    ".ape",
    ".ra",
    ".ram",
    ".rm",
    ".tta",
    ".cd",
    ".cda",
    ".swa",
    ".smp",
    ".snd",
    ".sf2",
    ".sfark",
    ".nwc",
    ".mid",
    ".midi",
    ".kar",
    ".rmi",
    ".psf",
    ".ssf",
    ".spc",
    ".gym",
    ".vgm",
    ".vgz",
    ".sap",
    ".sid",
    ".mod",
    ".s3m",
    ".it",
    ".xm",
    ".mo3",
    ".mt2",
    ".ptm",
    ".stm",
    ".ult",
    ".m15",
    ".med",
    ".669",
    ".far",
    ".plj",
    ".dsm",
    ".okt",
    ".umx",
    ".amf",
    ".mtm",
    ".ahx",
}


# --- Sidecar extensions ---
SIDECAR_EXTENSIONS: set[str] = {".xmp"}

# --- All supported extensions ---
ALL_EXTENSIONS: set[str] = (
    IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | SIDECAR_EXTENSIONS | AUDIO_EXTENSIONS
)


def _get_extension(filename: str) -> str | None:
    """Return the lowercased, dot-prefixed extension of filename, or None if it has none."""
    if "." not in filename:
        return None
    return "." + filename.rsplit(".", 1)[-1].lower()


def get_asset_type(filename: str) -> str:
    """Return 'image', 'video', 'audio', or 'other' based on the file extension."""
    ext: str | None = _get_extension(filename)
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return "other"


# Note: only image/video extensions are treated as "supported" here. Audio
# files are handled separately by create_asset, which wraps them to .mp4
# first (see immich_cli.helpers.wrap_audio_file) — the wrapped file then matches
# VIDEO_EXTENSIONS. Sidecar files are likewise excluded deliberately.
def is_supported_type(filename: str) -> bool:
    """Return boolean on if file type is supported"""
    ext: str | None = _get_extension(filename)
    if ext:
        if ext in IMAGE_EXTENSIONS:
            return True
        elif ext in VIDEO_EXTENSIONS:
            return True

    return False
