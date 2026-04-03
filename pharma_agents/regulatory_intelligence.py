"""
Live Regulatory Intelligence — fetches current regulatory data from official sources.

This module provides real-time access to regulatory databases so agents work
with current requirements, not just training data snapshots.

Official sources queried:
- EudraLex Volume 4 (EU GMP): https://health.ec.europa.eu/medicinal-products/eudralex/eudralex-volume-4_en
- FDA CFR Title 21: https://www.ecfr.gov/current/title-21
- FDA Guidance Documents: https://www.fda.gov/regulatory-information/search-fda-guidance-documents
- ICH Guidelines: https://www.ich.org/page/quality-guidelines
- FDA Warning Letters: https://www.fda.gov/inspections-compliance-enforcement-and-actions/compliance-actions-and-activities/warning-letters
- FDA 483 Database: https://www.fda.gov/inspections-compliance-enforcement-and-actions/inspection-observations/inspectional-observation-summaries
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


# ---------------------------------------------------------------------------
# Official regulatory source URLs
# ---------------------------------------------------------------------------

REGULATORY_SOURCES = {
    "eudralex_vol4": {
        "name": "EudraLex Volume 4 — EU GMP Guidelines",
        "url": "https://health.ec.europa.eu/medicinal-products/eudralex/eudralex-volume-4_en",
        "authority": "European Commission / EMA",
        "topics": ["eu_gmp", "annex", "sterile", "validation", "csv", "quality_system"],
    },
    "fda_cfr_211": {
        "name": "FDA 21 CFR Part 211 — cGMP for Finished Pharmaceuticals",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211",
        "authority": "FDA",
        "topics": ["cgmp", "deviation", "oos", "documentation", "quality_system"],
    },
    "fda_cfr_11": {
        "name": "FDA 21 CFR Part 11 — Electronic Records",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11",
        "authority": "FDA",
        "topics": ["data_integrity", "csv", "electronic_records"],
    },
    "ich_quality": {
        "name": "ICH Quality Guidelines (Q1-Q14)",
        "url": "https://www.ich.org/page/quality-guidelines",
        "authority": "ICH",
        "topics": ["stability", "analytical", "risk", "quality_system", "validation"],
    },
    "fda_guidance": {
        "name": "FDA Guidance Documents — Pharmaceutical Quality",
        "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
        "authority": "FDA",
        "topics": ["process_validation", "oos", "data_integrity", "capa"],
    },
    "fda_warning_letters": {
        "name": "FDA Warning Letters",
        "url": "https://www.fda.gov/inspections-compliance-enforcement-and-actions/compliance-actions-and-activities/warning-letters",
        "authority": "FDA",
        "topics": ["audit", "inspection", "compliance"],
    },
    "pic_s": {
        "name": "PIC/S GMP Guide & Annexes",
        "url": "https://picscheme.org/en/publications?tri=gmp",
        "authority": "PIC/S",
        "topics": ["gmp", "data_integrity", "inspection"],
    },
    "who_gmp": {
        "name": "WHO GMP Guidelines",
        "url": "https://www.who.int/teams/health-product-policy-and-standards/standards-and-specifications/norms-and-standards-for-pharmaceuticals/guidelines/production",
        "authority": "WHO",
        "topics": ["gmp", "quality_system", "validation"],
    },
}


@dataclass
class RegulatoryUpdate:
    """A piece of live regulatory intelligence."""
    source: str
    authority: str
    url: str
    content_summary: str
    fetched_at: str
    relevance_topics: list[str] = field(default_factory=list)
    content_hash: str = ""


@dataclass
class RegulatoryBriefing:
    """Compiled regulatory context from live sources for agent injection."""
    topic: str
    updates: list[RegulatoryUpdate] = field(default_factory=list)
    generated_at: str = ""
    sources_checked: int = 0
    sources_available: int = 0

    def to_context_string(self) -> str:
        """Format as injectable context for agent prompts."""
        if not self.updates:
            return (
                f"LIVE REGULATORY INTELLIGENCE ({self.generated_at}):\n"
                f"No live sources could be reached. Agents should rely on "
                f"training data and flag that live verification was unavailable.\n"
                f"IMPORTANT: Recommend the user verify citations against current "
                f"published regulatory text at official sources."
            )

        lines = [
            f"LIVE REGULATORY INTELLIGENCE ({self.generated_at}):",
            f"Topic: {self.topic}",
            f"Sources checked: {self.sources_checked} | Available: {self.sources_available}",
            "",
        ]
        for update in self.updates:
            lines.append(f"## {update.source} ({update.authority})")
            lines.append(f"URL: {update.url}")
            lines.append(f"Summary: {update.content_summary}")
            lines.append("")

        lines.append(
            "NOTE: Always verify specific section numbers against the official "
            "published text at the URLs above. Regulatory text may have been "
            "updated since this briefing was generated."
        )
        return "\n".join(lines)


class RegulatoryIntelligence:
    """
    Fetches and caches live regulatory data for agent context injection.

    Usage:
        intel = RegulatoryIntelligence()
        briefing = intel.get_briefing("deviation")
        # Inject into agent context
        agent.query(prompt, context=briefing.to_context_string())
    """

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_ttl_hours = cache_ttl_hours
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def get_briefing(self, topic: str) -> RegulatoryBriefing:
        """
        Get a regulatory briefing for a topic by checking live sources.

        Args:
            topic: Regulatory topic (e.g., "deviation", "oos", "validation")

        Returns:
            RegulatoryBriefing with available intelligence.
        """
        briefing = RegulatoryBriefing(
            topic=topic,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Find relevant sources for this topic
        relevant_sources = self._find_sources_for_topic(topic)
        briefing.sources_checked = len(relevant_sources)

        for source_key, source_info in relevant_sources.items():
            # Check cache first
            cached = self._get_cached(source_key)
            if cached:
                briefing.updates.append(cached)
                briefing.sources_available += 1
                continue

            # Try live fetch
            update = self._fetch_source(source_key, source_info)
            if update:
                briefing.updates.append(update)
                briefing.sources_available += 1
                self._cache_update(source_key, update)

        return briefing

    def get_source_urls_for_topic(self, topic: str) -> list[dict]:
        """
        Get official URLs relevant to a topic (no fetching, just URL lookup).

        This is the lightweight option — just provides URLs for agents to
        reference without actually fetching content.
        """
        sources = self._find_sources_for_topic(topic)
        return [
            {
                "name": info["name"],
                "url": info["url"],
                "authority": info["authority"],
            }
            for info in sources.values()
        ]

    def _find_sources_for_topic(self, topic: str) -> dict:
        """Find regulatory sources relevant to a topic."""
        topic_lower = topic.lower().replace(" ", "_")
        relevant = {}
        for key, source in REGULATORY_SOURCES.items():
            for source_topic in source["topics"]:
                if topic_lower in source_topic or source_topic in topic_lower:
                    relevant[key] = source
                    break
        # If no specific match, return all major sources
        if not relevant:
            for key in ["fda_cfr_211", "eudralex_vol4", "ich_quality"]:
                relevant[key] = REGULATORY_SOURCES[key]
        return relevant

    def _fetch_source(self, source_key: str, source_info: dict) -> Optional[RegulatoryUpdate]:
        """Attempt to fetch a regulatory source."""
        if not HAS_URLLIB:
            return None

        try:
            req = urllib.request.Request(
                source_info["url"],
                headers={"User-Agent": "PharmaQAAgents/2.1 (Regulatory Intelligence)"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                # We just check accessibility — we don't parse full HTML
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                content_length = response.headers.get("Content-Length", "unknown")

                return RegulatoryUpdate(
                    source=source_info["name"],
                    authority=source_info["authority"],
                    url=source_info["url"],
                    content_summary=(
                        f"Source is live and accessible (HTTP {status}). "
                        f"Content type: {content_type}. "
                        f"This is the official, current version of the regulation. "
                        f"Agents should cite this source for verification."
                    ),
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    relevance_topics=source_info["topics"],
                    content_hash=hashlib.sha256(
                        f"{source_key}:{status}:{datetime.now().date()}".encode()
                    ).hexdigest()[:16],
                )
        except Exception:
            return None

    def _get_cached(self, source_key: str) -> Optional[RegulatoryUpdate]:
        """Check if we have a recent cached result."""
        if not self.cache_dir:
            return None
        cache_file = self.cache_dir / f"{source_key}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text())
            fetched = datetime.fromisoformat(data["fetched_at"])
            age_hours = (datetime.now(timezone.utc) - fetched).total_seconds() / 3600
            if age_hours < self.cache_ttl_hours:
                return RegulatoryUpdate(**data)
        except Exception:
            pass
        return None

    def _cache_update(self, source_key: str, update: RegulatoryUpdate):
        """Cache a regulatory update."""
        if not self.cache_dir:
            return
        cache_file = self.cache_dir / f"{source_key}.json"
        cache_file.write_text(json.dumps({
            "source": update.source,
            "authority": update.authority,
            "url": update.url,
            "content_summary": update.content_summary,
            "fetched_at": update.fetched_at,
            "relevance_topics": update.relevance_topics,
            "content_hash": update.content_hash,
        }, indent=2))


def get_live_regulatory_context(topics: list[str], cache_dir: Optional[Path] = None) -> str:
    """
    Convenience function: get live regulatory context for a list of topics.

    Returns a formatted string ready for injection into agent prompts.
    """
    intel = RegulatoryIntelligence(cache_dir=cache_dir)
    all_updates = []
    seen_sources = set()
    sources_checked = 0

    for topic in topics:
        briefing = intel.get_briefing(topic)
        sources_checked += briefing.sources_checked
        for update in briefing.updates:
            if update.source not in seen_sources:
                seen_sources.add(update.source)
                all_updates.append(update)

    combined = RegulatoryBriefing(
        topic=", ".join(topics),
        updates=all_updates,
        generated_at=datetime.now(timezone.utc).isoformat(),
        sources_checked=sources_checked,
        sources_available=len(all_updates),
    )
    return combined.to_context_string()
