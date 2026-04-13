"""
Rule loading manager with support for multiple sources and fallback mechanisms.

This module provides a unified interface for loading validation rules from
various sources (files, MCP servers) with caching and fallback support.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import RuleLoader, RuleLoadingError
from .file_loader import FileRuleLoader
from ..models import ValidationRule


logger = logging.getLogger(__name__)


class RuleLoadingManager:
    """
    Unified rule loading manager with support for multiple sources and fallback.
    
    This manager coordinates rule loading from various sources, provides caching,
    and implements fallback mechanisms for reliability.
    """
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize the rule loading manager.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._loaders: Dict[str, RuleLoader] = {}
        
        # Register default file loader
        self.register_loader('file', FileRuleLoader())
        
        logger.info("Initialized RuleLoadingManager")
    
    def register_loader(self, loader_type: str, loader: RuleLoader) -> None:
        """
        Register a rule loader for a specific type.
        
        Args:
            loader_type: Type identifier for the loader (e.g., 'file', 'mcp')
            loader: RuleLoader instance
        """
        self._loaders[loader_type] = loader
        logger.debug(f"Registered loader for type: {loader_type}")
    
    def load_rules(
        self, 
        source: str, 
        loader_type: str = 'auto',
        fallback_sources: Optional[List[Dict[str, str]]] = None,
        use_cache: bool = True
    ) -> List[ValidationRule]:
        """
        Load validation rules from the specified source with fallback support.
        
        Args:
            source: Source identifier (file path, MCP rule set ID, etc.)
            loader_type: Type of loader to use ('auto', 'file', 'mcp')
            fallback_sources: List of fallback sources with their types
            use_cache: Whether to use cached results
            
        Returns:
            List of ValidationRule objects
            
        Raises:
            RuleLoadingError: If all sources fail to load
        """
        cache_key = f"{loader_type}:{source}"
        
        # Check cache first
        if use_cache and self._is_cached(cache_key):
            logger.debug(f"Using cached rules for: {source}")
            return self._cache[cache_key]['rules']
        
        # Determine loader type if auto
        if loader_type == 'auto':
            loader_type = self._detect_loader_type(source)
        
        # Try primary source
        try:
            rules = self._load_from_source(source, loader_type)
            
            # Cache successful result
            if use_cache:
                self._cache_rules(cache_key, rules)
            
            logger.info(f"Successfully loaded {len(rules)} rules from {source}")
            return rules
            
        except RuleLoadingError as e:
            logger.warning(f"Failed to load rules from primary source {source}: {e}")
            
            # Try fallback sources
            if fallback_sources:
                for fallback in fallback_sources:
                    try:
                        fallback_source = fallback['source']
                        fallback_type = fallback.get('type', 'auto')
                        
                        if fallback_type == 'auto':
                            fallback_type = self._detect_loader_type(fallback_source)
                        
                        logger.info(f"Trying fallback source: {fallback_source}")
                        rules = self._load_from_source(fallback_source, fallback_type)
                        
                        # Cache successful fallback result
                        if use_cache:
                            self._cache_rules(cache_key, rules)
                        
                        logger.info(f"Successfully loaded {len(rules)} rules from fallback source {fallback_source}")
                        return rules
                        
                    except RuleLoadingError as fallback_error:
                        logger.warning(f"Fallback source {fallback['source']} also failed: {fallback_error}")
                        continue
            
            # All sources failed
            raise RuleLoadingError(f"Failed to load rules from all sources. Primary error: {e}")
    
    def _load_from_source(self, source: str, loader_type: str) -> List[ValidationRule]:
        """
        Load rules from a specific source using the specified loader type.
        
        Args:
            source: Source identifier
            loader_type: Type of loader to use
            
        Returns:
            List of ValidationRule objects
            
        Raises:
            RuleLoadingError: If loading fails
        """
        if loader_type not in self._loaders:
            raise RuleLoadingError(f"No loader registered for type: {loader_type}")
        
        loader = self._loaders[loader_type]
        
        # Validate source before attempting to load
        if not loader.validate_source(source):
            raise RuleLoadingError(f"Source validation failed for {source}")
        
        return loader.load_rules(source)
    
    def _detect_loader_type(self, source: str) -> str:
        """
        Automatically detect the appropriate loader type for a source.
        
        Args:
            source: Source identifier
            
        Returns:
            Detected loader type
        """
        # Check if it's a file path
        try:
            path = Path(source)
            if path.exists() or path.suffix.lower() in ['.yaml', '.yml', '.json']:
                return 'file'
        except (OSError, ValueError):
            pass
        
        # Check if it looks like an MCP rule set ID
        if ':' in source or source.startswith('mcp://'):
            return 'mcp'
        
        # Default to file loader
        return 'file'
    
    def _is_cached(self, cache_key: str) -> bool:
        """
        Check if rules are cached and still valid.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cached and valid, False otherwise
        """
        if cache_key not in self._cache:
            return False
        
        cache_entry = self._cache[cache_key]
        current_time = time.time()
        
        return (current_time - cache_entry['timestamp']) < self.cache_ttl
    
    def _cache_rules(self, cache_key: str, rules: List[ValidationRule]) -> None:
        """
        Cache validation rules with timestamp.
        
        Args:
            cache_key: Key to cache under
            rules: Rules to cache
        """
        self._cache[cache_key] = {
            'rules': rules,
            'timestamp': time.time()
        }
        logger.debug(f"Cached {len(rules)} rules under key: {cache_key}")
    
    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        Clear cached rules.
        
        Args:
            cache_key: Specific cache key to clear, or None to clear all
        """
        if cache_key:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"Cleared cache for key: {cache_key}")
        else:
            self._cache.clear()
            logger.debug("Cleared all cached rules")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current cache state.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for cache_entry in self._cache.values():
            if (current_time - cache_entry['timestamp']) < self.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_ttl': self.cache_ttl
        }
    
    def validate_source(self, source: str, loader_type: str = 'auto') -> bool:
        """
        Validate that a source is accessible using the specified loader type.
        
        Args:
            source: Source identifier to validate
            loader_type: Type of loader to use for validation
            
        Returns:
            True if source is valid and accessible, False otherwise
        """
        try:
            if loader_type == 'auto':
                loader_type = self._detect_loader_type(source)
            
            if loader_type not in self._loaders:
                return False
            
            loader = self._loaders[loader_type]
            return loader.validate_source(source)
            
        except Exception:
            return False
    
    def list_registered_loaders(self) -> List[str]:
        """
        Get a list of registered loader types.
        
        Returns:
            List of registered loader type names
        """
        return list(self._loaders.keys())


