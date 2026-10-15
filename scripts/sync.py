#!/usr/bin/env python3
"""Build domain-only AI rules; publish only after every upstream validates."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/'
# slug, display name, upstream slug (None = maintained locally), default policy, seed domains
SERVICES = [
 ('chatgpt', 'ChatGPT', 'openai', 'proxy', 'openai.com chatgpt.com oaistatic.com oaiusercontent.com sora.com'),
 ('claude', 'Claude', 'anthropic', 'proxy', 'anthropic.com claude.ai claude.com claudeusercontent.com'),
 ('gemini', 'Gemini', 'google-gemini', 'proxy', 'gemini.google.com aistudio.google.com generativelanguage.googleapis.com notebooklm.google.com notebooklm.google ai.google.dev'),
 ('copilot', 'Copilot', None, 'proxy', 'copilot.microsoft.com sydney.bing.com copilot.cloud.microsoft githubcopilot.com copilot-proxy.githubusercontent.com'),
 ('grok', 'Grok', 'xai', 'proxy', 'grok.com x.ai grok.x.com'),
 ('perplexity', 'Perplexity', 'perplexity', 'proxy', 'perplexity.ai perplexity.com pplx.ai'),
 ('openrouter', 'OpenRouter', None, 'proxy', 'openrouter.ai'),
 ('poe', 'Poe', 'poe', 'proxy', 'poe.com poecdn.net'),
 ('cursor', 'Cursor', 'cursor', 'proxy', 'cursor.com cursor.sh cursorapi.com cursor-cdn.com'),
 ('windsurf', 'Windsurf', 'windsurf', 'proxy', 'windsurf.com windsurf.build codeium.com codeiumdata.com'),
 ('deepseek', 'DeepSeek', 'deepseek', 'direct', 'deepseek.com deepseeksvc.com'),
 ('qwen', '通义千问', None, 'direct', 'qwen.ai qwenlm.ai tongyi.com tongyi.aliyun.com dashscope.aliyuncs.com'),
 ('kimi', 'Kimi', None, 'direct', 'kimi.com kimi.moonshot.cn moonshot.cn moonshot.ai'),
 ('doubao', '豆包', 'doubao', 'direct', 'doubao.com doubaocdn.com'),
 ('glm', '智谱GLM', None, 'direct', 'chatglm.cn bigmodel.cn z.ai'),
 ('minimax', 'MiniMax', None, 'direct', 'minimax.io minimaxi.com minimax.chat hailuoai.com'),
]
CHECK_URLS = {
 'chatgpt': 'https://chatgpt.com/',
 'claude': 'https://claude.ai/',
 'gemini': 'https://gemini.google.com/',
 'copilot': 'https://copilot.microsoft.com/',
 'grok': 'https://grok.com/',
 'perplexity': 'https://www.perplexity.ai/',
 'openrouter': 'https://openrouter.ai/',
 'poe': 'https://poe.com/',
 'cursor': 'https://www.cursor.com/',
 'windsurf': 'https://windsurf.com/',
 'deepseek': 'https://www.deepseek.com/',
 'qwen': 'https://www.qwen.ai/',
 'kimi': 'https://www.kimi.com/',
 'doubao': 'https://www.doubao.com/',
 'glm': 'https://chatglm.cn/',
 'minimax': 'https://www.minimax.io/',
}
EXCLUDE = '到期|剩余|流量|套餐|官网|重置|Expire|Traffic|Reset'
REGIONS = '美国|US|United States|日本|JP|新加坡|SG'

DOMAIN = re.compile(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9-]{2,63}\Z')

def validate(text):
    result = set()
    if len(text) > 1_000_000 or '<html' in text.lower():
        raise ValueError('Not a domain list')
    for raw in text.splitlines():
        value = raw.strip().lower()
        if not value or value.startswith('#'):
            continue
        name = value[2:] if value.startswith('+.') else value
        if not DOMAIN.fullmatch(name):
            raise ValueError(f'Unsupported entry: {value!r}')
        result.add(value)
    if not result:
        raise ValueError('Empty upstream')
    return result

def build(offline=False):
    outputs, manifest = {}, {}
    for slug, name, upstream, policy, seeds in SERVICES:
        values = validate('\n'.join('+.' + d for d in seeds.split()))
        if upstream and not offline:
            request = urllib.request.Request(BASE + upstream + '.list', headers={'User-Agent': 'openclash-ai-rules-sync'})
            with urllib.request.urlopen(request, timeout=45) as response:
                values |= validate(response.read(1_000_001).decode('utf-8'))
        local = ROOT / 'custom' / (slug + '.list')
        if local.exists():
            values |= validate(local.read_text(encoding='utf-8'))
        body = 'payload:\n' + ''.join('  - ' + json.dumps(d) + '\n' for d in sorted(values))
        outputs['rules/' + slug + '.yaml'] = body
        manifest[slug] = {'name': name, 'count': len(values), 'source': BASE + upstream + '.list' if upstream else 'local seeds + custom/' + slug + '.list', 'default': policy, 'sha256': hashlib.sha256(body.encode()).hexdigest(), 'build': 'seed-only' if offline and upstream else 'upstream' if upstream else 'local'}
    groups = [
      {'name': '规则下载', 'type': 'select', 'proxies': ['DIRECT'], 'include-all-proxies': True},
      {'name': 'AI默认出口', 'type': 'select', 'proxies': ['普通代理'], 'include-all-proxies': True, 'filter': '美国|US|United States|日本|JP|新加坡|SG'},
      {'name': '普通代理', 'type': 'select', 'proxies': ['DIRECT'], 'include-all-proxies': True},
      {'name': '媒体自动测速', 'type': 'url-test', 'proxies': ['普通代理'], 'include-all-proxies': True, 'filter': '流媒体|Media|Netflix|香港|HK|日本|JP|新加坡|SG', 'url': 'https://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 150, 'lazy': True},
      {'name': '媒体分流', 'type': 'select', 'proxies': ['媒体自动测速', '普通代理'], 'include-all-proxies': True},
    ]
    providers, rules = {}, []
    for slug, name, upstream, policy, seeds in SERVICES:
        label = 'AI-' + name
        preferred = label + '-手动优先'
        groups.append({'name': preferred, 'type': 'select', 'proxies': ['DIRECT' if policy == 'direct' else 'AI默认出口'], 'include-all-proxies': True, 'exclude-filter': EXCLUDE})
        groups.append({'name': label, 'type': 'fallback', 'proxies': [preferred], 'include-all-proxies': True, 'exclude-filter': EXCLUDE, 'url': CHECK_URLS[slug], 'expected-status': '200-299', 'interval': 600, 'timeout': 8000, 'lazy': True, 'max-failed-times': 3})
        providers['ai-' + slug] = {'type': 'http', 'behavior': 'domain', 'format': 'yaml', 'url': 'https://raw.githubusercontent.com/jackzhang0525/openclash-ai-rules/main/rules/' + slug + '.yaml', 'path': './rule_provider/jack-ai-' + slug + '.yaml', 'interval': 86400, 'proxy': '规则下载'}
        # Local core domains also provide a bootstrap fallback before provider download.
        rules.extend('DOMAIN-SUFFIX,' + d + ',' + label for d in seeds.split())
        rules.append('RULE-SET,ai-' + slug + ',' + label)
    for domain in 'youtube.com youtu.be googlevideo.com ytimg.com youtubei.googleapis.com netflix.com netflix.net nflxvideo.net nflximg.net nflximg.com nflxso.net nflxext.com disneyplus.com disney-plus.net dssott.com disneystreaming.com bamgrid.com hulu.com huluim.com max.com hbo.com hbomax.com spotify.com scdn.co primevideo.com aiv-cdn.net aiv-delivery.net'.split():
        rules.append('DOMAIN-SUFFIX,' + domain + ',媒体分流')
    dns = {'ipv6': False, 'respect-rules': False, 'default-nameserver!': ['223.5.5.5', '119.29.29.29'], 'nameserver!': ['https://dns.alidns.com/dns-query', 'https://doh.pub/dns-query'], 'proxy-server-nameserver!': ['https://dns.alidns.com/dns-query', 'https://doh.pub/dns-query'], 'fallback!': ['https://1.1.1.1/dns-query#规则下载', 'https://8.8.8.8/dns-query#规则下载'], '+fake-ip-filter': ['*.lan', '*.local', 'localhost', '+.ntp.org', '+.pool.ntp.org', '+.msftconnecttest.com', '+.msftncsi.com']}
    # JSON objects are valid YAML values; avoid a third-party YAML dependency.
    module = '# No subscription URLs, passwords or controller secrets.\n[YAML]\nmode: rule\nipv6: false\ntcp-concurrent: true\nunified-delay: true\n'
    for key, value in [('dns', dns), ('rule-providers', providers), ('+proxy-groups', groups), ('+rules', rules)]:
        module += key + ': ' + json.dumps(value, ensure_ascii=False) + '\n'
    outputs['templates/AI_Services.conf'] = module
    outputs['manifest.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    # No writes until every source has passed validation.
    for filename, body in outputs.items():
        dest = ROOT / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding='utf-8', newline='\n')
    print(json.dumps({k: v['count'] for k, v in manifest.items()}, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true', help='Build seed-only artifacts for local validation; do not publish as upstream-synced')
    build(parser.parse_args().offline)
