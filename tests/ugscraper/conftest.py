import pytest

import json
from dataclasses import dataclass
from typing import List
from ugscraper.ugscraper.spiders.tab_spider import FilterValue, TabSpider
import pickle
import requests
from scrapy.http import TextResponse
from scrapy.spiders import Spider
import scrapy
import tempfile


class MockSpider(Spider):
    name = "mock_spider"
    allowed_domains = ["example.com"]
    start_urls = ["https://www.example.com"]

    def parse(self, response):
        yield {
            "title": "Example",
            "url": "https://www.example.com",
        }


@pytest.fixture
def mock_spider():
    return MockSpider()


@pytest.fixture
def tab_spider():
    return TabSpider()


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def explore_response():
    pickle_file_path = "tests/ugscraper/data/test_explore_response_20231129.pickle"
    with open(pickle_file_path, "rb") as f:
        response = pickle.load(f)

    scrapy_response = TextResponse(
        url=response.url, body=response.content, encoding="utf-8"
    )

    return scrapy_response


@pytest.fixture
def js_store_sample():
    with open("js-store-sample.json", "r") as f:
        data = json.load(f)

    return data


@pytest.fixture
def filter_group_sample(js_store_sample):

    filter_group = js_store_sample["store"]["page"]["data"]["data"]["filters"]

    return filter_group


@pytest.fixture
def filter_group_sample_flat(filter_group_sample):
    filter_group = filter_group_sample
    filter_group_flat = []
    for filter in filter_group:
        filter_group_flat += filter["values"]

    return filter_group_flat


def store_requests_response(url, pickle_file_path):
    """
    Fetches the response from a URL and pickles it to a file.

    :param url: URL to fetch.
    :param pickle_file_path: File path to store the pickled response.
    """
    r = requests.get(url)
    with open(pickle_file_path, "wb") as f:
        pickle.dump(r, f)
