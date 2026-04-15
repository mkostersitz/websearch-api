"""Policy engine for content filtering and guardrails."""

from typing import List, Optional
from loguru import logger

from src.models.database import Policy, PolicyScope
from src.models.search import SearchResult
from src.core.database import Database
from src.middleware.tracing import trace_function


class PolicyEngine:
    """Engine for evaluating and applying search policies."""
    
    @trace_function("get_applicable_policies")
    async def get_applicable_policies(
        self,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> List[Policy]:
        """
        Get all applicable policies for a user/client.
        Applies policy inheritance: global → organization → user
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            List of applicable policies sorted by priority
        """
        db = Database.get_db()
        policies = []
        
        # Get global policies
        global_policies = db.policies.find({
            "scope": PolicyScope.GLOBAL.value,
            "is_active": True
        })
        async for policy_doc in global_policies:
            policies.append(Policy(**policy_doc))
        
        # Get user-specific policies
        if user_id:
            user_policies = db.policies.find({
                "scope": PolicyScope.USER.value,
                "target_id": user_id,
                "is_active": True
            })
            async for policy_doc in user_policies:
                policies.append(Policy(**policy_doc))
        
        # Sort by priority (higher priority overrides lower)
        policies.sort(key=lambda p: (p.priority, p.created_at), reverse=True)
        
        return policies
    
    @trace_function("merge_policies")
    def merge_policies(self, policies: List[Policy]) -> Policy:
        """
        Merge multiple policies into a single effective policy.
        Higher priority policies override lower ones.
        
        Args:
            policies: List of policies to merge
            
        Returns:
            Merged policy
        """
        if not policies:
            # Return default restrictive policy
            return Policy(
                policy_id="default",
                policy_name="Default Policy",
                scope=PolicyScope.GLOBAL,
                safe_search=True,
                blocked_keywords=[],
                blocked_domains=[],
                parental_control_enabled=False,
                max_results_per_query=100
            )
        
        # Start with lowest priority policy
        merged = policies[-1].model_copy(deep=True)
        
        # Apply higher priority policies
        for policy in reversed(policies[:-1]):
            if policy.priority >= merged.priority:
                # Override settings from higher priority policy
                merged.safe_search = policy.safe_search
                merged.parental_control_enabled = policy.parental_control_enabled
                merged.min_age_rating = policy.min_age_rating
                merged.max_results_per_query = min(merged.max_results_per_query, policy.max_results_per_query)
                merged.enable_caching = policy.enable_caching
                
                # Merge lists (union for blocks, intersection for allows)
                merged.blocked_keywords = list(set(merged.blocked_keywords) | set(policy.blocked_keywords))
                merged.blocked_domains = list(set(merged.blocked_domains) | set(policy.blocked_domains))
                
                if policy.allowed_domains:
                    if merged.allowed_domains:
                        # Intersection of allowed domains
                        merged.allowed_domains = list(
                            set(merged.allowed_domains) & set(policy.allowed_domains)
                        )
                    else:
                        merged.allowed_domains = policy.allowed_domains
                
                # Preferred providers from highest priority
                if policy.preferred_providers:
                    merged.preferred_providers = policy.preferred_providers
        
        return merged
    
    @trace_function("apply_policy")
    async def apply_policy(
        self,
        results: List[SearchResult],
        policy: Policy
    ) -> tuple[List[SearchResult], int]:
        """
        Apply policy filters to search results.
        
        Args:
            results: Search results to filter
            policy: Policy to apply
            
        Returns:
            Tuple of (filtered results, number of filtered results)
        """
        filtered_results = []
        filtered_count = 0
        
        for result in results:
            if await self._should_filter_result(result, policy):
                filtered_count += 1
                logger.debug(f"Filtered result: {result.url}")
            else:
                filtered_results.append(result)
        
        # Limit to max results
        if len(filtered_results) > policy.max_results_per_query:
            filtered_results = filtered_results[:policy.max_results_per_query]
        
        logger.info(
            f"Policy applied: {len(filtered_results)}/{len(results)} results passed, "
            f"{filtered_count} filtered"
        )
        
        return filtered_results, filtered_count
    
    async def _should_filter_result(self, result: SearchResult, policy: Policy) -> bool:
        """
        Check if a result should be filtered based on policy.
        
        Args:
            result: Search result
            policy: Policy to check against
            
        Returns:
            True if result should be filtered (removed), False otherwise
        """
        # Check blocked keywords in title and snippet
        text_to_check = f"{result.title} {result.snippet}".lower()
        for keyword in policy.blocked_keywords:
            if keyword.lower() in text_to_check:
                logger.debug(f"Blocked keyword '{keyword}' found in result")
                return True
        
        # Check domain filters
        domain = self._extract_domain(result.url)
        
        # Check blocked domains
        for blocked in policy.blocked_domains:
            if self._domain_matches(domain, blocked):
                logger.debug(f"Result from blocked domain: {domain}")
                return True
        
        # Check allowed domains (if specified)
        if policy.allowed_domains:
            is_allowed = False
            for allowed in policy.allowed_domains:
                if self._domain_matches(domain, allowed):
                    is_allowed = True
                    break
            
            if not is_allowed:
                logger.debug(f"Result from non-allowed domain: {domain}")
                return True
        
        return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def _domain_matches(self, domain: str, pattern: str) -> bool:
        """
        Check if domain matches pattern (supports wildcards).
        
        Args:
            domain: Domain to check (e.g., "www.example.com")
            pattern: Pattern to match (e.g., "*.example.com" or "example.com")
            
        Returns:
            True if matches, False otherwise
        """
        pattern = pattern.lower()
        domain = domain.lower()
        
        if pattern.startswith("*."):
            # Wildcard subdomain match
            base = pattern[2:]
            return domain.endswith(base) or domain == base
        else:
            # Exact match
            return domain == pattern


# Global instance
policy_engine = PolicyEngine()
