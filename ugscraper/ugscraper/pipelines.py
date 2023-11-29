# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import json
import uuid
import os


class SplitFilePipeline:
    def __init__(self, items_per_file, output_dir):
        self.items_per_file = items_per_file
        self.output_dir = output_dir
        self.current_item_count = 0
        self.current_file = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            items_per_file=crawler.settings.getint("SPLIT_ITEMS_PER_FILE"),
            output_dir=crawler.settings.get("SPLIT_OUTPUT_DIR"),
        )

    def open_spider(self, spider):
        self._open_new_file()

    def close_spider(self, spider):
        self.current_file.close()

    def process_item(self, item, spider):
        if self.current_item_count >= self.items_per_file:
            self.current_file.close()
            self.current_item_count = 0
            self._open_new_file()

        line = json.dumps(dict(item)) + "\n"
        self.current_file.write(line)
        self.current_item_count += 1
        return item

    def _open_new_file(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        file_uuid = uuid.uuid4()
        file_path = f"{self.output_dir}/output_{file_uuid}.json"
        self.current_file = open(file_path, "w")
