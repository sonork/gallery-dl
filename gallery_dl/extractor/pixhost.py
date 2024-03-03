# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://pixhost.to/"""

from .common import Extractor, Message
from .. import text, exception
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class PixhostExtractor(Extractor):

    category = "pixhost"
    root = "https://pixhost.to/"
    
    def __init__(self, match):
        Extractor.__init__(self, match)
        self.path = match.group(1)
    
    def _parse_image_page(self, path):
        url = urljoin(self.root, path)
        page = self.request(url).text
        soup = BeautifulSoup(page)
        img = soup.find('img', id='image', src=True)
        url = img['src']
        filename = img['alt']

        data = {
            "url"      : url,
            "image_key": filename,
        }
        data["filename"], _, data["extension"] = filename.rpartition(".")
        return data


class PixhostGalleryExtractor(PixhostExtractor):
    """Extractor for pixhost galleries"""
    subcategory = "gallery"
    directory_fmt = ("{category}", "{title} {gallery_key}")
    filename_fmt = "{num:>03} {filename}.{extension}"
    archive_fmt = "{gallery_key}_{image_key}"

    pattern = (r"(?:https?://)?pixhost\.to"
               r"(/(?:gallery/)[a-zA-Z0-9]+)")

    def __init__(self, match):
        Extractor.__init__(self, match)
        self.path = match.group(1)

    @staticmethod
    def metadata(page):
        soup = BeautifulSoup(page)
        return {"title": soup.find('h2').text}

    def items(self):
        url = urljoin(self.root, self.path)
        page = self.request(url).text

        images = self.images(page)
        images.reverse()

        data = self.metadata(page)
        data["count"] = len(images)
        data["gallery_key"] = self.path.rpartition("/")[2]

        yield Message.Directory, data
        for data["num"], path in enumerate(images, 1):
            image = self._parse_image_page(path)
            image.update(data)
            yield Message.Url, image["url"], image

    def images(self, page):
        soup = BeautifulSoup(page)
        images = soup.find_all('a', href=re.compile('/show/'))
        return list(map(lambda x: x["href"], images))

class PixhostImageExtractor(PixhostExtractor):
    """Extractor for single pixhost images"""
    subcategory = "image"
    archive_fmt = "{image_key}"
    pattern = (r"(?:https?://)?pixhost\.to"
               r"(/(?:show(?:[0-9a-f]{2}/){3})[a-zA-Z0-9]+)")\
    
    def items(self):
        image = self._parse_image_page(self.path)
        yield Message.Directory, image
        yield Message.Url, image["url"], image
