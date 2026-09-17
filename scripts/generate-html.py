from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SITE = ROOT / "site"

TOWN_COORDS = {
    "lenoir": [35.914, -81.539], "happy-valley": [36.011, -81.633], "hudson": [35.848, -81.496],
    "granite-falls": [35.797, -81.431], "collettsville": [35.948, -81.673], "wilson-creek": [35.963, -81.762],
    "blowing-rock": [36.135, -81.678], "boone": [36.216, -81.674], "banner-elk": [36.163, -81.871],
    "beech-mountain": [36.211, -81.889], "grandfather-mountain": [36.095, -81.835], "linville": [36.067, -81.870],
    "morganton": [35.746, -81.684], "valdese": [35.742, -81.563], "connelly-springs": [35.742, -81.514],
    "marion": [35.684, -82.009], "old-fort": [35.629, -82.180], "little-switzerland": [35.847, -82.091],
    "spruce-pine": [35.916, -82.064], "hickory": [35.734, -81.344], "newton": [35.669, -81.221],
    "catawba": [35.707, -81.075], "taylorsville": [35.921, -81.177], "statesville": [35.782, -80.887],
    "north-wilkesboro": [36.158, -81.147], "ferguson": [36.111, -81.427], "west-jefferson": [36.403, -81.492],
    "weaverville": [35.697, -82.565],
    "asheville": [35.595, -82.552], "black-mountain": [35.609, -82.321], "montreat": [35.623, -82.299],
    "swannanoa": [35.599, -82.397], "fairview": [35.478, -82.451], "arden": [35.463, -82.530],
    "fletcher": [35.429, -82.489],
}


def parse_value(value: str):
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("["):
        try:
            return ast.literal_eval(value)
        except Exception:
            return []
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"')
    return value


