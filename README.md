# 9gag-scraper

A simple scraper for [9gag](https://9gag.com).

# Output examples

Can be found in [examples](examples/).

# Usage

Download all pages in home feed to `d` directory

```shell
./9gag.py -d ./d/
```

I don't know of any way to access historic pages of 9gag, even though they are being kept alive, new comments are allowed and posts aren't deleted. Activity of posts die because of lack of any links to them for users to find. In their sitemap only other feed links are provided, they number in hundreds and traversing all of them might provide with more posts found.

There's no need to concern yourselves with anti-scraping protections, since there aren't any :D

All pages will be traversed saving json files named by their number e.g. `0000`, `0001`, `0002` etc. In consecutive calls the new pages will have the same names and will overwrite previous pages no matter if content has already changed.

At the same time, posts on the pages are scraped, all comments and replies to them are traversed. Files are named by their ids e.g. `agmErnn`, `aqyYm8p` and aren't overwritten in later calls.

All files created are in raw json format provided by 9gag, any changes are minimal and only to incorporate data retrieved in later calls so only singular files are returned.

Get specific posts

    ./9gag.py 'https://9gag.com/gag/a9yOy7j' 'https://9gag.com/gag/abAQA5L'

Get posts from specific feeds

    ./9gag.py 'https://9gag.com/interest/news' 'https://9gag.com/tag/crypto/hot'

Running with `--help` option will print available options.

    ./9gag.py --help

```
usage: 9gag.py [-h] [-d DIR] [-w TIME] [-W TIME] [-r NUM] [--retry-delay TIME]
               [--retry-all-errors] [-m TIMEOUT] [-k] [-L] [--max-redirs NUM]
               [-A UA] [-x PROXY] [-H HEADER] [-b COOKIE] [-B BROWSER]
               [URL ...]

A simple scraper for 9gag, if no url are specified downloads from home feed

positional arguments:
  URL                   urls

options:
  -h, --help            Show this help message and exit
  -d, --directory DIR   Use DIR as working directory

Request settings:
  -w, --wait TIME       Set waiting time for each request
  -W, --wait-random TIME
                        Set random waiting time for each request to be from 0
                        to TIME
  -r, --retry NUM       Set number of retries for failed request to NUM
  --retry-delay TIME    Set interval between each retry
  --retry-all-errors    Retry no matter the error
  -m, --timeout TIMEOUT
                        Set request timeout, if in TIME format it'll be set
                        for the whole request. If in TIME,TIME format first
                        TIME will specify connection timeout, the second read
                        timeout. If set to '-' timeout is disabled
  -k, --insecure        Ignore ssl errors
  -L, --location        Allow for redirections, can be dangerous if
                        credentials are passed in headers
  --max-redirs NUM      Set the maximum number of redirections to follow
  -A, --user-agent UA   Sets custom user agent
  -x, --proxy PROXY     Use the specified proxy, can be used multiple times.
                        If set to URL it'll be used for all protocols, if in
                        PROTOCOL URL format it'll be set only for given
                        protocol, if in URL URL format it'll be set only for
                        given path. If first character is '@' then headers are
                        read from file
  -H, --header HEADER   Set curl style header, can be used multiple times e.g.
                        -H 'User: Admin' -H 'Pass: 12345', if first character
                        is '@' then headers are read from file e.g. -H @file
  -b, --cookie COOKIE   Set curl style cookie, can be used multiple times e.g.
                        -b 'auth=8f82ab' -b 'PHPSESSID=qw3r8an829', without
                        '=' character argument is read as a file
  -B, --browser BROWSER
                        Get cookies from specified browser e.g. -B firefox
```

# cronjobs

Since there's no way of getting old posts, the only way to get things is to periodically scrape. The following rule will run the scraper every 8 hours

    0 */8 * * * 9gag.py -d /var/9gag
