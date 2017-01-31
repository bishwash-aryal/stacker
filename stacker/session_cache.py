import json
import os
import botocore
import boto3


def get_session(region):
    """Creates a boto3 session with a cache

    Args:
        region (str): The region for the session

    Returns:
        Object: A  boto3 session with credential
                caching
    """
    session = botocore.session.get_session()
    session.set_config_variable('region',  region)
    c = session.get_component('credential_provider')
    provider = c.get_provider('assume-role')
    provider.cache = CredentialCache()
    return boto3.session.Session(botocore_session=session)


class CredentialCache(object):

    """JSON file cache.
    This provides a dict like interface that stores JSON serializable
    objects.
    The objects are serialized to JSON and stored in a file.  These
    values can be retrieved at a later time.
    """

    CACHE_DIR = os.path.expanduser(
        os.path.join('~', '.aws', 'cli', 'cache'))

    def __init__(self, working_dir=CACHE_DIR):
        self._working_dir = working_dir

    def __contains__(self, cache_key):
        actual_key = self._convert_cache_key(cache_key)
        return os.path.isfile(actual_key)

    def __getitem__(self, cache_key):
        """Retrieve value from a cache key."""
        actual_key = self._convert_cache_key(cache_key)
        try:
            with open(actual_key) as f:
                return json.load(f)
        except (OSError, ValueError, IOError):
            raise KeyError(cache_key)

    def __setitem__(self, cache_key, value):
        full_key = self._convert_cache_key(cache_key)
        try:
            file_content = json.dumps(value, default=str)
        except (TypeError, ValueError):
            raise ValueError("Value cannot be cached, must be "
                             "JSON serializable: %s" % value)
        if not os.path.isdir(self._working_dir):
            os.makedirs(self._working_dir)
        with os.fdopen(os.open(full_key,
                               os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
            f.truncate()
            f.write(file_content)

    def _convert_cache_key(self, cache_key):
        full_path = os.path.join(self._working_dir, cache_key + '.json')
        return full_path