def parse_entry(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\s*\n(.*?)\n---\s*\n?(.*)", text, re.S)
    frontmatter = match.group(1) if match else ""
    body = match.group(2) if match else text
    entry: dict = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        entry[key.strip()] = parse_value(value)

    body_preview = re.sub(r"[#*_`>\-]+", " ", body)
    body_preview = re.sub(r"\s+", " ", body_preview).strip()
    entry["path"] = str(path.relative_to(ROOT)).replace("\\", "/")
    entry["slug"] = path.stem
    entry["body_preview"] = body_preview[:260]
    entry.setdefault("tags", [])
    entry.setdefault("source_urls", [])
    if not isinstance(entry["tags"], list):
        entry["tags"] = []
    if not isinstance(entry["source_urls"], list):
        entry["source_urls"] = []
    return entry


def main() -> None:
    SITE.mkdir(exist_ok=True)
    entries = [parse_entry(path) for path in sorted(CONTENT.rglob("*.md"))]
    entries.sort(
        key=lambda item: (
            item.get("date_start") in ("", None),
            str(item.get("date_start") or ""),
            str(item.get("title") or ""),
        )
    )
    stats = {
        "total": len(entries),
        "events": sum(1 for item in entries if item.get("type") == "event"),
        "places": sum(1 for item in entries if item.get("type") == "place"),
        "towns": len({item.get("town") for item in entries if item.get("town")}),
        "review": sum(
            1
            for item in entries
            if item.get("status") in {"needs-confirmation", "expected", "confirmed-pattern"}
        ),
        "past": sum(1 for item in entries if item.get("status") == "past"),
    }
    data_json = json.dumps(entries, ensure_ascii=False)
    coords_json = json.dumps(TOWN_COORDS, ensure_ascii=False)

    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Happy Valley Field Guide</title>
<link rel="icon" href="data:,">
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css">
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<script>
  (() => {
    const param = new URLSearchParams(window.location.search).get("scoutTheme");
    const theme =
      param || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  })();
</script>
<style>
:root {
  color-scheme: light;
  --cp-bg: #f7f4ef;
  --cp-bg-elevated: #fcfbf8;
  --cp-surface: #ffffff;
  --cp-surface-soft: #f5f5f5;
  --cp-border: #dedede;
  --cp-border-strong: #919191;
  --cp-text: #242424;
  --cp-text-muted: #5c5c5c;
  --cp-text-soft: #6f6f6f;
  --cp-accent: #b11f4b;
  --cp-accent-hover: #9a1a41;
  --cp-accent-soft: rgba(177, 31, 75, 0.08);
  --cp-accent-fg: #ffffff;
  --cp-success: #16a34a;
  --cp-danger: #dc2626;
  --cp-warning: #f59e0b;
  --cp-link: #0078d4;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.12);
  --cp-overlay: rgba(255, 255, 255, 0.8);
  --cp-panel: rgba(255, 255, 255, 0.86);
  --cp-panel-strong: rgba(255, 255, 255, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.55);
  --cp-highlight: rgba(177, 31, 75, 0.12);
}
html[data-theme="dark"] {
  color-scheme: dark;
  --cp-bg: #3d3b3a;
  --cp-bg-elevated: #343231;
  --cp-surface: #292929;
  --cp-surface-soft: #2e2e2e;
  --cp-border: #474747;
  --cp-border-strong: #5f5f5f;
  --cp-text: #dedede;
  --cp-text-muted: #919191;
  --cp-text-soft: #b0b0b0;
  --cp-accent: #fd8ea1;
  --cp-accent-hover: #fb7b91;
  --cp-accent-soft: rgba(253, 142, 161, 0.14);
  --cp-accent-fg: #1a1a1a;
  --cp-success: #4ade80;
  --cp-danger: #f87171;
  --cp-warning: #fbbf24;
  --cp-link: #4da6ff;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.32);
  --cp-overlay: rgba(41, 41, 41, 0.88);
  --cp-panel: rgba(41, 41, 41, 0.72);
  --cp-panel-strong: rgba(41, 41, 41, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.04);
  --cp-highlight: rgba(253, 142, 161, 0.12);
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--cp-bg); color: var(--cp-text); font-family: "Segoe UI", Aptos, Calibri, -apple-system, BlinkMacSystemFont, sans-serif; }
a { color: var(--cp-link); }
header { background: var(--cp-bg-elevated); border-bottom: 1px solid var(--cp-border); padding: 32px 24px; }
.wrap { max-width: 1180px; margin: 0 auto; }
h1 { margin: 0 0 8px; font-size: clamp(32px, 5vw, 56px); letter-spacing: -0.04em; }
.subtitle { color: var(--cp-text-muted); font-size: 18px; max-width: 860px; line-height: 1.45; }
.tabs { display: inline-flex; flex-wrap: wrap; gap: 6px; margin-top: 24px; padding: 6px; background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 16px; box-shadow: var(--cp-shadow); }
.tab, .view-button { appearance: none; border: 1px solid var(--cp-border); background: var(--cp-surface-soft); color: var(--cp-text-muted); border-radius: 0.625rem; padding: 9px 14px; font: inherit; cursor: pointer; }
.tab strong { color: var(--cp-text); margin-left: 6px; }
.tab:hover, .tab.active, .view-button:hover, .view-button.active { border-color: var(--cp-accent); background: var(--cp-accent-soft); color: var(--cp-accent); }
.tab:focus-visible, .view-button:focus-visible, .filter-chip:focus-visible, .town-pin:focus-visible { outline: 2px solid var(--cp-accent); outline-offset: 2px; }
.controls { position: sticky; top: 0; z-index: 2; background: var(--cp-panel-strong); border-bottom: 1px solid var(--cp-border); padding: 16px 24px; }
.control-grid { display: grid; grid-template-columns: minmax(240px, 1fr) auto; gap: 12px; align-items: center; }
input, select { width: 100%; border: 1px solid var(--cp-border); border-radius: 0.625rem; padding: 10px 12px; background: var(--cp-surface); color: var(--cp-text); font: inherit; }
.view-switch { display: inline-flex; gap: 6px; justify-self: end; }
.filter-chip { appearance: none; border: 1px solid var(--cp-border); background: var(--cp-surface); color: var(--cp-text-muted); border-radius: 999px; padding: 6px 10px; font: inherit; font-size: 13px; cursor: pointer; }
.filter-chip:hover, .filter-chip.active { background: var(--cp-accent-soft); color: var(--cp-accent); border-color: var(--cp-accent); }
.filter-chip.clear { color: var(--cp-text-muted); }
.active-filter { display: none; align-items: center; gap: 8px; color: var(--cp-text-muted); margin-top: 12px; }
.active-filter.show { display: flex; }
main { padding: 24px; }
.meta-line { display: flex; justify-content: space-between; gap: 16px; color: var(--cp-text-muted); margin-bottom: 16px; }
.view-section { display: none; }
.view-section.active { display: block; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.card { background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 16px; padding: 18px; box-shadow: var(--cp-shadow); display: flex; flex-direction: column; gap: 10px; }
.card h2 { margin: 0; font-size: 20px; }
.kicker { display: flex; flex-wrap: wrap; gap: 8px; font-size: 12px; color: var(--cp-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.badge { display: inline-flex; align-items: center; border: 1px solid var(--cp-border); background: var(--cp-surface-soft); border-radius: 999px; padding: 4px 8px; font-size: 12px; color: var(--cp-text-muted); }
.badge.strong { background: var(--cp-accent-soft); color: var(--cp-accent); border-color: var(--cp-border-strong); }
.desc { color: var(--cp-text); line-height: 1.45; }
.details { color: var(--cp-text-muted); font-size: 13px; line-height: 1.45; }
.sources { font-size: 12px; color: var(--cp-text-muted); }
.map-shell, .calendar-shell { background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 16px; padding: 18px; box-shadow: var(--cp-shadow); }
.map-layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr); gap: 16px; }
.map-canvas { width: 100%; min-height: 560px; border: 1px solid var(--cp-border); border-radius: 16px; background: var(--cp-bg-elevated); overflow: hidden; }
.maplibregl-map { font-family: "Segoe UI", Aptos, Calibri, -apple-system, BlinkMacSystemFont, sans-serif; }
.maplibregl-ctrl-attrib { background: var(--cp-panel-strong); color: var(--cp-text-muted); }
.cluster-marker, .entry-marker { display: grid; place-items: center; border-radius: 999px; border: 2px solid var(--cp-surface); background: var(--cp-accent); color: var(--cp-accent-fg); box-shadow: var(--cp-shadow); font-weight: 700; cursor: pointer; }
.cluster-marker { width: 38px; height: 38px; }
.entry-marker { width: 16px; height: 16px; }
.cluster-marker.is-expanded { background: var(--cp-accent-hover); }
.map-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.map-side, .calendar-list { display: grid; gap: 8px; align-content: start; }
.town-row, .calendar-item { border: 1px solid var(--cp-border); background: var(--cp-surface-soft); border-radius: 0.625rem; padding: 10px; }
.town-row { cursor: pointer; text-align: left; color: var(--cp-text); font: inherit; }
.town-row:hover, .town-row.active { border-color: var(--cp-accent); background: var(--cp-accent-soft); }
.calendar-month { margin: 0 0 10px; font-size: 18px; }
.calendar-group { margin-bottom: 20px; }
footer { padding: 24px; color: var(--cp-text-muted); border-top: 1px solid var(--cp-border); }
@media (max-width: 860px) { .control-grid, .map-layout { grid-template-columns: 1fr; } .view-switch { justify-self: stretch; } .view-button { flex: 1; } .map-canvas { min-height: 420px; } }
</style>
</head>
<body>
<header><div class="wrap"><h1>Happy Valley Field Guide</h1><div class="subtitle">A Markdown-first acclimation guide for the Lenoir region: towns, events, places, fairs, art, music, outdoors, cars, tractors, horses, and seasonal day trips.</div><nav class="tabs" aria-label="Content type"><button class="tab active" type="button" data-type-tab="" aria-pressed="true">All <strong>__TOTAL__</strong></button><button class="tab" type="button" data-type-tab="event" aria-pressed="false">Events <strong>__EVENTS__</strong></button><button class="tab" type="button" data-type-tab="place" aria-pressed="false">Places <strong>__PLACES__</strong></button></nav></div></header>
<section class="controls"><div class="wrap"><div class="control-grid"><input id="q" placeholder="Search title, town, tags, description"><div class="view-switch" aria-label="View mode"><button class="view-button active" type="button" data-view="cards" aria-pressed="true">Cards</button><button class="view-button" type="button" data-view="map" aria-pressed="false">Map</button><button class="view-button" type="button" data-view="calendar" aria-pressed="false">Calendar</button></div></div><div id="activeTown" class="active-filter"></div></div></section>
<main><div class="wrap"><div class="meta-line"><div id="count"></div><div>Source: <code>content/&lt;town&gt;/*.md</code></div></div><section id="cardsView" class="view-section active"><div id="cards" class="grid"></div></section><section id="mapView" class="view-section"><div id="mapContent" class="map-shell"></div></section><section id="calendarView" class="view-section"><div id="calendarContent" class="calendar-shell"></div></section></div></main>
<footer><div class="wrap">Generated locally from Markdown. Items marked expected, confirmed-pattern, or needs-confirmation should be checked before planning.</div></footer>
<script>
const DATA = __DATA__;
const TOWN_COORDS = __COORDS__;
const byId = id => document.getElementById(id);
const escapeHtml = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let activeType = '';
let activeTown = '';
let viewMode = 'cards';
let expandedMapTown = '';
let guideMap = null;
let mapMarkers = [];
function updateTabs() {
  document.querySelectorAll('[data-type-tab]').forEach(button => {
    const active = button.dataset.typeTab === activeType;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  document.querySelectorAll('[data-view]').forEach(button => {
    const active = button.dataset.view === viewMode;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  for (const section of ['cardsView','mapView','calendarView']) byId(section).classList.remove('active');
  byId(`${viewMode}View`).classList.add('active');
}
function setActiveTown(town) {
  activeTown = activeTown === town ? '' : town;
  if (!activeTown) expandedMapTown = '';
  render();
}
function renderActiveTown() {
  const el = byId('activeTown');
  if (!activeTown) {
    el.classList.remove('show');
    el.innerHTML = '';
    return;
  }
  el.classList.add('show');
  el.innerHTML = `<span>Town filter:</span><button type="button" class="filter-chip active" id="clearTown">${escapeHtml(activeTown)} ×</button>`;
  byId('clearTown').addEventListener('click', () => setActiveTown(''));
}
function card(e) {
  const date = formatDateRange(e.date_start, e.date_end);
  const sourceLinks = (e.source_urls || []).slice(0,3).map((s,i)=>`<a href="${escapeHtml(s)}">source ${i+1}</a>`).join(' · ');
  return `<article class="card"><div class="kicker"><span class="badge strong">${escapeHtml(e.type)}</span><span class="badge">${escapeHtml(e.town)}</span><span class="badge">${escapeHtml(e.status)}</span>${e.scope && e.scope !== 'core' ? `<span class="badge">${escapeHtml(e.scope)}</span>` : ''}</div><h2>${escapeHtml(e.title)}</h2><div class="details">${date ? `<strong>${escapeHtml(date)}</strong><br>` : ''}${escapeHtml(e.timing || e.time || 'Year-round / see details')}<br>${escapeHtml(e.address || '')}</div><div class="desc">${escapeHtml(e.description_short || e.body_preview || '')}</div><div class="sources">${sourceLinks}<br>${escapeHtml(e.path)}</div></article>`;
}
function matchingRows(ignoreTown=false) {
  const q=byId('q').value.trim().toLowerCase();
  return DATA.filter(e => (!activeType || e.type === activeType) && (ignoreTown || !activeTown || e.town === activeTown) && (!q || JSON.stringify(e).toLowerCase().includes(q)));
}
function renderMap(rowsForPins, rows) {
  const grouped = new Map();
  for (const e of rowsForPins) {
    if (!TOWN_COORDS[e.town]) continue;
    if (!grouped.has(e.town)) grouped.set(e.town, []);
    grouped.get(e.town).push(e);
  }
  if (!grouped.size) {
    byId('mapContent').innerHTML = '<p>No mapped towns in the current filter.</p>';
    return;
  }
  const townRows = [...grouped.entries()].sort((a,b)=>b[1].length-a[1].length || a[0].localeCompare(b[0])).map(([town, items]) => `<button type="button" class="town-row ${town===expandedMapTown?'active':''}" data-town="${escapeHtml(town)}"><strong>${escapeHtml(town)}</strong><br>${items.length} matching entries</button>`).join('');
  const expandedText = expandedMapTown ? `<button type="button" class="filter-chip active" id="resetMap">Reset map ×</button><span class="details">Expanded: ${escapeHtml(expandedMapTown)}</span>` : `<span class="details">Click a numbered cluster to zoom in and expand it into individual entry points.</span>`;
  byId('mapContent').innerHTML = `<div class="map-layout"><div><div class="map-actions">${expandedText}</div><div id="guideMap" class="map-canvas"></div></div><div class="map-side"><div class="details">${rows.length} entries shown. Map markers are approximate town/entry locations.</div>${townRows}</div></div>`;
  requestAnimationFrame(() => drawGuideMap(grouped));
  const reset = byId('resetMap');
  if (reset) reset.addEventListener('click', () => { expandedMapTown = ''; activeTown = ''; render(); });
}
function entryCoord(center, index, total) {
  if (total <= 1) return center;
  const angle = (index / total) * Math.PI * 2;
  const ring = 0.006 + Math.floor(index / 10) * 0.004;
  return [center[0] + Math.sin(angle) * ring, center[1] + Math.cos(angle) * ring];
}
function lngLat(coord) {
  return [coord[1], coord[0]];
}
function addMarker(coord, element, popupHtml) {
  const marker = new maplibregl.Marker({ element }).setLngLat(lngLat(coord)).addTo(guideMap);
  if (popupHtml) marker.setPopup(new maplibregl.Popup({ offset: 16 }).setHTML(popupHtml));
  mapMarkers.push(marker);
  return marker;
}
function drawGuideMap(grouped) {
  if (typeof maplibregl === 'undefined') {
    byId('guideMap').innerHTML = '<p class="details">The map library did not load. Publish the site folder through a static web host and reload the page.</p>';
    return;
  }
  if (guideMap) {
    guideMap.remove();
    guideMap = null;
  }
  mapMarkers = [];
  guideMap = new maplibregl.Map({
    container: 'guideMap',
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: [-81.539, 35.914],
    zoom: 8,
    attributionControl: true
  });
  const bounds = new maplibregl.LngLatBounds();
  for (const [town, items] of grouped.entries()) {
    const center = TOWN_COORDS[town];
    if (!center) continue;
    if (expandedMapTown === town) {
      items.forEach((entry, index) => {
        const coord = entryCoord(center, index, items.length);
        bounds.extend(lngLat(coord));
        const element = document.createElement('div');
        element.className = 'entry-marker';
        element.title = entry.title;
        addMarker(coord, element, `<strong>${escapeHtml(entry.title)}</strong><br>${escapeHtml(entry.type)} · ${escapeHtml(entry.town)}<br>${escapeHtml(entry.timing || formatDateRange(entry.date_start, entry.date_end) || '')}`);
      });
    } else {
      bounds.extend(lngLat(center));
      const element = document.createElement('button');
      element.type = 'button';
      element.className = `cluster-marker ${town === expandedMapTown ? 'is-expanded' : ''}`;
      element.textContent = String(items.length);
      element.title = town;
      element.setAttribute('aria-label', `${town}, ${items.length} entries`);
      element.addEventListener('click', () => { expandedMapTown = town; activeTown = town; render(); });
      addMarker(center, element);
    }
  }
  if (!bounds.isEmpty()) guideMap.fitBounds(bounds, { padding: 28, maxZoom: expandedMapTown ? 12 : 11 });
}
function monthName(value) {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? 'Date TBD' : date.toLocaleString(undefined, { month: 'long', year: 'numeric' });
}
function parseDateParts(value) {
  const match = String(value || '').match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);
  if (!match) return null;
  return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) };
}
function monthLabel(month) {
  return new Date(2026, month - 1, 1).toLocaleString(undefined, { month: 'long' });
}
function formatDate(value) {
  const date = parseDateParts(value);
  if (!date) return '';
  return `${monthLabel(date.month)} ${date.day}, ${date.year}`;
}
function formatDateRange(startValue, endValue) {
  const start = parseDateParts(startValue);
  if (!start) return '';
  const end = parseDateParts(endValue);
  if (!end || startValue === endValue) return formatDate(startValue);
  if (start.year === end.year && start.month === end.month) {
    return `${monthLabel(start.month)} ${start.day}-${end.day}, ${start.year}`;
  }
  if (start.year === end.year) {
    return `${monthLabel(start.month)} ${start.day} - ${monthLabel(end.month)} ${end.day}, ${start.year}`;
  }
  return `${formatDate(startValue)} - ${formatDate(endValue)}`;
}
function renderCalendar(rows) {
  const dated = rows.filter(e => e.type === 'event' && e.date_start).sort((a,b)=>String(a.date_start).localeCompare(String(b.date_start)));
  const undated = rows.filter(e => e.type === 'event' && !e.date_start).length;
  const groups = new Map();
  for (const e of dated) {
    const key = monthName(e.date_start);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(e);
  }
  const html = [...groups.entries()].map(([month, items]) => `<section class="calendar-group"><h2 class="calendar-month">${escapeHtml(month)}</h2><div class="calendar-list">${items.map(e => `<article class="calendar-item"><strong>${escapeHtml(formatDateRange(e.date_start, e.date_end))}</strong><br>${escapeHtml(e.title)}<br><span class="details">${escapeHtml(e.town)} · ${escapeHtml(e.timing || '')}</span></article>`).join('')}</div></section>`).join('');
  byId('calendarContent').innerHTML = html || '<p>No dated events match the current filters.</p>';
  if (undated) byId('calendarContent').insertAdjacentHTML('beforeend', `<p class="details">${undated} matching event${undated === 1 ? '' : 's'} have no exact date yet and are not shown on the calendar.</p>`);
}
function render() {
  const rows=matchingRows(false);
  const rowsForMap=matchingRows(true);
  byId('count').textContent = `${rows.length} shown of ${DATA.length} entries`;
  byId('cards').innerHTML = rows.map(card).join('');
  renderActiveTown();
  renderMap(rowsForMap, rows);
  renderCalendar(rows);
  updateTabs();
}
byId('q').addEventListener('input', render);
document.querySelectorAll('[data-type-tab]').forEach(button => button.addEventListener('click', () => { activeType = button.dataset.typeTab; render(); }));
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => { viewMode = button.dataset.view; render(); }));
byId('mapContent').addEventListener('click', event => {
  const button = event.target.closest('[data-town]');
  if (button) {
    expandedMapTown = expandedMapTown === button.dataset.town ? '' : button.dataset.town;
    activeTown = expandedMapTown;
    render();
  }
});
byId('mapContent').addEventListener('keydown', event => {
  if (event.key === 'Enter' || event.key === ' ') {
    const button = event.target.closest('[data-town]');
    if (button) {
      event.preventDefault();
      expandedMapTown = expandedMapTown === button.dataset.town ? '' : button.dataset.town;
      activeTown = expandedMapTown;
      render();
    }
  }
});
updateTabs();
render();
</script>
</body>
</html>
"""

    html = (
        template.replace("__DATA__", data_json)
        .replace("__COORDS__", coords_json)
        .replace("__TOTAL__", str(stats["total"]))
        .replace("__EVENTS__", str(stats["events"]))
        .replace("__PLACES__", str(stats["places"]))
        .replace("__TOWNS__", str(stats["towns"]))
        .replace("__REVIEW__", str(stats["review"]))
        .replace("__PAST__", str(stats["past"]))
    )
    site_output = SITE / "index.html"
    pages_output = ROOT / "index.html"
    site_output.write_text(html, encoding="utf-8")
    pages_output.write_text(html, encoding="utf-8")
    print(site_output)
    print(pages_output)
    print(stats)


if __name__ == "__main__":
    main()
