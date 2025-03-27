import os
import re
import requests
from urllib.parse import urlparse

def natural_sort_key(s):
    """自然排序键生成函数，支持数字顺序"""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)
    ]

def parse_m3u(content):
    """解析M3U/M3U8格式内容"""
    channels = []
    extinf_pattern = re.compile(r'#EXTINF:-?\d+.*?,(.*)')
    
    lines = content.splitlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#EXTINF'):
            match = extinf_pattern.match(line)
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
        line = line.strip()
        if line:
            parts = line.split(',', 1)
            if len(parts) == 2:
                name, url = parts.strip(), parts.strip()
            else:
                url = line
                name = urlparse(url).netloc.split('.')[-2].capitalize()
            channels.append({'name': name, 'url': url})
    return channels

def fetch_source(source):
    """获取内容（支持本地文件和远程URL）"""
    try:
        if source.startswith(('http://', 'https://')):
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            return response.text
        elif os.path.exists(source):
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"File not found: {source}")
            return None
    except Exception as e:
        print(f"Error processing {source}: {str(e)}")
        return None

def process_sources(sources):
    """处理所有输入源并去重排序"""
    all_channels = []
    seen_urls = set()
    
    for source in sources:
        content = fetch_source(source)
        if not content:
            continue
            
        if source.endswith(('.m3u', '.m3u8')):
            channels = parse_m3u(content)
        elif source.endswith('.txt'):
            channels = parse_txt(content)
        else:
            print(f"Unsupported file format: {source}")
            continue
            
        for chan in channels:
            if chan['url'] not in seen_urls:
                seen_urls.add(chan['url'])
                all_channels.append(chan)
    
    # 按自然顺序排序
    return sorted(all_channels, key=lambda x: natural_sort_key(x['name']))

def generate_files(channels):
    """生成输出文件"""
    os.makedirs('output', exist_ok=True)
    
    # 生成M3U文件
    with open('output/live.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for chan in channels:
            f.write(f'#EXTINF:-1,{chan["name"]}\n{chan["url"]}\n')
    
    # 生成TXT文件
    with open('output/live.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(chan['url'] for chan in channels))

if __name__ == '__main__':
    # 从环境变量获取输入源
    sources = os.getenv('INPUT_SOURCES', '').split()
    
    if not sources:
        # 默认源（用于测试）
        sources = [
            'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u',
            'https://raw.githubusercontent.com/Free-IPTV/Countries/master/CN.m3u'
        ]
    
    sorted_channels = process_sources(sources)
    
    if sorted_channels:
        generate_files(sorted_channels)
        print(f"成功生成 {len(sorted_channels)} 个频道列表")
        print("输出文件: output/live.m3u 和 output/live.txt")
    else:
        print("未发现有效频道源")
        exit(1)
