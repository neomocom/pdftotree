import os
from subprocess import PIPE, Popen
from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Tag
from shapely.geometry import box

import pdftotree

with open(os.path.join(os.path.dirname(__file__), "input/paleo.pdf"), "rb") as fp:
    paleo_string = fp.read()

with open(os.path.join(os.path.dirname(__file__), "input/md.pdf"), "rb") as fp:
    md_string = fp.read()

with open(os.path.join(os.path.dirname(__file__), "input/112823.pdf"), "rb") as fp:
    eleven_string = fp.read()

with open(
    os.path.join(os.path.dirname(__file__), "input/CaseStudy_ACS.pdf"), "rb"
) as fp:
    case_study_string = fp.read()

with open(
    os.path.join(
        os.path.dirname(__file__), "input/CentralSemiconductorCorp_2N4013.pdf"
    ),
    "rb",
) as fp:
    central_semi_string = fp.read()

with open(
    os.path.join(
        os.path.dirname(__file__),
        "input/UACompanionSpecificationforIEC611313Model_p41.pdf",
    ),
    "rb",
) as fp:
    ua_companion_string = fp.read()


# Adapted from https://github.com/ocropus/hocr-tools/blob/v1.3.0/hocr-check
def get_prop(node: Tag, name: str) -> Optional[str]:
    title = node.get("title")
    if not title:
        return None
    props = title.split(";")
    for prop in props:
        (key, args) = prop.split(None, 1)
        if key == name:
            return args
    return None


# Adapted from https://github.com/ocropus/hocr-tools/blob/v1.3.0/hocr-check
def get_bbox(node: Tag) -> box:
    bbox = get_prop(node, "bbox")
    if not bbox:
        return None
    return box(*[int(x) for x in bbox.split()])


def test_heuristic_completion():
    """Simply test that parse runs to completion without errors."""
    output = pdftotree.parse(paleo_string)
    assert output is not None


def test_cli_should_output_at_given_path(tmp_path):
    """Test if CLI produces an HTML at a given path."""
    html_path = os.path.join(tmp_path, "paleo.html")
    pdftotree.parse(paleo_string, html_path)
    assert os.path.isfile(html_path)


def test_output_should_conform_to_hocr(tmp_path):
    """Test if an exported file conform to hOCR."""
    html_path = os.path.join(tmp_path, "md.html")
    pdftotree.parse(md_string, html_path)
    with Popen(["hocr-check", html_path], stderr=PIPE) as proc:
        assert all([line.decode("utf-8").startswith("ok") for line in proc.stderr])

    # Check detailed things that hocr-check does not check.
    with open(html_path) as fp:
        soup = BeautifulSoup(fp, "lxml")
    capabilities = soup.find("meta", attrs={"name": "ocr-capabilities"})
    # Check the list as hocr-check only checks the existence of "ocr-capabilities".
    assert capabilities["content"].split() == [
        "ocr_page",
        "ocr_table",
        "ocrx_block",
        "ocrx_line",
        "ocrx_word",
    ]


def test_no_out_of_order(caplog):
    """Test if no out of order warning is issued."""
    pdftotree.parse(md_string, model_type="heuristics")
    assert "Out of order" not in caplog.text

    pdftotree.parse(paleo_string)
    assert "Out of order" not in caplog.text


def test_visualize_output(tmp_path):
    """Test if an output can be visualized."""
    html_path = os.path.join(tmp_path, "md.html")
    pdftotree.parse(md_string, html_path, model_type="heuristics", visualize=True)


def test_looks_scanned():
    """Test on a PDF that looks like a scanned one but not.

    CaseStudy_ACS.pdf contains a transparent image overlaying the entire page.
    This overlaying transparent image fools TreeExtractor into thinking it is scanned.
    """
    output = pdftotree.parse(case_study_string)
    soup = BeautifulSoup(output, "lxml")
    assert len(soup.find_all(class_="ocrx_word")) >= 1000
    assert len(soup.find_all("figure")) == 3

    # Check if words are extracted even though they are overlapped by a figure (#77).
    page = soup.find(class_="ocr_page")  # checking only 1st page is good enough.
    words = [get_bbox(word) for word in page.find_all(class_="ocrx_word")]
    figure = get_bbox(page.find("figure"))
    assert all([figure.contains(word) for word in words])


def test_LTChar_under_LTFigure(tmp_path):
    """Test on a PDF where LTChar(s) are children of LTFigure."""
    html_path = os.path.join(tmp_path, "paleo.html")
    pdftotree.parse(central_semi_string, html_path, model_type="heuristics")
    with open(html_path) as f:
        soup = BeautifulSoup(f, "lxml")
    line: Tag = soup.find(class_="ocrx_line")
    assert [word.text for word in line.find_all(class_="ocrx_word")] == [
        "Small",
        "Signal",
        "Transistors",
    ]

    # The table in the 1st page should contain 18 columns
    page = soup.find(class_="ocr_page")
    table = page.find(class_="ocr_table")
    assert len(table.find("tr").find_all("td")) == 18
    assert get_bbox(table) is not None

    # Find a cell containing one or more of ocrx_word and check if it has bbox
    cell = table.find(class_="ocrx_word").parent.parent
    assert get_bbox(cell) is not None

    with Popen(["hocr-check", html_path], stderr=PIPE) as proc:
        assert all([line.decode("utf-8").startswith("ok") for line in proc.stderr])


def test_overflowerror_should_not_happen():
    """Test if OverflowError does not happen (#104)."""
    output = pdftotree.parse(ua_companion_string)
    assert output is not None


def test_ml_completion():
    """Simply test that ML-based parse runs without errors."""
    output = pdftotree.parse(
        paleo_string,
        model_type="ml",
        model_path=os.path.join(os.path.dirname(__file__), "input/paleo_model.pkl"),
    )
    assert output is not None


def test_vision_completion():  # TODO
    """Simply test that vision-based parse runs without errors."""
    output = pdftotree.parse(
        paleo_string,
        model_type="vision",
        model_path=os.path.join(
            os.path.dirname(__file__), "input/paleo_visual_model.h5"
        ),
    )
    soup = BeautifulSoup(output, "lxml")
    assert len(soup.find_all("table")) == 2
