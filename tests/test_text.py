"""Test extracted text."""

import os
import re

from bs4 import BeautifulSoup

import pdftotree


def test_text_is_escaped():
    with open(os.path.join(os.path.dirname(__file__), "input/md.pdf"), "rb") as fp:
        """Test if text is properly escaped."""
        output = pdftotree.parse(fp.read())
        soup = BeautifulSoup(output, "lxml")
        words = soup.find_all(class_="ocrx_word")
        # Use str() instead of .text as the latter gives unescaped text.
        m = re.search(r">(.+?)<", str(words[66]))
        assert m[1] == "'bar';."

    with open(os.path.join(os.path.dirname(__file__), "input/112823.pdf"), "rb") as fp:
        output = pdftotree.parse(fp.read())
        soup = BeautifulSoup(output, "lxml")
        words = soup.find_all(class_="ocrx_word")
        m = re.search(r">(.+?)<", str(words[117]))
        assert m[1] == "&amp;"
