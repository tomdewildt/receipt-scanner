from skimage.filters import threshold_local

import pytesseract
import numpy as np
import cv2


class InvalidContoursError(Exception):
    pass


class OpenCVRepository:
    def __init__(
        self,
        scale_factor=500,
        gaussian_kernel=(5, 5),
        rectangle_kernel=(9, 9),
        edges_threshold1=100,
        edges_threshold2=200,
        threshold_enabled=False,
        threshold_block_size=21,
        threshold_offset=5,
    ):
        self._scale_factor = scale_factor
        self._gaussian_kernel = gaussian_kernel
        self._rectangle_kernel = rectangle_kernel
        self._edges_threshold1 = edges_threshold1
        self._edges_threshold2 = edges_threshold2
        self._threshold_enabled = threshold_enabled
        self._threshold_block_size = threshold_block_size
        self._threshold_offset = threshold_offset

    def load(self, file):
        return cv2.imdecode(np.fromstring(file.getvalue(), np.uint8), cv2.IMREAD_COLOR)

    def process(self, image):
        # Downscale image
        ratio = self._scale_factor / image.shape[0]
        processed = self._resize(image, ratio)

        # Grayscale image
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # Remove noise
        blurred = cv2.GaussianBlur(gray, self._gaussian_kernel, 0)

        # Detect white regions
        rectangle_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            self._rectangle_kernel,
        )
        dilated = cv2.dilate(blurred, rectangle_kernel)

        # Detect edges
        edges = cv2.Canny(
            dilated,
            self._edges_threshold1,
            self._edges_threshold2,
            apertureSize=3,
        )

        # Detect contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        # Detect receipt contour
        receipt_contour = self._get_receipt_contour(contours)

        # Warp perspective
        warped = self._warp_perspective(
            image.copy(),
            self._get_receipt_rectangle(receipt_contour, ratio),
        )

        # Greyscale image
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

        # Threshold image
        if self._threshold_enabled:
            threshold = threshold_local(
                gray,
                self._threshold_block_size,
                offset=self._threshold_offset,
                method="gaussian",
            )

            return (gray > threshold).astype("uint8") * 255

        return gray

    def _resize(self, image, ratio):
        width = int(image.shape[1] * ratio)
        height = int(image.shape[0] * ratio)

        return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

    def _warp_perspective(self, image, rectangle):
        (tl, tr, br, bl) = rectangle

        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))

        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))

        max_width = max(int(width_a), int(width_b))
        max_height = max(int(height_a), int(height_b))

        destination = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1],
            ],
            dtype="float32",
        )

        transformation = cv2.getPerspectiveTransform(rectangle, destination)

        return cv2.warpPerspective(image, transformation, (max_width, max_height))

    def _approximate_contour(self, contour):
        perimeter = cv2.arcLength(contour, True)

        return cv2.approxPolyDP(contour, 0.032 * perimeter, True)

    def _get_receipt_contour(self, contours):
        for contour in contours:
            approximation = self._approximate_contour(contour)

            if len(approximation) == 4:
                return approximation

        raise InvalidContoursError("no contours of length 4 found in image")

    def _get_receipt_rectangle(self, contour, ratio):
        points = contour.reshape(4, 2)
        rectangle = np.zeros((4, 2), dtype="float32")

        points_sum = points.sum(axis=1)
        rectangle[0] = points[np.argmin(points_sum)]
        rectangle[2] = points[np.argmax(points_sum)]

        difference = np.diff(points, axis=1)
        rectangle[1] = points[np.argmin(difference)]
        rectangle[3] = points[np.argmax(difference)]

        return rectangle / ratio


class TesseractRepository:
    def __init__(self, lang_default="eng+nld"):
        self._lang_default = lang_default

    def scan(self, image, lang=None):
        return pytesseract.image_to_string(image, lang=lang or self._lang_default)
