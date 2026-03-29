"""
Aggregation functions for product queries.
"""
from typing import List, Dict, Optional, Any
from collections import defaultdict


class ProductAggregator:
    """Aggregate product queries into summary statistics."""
    
    @staticmethod
    def most_recent(product_queries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find most recent product search.
        
        Args:
            product_queries: List of product query dicts
        
        Returns:
            Most recent product dict or None
        """
        if not product_queries:
            return None
        
        most_recent = max(product_queries, key=lambda x: x['timestamp'])
        
        return {
            'timestamp': most_recent['timestamp'].isoformat(),
            'query': most_recent['query'],
            'category': most_recent['category'],
            'product': most_recent['product'],
            'brand': most_recent['brand'],
            'model': most_recent['model'],
            'engagement_score': most_recent['engagement_score'],
            'source': most_recent['source']
        }
    
    @staticmethod
    def most_dominant_product(
        product_queries: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find most dominant product by total engagement score.
        
        Args:
            product_queries: List of product query dicts
        
        Returns:
            Most dominant product dict or None
        """
        if not product_queries:
            return None
        
        product_engagement = defaultdict(
            lambda: {'score': 0.0, 'count': 0, 'details': {}}
        )
        
        for pq in product_queries:
            key = f"{pq['brand']}|{pq['product']}|{pq['model']}".lower()
            product_engagement[key]['score'] += pq['engagement_score']
            product_engagement[key]['count'] += 1
            
            if not product_engagement[key]['details']:
                product_engagement[key]['details'] = {
                    'category': pq['category'],
                    'product': pq['product'],
                    'brand': pq['brand'],
                    'model': pq['model']
                }
        
        dominant_product_key = max(
            product_engagement.items(),
            key=lambda x: x[1]['score']
        )
        
        return {
            'category': dominant_product_key[1]['details']['category'],
            'product': dominant_product_key[1]['details']['product'],
            'brand': dominant_product_key[1]['details']['brand'],
            'model': dominant_product_key[1]['details']['model'],
            'total_engagement_score': dominant_product_key[1]['score'],
            'search_count': dominant_product_key[1]['count']
        }
    
    @staticmethod
    def dominant_category_subcategory(
        product_queries: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find dominant category-subcategory by total engagement score.
        
        Args:
            product_queries: List of product query dicts
        
        Returns:
            Dominant category-subcategory dict or None
        """
        if not product_queries:
            return None
        
        category_product_engagement = defaultdict(
            lambda: {'score': 0.0, 'count': 0, 'details': {}}
        )
        
        for pq in product_queries:
            if pq['category'] and pq['product']:
                key = f"{pq['category']}|{pq['product']}".lower()
                category_product_engagement[key]['score'] += pq['engagement_score']
                category_product_engagement[key]['count'] += 1
                
                if not category_product_engagement[key]['details']:
                    category_product_engagement[key]['details'] = {
                        'category': pq['category'],
                        'product': pq['product']
                    }
        
        if not category_product_engagement:
            return None
        
        dominant_cat_prod_key = max(
            category_product_engagement.items(),
            key=lambda x: x[1]['score']
        )
        
        return {
            'category': dominant_cat_prod_key[1]['details']['category'],
            'subcategory': dominant_cat_prod_key[1]['details']['product'],
            'total_engagement_score': dominant_cat_prod_key[1]['score'],
            'search_count': dominant_cat_prod_key[1]['count']
        }
    
    @staticmethod
    def dominant_category(
        product_queries: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find dominant category by total engagement score.
        
        Args:
            product_queries: List of product query dicts
        
        Returns:
            Dominant category dict or None
        """
        if not product_queries:
            return None
        
        category_engagement = defaultdict(lambda: {'score': 0.0, 'count': 0})
        
        for pq in product_queries:
            if pq['category']:
                category_engagement[pq['category'].lower()]['score'] += pq['engagement_score']
                category_engagement[pq['category'].lower()]['count'] += 1
        
        if not category_engagement:
            return None
        
        dominant_category = max(
            category_engagement.items(),
            key=lambda x: x[1]['score']
        )
        
        return {
            'category': dominant_category[0],
            'total_engagement_score': dominant_category[1]['score'],
            'search_count': dominant_category[1]['count']
        }