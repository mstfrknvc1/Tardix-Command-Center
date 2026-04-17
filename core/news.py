"""
Tardix Command Center – RSS news fetcher.

Fetches headlines from freely available, publicly indexable RSS feeds.
Only titles and links are displayed — no full article content is reproduced.

DISCLAIMER
----------
This module displays publicly available RSS feed headlines as provided by
the respective publishers.  Tardix Command Center does not host, cache, or
redistribute article content.  All content remains the property of its
original publishers.  The maintainers of this project accept no
responsibility for the accuracy, legality, or availability of third-party
content.  Refer to LEGAL_NOTICE.md for the full disclaimer.

Feed sources used:
  • Hacker News (via hnrss.org – MIT licensed open-source RSS bridge)
  • Phoronix (Linux/open-source tech news – public RSS endpoint)
  • Linux.com News (public RSS)
  • Rock Paper Shotgun (gaming news – public RSS)
  • Eurogamer (gaming news – public RSS)
"""

from __future__ import annotations

import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import QObject, QThread, Signal, Slot

# ── feed registry ─────────────────────────────────────────────────────────────

@dataclass
class FeedItem:
    title: str
    link: str
    source: str
    description: str = ""
    image_url: str = ""


# Feeds that are safe to use (public RSS, no login, no paid wall on the feed
# endpoint itself).  Only headlines + links are fetched and displayed.
FEEDS_BY_LANG: dict[str, list[tuple[str, str]]] = {
    "Türkçe": [
        ("Rock Paper Shotgun", "https://www.rockpapershotgun.com/feed"),
        ("Eurogamer",      "https://www.eurogamer.net/?format=rss"),
    ],
    "English": [
        ("Rock Paper Shotgun", "https://www.rockpapershotgun.com/feed"),
        ("Eurogamer",      "https://www.eurogamer.net/?format=rss"),
    ],
}

_ITEMS_PER_FEED = 5
_FETCH_TIMEOUT  = 8   # seconds per feed


# ── XML parsing ───────────────────────────────────────────────────────────────

def _parse_rss(xml_bytes: bytes, source: str) -> list[FeedItem]:
    items: list[FeedItem] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    # Handle both RSS 2.0 (<channel><item>) and Atom (<entry>)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # RSS 2.0
    for item in root.iter("item"):
        title_el = item.find("title")
        link_el  = item.find("link")
        image_url = ""
        description = ""
        
        # Extract description and image from description if available
        desc_el = item.find("description")
        if desc_el is not None and desc_el.text:
            desc_text = desc_el.text
            # Clean HTML tags for description
            import re
            clean_desc = re.sub(r'<[^>]+>', '', desc_text)
            description = clean_desc.strip()[:200]  # Limit to 200 chars
            
            # Extract image from description
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_text)
            if img_match:
                image_url = img_match.group(1)
        
        if title_el is not None and link_el is not None:
            title = (title_el.text or "").strip()
            link  = (link_el.text or "").strip()
            if title and link:
                items.append(FeedItem(title=title, link=link, source=source, description=description, image_url=image_url))
        if len(items) >= _ITEMS_PER_FEED:
            break

    # Atom fallback
    if not items:
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            link_el  = entry.find("atom:link", ns)
            image_url = ""
            description = ""
            
            # Extract description and image from content/summary if available
            content_el = entry.find("atom:content", ns)
            if content_el is None:
                content_el = entry.find("atom:summary", ns)
            if content_el is not None and content_el.text:
                content_text = content_el.text
                import re
                # Clean HTML tags for description
                clean_desc = re.sub(r'<[^>]+>', '', content_text)
                description = clean_desc.strip()[:200]  # Limit to 200 chars
                
                # Extract image from content
                img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_text)
                if img_match:
                    image_url = img_match.group(1)
            
            if title_el is not None and link_el is not None:
                title = (title_el.text or "").strip()
                link  = link_el.get("href", "").strip()
                if title and link:
                    items.append(FeedItem(title=title, link=link, source=source, description=description, image_url=image_url))
            if len(items) >= _ITEMS_PER_FEED:
                break

    return items[:_ITEMS_PER_FEED]


# ── fetcher ───────────────────────────────────────────────────────────────────

def fetch_news(lang: str) -> list[FeedItem]:
    """Fetch headlines for *lang* synchronously.  Called from a worker thread."""
    feeds = FEEDS_BY_LANG.get(lang, FEEDS_BY_LANG["English"])
    all_items: list[FeedItem] = []
    for source, url in feeds:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Tardix-Command-Center/0.7 RSS-reader"},
            )
            with urllib.request.urlopen(req, timeout=_FETCH_TIMEOUT) as resp:
                data = resp.read(512 * 1024)   # 512 KB cap
            all_items.extend(_parse_rss(data, source))
        except Exception:
            continue
    return all_items


# ── Qt worker ─────────────────────────────────────────────────────────────────

class NewsWorker(QObject):
    """Runs in a QThread.  Emits *news_ready* with the fetched items."""

    news_ready = Signal(list)   # list[FeedItem]
    error      = Signal(str)

    def __init__(self, lang: str, parent: QObject | None = None):
        super().__init__(parent)
        self._lang = lang

    @Slot()
    def fetch(self):
        try:
            items = fetch_news(self._lang)
            self.news_ready.emit(items)
        except Exception as exc:
            self.error.emit(str(exc))


class NewsPoller(QObject):
    """
    Periodically fetches news in a background thread.

    Usage::
        poller = NewsPoller(lang="Türkçe", interval_ms=900_000, parent=window)
        poller.news_ready.connect(my_slot)
        poller.start()
    """

    news_ready = Signal(list)   # list[FeedItem]

    def __init__(
        self,
        lang: str = "English",
        interval_ms: int = 900_000,   # 15 minutes
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._lang        = lang
        self._interval_ms = interval_ms
        self._thread: QThread | None = None
        self._worker: NewsWorker | None = None

    # public API
    def set_lang(self, lang: str) -> None:
        self._lang = lang

    def start(self) -> None:
        self._spawn_fetch()
        # periodic re-fetch via a QTimer in the main thread is fine because
        # we immediately hand work to the background thread.
        from PySide6.QtCore import QTimer  # local import avoids circular
        self._timer = QTimer(self)
        self._timer.setInterval(self._interval_ms)
        self._timer.timeout.connect(self._spawn_fetch)
        self._timer.start()

    def stop(self) -> None:
        if hasattr(self, "_timer"):
            self._timer.stop()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(3000)

    def _spawn_fetch(self) -> None:
        # Clean up previous worker/thread pair
        if self._thread is not None and self._thread.isRunning():
            return   # still busy, skip this cycle

        self._thread = QThread(self)
        self._worker = NewsWorker(lang=self._lang)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.fetch)
        self._worker.news_ready.connect(self.news_ready)
        self._worker.news_ready.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def _cleanup_thread(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
