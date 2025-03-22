from cijoe.core.misc import download
import logging as log
from fnmatch import fnmatch
from pathlib import Path


def main(args, cijoe, step):
    """Download diskimages"""

    pattern = step.get("with", {}).get("pattern", None)
    if pattern is None:
        log.error("missing step-argument: with.pattern")
        return 1

    log.info(f"Got pattern({pattern})")

    entry_name = "system-imaging.images"
    images = cijoe.getconf(entry_name, {})
    if not images:
        log.error(f"missing: '{entry_name}' in configuration file")
        return 1

    count = 0
    for image_name, image in cijoe.getconf("system-imaging.images", {}).items():
        if not fnmatch(image_name.lower(), pattern.lower()):
            log.info(f"image_name({image_name}); did not match pattern({pattern}")
            continue

        log.info(f"image_name({image_name}); matched pattern({pattern})")

        disk_image_url = image.get("disk", {}).get("url")
        disk_image_path = Path(image.get("disk", {}).get("path"))
        disk_image_path.parent.mkdir(parents=True, exist_ok=True)

        err, path = download(disk_image_url, disk_image_path)
        if err:
            log.error(f"download({disk_image_url}), {disk_image_path}: failed")
            return err

        count += 1

    if not count:
        log.error(f"did not build anything, count({count}); invalid with.pattern?")
        return 1

    return 0
