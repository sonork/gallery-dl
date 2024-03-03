# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for piwigo sites"""

from .common import Extractor, Message, GalleryExtractor
from .. import text, exception
import re
import json
import typing
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class PiwigoMixin:
    def parse_page(self, page: str, domain: str, image_id: str) -> typing.Tuple[str, dict]:
        soup = BeautifulSoup(page, features="html.parser")
        img = soup.find("img", id="theMainImage", src=True)
        filename = img["alt"]

        # link has format: action.php?id=42&part=e&download
        dl_link = f"https://{domain}/action.php?id={image_id}&part=e&download"

        data = {
            "title": img["title"],
            "image_id": text.parse_int(image_id),
            "filename": filename,
            "domain": domain,
        }

        data["filename"], _, data["extension"] = filename.rpartition(".")
        return dl_link, data

class PiwigoImageExtractor(PiwigoMixin, Extractor):
    category = "piwigo"
    subcategory = "image"
    directory_fmt = ("{category}", "{domain}")
    filename_fmt = "{filename}-{image_id}.{extension}"
    archive_fmt = "{image_id}"

    pattern = r"(?:piwigo:(?:https?://)?)(?P<domain>[\w.-]+)/picture\?/(?P<image_id>\d+)"
    r"(?:piwigo:(?:https?://)?)(?P<domain>[\w.-]+)/picture\?/(?P<image_id>\d+)(?:/category)?(?P<category>/.*)?"
    test = (
        ("https://instantsphotos.fr/picture?/7290/category/168-blaireau_europeen"),
        ("https://instantsphotos.fr/picture?/7290"),
        ("https://instantsphotos.fr/picture?/1636/category/inde"),
    )

    def __init__(self, match):
        Extractor.__init__(self, match)
        groups = match.groupdict()
        self.domain = groups["domain"]
        self.image_id = groups["image_id"]
        self.collection_name = groups.get("category")

    def items(self):
        self.log.debug("Processing %s, %s", self.domain, self.image_id)
        url = f"https://{self.domain}/picture?/{self.image_id}"

        page = self.request(url).text
        dl_link, data = self.parse_page(page, self.domain, self.image_id)
        data["url"] = url
        data["collection_name"]= self.collection_name
        self.log.debug(str(data))

        yield Message.Directory, data
        yield Message.Url, dl_link, data
