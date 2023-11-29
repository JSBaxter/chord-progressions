import pytest
import json
import tempfile
import os

from ugscraper.ugscraper.pipelines import SplitFilePipeline
from ugscraper.ugscraper.spiders.tab_spider import TabsSpider

from scrapy.spiders import Spider


class MockSpider(Spider):
    name = "mock_spider"
    allowed_domains = ["example.com"]
    start_urls = ["https://www.example.com"]

    def parse(self, response):
        yield {
            "title": "Example",
            "url": "https://www.example.com",
        }


def test_split_item_pipelines(tmpdir):
    pipeline = SplitFilePipeline(5, tmpdir)
    spider = MockSpider()
    pipeline.open_spider(spider)
    items = [
        {
            "title": "Example",
            "url": "https://www.example.com",
        }
        for _ in range(10)
    ]
    for item in items:
        assert pipeline.process_item(item, spider) == item
    pipeline.close_spider(spider)
    files = os.listdir(tmpdir)
    assert len(files) == 2
    for file in files:
        with open(f"{tmpdir}/{file}", "r") as f:
            lines = f.readlines()
            assert len(lines) == 5
            for line in lines:
                item = json.loads(line)
                assert item in items
