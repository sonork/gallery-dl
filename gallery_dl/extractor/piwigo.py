# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for piwigo sites"""

from .common import Extractor, Message
from .. import text, exception
import re
from bs4 import BeautifulSoup


class PiwigoImageExtractor(Extractor):
    category = "piwigo"
    subcategory = "image"
    filename_fmt = "{filename}-{image_id}.{extension}"
    archive_fmt = "{image_id}"

    pattern = r"(?:piwigo:(?:https?://)?)([\w.-]+)/picture\?/(\d+)"
    r"(?:piwigo:(?:https?://)?)([\w.-]+)/picture\?/(\d+)(?:/category)?(/.*)?"
    test = (
        ("https://instantsphotos.fr/picture?/7290/category/168-blaireau_europeen"),
        ("https://instantsphotos.fr/picture?/7290"),
        ("https://instantsphotos.fr/picture?/1636/category/inde"),
    )
    
    def __init__(self, match):
        Extractor.__init__(self, match)
        self.domain = match.group(1)
        self.image_id = match.group(2)
        self.category = match.group(3)

    def items(self):
        self.log.debug("Processing %s, %s", self.domain, self.image_id)
        url = f"https://{self.domain}/picture?/{self.image_id}"

        page = self.request(url).text
        soup = BeautifulSoup(page, features="html.parser")
        img = soup.find('img', id='theMainImage', src=True)
        filename = img['alt']

        # link has format: action.php?id=42&part=e&download
        dl_link = f"https://{self.domain}/action.php?id={self.image_id}&part=e&download"

        data = {
            "url"      : url,
            "title": img['title'],
            "image_id": text.parse_int(self.image_id),
            "filename": filename,
        }

        data["filename"], _, data["extension"] = filename.rpartition(".")
        self.log.debug(str(data))
        
        yield Message.Directory, data
        yield Message.Url, dl_link, data
