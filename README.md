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
usage: 9gag.py [-h] [-d DIR] [-w TIME] [-W MILISECONDS] [-r NUM]
               [--retry-wait TIME] [--force-retry] [-m TIME] [-k] [-L] [-A UA]
               [-x DICT] [-H HEADER] [-b COOKIE] [-B BROWSER]
               [URL ...]

A simple scraper for 9gag, if no url are specified downloads from home feed

positional arguments:
  URL                   urls

options:
  -h, --help            Show this help message and exit
  -d, --directory DIR   Use DIR as working directory

Request settings:
  -w, --wait TIME       Sets waiting time for each request
  -W, --wait-random MILISECONDS
                        Sets random waiting time for each request to be at max
                        MILISECONDS
  -r, --retries NUM     Sets number of retries for failed request to NUM
  --retry-wait TIME     Sets interval between each retry
  --force-retry         Retry no matter the error
  -m, --timeout TIME    Sets request timeout
  -k, --insecure        Ignore ssl errors
  -L, --location        Allow for redirections, can be dangerous if
                        credentials are passed in headers
  -A, --user-agent UA   Sets custom user agent
  -x, --proxies DICT    Set requests proxies dictionary, e.g. -x
                        '{"http":"127.0.0.1:8080","ftp":"0.0.0.0"}'
  -H, --header HEADER   Set curl style header, can be used multiple times e.g.
                        -H 'User: Admin' -H 'Pass: 12345'
  -b, --cookie COOKIE   Set curl style cookie, can be used multiple times e.g.
                        -b 'auth=8f82ab' -b 'PHPSESSID=qw3r8an829'
  -B, --browser BROWSER
                        Get cookies from specified browser e.g. -B firefox
```

# cronjobs

Since there's no way of getting old posts, the only way to get things is to periodically scrape. The following rule will run the scraper every 8 hours

    0 */8 * * * 9gag.py -d /var/9gag
