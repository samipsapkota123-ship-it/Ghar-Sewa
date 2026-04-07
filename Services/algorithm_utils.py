

from __future__ import annotations

from typing import List, Sequence, TypeVar

from django.db.models import Avg, Count

from Bookings.models import ReviewRating

T = TypeVar('T')


# Data harvesting algorithm



def get_rating_summary_for_providers(provider_ids: Sequence[int]) -> dict[int, dict]:
    """
    Data harvesting : one DB query for all providers’ rating stats.
    Returns { provider_id: {'avg': float|None, 'n': int}, ... }.
    """
    if not provider_ids:
        return {}
    rows = (
        ReviewRating.objects.filter(provider_id__in=provider_ids, status=True)
        .values('provider_id')
        .annotate(avg=Avg('rating'), n=Count('id'))
    )
    return {r['provider_id']: r for r in rows}


def add_ratings_to_provider_items(items: List[dict]) -> None:
    """Data harvesting : merge harvested summaries into each provider item dict."""
    if not items:
        return
    ids = list({item['provider'].id for item in items})
    summary = get_rating_summary_for_providers(ids)
    for item in items:
        r = summary.get(item['provider'].id)
        item['rating_avg'] = float(r['avg']) if r and r['avg'] is not None else None
        item['rating_count'] = r['n'] if r else 0


def add_ratings_to_category_list(categories_list: list) -> None:
    """Data harvesting : one harvest for the whole nested category → company → provider tree."""
    pids = set()
    for cat_data in categories_list:
        for co in cat_data.get('companies', []):
            for pd in co['providers']:
                pids.add(pd['provider'].id)
    summary = get_rating_summary_for_providers(pids)
    for cat_data in categories_list:
        for co in cat_data.get('companies', []):
            for pd in co['providers']:
                r = summary.get(pd['provider'].id)
                pd['rating_avg'] = float(r['avg']) if r and r['avg'] is not None else None
                pd['rating_count'] = r['n'] if r else 0


#  Binary search algorithm

def binary_search(sorted_seq: Sequence[T], target: T) -> int:
    """Binary search : index of target in a sorted sequence, or -1 if missing."""
    lo, hi = 0, len(sorted_seq)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_seq[mid] < target:
            lo = mid + 1
        elif sorted_seq[mid] > target:
            hi = mid
        else:
            return mid
    return -1


def match_exact_username(providers: Sequence, search_lower: str) -> tuple[list, bool]:
    """
    Binary search : sort usernames, then binary_search for an exact case-insensitive match.
    If found: return ([that user], True). Else: return (full list, False) for filtering (5.4.3).
    """
    plist = list(providers)
    if not search_lower or not plist:
        return plist, False
    pairs = sorted((p.username.lower(), p) for p in plist)
    keys = [t[0] for t in pairs]
    idx = binary_search(keys, search_lower)
    if idx >= 0:
        return [pairs[idx][1]], True
    return plist, False



# Filtering algorithm (filter-based methods)



def provider_matches_search(provider, services, category: str, raw_search: str) -> bool:
    """Filtering : True if any predicate matches (profile, category label, service name)."""
    if not raw_search:
        return True
    q = raw_search.strip().lower()
    raw = raw_search.strip()
    return (
        q in provider.username.lower()
        or q in (provider.first_name or '').lower()
        or q in (provider.last_name or '').lower()
        or q in (provider.company_name or '').lower()
        or q in category.lower()
        or services.filter(name__icontains=raw).exists()
    )


def filter_providers_by_search(items: List[dict], search_query: str) -> List[dict]:
    """Filtering : keep only items whose provider fields contain the search text."""
    if not search_query:
        return items
    q = search_query.lower()
    return [
        item
        for item in items
        if q in item['provider'].username.lower()
        or q in (item['provider'].first_name or '').lower()
        or q in (item['provider'].last_name or '').lower()
        or q in (item['provider'].company_name or '').lower()
    ]
