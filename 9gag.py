#!/usr/bin/env python
# by Dominik Stanisław Suchora <hexderm@gmail.com>
# License: GNU GPLv3

import hashlib
import os
import sys
import re
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse
from functools import partial

from reliq import RQ

# from curl_cffi import requests
import requests
import treerequests

reliq = RQ(cached=True)


def jsondump(data, file):
    json.dump(data, file, separators=(",", ":"))


def strtosha256(string):
    if isinstance(string, str):
        string = string.encode()

    return hashlib.sha256(string).hexdigest()


def valid_directory(directory: str):
    if os.path.isdir(directory):
        return directory
    else:
        raise argparse.ArgumentTypeError('"{}" is not a directory'.format(directory))


class Ngag:
    def __init__(self, **kwargs):
        self.ses = treerequests.Session(
            requests,
            requests.Session,
            lambda x, y: treerequests.reliq(x, y, obj=reliq),
            **kwargs,
        )

    def get_comment(self, baseurl, appid, c):
        if c["childrenTotal"] == 0:
            return []

        return self.get_comment_list(0, appid, nexturl=c["childrenUrl"])

    def get_comment_list(self, postid, appid, nexturl=""):
        if len(nexturl) == 0:
            baseurl = "https://comment-cdn.9gag.com/v2/cacheable/comment-list.json?viewMode=list&postKey={}&origin=https%3A%2F%2F9gag.com".format(
                postid
            )
            nexturl = (
                baseurl
                + "&appId={}&count=10&type=hot&url=http%3A%2F%2F9gag.com%2Fgag%2F{}".format(
                    appid, postid
                )
            )
        else:
            baseurl = "https://comment-cdn.9gag.com/v2/cacheable/comment-list.json?appId={}&type=old&origin=https%3A%2F%2F9gag.com".format(
                appid
            )
            nexturl = baseurl + "&" + nexturl

        comments = []

        while True:
            r = self.ses.get_json(nexturl)

            payload = r["payload"]
            for i in payload["comments"]:
                i["comments"] = self.get_comment(baseurl, appid, i)
                comments.append(i)

            after = payload["next"]
            if after is None or len(after) == 0:
                break
            nexturl = baseurl + "&" + after

        return comments

    @staticmethod
    def get_post_postid(url):
        url = re.sub(r".*/gag/", "", url)
        url = re.sub(r"#.*/", "", url)
        return url

    def get_post(self, url):
        rq = self.ses.get_html(url)

        r = json.loads(
            rq.search(
                r'[0] script type="text/javascript" i@b>window. | "%i" / sed "s/[^(]*parse\(\"//; s/\");$//; s/\\\\(.)/\1/g" "E"'
            )
        )
        postid = r["data"]["post"]["id"]
        appid = r["config"]["commentOptions"]["appId"]

        r["comments"] = self.get_comment_list(postid, appid)

        return r

    def save_post(self, url, path=""):
        postid = self.get_post_postid(url)
        path = Path(path) / postid

        if os.path.exists(path):
            return

        post = self.get_post(url)

        with open(path, "w") as f:
            jsondump(post, f)

    def go_though_pages(self, func, url, maxi=0):
        nexturl = url

        page = 0
        while True:
            if maxi != 0 and page >= maxi:
                break

            results, nexturl = func(nexturl)
            yield results

            if nexturl is None or len(nexturl) == 0:
                break

            page += 1

    def get_page(self, url, post=False):
        if post:
            r = self.ses.post_json(url)
        else:
            r = self.ses.get_json(url)

        data = r["data"]

        try:
            after = data["nextCursor"]
        except KeyError:
            return r, None
        if after is None or len(after) == 0:
            return r, None

        nexturl = re.sub(r"\?.*", "", url) + "?" + after

        return r, nexturl

    def get_pages(self, url, maxi=0, post=False):
        return self.go_though_pages(partial(self.get_page, post=post), url, maxi=maxi)

    def get_post_urls(self, page):
        ret = []
        for i in page["data"]["posts"]:
            url = i["url"]
            url = re.sub(r"^http://", "https://", url)
            ret.append(url)
        return ret

    def save_pages(self, url, maxi=0, path="", prefix="", post=False):
        page = 0
        prefix = str(Path(path) / prefix) if len(path) > 0 else prefix
        for i in self.get_pages(url, maxi=maxi, post=post):
            with open(prefix + str(page).zfill(4), "w") as f:
                jsondump(i, f)

            yield i
            page += 1

    def save_pages_posts(self, url, maxi=0, path="", prefix="", post=False):
        for i in self.save_pages(url, maxi=maxi, path=path, prefix=prefix, post=post):
            for j in self.get_post_urls(i):
                self.save_post(j, path=path)

    def get_home(self, maxi=0):
        self.save_pages_posts("https://9gag.com/v1/feed-posts/type/home", maxi)
        # https://9gag.com/v1/interest-posts/interest/oldmeme/type/hot?after=aW4Dgpx%2Ca0eMZnL%2CazxYe4b&c=10
        # https://9gag.com/v1/interest-posts/interest/oldmeme/type/hot?after=aW4Dgpx%2Ca0eMZnL%2CaXPKr7b&c=10

        # https://9gag.com/v1/tag-posts/tag/old-meme/type/hot?c=20
        # https://9gag.com/tag/old-meme?ref=post-tag

    def guess(self, url: str, *args, **kwargs):
        r = urlparse(url)

        def err():
            raise Exception("unknown url - " + url)

        if (
            len(r.scheme) == 0
            or r.scheme not in ("https", "http")
            or r.netloc != "9gag.com"
        ):
            err()

        path = r.path

        if len(path) == 0 or path == "/":
            return self.save_pages_posts(
                "https://9gag.com/v1/feed-posts/type/home", *args, **kwargs
            )
        elif re.fullmatch(r"/gag/[0-9A-Za-z]+", path):
            return self.save_post(url, *args, **kwargs)
        elif arg := re.fullmatch(r"/u/([^/]+)(/(likes|posts|comments))?", path):
            user = arg[1]
            path = arg[2] if arg[2] is not None else "/likes"
            return self.save_pages_posts(
                "https://9gag.com/v1/user-posts/username/" + user + "/type" + path,
                post=True,
                *args,
                **kwargs,
            )
        elif re.fullmatch(r"/search", path) and re.search("^query=[^&]+", r.query):
            return self.save_pages_posts(
                "https://9gag.com/v1/search-posts?" + r.query.split("&")[0],
                *args,
                **kwargs,
            )
        elif re.fullmatch(r"/(forum|fresh|hot|home)", path):
            return self.save_pages_posts(
                "https://9gag.com/v1/feed-posts/type" + path, *args, **kwargs
            )
        elif arg := re.fullmatch(r"/interest/[^/]+(/(fresh|hot|forum))?", path):
            path = re.sub(r"/(fresh|hot|forum)$", "", path)
            sort = arg[1] if arg[1] is not None else "/fresh"

            return self.save_pages_posts(
                "https://9gag.com/v1/interest-posts" + path + "/type" + sort,
                *args,
                **kwargs,
            )
        elif arg := re.fullmatch(r"/tag/[^/]+(/(fresh|hot))?", path):
            path = re.sub(r"/(fresh|hot)$", "", path)
            sort = arg[1] if arg[1] is not None else "/fresh"

            return self.save_pages_posts(
                "https://9gag.com/v1/tag-posts" + path + "/type" + sort,
                *args,
                **kwargs,
            )
        else:
            err()


def argparser():
    parser = argparse.ArgumentParser(
        description="A simple scraper for 9gag, if no url are specified downloads from home feed",
        add_help=False,
    )

    parser.add_argument(
        "urls",
        metavar="URL",
        type=str,
        nargs="*",
        help="urls",
    )

    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit",
    )
    parser.add_argument(
        "-d",
        "--directory",
        metavar="DIR",
        type=valid_directory,
        help="Use DIR as working directory",
        default=".",
    )

    treerequests.args_section(parser)

    return parser


def cli(argv: list[str]):
    args = argparser().parse_args(argv)

    os.chdir(args.directory)

    gag = Ngag(logger=treerequests.simple_logger(sys.stdout))
    treerequests.args_session(gag.ses, args)

    for i in args.urls:
        gag.guess(i)

    if len(args.urls) == 0:
        gag.get_home()


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
