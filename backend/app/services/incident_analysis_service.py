"""Deterministic incident-context analysis for KARNA."""

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class IncidentAnalysisResult:
    """Normalized context extracted from an incoming incident report."""

    symptoms: list[str]
    technologies: list[str]
    keywords: list[str]
    category: str
    summary: str


class IncidentAnalysisService:
    """Extracts consistent incident context without using an LLM."""

    _CATEGORY_TERMS: dict[str, tuple[str, ...]] = {
        "Database Issues": (
            "database",
            "connection pool",
            "sql",
            "query timeout",
            "postgres",
            "mysql",
        ),
        "Memory Leaks": (
            "memory leak",
            "out of memory",
            "oom",
            "heap",
            "memory usage",
        ),
        "CrashLoopBackOff": (
            "crashloopbackoff",
            "crash loop",
            "container restart",
            "pod restarting",
        ),
        "Config Errors": (
            "configuration",
            "config error",
            "environment variable",
            "misconfigured",
        ),
        "DNS Failures": (
            "dns",
            "hostname",
            "name resolution",
            "resolve host",
        ),
        "High Latency": (
            "latency",
            "slow response",
            "response time",
            "timeout",
        ),
    }
    _TECHNOLOGY_TERMS: tuple[str, ...] = (
        "postgres",
        "postgresql",
        "mysql",
        "redis",
        "kubernetes",
        "docker",
        "nginx",
        "fastapi",
        "python",
        "java",
        "node.js",
        "mongodb",
    )
    _SYMPTOM_TERMS: tuple[str, ...] = (
        "timeout",
        "connection refused",
        "connection pool exhausted",
        "high latency",
        "error rate",
        "out of memory",
        "crashloopbackoff",
        "restart",
        "failed",
        "unavailable",
    )
    _STOP_WORDS: frozenset[str] = frozenset(
        {
            "about",
            "after",
            "and",
            "are",
            "because",
            "from",
            "have",
            "into",
            "that",
            "the",
            "this",
            "with",
        }
    )

    def analyze(
        self,
        *,
        title: str,
        description: str,
        logs: str | None = None,
    ) -> IncidentAnalysisResult:
        """Extract deterministic normalized context from incident input.

        Args:
            title: Concise incident title.
            description: Engineer-provided incident description.
            logs: Optional relevant log excerpt.

        Returns:
            Normalized symptoms, technologies, keywords, category, and summary.

        Raises:
            ValueError: If title or description contains no meaningful text.
        """
        normalized_title = title.strip()
        normalized_description = description.strip()
        if not normalized_title or not normalized_description:
            raise ValueError("Incident title and description must not be empty.")

        source_text = " ".join(
            part for part in (normalized_title, normalized_description, logs or "") if part
        )
        normalized_text = source_text.casefold()
        symptoms = self._extract_matching_terms(normalized_text, self._SYMPTOM_TERMS)
        technologies = self._extract_matching_terms(
            normalized_text,
            self._TECHNOLOGY_TERMS,
        )
        keywords = self._extract_keywords(normalized_text)
        category = self._detect_category(normalized_text)
        summary = self._build_summary(normalized_title, category, symptoms)

        return IncidentAnalysisResult(
            symptoms=symptoms,
            technologies=technologies,
            keywords=keywords,
            category=category,
            summary=summary,
        )

    @staticmethod
    def _extract_matching_terms(text: str, terms: tuple[str, ...]) -> list[str]:
        """Return configured terms present in normalized incident text."""
        return [term for term in terms if term in text]

    def _detect_category(self, text: str) -> str:
        """Return the category with the greatest number of matching cues."""
        scored_categories = {
            category: sum(term in text for term in terms)
            for category, terms in self._CATEGORY_TERMS.items()
        }
        category, score = max(scored_categories.items(), key=lambda item: item[1])
        return category if score > 0 else "Uncategorized"

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract unique, useful lexical tokens for memory retrieval."""
        tokens = re.findall(r"[a-z][a-z0-9._-]{2,}", text)
        keywords: list[str] = []
        for token in tokens:
            if token not in self._STOP_WORDS and token not in keywords:
                keywords.append(token)
            if len(keywords) == 12:
                break
        return keywords

    @staticmethod
    def _build_summary(title: str, category: str, symptoms: list[str]) -> str:
        """Build a concise, stable summary for memory and UI display."""
        symptom_summary = ", ".join(symptoms) if symptoms else "no known symptom cues"
        return f"{title} — category: {category}; symptoms: {symptom_summary}."
