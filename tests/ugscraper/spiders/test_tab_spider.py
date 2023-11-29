import pytest

from ugscraper.ugscraper.spiders.tab_spider import TabSpider


def test_get_data_content(explore_response, tab_spider):
    response = None
    data_content = tab_spider.get_data_content(explore_response)
    assert data_content is not None
    assert data_content["store"]["page"]["data"]["filters"] is not None
