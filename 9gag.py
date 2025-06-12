#!/usr/bin/env python
# by Dominik Stanisław Suchora <suchora.dominik7@gmail.com>
# License: GNU GPLv3

import time
import random
import hashlib
import os
import sys
import re
import json

from reliq import RQ

# from curl_cffi import requests
import requests
import treerequests

reliq = RQ(cached=True)


class RequestError(Exception):
    pass


class AlreadyVisitedError(Exception):
    pass


def strtosha256(string):
    if isinstance(string, str):
        string = string.encode()

    return hashlib.sha256(string).hexdigest()


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
        if os.path.exists(self.get_post_postid(url)):
            return
        rq = self.ses.get_html(url)

        r = json.loads(
            rq.search(
                r'[0] script type="text/javascript" i@b>window. | "%i" / sed "s/[^(]*parse\(\"//; s/\");$//; s/\\\\(.)/\1/g" "E"'
            )
        )
        postid = r["data"]["post"]["id"]
        appid = r["config"]["commentOptions"]["appId"]

        r["comments"] = self.get_comment_list(postid, appid)

        with open(postid, "w") as f:
            f.write(json.dumps(r))

    def get_home_page(self, url, maxi=0):
        nexturl = url

        page = 0
        while True:
            if maxi != 0 and page >= maxi:
                break

            r = self.ses.get_json(nexturl)
            with open(str(page).zfill(4), "w") as f:
                f.write(json.dumps(r))

            data = r["data"]

            for i in data["posts"]:
                url = i["url"]
                url = re.sub(r"^http://", "https://", url)
                self.get_post(url)

            try:
                after = data["nextCursor"]
            except KeyError:
                break
            if after is None or len(after) == 0:
                break

            if page == 0:
                nexturl += "?" + after
            else:
                nexturl = re.sub(r"\?after=.*", "?", nexturl) + after
            page += 1

    def get_home(self, maxi=0):
        self.get_home_page("https://9gag.com/v1/feed-posts/type/home", maxi)


gag = Ngag(logger=treerequests.simple_logger(sys.stderr))
gag.get_home()
