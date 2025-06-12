#!/usr/bin/env python
# by Dominik Stanisław Suchora <suchora.dominik7@gmail.com>
# License: GNU GPLv3

import time
import random
import hashlib
import os
import sys
import re
import argparse
import json

from reliq import reliq

# from curl_cffi import requests
import requests
from urllib.parse import urljoin


class RequestError(Exception):
    pass


class AlreadyVisitedError(Exception):
    pass


def strtosha256(string):
    if isinstance(string, str):
        string = string.encode()

    return hashlib.sha256(string).hexdigest()


def int_get(obj, name):
    x = obj.get(name)
    if x is None:
        return 0
    return int(x)


def float_get(obj, name):
    x = obj.get(name)
    if x is None:
        return 0
    return float(x)


class Session(requests.Session):
    def __init__(self, **kwargs):
        # super().__init__(impersonate="firefox", timeout=30)
        super().__init__()

        t = kwargs.get("timeout")
        self.timeout = 30 if t is None else t

        t = kwargs.get("user_agent")
        self.user_agent = (
            t
            if t is not None
            else "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0"
        )

        self.headers.update(
            {"User-Agent": self.user_agent, "Referer": "https://9gag.com/"}
        )

        self.cookies.update(
            {
                "____ri": "7378",
                "____lo": "PL",
                "sign_up_referer": "",
            }
        )

        self.retries = int_get(kwargs, "retries")
        self.retry_wait = float_get(kwargs, "retry_wait")
        self.wait = float_get(kwargs, "wait")
        self.wait_random = int_get(kwargs, "wait_random")
        self.visited_c = kwargs.get("visited")
        if self.visited_c is None:
            self.visited_c = False
        self.visited = set()

        self.logger = kwargs.get("logger")

    @staticmethod
    def base(rq, url):
        ref = url
        u = rq.search(r'[0] head; [0] base href=>[1:] | "%(href)v"')
        if u != "":
            u = urljoin(url, u)
            if u != "":
                ref = u
        return ref

    def get_req_try(self, url, retry=False):
        if not retry:
            if self.wait != 0:
                time.sleep(self.wait)
            if self.wait_random != 0:
                time.sleep(random.randint(0, self.wait_random + 1) / 1000)

        if self.logger is not None:
            print(url, file=self.logger)

        return self.get(url, timeout=self.timeout)

    def get_req(self, url):
        if self.visited_c:
            if url in self.visited:
                raise AlreadyVisitedError(url)

            self.visited.add(url)

        tries = self.retries
        retry_wait = self.retry_wait

        instant_end_code = [400, 401, 402, 403, 404, 410, 412, 414, 421, 505]

        i = 0
        while True:
            try:
                resp = self.get_req_try(url, retry=(i != 0))
            except (
                requests.ConnectTimeout,
                requests.ConnectionError,
                requests.ReadTimeout,
                requests.exceptions.ChunkedEncodingError,
                RequestError,
            ):
                resp = None

            if resp is None or not (
                resp.status_code >= 200 and resp.status_code <= 299
            ):
                if resp is not None and resp.status_code in instant_end_code:
                    raise RequestError(
                        "failed completely {} {}".format(resp.status_code, url)
                    )
                if i >= tries:
                    raise RequestError(
                        "failed {} {}".format(
                            "connection" if resp is None else resp.status_code, url
                        )
                    )
                i += 1
                if retry_wait != 0:
                    time.sleep(retry_wait)
            else:
                return resp

    def get_html(self, url, return_cookies=False):
        resp = self.get_req(url)

        rq = reliq(resp.text)
        ref = self.base(rq, url)

        if return_cookies:
            return (rq, ref, resp.cookies.get_dict())
        return (rq, ref)

    def get_json(self, url):
        resp = self.get_req(url)
        return resp.json()


class Ngag:
    def __init__(self, **kwargs):
        self.ses = Session(
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
        rq, ref = self.ses.get_html(url)

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


gag = Ngag(logger=sys.stderr)
gag.get_home()
