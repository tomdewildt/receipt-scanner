# pylint: disable=line-too-long
from functools import reduce

import re


# ^([0-9]{1,3})             : Match digits 0-9 between 1 and 3 times
# (.*?)                     : Match any characters between 1 and unlimited times (as few as possible)
# ([0-9]{1,3}[.,;]\d{1,2})$ : Match digits 0-9 between 1 and 3 times then . or , and then digits 0-9 between 1 and 2 times
RECEIPT_REGEX = re.compile(
    r"^([0-9]{1,3})(.*?)([0-9]{1,3}[.,;]\d{1,2})$",
    flags=re.MULTILINE,
)


class ReceiptInteractions:
    def __init__(self, **repositories):
        self._image_repository = repositories["image_repository"]
        self._ocr_repository = repositories["ocr_repository"]

    def scan(self, file):
        image = self._image_repository.load(file)
        image = self._image_repository.process(image)

        data = self._ocr_repository.scan(image)

        items = []
        for qty, name, subtotal in RECEIPT_REGEX.findall(data):
            qty = int(qty.strip())
            name = name.strip()
            subtotal = float(subtotal.strip())
            price = round(subtotal / qty, 2)

            items.append(
                {
                    "name": name,
                    "qty": qty,
                    "price": price,
                    "subtotal": subtotal,
                }
            )

        return {
            "items": items,
            "total": reduce(lambda total, item: total + item["subtotal"], items, 0),
        }
