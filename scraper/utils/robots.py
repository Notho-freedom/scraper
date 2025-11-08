"""Robots.txt handler"""

from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging


async def can_fetch(session, url: str, state, user_agent: str) -> bool:
    """Check if URL can be fetched according to robots.txt"""
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    if base not in state.robots_cache:
        rp = RobotFileParser()
        robots_url = urljoin(base, "/robots.txt")
        try:
            async with session.get(robots_url, timeout=5) as r:
                if r.status == 200:
                    content = await r.text()
                    rp.parse(content.splitlines())
                else:
                    rp.allow_all = True
        except Exception as e:
            logging.debug(f"Could not fetch robots.txt for {base}: {e}")
            rp.allow_all = True
        state.robots_cache[base] = rp
    
    return state.robots_cache[base].can_fetch(user_agent, url)
