# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://pimpandhost.com/"""

from .common import Extractor, Message
from .. import text, exception
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class PimpAndHostExtractor(Extractor):

    category = "pimpandhost"
    root = "https://pimpandhost.com/"
    
    def __init__(self, match):
        Extractor.__init__(self, match)
        self.path = match.group(1)
    
    def _parse_image_page(self, path):
        url = urljoin(self.root, path)
        page = self.request(url).text
        soup = BeautifulSoup(page, features="html.parser")
        img = soup.find('img', id=re.compile(r"img_\d+"), src=True)
        url = urljoin(self.root, img['src'])
        filename = img['alt']

        data = {
            "url"      : url,
            "image_key": path.rpartition("/")[2],
        }
        data["filename"], _, data["extension"] = filename.rpartition(".")
        return data


class PimpAndHostGalleryExtractor(PimpAndHostExtractor):
    """Extractor for PimpAndHost galleries"""
    subcategory = "gallery"
    directory_fmt = ("{category}", "{title} {gallery_key}")
    filename_fmt = "{num:>03} {filename}.{extension}"
    archive_fmt = "{gallery_key}_{image_key}"

    pattern = (r"(?:https?://)?pimpandhost\.com"
               r"(/(?:album/)[a-zA-Z0-9]+)")

    def __init__(self, match):
        Extractor.__init__(self, match)
        self.path = match.group(1)

    @staticmethod
    def metadata(page):
        soup = BeautifulSoup(page, features="html.parser")
        return {"title": soup.find('div', {"class": "image-header"}).find('span').text}

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
        images = []
        
        while True:
            soup = BeautifulSoup(page, features="html.parser")
            image_tags = soup.find(id='album-images').find_all('a', href=re.compile('/image/'))
            
            if image_tags:
                images.extend(map(lambda x: x["href"], image_tags))
            
            next_li = soup.find('li', {"class": "next"})
            if not next_li:
                break
            
            next_ref = next_li.find('a', href=True)
            if not next_ref:
                break
            
            next_url = urljoin(self.root, next_ref['href'])
            page = self.request(next_url).content


        return images

class PimpAndHostImageExtractor(PimpAndHostExtractor):
    """Extractor for single PimpAndHost images"""
    subcategory = "image"
    archive_fmt = "{image_key}"
    pattern = (r"(?:https?://)?pimpandhost\.com"
               r"(/(?:image/)[a-zA-Z0-9]+)")
    
    def items(self):
        image = self._parse_image_page(self.path)
        yield Message.Directory, image
        yield Message.Url, image["url"], image
