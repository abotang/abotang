"""Generate the profile orbit from GitHub's public contribution calendar."""

import argparse
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from math import dist
from pathlib import Path
from time import sleep
from urllib.error import URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


URL = 'https://github.com/users/abotang/contributions'
OUTPUT = Path(__file__).resolve().parents[1] / 'assets' / 'contributions-orbit.svg'
COLORS = ['#403454', '#82529b', '#b76ba9', '#ee90ad', '#ffcf95']
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'td':
            return
        attrs = dict(attrs)
        if 'data-date' in attrs and 'data-level' in attrs:
            day = date.fromisoformat(attrs['data-date'])
            level = int(attrs['data-level'])
            if level not in range(5) or day in self.days:
                raise ValueError(f'Unexpected calendar cell for {day}')
            self.days[day] = level


def read_calendar(html):
    calendar = Calendar()
    calendar.feed(html)
    calendar.close()
    days = dict(sorted(calendar.days.items()))
    if not 350 <= len(days) <= 378:
        raise ValueError(f'Incomplete GitHub calendar: {len(days)} days')
    if (max(days) - min(days)).days + 1 != len(days):
        raise ValueError('GitHub calendar contains missing days')
    return days


def fetch_calendar():
    request = Request(URL, headers={'User-Agent': 'abotang-contribution-orbit', 'Accept': 'text/html'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                days = read_calendar(response.read().decode('utf-8'))
            today = datetime.now(timezone.utc).date()
            if not today - timedelta(days=1) <= max(days) <= today + timedelta(days=1):
                raise ValueError('GitHub returned an outdated calendar')
            return days
        except (URLError, TimeoutError, ValueError):
            if attempt == 2:
                raise
            sleep(2 ** (attempt + 1))


def comet(active):
    # Interpolate along the quiet stretches, then visit every active day in order.
    points = [(46, 160), *active, (926, 152)]
    if not active:
        points.insert(1, (480, 121))
    path = 'M ' + ' L '.join(f'{x:.2f} {y:.2f}' for x, y in points)
    distances = [0.0]
    for start, end in zip(points, points[1:]):
        distances.append(distances[-1] + dist(start, end))
    pulse = []
    for (x, y), distance in zip(active, distances[1:]):
        # A negative delay initializes the pulse at the matching phase of the comet.
        delay = 18 * (distance / distances[-1] - 1)
        pulse.append(f'<circle class="ping" cx="{x:.2f}" cy="{y:.2f}" r="7" style="animation-delay:{delay:.4f}s"/>')
    return f'''<g class="motion">
<path d="{path}" fill="none" stroke="#ca8ecf" stroke-width="1.3" stroke-linejoin="round" opacity=".32"/>
<g fill="none" stroke="#ffe2b3">{''.join(pulse)}</g>
<g><circle r="9" fill="#ffb8a8" opacity=".26"/><circle r="3.7" fill="#fff1cf"/>
<animateMotion dur="18s" repeatCount="indefinite" path="{path}"/></g></g>'''


def render(days):
    first, last = min(days), max(days)
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    weeks = (last - sunday).days // 7
    grid, labels, active = [], [], []
    previous_label = -100
    for day, level in days.items():
        week, row = divmod((day - sunday).days, 7)
        x, y = 52 + 856 * week / weeks, 99 + 16 * row
        grid.append(f'<rect x="{x:.2f}" y="{y}" width="11" height="11" rx="3" fill="{COLORS[level]}"><title>{day} · {level}/4</title></rect>')
        if (day == first or day.day == 1) and x - previous_label > 43 and x < 900:
            labels.append(f'<text x="{x:.2f}" y="85">{MONTHS[day.month-1]}</text>')
            previous_label = x
        if level:
            active.append((x + 5.5, y + 5.5))
    legend = ''.join(f'<rect x="{813 + i*16}" y="235" width="10" height="10" rx="2" fill="{color}"/>' for i, color in enumerate(COLORS))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="267" viewBox="0 0 960 267" role="img" aria-labelledby="title desc">
<title id="title">贡献星轨</title>
<desc id="desc">{first} 至 {last} 的公开贡献日历，{len(active)} 个活跃日。颜色越亮，贡献越多。</desc>
<style>
text {{font-family:"Segoe UI","Microsoft YaHei","PingFang SC",Arial,sans-serif}}
.ping {{opacity:0; animation:ping 18s linear infinite}}
@keyframes ping {{0% {{opacity:.8}} 4%,100% {{opacity:0}}}}
@media (prefers-reduced-motion:reduce) {{.motion {{display:none}}}}
</style>
<defs>
  <linearGradient id="sky" x2="1" y2="1"><stop stop-color="#211436"/><stop offset=".48" stop-color="#33204c"/><stop offset="1" stop-color="#18132e"/></linearGradient>
  <radialGradient id="aurora" cx=".77" cy="0" r=".82"><stop stop-color="#b44a9c" stop-opacity=".48"/><stop offset=".52" stop-color="#8e499f" stop-opacity=".16"/><stop offset="1" stop-color="#362155" stop-opacity="0"/></radialGradient>
  <clipPath id="edge"><rect x=".5" y=".5" width="959" height="266" rx="20"/></clipPath>
</defs>
<g clip-path="url(#edge)">
<rect width="960" height="267" fill="url(#sky)"/><rect width="960" height="267" fill="url(#aurora)"/>
<g fill="none" stroke-width="1.2">
<path d="M480 0Q643 98 785 32T990 26" stroke="#f1a0c4" opacity=".25"/>
<path d="M544 -1Q652 83 793 24T998 17" stroke="#fbd19d" opacity=".29"/>
<path d="M610 -5Q684 65 814 13T987 8" stroke="#ef91c8" opacity=".19"/>
</g>
<g fill="#fff0d4"><circle cx="498" cy="38" r="1.2"/><circle cx="718" cy="29" r="1.4"/><circle cx="809" cy="56" r="1.05"/><path d="m756 35 1.2 3.8 3.8 1.2-3.8 1.2-1.2 3.8-1.2-3.8-3.8-1.2 3.8-1.2Z" opacity=".8"/></g>
<text x="36" y="47" fill="#fff2de" font-size="25" font-weight="600">贡献星轨</text>
<text x="923" y="46" text-anchor="end" fill="#ffdaac" font-size="15">{len(active)} 个活跃日</text>
<g font-size="12" fill="#d6c8df">{''.join(labels)}</g>
<g fill="#c9bad2" text-anchor="middle" font-size="10"><text x="27" y="124">一</text><text x="27" y="156">三</text><text x="27" y="188">五</text></g>
{chr(10).join(grid)}
{comet(active)}
<path d="M36 220H924" stroke="#b998c5" stroke-opacity=".19"/>
<text x="36" y="245" font-size="13" fill="#d7c8de">{first} — {last}　·　公开贡献</text>
<g font-size="12" fill="#d7c8de"><text x="788" y="245">少</text>{legend}<text x="901" y="245">多</text></g>
</g><rect x=".5" y=".5" width="959" height="266" rx="20" fill="none" stroke="#67426e"/>
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Read a saved GitHub contributions HTML file')
    args = parser.parse_args()
    days = read_calendar(args.source.read_text(encoding='utf-8')) if args.source else fetch_calendar()
    svg = render(days).encode('utf-8')
    ET.fromstring(svg)
    if not OUTPUT.exists() or OUTPUT.read_bytes() != svg:
        temporary = OUTPUT.with_suffix('.svg.tmp')
        temporary.write_bytes(svg)
        temporary.replace(OUTPUT)
    print(f'Public calendar: {min(days)} through {max(days)}, {sum(level > 0 for level in days.values())} active days')


if __name__ == '__main__':
    main()
