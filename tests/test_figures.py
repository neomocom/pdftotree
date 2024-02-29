"""Test figures."""

import os

from bs4 import BeautifulSoup

import pdftotree


def test_figures():
    with open(os.path.join(os.path.dirname(__file__), "input/md.pdf"), "rb") as fp:
        output = pdftotree.parse(fp.read())
        soup = BeautifulSoup(output, "lxml")
        imgs = soup.find_all("img")
        assert len(imgs) == 1

    with open(
        os.path.join(os.path.dirname(__file__), "input/CaseStudy_ACS.pdf"), "rb"
    ) as fp:
        output = pdftotree.parse(fp.read())
        soup = BeautifulSoup(output, "lxml")
        imgs = soup.find_all("img")
        # 3 jpg, 2 bmp, 5 total images
        assert len(imgs) == 5
        assert (
            len([img for img in imgs if img["src"].startswith("data:image/jpeg")]) == 3
        )
        assert (
            len([img for img in imgs if img["src"].startswith("data:image/bmp")]) == 2
        )
