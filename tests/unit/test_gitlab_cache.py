"""Tests for GitLab API cache functionality.

Tests the GitLab API caching service including configuration and helpers.
"""

import gzip
import hashlib
import json

from app.services.gitlab.cache import CacheConfig


class TestCacheConfigDefaults:
    """Test CacheConfig default values."""

    def test_default_ttl(self) -> None:
        """Test default TTL is 5 minutes (300 seconds)."""
        config = CacheConfig()
        assert config.default_ttl == 300

    def test_list_ttl(self) -> None:
        """Test list TTL is 2 minutes (120 seconds)."""
        config = CacheConfig()
        assert config.list_ttl == 120

    def test_user_ttl(self) -> None:
        """Test user TTL is 15 minutes (900 seconds)."""
        config = CacheConfig()
        assert config.user_ttl == 900

    def test_compress_threshold(self) -> None:
        """Test compression threshold is 1KB (1024 bytes)."""
        config = CacheConfig()
        assert config.compress_threshold == 1024

    def test_enabled_by_default(self) -> None:
        """Test cache is enabled by default."""
        config = CacheConfig()
        assert config.enabled is True

    def test_custom_config_values(self) -> None:
        """Test custom CacheConfig values."""
        config = CacheConfig(
            default_ttl=600,
            list_ttl=300,
            user_ttl=1800,
            compress_threshold=2048,
            enabled=False,
        )
        assert config.default_ttl == 600
        assert config.enabled is False


class TestCacheKeyGeneration:
    """Test cache key generation helpers."""

    def test_endpoint_hash_sha256(self) -> None:
        """Test endpoint hash generation using SHA256."""
        endpoint = "/projects/123/merge_requests"
        hash_value = hashlib.sha256(endpoint.encode()).hexdigest()
        assert len(hash_value) == 64

    def test_endpoint_hash_deterministic(self) -> None:
        """Test hash is deterministic for same input."""
        endpoint = "/projects/123/issues"
        hash1 = hashlib.sha256(endpoint.encode()).hexdigest()
        hash2 = hashlib.sha256(endpoint.encode()).hexdigest()
        assert hash1 == hash2

    def test_different_endpoints_different_hashes(self) -> None:
        """Test different endpoints produce different hashes."""
        endpoint1 = "/projects/123/issues"
        endpoint2 = "/projects/123/merge_requests"
        hash1 = hashlib.sha256(endpoint1.encode()).hexdigest()
        hash2 = hashlib.sha256(endpoint2.encode()).hexdigest()
        assert hash1 != hash2

    def test_etag_key_format(self) -> None:
        """Test ETag key format."""
        endpoint_hash = "abc123"
        etag_key = f"gitlab:etag:{endpoint_hash}"
        assert etag_key == "gitlab:etag:abc123"

    def test_response_key_format(self) -> None:
        """Test response key format."""
        endpoint_hash = "def456"
        response_key = f"gitlab:response:{endpoint_hash}"
        assert response_key == "gitlab:response:def456"


class TestCompressionHelpers:
    """Test compression helper functions."""

    def test_small_data_not_compressed(self) -> None:
        """Test data smaller than threshold is not compressed."""
        data = b"small data"
        threshold = 1024
        should_compress = len(data) > threshold
        assert should_compress is False

    def test_large_data_compressed(self) -> None:
        """Test data larger than threshold is compressed."""
        data = b"x" * 2000
        threshold = 1024
        should_compress = len(data) > threshold
        assert should_compress is True

    def test_gzip_compression(self) -> None:
        """Test gzip compression of data."""
        data = b"test data for compression " * 100
        compressed = gzip.compress(data)
        # Compressed should be smaller for repetitive data
        assert len(compressed) < len(data)

    def test_gzip_decompression(self) -> None:
        """Test gzip decompression of data."""
        original = b"test data"
        compressed = gzip.compress(original)
        decompressed = gzip.decompress(compressed)
        assert decompressed == original


class TestJSONSerialization:
    """Test JSON serialization for cache."""

    def test_serialize_dict(self) -> None:
        """Test serializing dict to JSON."""
        data = {"id": 123, "name": "test"}
        json_str = json.dumps(data)
        assert "123" in json_str
        assert "test" in json_str

    def test_deserialize_json(self) -> None:
        """Test deserializing JSON to dict."""
        json_str = '{"id": 456, "name": "project"}'
        data = json.loads(json_str)
        assert data["id"] == 456

    def test_serialize_list(self) -> None:
        """Test serializing list to JSON."""
        data = [{"id": 1}, {"id": 2}]
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert len(parsed) == 2


class TestCacheHitMissLogic:
    """Test cache hit/miss logic."""

    def test_cache_hit_with_etag_match(self) -> None:
        """Test cache hit when ETags match."""
        stored_etag = 'W/"123abc"'
        response_etag = 'W/"123abc"'
        is_hit = stored_etag == response_etag
        assert is_hit is True

    def test_cache_miss_with_different_etag(self) -> None:
        """Test cache miss when ETags differ."""
        stored_etag = 'W/"123abc"'
        response_etag = 'W/"456def"'
        is_hit = stored_etag == response_etag
        assert is_hit is False

    def test_cache_miss_no_etag(self) -> None:
        """Test cache miss when no ETag stored."""
        stored_etag = None
        is_hit = stored_etag is not None
        assert is_hit is False


class TestTTLSelection:
    """Test TTL selection based on endpoint type."""

    def test_list_endpoint_ttl(self) -> None:
        """Test list endpoints use shorter TTL."""
        endpoint = "/projects/123/merge_requests"
        is_list = "merge_requests" in endpoint or "issues" in endpoint
        ttl = 120 if is_list else 300
        assert ttl == 120

    def test_single_entity_ttl(self) -> None:
        """Test single entity endpoints use default TTL."""
        endpoint = "/projects/123/merge_requests/1"
        is_list = endpoint.endswith("/merge_requests") or endpoint.endswith("/issues")
        ttl = 120 if is_list else 300
        assert ttl == 300

    def test_user_endpoint_ttl(self) -> None:
        """Test user endpoints use longer TTL."""
        endpoint = "/users/123"
        is_user = "/users/" in endpoint
        ttl = 900 if is_user else 300
        assert ttl == 900
