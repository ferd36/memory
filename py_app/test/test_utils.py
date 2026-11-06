"""utils regressions: .env discovery, dictionary loading, headline fetches."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import utils


class TestEnvPaths(unittest.TestCase):
    def test_candidates_point_at_existing_directories(self):
        # After the move into py_app/, the paths pointed at apps/.env and
        # apps/memory/news/.env instead of src/.env and apps/news/.env.
        for env_path in utils._ENV_PATHS:
            with self.subTest(env_path=env_path):
                self.assertTrue(env_path.parent.is_dir())

    def test_first_candidate_is_the_src_directory(self):
        src_dir = utils._ENV_PATHS[0].parent
        self.assertEqual(src_dir.name, "src")
        self.assertTrue((src_dir / "apps" / "memory" / "py_app" / "utils.py").is_file())

    def test_second_candidate_is_the_news_app(self):
        news_env = utils._ENV_PATHS[1]
        self.assertEqual(news_env.parent, Path(utils.__file__).resolve().parents[2] / "news")


class TestLoadDicts(unittest.TestCase):
    def setUp(self):
        self.saved_words = list(utils.words)
        self.saved_paths = utils.dict_paths
        self.addCleanup(self._restore)

    def _restore(self):
        utils.words[:] = self.saved_words
        utils.dict_paths = self.saved_paths

    def test_a_missing_system_dictionary_does_not_stop_startup(self):
        # /usr/share/dict/words is absent on many Linux systems.
        utils.dict_paths = ["/nonexistent_dict_xyz_123"] + list(utils._APP_DICT_PATHS)
        utils.words.clear()
        utils.load_dicts()
        self.assertEqual(len(utils.words), 1 + len(utils._APP_DICT_PATHS))

    def test_a_missing_system_dictionary_keeps_the_list_indexes(self):
        # Anagram reads words[1] as English and words[2] as French.
        utils.dict_paths = ["/nonexistent_dict_xyz_123"] + list(utils._APP_DICT_PATHS)
        utils.words.clear()
        utils.load_dicts()
        self.assertEqual(utils.words[0], [])
        self.assertIn("table", utils.words[1])


class TestFetchHeadlinesCache(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.cache_file = Path(directory.name) / "data" / "headlines.json"
        patcher = patch.object(utils, "_HEADLINE_CACHE_FILE", self.cache_file)
        patcher.start()
        self.addCleanup(patcher.stop)
        saved = os.environ.get("GNEWS_KEY")
        self.addCleanup(lambda: os.environ.__setitem__("GNEWS_KEY", saved) if saved is not None
                        else os.environ.pop("GNEWS_KEY", None))
        os.environ["GNEWS_KEY"] = "cache_test_key"

    def test_repeated_calls_make_one_request(self):
        # With the key loaded, every SentenceCompletion round made a request.
        resp = MagicMock()
        resp.json.return_value = {"articles": [{"title": "One Two Three Four"}]}
        import requests
        with patch.object(requests, "get", return_value=resp) as get:
            first = utils.fetch_gnews_headlines()
            second = utils.fetch_gnews_headlines()
        self.assertEqual(get.call_count, 1)
        self.assertEqual(first, second)
        self.assertEqual(first, ["One Two Three Four"])

    def test_the_cache_expires(self):
        resp = MagicMock()
        resp.json.return_value = {"articles": [{"title": "One Two Three Four"}]}
        import requests
        with patch.object(requests, "get", return_value=resp) as get, \
                patch.object(utils.time, "time", side_effect=[0.0, utils._HEADLINE_TTL_S + 1]):
            utils.fetch_gnews_headlines()
            utils.fetch_gnews_headlines()
        self.assertEqual(get.call_count, 2)

    def _response(self):
        resp = MagicMock()
        resp.json.return_value = {"articles": [{"title": "One Two Three Four"}]}
        return resp

    def test_the_cache_is_a_file_and_does_not_contain_the_key(self):
        # A cache in memory did not help the Electron app: each round is a new process.
        import requests
        with patch.object(requests, "get", return_value=self._response()):
            utils.fetch_gnews_headlines()
        text = self.cache_file.read_text(encoding="utf-8")
        self.assertIn("One Two Three Four", text)
        self.assertNotIn("cache_test_key", text)

    def test_a_failed_request_is_cached_too(self):
        # Without this, each round of an offline game waits for a timeout.
        import requests
        with patch.object(requests, "get", side_effect=requests.ConnectionError) as get:
            self.assertEqual(utils.fetch_gnews_headlines(), [])
            self.assertEqual(utils.fetch_gnews_headlines(), [])
        self.assertEqual(get.call_count, 1)

    def test_a_request_cannot_block_the_app_for_long(self):
        import requests
        with patch.object(requests, "get", return_value=self._response()) as get:
            utils.fetch_gnews_headlines()
        self.assertLessEqual(get.call_args.kwargs["timeout"], 5)

    def test_a_damaged_cache_file_is_ignored(self):
        import requests
        self.cache_file.parent.mkdir(parents=True)
        for content in ("{oops", "[]", '{"titles": 5, "used": 5}', '{"titles": {"general|10": {"fetched_at": "x"}}}'):
            with self.subTest(content=content):
                self.cache_file.write_text(content, encoding="utf-8")
                with patch.object(requests, "get", return_value=self._response()):
                    self.assertEqual(utils.fetch_gnews_headlines(), ["One Two Three Four"])
                utils.mark_headline_used("A")
                self.assertIn("A", utils.used_headlines())

    def test_an_unexpected_response_gives_no_headlines(self):
        import requests
        resp = MagicMock()
        resp.json.return_value = ["not", "an", "object"]
        with patch.object(requests, "get", return_value=resp):
            self.assertEqual(utils.fetch_gnews_headlines(), [])

    def test_the_used_list_keeps_its_size_limit(self):
        for number in range(utils._MAX_USED_HEADLINES + 5):
            utils.mark_headline_used(str(number))
        store = json.loads(self.cache_file.read_text(encoding="utf-8"))
        self.assertEqual(len(store["used"]), utils._MAX_USED_HEADLINES)
        self.assertIn(str(utils._MAX_USED_HEADLINES + 4), utils.used_headlines())


if __name__ == "__main__":
    unittest.main()
