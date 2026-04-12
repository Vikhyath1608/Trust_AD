"""
FastAPI dependency injection — singletons wired once.
"""
from functools import lru_cache

from services.ad_repository import AdRepository
from services.ad_analyzer import AdAnalyzer
from services.ad_matcher import AdMatcher
from services.ad_generator import AdGeneratorService


@lru_cache()
def get_ad_repository() -> AdRepository:
    return AdRepository()


@lru_cache()
def get_ad_analyzer() -> AdAnalyzer:
    return AdAnalyzer()


@lru_cache()
def get_ad_matcher() -> AdMatcher:
    return AdMatcher()


@lru_cache()
def get_ad_generator() -> AdGeneratorService:
    return AdGeneratorService()