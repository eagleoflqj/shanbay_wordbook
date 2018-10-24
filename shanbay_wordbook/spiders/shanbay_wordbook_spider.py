import json
import math
import os

import scrapy


class shanbay_wordbook_Spider(scrapy.Spider):
    name = 'shanbay'

    def start_requests(self):
        wordbook = getattr(self, 'wordbook', None)
        if not wordbook:
            self.logger.error('no wordbook provided')
            return
        yield scrapy.Request(wordbook, callback=self.parse_wordbook)

    def parse_wordbook(self, response: scrapy.http.HtmlResponse):
        # 单词书名，作为列表目录名
        self.directory = response.xpath(
            "//div[@class='wordbook-title']/a/text()").extract_first()
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        wordlists = response.xpath(
            "//td[@class='wordbook-wordlist-name']/a")  # 列表项
        word_nums = response.xpath(
            "//td[@class='wordbook-wordlist-count']/text()").re(r'\d+')  # 单词数
        for i, wordlist in enumerate(wordlists):
            wordlist_name = wordlist.xpath('./text()').extract_first()  # 列表项名
            wordlist_link = wordlist.xpath('./@href').extract_first()  # 列表项链接
            # 根据扇贝的展示规则，每页最多20个
            yield response.follow(wordlist_link, callback=self.parse_wordlist, meta={'name': wordlist_name, 'page': 1, 'total': math.ceil(int(word_nums[i])/20)})

    def parse_wordlist(self, response: scrapy.http.HtmlResponse):
        words = response.xpath("//tbody/tr[@class='row']")  # 词条
        with open(os.path.join(self.directory, f"{response.meta['name']}-{response.meta['page']}.txt"), 'w', encoding='utf-8') as f:
            for item in words:
                word, expression = item.xpath(
                    "./td//text()").extract()  # 单词和解释
                # 存成jsonline格式
                f.write(json.dumps(
                        {'w': word.strip(), 'e': expression.strip()}, ensure_ascii=False))
                f.write('\n')
        # 模拟下一页爬取
        next_page = response.meta['page']+1
        if next_page <= response.meta['total']:
            yield response.follow(f"?page={next_page}", callback=self.parse_wordlist, meta={'name': response.meta['name'], 'page': next_page, 'total': response.meta['total']})
