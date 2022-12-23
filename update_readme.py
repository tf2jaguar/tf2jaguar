#!/usr/bin/python3

import asyncio
import os
import pathlib
import re

import aiohttp
import feedparser

from github_stats import Stats
from update_stats_img import generate_languages, generate_overview

root_path = pathlib.Path(__file__).parent.resolve()
readme_file = root_path / "README.md"


def replace_chunk(content, marker, chunk, inline=False):
    """
    replace chunk by marker in content
    :param content:  content
    :param marker:  marker
    :param chunk: chunk
    :param inline: inline
    :return: after replace
    """
    r = re.compile(
        r"<!-- {} starts -->.*<!-- {} ends -->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


async def update_recent_releases(s: Stats) -> None:
    sorted_releases = sorted((await s.releases), reverse=True, key=lambda r: r['release_time'])
    md = "\n".join([
        "* <a href='{release_url}' target='_blank'>{repo_name} ({repo_des}) {release_name}</a> - {release_time}".format(**release)
        for release in sorted_releases[:5]
    ])
    print('write recent_releases md:\n', md)
    rewritten = replace_chunk(readme_file.open().read(), "github_recent_releases", md)
    readme_file.open("w").write(rewritten)


def update_recent_blogs() -> None:
    entries = feedparser.parse("https://tf2jaguar.github.io/atom.xml")["entries"]
    blogs = [
        {
            "title": entry["title"],
            "url": entry["link"].split("#")[0],
            "published": entry["published"].split("T")[0],
        }
        for entry in entries
    ]
    md = "\n".join([
        "* <a href='{url}' target='_blank'>{title}</a> - {published}".format(**entry) for entry in blogs[:10]
    ])
    print('write recent_blogs md:\n', md)
    rewritten = replace_chunk(readme_file.open().read(), "recent_blogs", md)
    readme_file.open("w").write(rewritten)


async def main() -> None:
    """
    Update README.md
    """
    access_token = os.getenv("GITHUB_TOKEN")
    if not access_token:
        raise Exception("A personal access token is required to proceed!")
    user = os.getenv("GITHUB_ACTOR")
    exclude_repos = os.getenv("EXCLUDED")
    exclude_repos = ({x.strip() for x in exclude_repos.split(",")}
                     if exclude_repos else None)
    exclude_langs = os.getenv("EXCLUDED_LANGS")
    exclude_langs = ({x.strip() for x in exclude_langs.split(",")}
                     if exclude_langs else None)
    count_stats_from_forks = os.getenv("COUNT_STATS_FROM_FORKS")
    consider_forked_repos = count_stats_from_forks if count_stats_from_forks else False
    async with aiohttp.ClientSession() as session:
        s = Stats(user, access_token, session, exclude_repos=exclude_repos,
                  exclude_langs=exclude_langs,
                  consider_forked_repos=consider_forked_repos)
        await asyncio.gather(generate_languages(s), generate_overview(s))
        await update_recent_releases(s)
        update_recent_blogs()


if __name__ == "__main__":
    asyncio.run(main())
