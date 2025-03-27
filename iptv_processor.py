#!/usr/bin/env python3
import re
import requests
from urllib.parse import urlparse
from pathlib import Path
from collections import defaultdict

class M3UProcessor:
    def __init__(self):
        self.channels = defaultdict(list)
        self.unique_urls = set()

    def parse_file(self, content, base_url=None):
        entries = []
        extinf_pattern = re.compile(
            r'#EXTINF:-1\s+(.*?),\s*(.*)',
            re.DOTALL
        )
        current = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#EXTINF'):
                match = extinf_pattern.search(line)
                if match:
                    attrs = self.parse_attributes(match.group(1))
                    current = {
                        'tvg_name': attrs.get('tvg-name', ''),
                        'tvg_logo': attrs.get('tvg-logo', ''),
                        'group': attrs.get('group-title', '未分类'),
                        'name': match.group(2).strip(),
                    }
            elif line and not line.startswith('#'):
                if current and line:
                    current['url'] = self.resolve_url(line, base_url)
                    if current['url'] not in self.unique_urls:
                        entries.append(current)
                        self.unique_urls.add(current['url'])
                    current = {}
        return entries

    @staticmethod
    def parse_attributes(attr_str):
        attrs = {}
        matches = re.finditer(r'(\S+?)="(.*?)"', attr_str)
        for match in matches:
            attrs[match.group(1)] = match.group(2)
        return attrs

    def resolve_url(self, url, base_url):
        if urlparse(url).scheme in ('http', 'https', 'rtmp'):
            return url
        if base_url:
            return requests.compat.urljoin(base_url, url)
        return url

    def process_sources(self, urls):
        all_entries = []
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                content_type = response.headers.get('Content-Type', '')
                content = response.text
                
                if url.endswith(('.m3u', '.m3u8')):
                    entries = self.parse_file(content, url)
                elif url.endswith('.txt'):
                    entries = self.parse_txt(content)
                else:
                    entries = []
                
                all_entries.extend(entries)
                print(f"Processed {url} ({len(entries)} channels)")
                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
        
        return all_entries

    def parse_txt(self, content):
        entries = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(',')
                if len(parts) >= 2:
                    entries.append({
                        'name': parts.strip(),
                        'url': parts[-1].strip(),
                        'group': '未分类',
                        'tvg_name': parts.strip(),
                        'tvg_logo': ''
                    })
        return entries

    def generate_m3u(self, entries):
        m3u_content = ["#EXTM3U"]
        for entry in entries:
            m3u_content.append(
                f'#EXTINF:-1 tvg-name="{entry["tvg_name"]}" '
                f'tvg-logo="{entry["tvg_logo"]}" '
                f'group-title="{entry["group"]}",{entry["name"]}\n'
                f'{entry["url"]}'
            )
        return '\n'.join(m3u_content)

    def generate_txt(self, entries):
        txt_content = []
        for entry in entries:
            txt_content.append(f'{entry["name"]}, {entry["url"]}')
        return '\n'.join(txt_content)

if __name__ == "__main__":
    # 配置源列表（支持多个源）
    SOURCE_URLS = [
        "https://gh.tryxd.cn/https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u",
        "https://gh.tryxd.cn/https://raw.githubusercontent.com/alantang1977/auto-iptv/main/live_ipv4.txt",
        "https://live.kilvn.com/iptv.m3u",
        "https://codeberg.org/sy147258/iptv/raw/branch/main/电视",
        "https://gh.tryxd.cn/https://raw.githubusercontent.com/hjdhnx/hipy-sniffer/refs/heads/main/static/lives/lives.txt",
        "https://gh.tryxd.cn/https://raw.githubusercontent.com/tianya7981/jiekou/refs/heads/main/野火959",
        "https://tv.iill.top/m3u/Gather",
        "https://gh.tryxd.cn/https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.txt",
        "https://gh.tryxd.cn/https://raw.githubusercontent.com/wwb521/live/main/tv.m3u",
        "http://aktv.space/live.m3u",
        # 在此添加更多源...
    ]

    processor = M3UProcessor()
    entries = processor.process_sources(SOURCE_URLS)
    
    # 生成输出文件
    with open('live.m3u', 'w', encoding='utf-8') as f:
        f.write(processor.generate_m3u(entries))
    
    with open('live.txt', 'w', encoding='utf-8') as f:
        f.write(processor.generate_txt(entries))
    
    print(f"Generated {len(entries)} channels")
