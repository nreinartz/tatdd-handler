from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel


class QueryType(int, Enum):
    CITATION_RECOMMENDATION = 1
    TREND_ANALYSIS = 2
    COMPLETE = CITATION_RECOMMENDATION | TREND_ANALYSIS


class QueryProgress(int, Enum):
    QUEUED = 1
    DATA_RETRIEVAL = 2
    ANALYSING_TRENDS = 3
    GENERATING_DESCRIPTION = 4
    DISCOVERING_TOPICS = 5
    CITATION_RETRIEVAL = 6
    FINISHED = 7
    FAILED = 8


class QueryRequest(BaseModel):
    query_type: QueryType
    topics: list[str]
    start_year: int
    end_year: int
    distance: float = 0.11
    min_citations: int = 0


@dataclass
class SearchResults:
    raw: list[float]
    adjusted: list[float]
    pub_types: dict[str, int]


class TrendType(int, Enum):
    NONE = 0
    INCREASING = 1
    DECREASING = 2


@dataclass
class Trend:
    start: int
    end: int
    type: TrendType
    slope: float
    line: list[float]


@dataclass
class TrendResults:
    breakpoints: list[int]
    global_trend: Trend
    sub_trends: list[Trend]
    trend_description: str | None = None


@dataclass
class Publication:
    title: str
    doi: str
    authors: list[str]
    year: int
    type: str
    distance: float
    abstract: str
    citations: int


@dataclass
class DiscoveredTopic:
    name: str
    words: list[list[str]]
    frequencies: list[int]
    timestamps: list[int]


@dataclass
class TopicDiscoveryResults:
    topics: list[DiscoveredTopic]


@dataclass
class CitationRecommendationResults:
    publications: list[Publication]


@dataclass
class AnalysisResults:
    search_results: SearchResults | None = None
    trend_results: TrendResults | None = None
    topic_discovery_results: TopicDiscoveryResults | None = None
    citation_results: CitationRecommendationResults | None = None


@dataclass
class QueryEntry:
    uuid: str
    type: QueryType
    progress: QueryProgress
    topics: list[str]
    start_year: int
    end_year: int
    distance: float
    min_citations: int
    results: None | AnalysisResults | CitationRecommendationResults