class MCPRuleLoadingManager(RuleLoadingManager):
    """
    Extended rule loading manager with MCP-specific functionality.
    
    This manager includes additional features for MCP rule loading such as
    connection pooling and advanced fallback strategies.
    """
    
    def __init__(self, cache_ttl: int = 300, mcp_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MCP rule loading manager.
        
        Args:
            cache_ttl: Cache time-to-live in seconds
            mcp_config: MCP server configuration
        """
        super().__init__(cache_ttl)
        self.mcp_config = mcp_config or {}
        
        # Register MCP loader if configuration is provided
        if mcp_config:
            self._register_mcp_loader()
    
    def _register_mcp_loader(self) -> None:
        """Register MCP loader with the provided configuration."""
        try:
            from ..mcp.rule_loader import MCPRuleLoader
            mcp_loader = MCPRuleLoader(self.mcp_config)
            self.register_loader('mcp', mcp_loader)
            logger.info("Registered MCP rule loader")
        except ImportError as e:
            logger.warning(f"Failed to register MCP loader: {e}")
    
    def load_rules_with_mcp_fallback(
        self, 
        mcp_source: str,
        file_fallback: str,
        use_cache: bool = True
    ) -> List[ValidationRule]:
        """
        Load rules from MCP with file fallback.
        
        Args:
            mcp_source: MCP rule set identifier
            file_fallback: Fallback file path
            use_cache: Whether to use cached results
            
        Returns:
            List of ValidationRule objects
        """
        fallback_sources = [{'source': file_fallback, 'type': 'file'}]
        
        return self.load_rules(
            source=mcp_source,
            loader_type='mcp',
            fallback_sources=fallback_sources,
            use_cache=use_cache
        )
    
    def update_mcp_config(self, config: Dict[str, Any]) -> None:
        """
        Update MCP configuration and re-register the loader.
        
        Args:
            config: New MCP configuration
        """
        self.mcp_config = config
        self._register_mcp_loader()
        
        # Clear MCP-related cache entries
        mcp_keys = [key for key in self._cache.keys() if key.startswith('mcp:')]
        for key in mcp_keys:
            self.clear_cache(key)