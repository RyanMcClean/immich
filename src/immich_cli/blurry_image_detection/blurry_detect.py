#!./venv/bin/python

import cv2
import rawpy
import logging
import traceback

unworkable_file_types = ["xmp", "gif", "mp4"]


def is_blurry(imagePath: str):
    """
    Detect if an image is blurry using the Laplacian variance method.

    Args:
        image (numpy.ndarray): The input image.
        threshold (float): Variance threshold below which the image is considered blurry.

    Returns:
        bool: True if the image is blurry, False otherwise.
        float: The variance of the Laplacian.
    """

    logger = logging.getLogger(__name__)
    if any(file_type in imagePath for file_type in unworkable_file_types):
        return 0

    logging.info(f"Processing {imagePath}")

    try:
        if "cr2" in imagePath.lower():
            raw = rawpy.imread(imagePath)
            rgb = raw.postprocess()
        else:
            rgb = cv2.imread(imagePath)

        # Convert the image to grayscale
        gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)

        # Cut image into four parts
        x, y = gray.shape
        half_x = int(x / 2)
        half_y = int(y / 2)

        total_variance = 0

        img_corners = [
            gray[:half_x, :half_y],
            gray[half_x:, :half_y],
            gray[:half_x, half_y:],
            gray[half_x:, half_y:],
        ]

        for corner in img_corners:
            # Compute the Laplacian of the image
            laplacian = cv2.Laplacian(corner, cv2.CV_64F)

            # Compute the variance of the Laplacian
            variance = laplacian.var()

            total_variance += variance

        # Determine if the image is blurry
        logger.info(f"{total_variance/4}")
        return int(total_variance / 4)
    except:
        logger.error(f"{traceback.format_exc()}")
        logger.error("There was an error, assuming blurry")
        return 1000
