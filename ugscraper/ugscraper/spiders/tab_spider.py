from ugscraper.ugscraper.redis.redis_helper import RedisFilterRepository
from ugscraper.ugscraper.json_logger import JsonLogFormatter
from dataclasses import dataclass
import logging, scrapy, json, random
from typing import Tuple, Set, List


@dataclass(frozen=True)
class FilterValue:
    name: str
    param_name: str
    value: str
    url_name: str


class TabsSpider(scrapy.Spider):
    name = "ugscraper"
    allowed_domains = ["ultimate-guitar.com"]
    start_urls = ["https://www.ultimate-guitar.com/explore?type[]=Chords"]

    def __init__(self, *args, **kwargs):
        super(TabsSpider, self).__init__(*args, **kwargs)
        self.logger.info("Initializing the spider.")
        self.filter_cache = RedisFilterRepository(host="redis", port=6379)

    def get_data_content(self, response):
        return json.loads(response.css(".js-store")[0].attrib["data-content"])

    def serialize_filters(self, filter_group: List[FilterValue]):
        filters = sorted({f.name: f.value for f in filter_group})
        return json.dumps(filters)

    def create_url(self, filter_group):
        applied_filters = "&".join(
            [f"{f.param_name}[]={f.url_name}" for f in filter_group]
        )
        return (
            f"https://www.ultimate-guitar.com/explore?type[]=Chords&{applied_filters}"
        )

    def open_spider(self, spider):
        print("Executed when the spider opens.")
        logging.info("Executed when the spider opens.")
        self.logger.info("Executed when the spider opens.")
        # If you prefer, you can initialize RedisHelper here instead
        # This ensures the connection is set up when the spider starts crawling
        # Additional startup actions

    def parse_results_page(self, response):
        # use the parse_tab callback to parse the tabs on the results page
        data = self.get_data_content(response)
        songs = data["store"]["page"]["data"]["data"]["tabs"]

        for song in songs:
            yield scrapy.Request(url=song["tab_url"], callback=self.parse_tab)

        pagination = data["store"]["page"]["data"]["pagination"]

        if pagination["current"] < pagination["pages"]:
            next_page = pagination["current"] + 1
            yield scrapy.Request(
                url=f"https://www.ultimate-guitar.com/explore?type[]=Chords&page={next_page}",
                callback=self.parse_results_page,
            )

    def parse_tab(self, response):
        data = self.get_data_content(response)

        fields = {
            "id",
            "song_id",
            "song_name",
            "artist_id",
            "artist_name",
            "votes",
            "rating",
            "tonality_name",
            "tab_url",
            "type",
        }
        tab_meta = data["store"]["page"]["data"]["tab"]
        song_data = {key: value for key, value in tab_meta.items() if key in fields}

        fields = {"votes", "rating", "tab_url"}
        vsns = data["store"]["page"]["data"]["tab_view"]["versions"]
        song_data["versions"] = [
            {key: value for key, value in ver.items() if key in fields} for ver in vsns
        ]
        song_data["view_meta"] = data["store"]["page"]["data"]["tab_view"]["meta"]

        song_data["content"] = data["store"]["page"]["data"]["tab_view"]["wiki_tab"][
            "content"
        ]
        return song_data

    def parse(self, response):
        data_content = self.get_data_content(response)

        filters = data_content["store"]["page"]["data"]["filters"]

        if response.meta.get("applied_filters"):
            applied_filters = response.meta["applied_filters"]
            filter_names = {f.name for f in applied_filters} | "type"

            candidate_filters = [i for i in filters if i["name"] not in filter_names]
        else:
            candidate_filters = filters
            applied_filters = []

        self.logger.info(f"Applied filters: {applied_filters}")
        self.logger.info(f"Candidate_filters filters: {candidate_filters}")

        candidate_filters = [
            FilterValue(
                name=i["name"], param_name=i["param_name"], value=None, url_name=None
            )
            for i in candidate_filters
        ]

        del filters

        def flatten_filters(filters):
            flat_filters = []
            for f in filters:
                for v in f["values"]:
                    flat_filters.append(
                        {"name": f["name"], "value": v["name"], "count": v["count"]}
                    )
            return flat_filters

        def sample_flat_filters(flat_filters):
            values = [i["count"] for i in flat_filters]
            return random.choices(flat_filters, values, k=1)[0]

        def next_filter(filter_group):
            flat_filters = flatten_filters(candidate_filters)
            chosen_filter = sample_flat_filters(flat_filters)
            filter_category = [
                i for i in candidate_filters if i["name"] == chosen_filter["name"]
            ][0]
            return filter_category

        if candidate_filters:
            filter_category = next_filter(candidate_filters)
            del candidate_filters

            for val in filter_category["values"]:
                filter_value = FilterValue(
                    name=filter_category["name"],
                    param_name=filter_category["param_name"],
                    value=val["name"],
                    url_name=val["url_name"],
                )

                filter_group = applied_filters + [filter_value]

                if self.serialize_filters(filter_group) not in self.filter_cache:
                    self.filter_cache.write_item(
                        "filterGroups", self.serialize_filters(filter_group)
                    )

                    yield scrapy.Request(
                        url=self.create_url(filter_group),
                        callback=self.parse,
                        meta={
                            "applied_filters": sorted(
                                applied_filters + [filter_category]
                            )
                        },
                    )
        else:
            yield scrapy.Request(
                url=self.create_url(filter_group), callback=self.parse_pages
            )
