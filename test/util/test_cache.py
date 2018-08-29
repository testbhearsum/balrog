from auslib.util.cache import MaybeCacher

def test_no_caching(mocker):
    lru = mocker.patch("auslib.util.cache.ExpiringLRUCache")
    cache = MaybeCacher()
    cache.put("cache1", "foo", "bar")
    # Nothing should be in the cache, because there _isn't_ one.
    assert cache.get("cache1", "foo") == None
    # And the underlying cache object should not have been touched.
    assert lru.put.called == False
    assert lru.get.called == False

def test_simple_cache():
    cache = MaybeCacher()
    cache.make_cache("cache1", 5, 5)
    cache.put("cache1", "foo", "bar")
    assert cache.get("cache1", "foo") == "bar"

def test_cache_expired(mocker):
    t = mocker.patch("time.time")
    cache = MaybeCacher()
    cache.make_cache("cache1", 5, 5)
    # In order to avoid tests failing due to clock skew or other
    # issues with system clocks we can mock time.time() and make sure
    # it always returns a difference large enough to force a cache expiry
    t.return_value = 100
    cache.put("cache1", "foo", "bar")
    t.return_value = 200
    assert cache.get("cache1", "foo") == None

def test_get_doesnt_copy_by_default():
    cache = MaybeCacher()
    cache.make_cache("cache1", 5, 5)
    obj = [1, 2, 3]
    # We put this into the cache manually to avoid a false pass from something .put does
    # cache entry format is (pos, value, expiration)
    cache.caches["cache1"].data["foo"] = (0, obj, 9999999999999999)
    cached_obj = cache.get("cache1", "foo")
    assert id(obj) == id(cached_obj)

def test_put_doesnt_copy_by_default():
    cache = MaybeCacher()
    cache.make_cache("cache1", 5, 5)
    obj = [1, 2, 3]
    # We put this into the cache manually to avoid a false pass from something .get does
    cache.put("cache1", "foo", obj)
    cached_obj = cache.caches["cache1"].data["foo"][1]
    assert id(obj) == id(cached_obj)

def test_copy_on_get():
    cache = MaybeCacher()
    cache.make_cache("cache1", 5, 5)
    cache.make_copies = True
    obj = [1, 2, 3]
    # We put this into the cache manually to avoid a false pass from something .put does
    cache.caches["cache1"].data["foo"] = obj
    cached_obj = cache.get("cache1", "foo")
    assert id(obj) != id(cached_obj)

def test_copy_on_put():
    cache = MaybeCacher()
    cache.make_cache("cache1", 5, 5)
    cache.make_copies = True
    obj = [1, 2, 3]
    # We put this into the cache manually to avoid a false pass from something .get does
    cache.put("cache1", "foo", obj)
    cached_obj = cache.caches["cache1"].data["foo"]
    assert id(obj) != id(cached_obj)
