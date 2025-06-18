#!/usr/bin/env python

import os
import sys
import tempfile
import json
from pathlib import Path

_9gag = __import__("9gag")

ngag = _9gag.Ngag()


def intemp(func):
    prev = os.getcwd()

    with tempfile.TemporaryDirectory() as dir:
        os.chdir(dir)

        func()

    os.chdir(prev)


def post_test(url, p_id, size=250000):
    def t():
        ngag.guess(url)
        path = Path(p_id)
        data = path.read_text()
        assert len(data) > size

        js = json.loads(data)

    intemp(t)


def test_posts_1():
    post_test("https://9gag.com/gag/aAyOG9p", "aAyOG9p")


def test_posts_2():
    post_test("https://9gag.com/gag/axyYMY1", "axyYMY1")


def test_posts_3():
    post_test("https://9gag.com/gag/azxY29m", "azxY29m")


def pages_test(url, size=1200000, count=18):
    def t():
        ngag.guess(url, maxi=2)
        assert os.path.exists("0000")
        assert os.path.getsize("0000") > 10000

        sizes = [i.stat().st_size for i in os.scandir(".")]
        assert len(sizes) >= count
        assert sum(sizes) > size

    intemp(t)


def test_pages_1():
    pages_test("https://9gag.com/", size=5000000)


def test_pages_2():
    pages_test("https://9gag.com/interest/movies")


def test_pages_3():
    pages_test("https://9gag.com/interest/news/hot")


def test_pages_4():
    pages_test("https://9gag.com/interest/anime/forum")


def test_pages_5():
    pages_test("https://9gag.com/tag/bitcoin/hot")


def test_pages_6():
    pages_test("https://9gag.com/tag/cute")
