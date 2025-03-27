import os
import re
import requests
from urllib.parse import urlparse

def natural_sort_key(s):
    """自然排序键生成函数 (支持数字顺序)"""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)
    ]

def parse_m3u(content):
    """解析M3U/M3U8格式内容"""
    channels = []
    lines = content.splitlines()
    extinf_pattern = re.compile(r'#EXTINF:-?\d+.*?,(.*)')
    
    for i in range(len(lines)):
        if lines[i].startswith('#EXTINF'):
            match = extinf_pattern.match(lines[i].strip())
            if match and (i+1) < len(lines):
                name = match.group(1).strip()
                url = lines[i+1].strip()
                if url and not url.startswith('#'):
                    channels.append({'name': name, 'url': url})
    return channels

def parse_txt(content):
    """解析TXT格式内容"""
    channels = []
    for line in content.splitlines():
        if line.strip():
            parts = line.split(',', 1)
            if len(parts) == 2:
                name, url = parts.strip(), parts.strip()
            else:
                url = line.strip()
                name = urlparse(url).netloc.split('.')[-2].capitalize()
            channels.append({'name': name, 'url': url})
    return channels

def fetch_source(source):
    """获取内容 (支持本地文件和远程URL)"""
    try:
        if source.startswith(('https://gh.tryxd.cn/https://raw.githubusercontent.com/alantang1977/auto-iptv/main/live_ipv4.txt', 'https://gh.tryxd.cn/https://raw.githubusercontent.com/alantang1977/JunTV/refs/heads/main/output/result.m3u')):
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            return response.text
        else:
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Error processing {source}: {str(e)}")
        return None

def process_sources(sources):
    """处理所有输入源并去重排序"""
    channels = []
    seen_urls = set()
    
    for src in sources:
        content = fetch_source(src)
        if not content:
            continue
            
        if src.endswith(('.m3u', '.m3u8')):
            parsed = parse_m3u(content)
        elif src.endswith('.txt'):
            parsed = parse_txt(content)
        else:
            continue
            
        for chan in parsed:
            if chan['url'] not in seen_urls:
                seen_urls.add(chan['url'])
                channels.append(chan)
    
    # 按自然顺序排序
    return sorted(channels, key=lambda x: natural_sort_key(x['name']))

def generate_files(channels):
    """生成输出文件"""
    os.makedirs('output', exist_ok=True)
    
    # 生成M3U
    with open('output/live.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for chan in channels:
            f.write(f'#EXTINF:-1,{chan["name"]}\n{chan["url"]}\n\n')
    
    # 生成TXT
    with open('output/live.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(chan['url'] for chan in channels))

if __name__ == '__main__':
    # 从环境变量获取输入源
    sources = os.getenv('INPUT_SOURCES', '').split()
    
    if not sources:
        # 默认测试源
        sources = [
            'https://gitlab.com/iptv-org/iptv/-/raw/master/streams/cn.m3u',
            'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u'
        ]
    
    channels = process_sources(sources)
    
    if channels:
        generate_files(channels)
        print(f"成功生成 {len(channels)} 个频道列表")
    else:
        print("未发现有效频道源")
        exit(1)
