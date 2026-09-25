#!/usr/bin/env python3
import json, os, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "NFL.ics"
FOLLOWED_TEAMS = {"SF", "LAR", "LA", "KC", "BUF"}
ESPN_URLS = [
    "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
]

COUNTRY_FR = {
    "USA": "États-Unis", "United States": "États-Unis", "United States of America": "États-Unis",
    "US": "États-Unis", "England": "Angleterre", "United Kingdom": "Royaume-Uni", "UK": "Royaume-Uni",
    "Germany": "Allemagne", "Spain": "Espagne", "Brazil": "Brésil", "Mexico": "Mexique", "Canada": "Canada",
}
AFC = {"BUF","MIA","NE","NYJ","BAL","CIN","CLE","PIT","HOU","IND","JAX","JAC","TEN","DEN","KC","LV","LAC"}
NFC = {"DAL","NYG","PHI","WSH","WAS","CHI","DET","GB","MIN","ATL","CAR","NO","TB","ARI","LAR","LA","SF","SEA"}

def current_nfl_season():
    override = os.getenv("NFL_SEASON")
    if override:
        return int(override)
    now = datetime.now(timezone.utc)
    return now.year - 1 if now.month <= 3 else now.year

def fetch_json(params):
    last = None

    for base_url in ESPN_URLS:
        url = f"{base_url}?{urlencode(params)}"

        for attempt in range(3):
            try:
                req = Request(
                    url,
                    headers={
                        "User-Agent": "curl/8.5.0",
                        "Accept": "application/json, text/plain, */*",
                    },
                )

                with urlopen(req, timeout=30) as r:
                    return json.load(r)

            except Exception as exc:
                last = exc

                if attempt < 2:
                    time.sleep(2 * (attempt + 1))

    raise RuntimeError(
        f"Impossible de récupérer les données ESPN après plusieurs essais: {last}"
    )

def score_value(c):
    s = (c or {}).get("score")
    if isinstance(s, dict):
        for k in ("displayValue","value"):
            if s.get(k) is not None:
                return str(s[k])
    return "" if s is None else str(s)

def get_competitors(event):
    comps = event.get("competitions") or []
    if not comps: return None, None, None
    comp = comps[0]
    competitors = comp.get("competitors") or []
    home = next((x for x in competitors if x.get("homeAway")=="home"), None)
    away = next((x for x in competitors if x.get("homeAway")=="away"), None)
    return home, away, comp

def abbreviation(c):
    team = (c or {}).get("team") or {}
    return (team.get("abbreviation") or team.get("shortDisplayName") or "").strip()

def team_name(c):
    team = (c or {}).get("team") or {}
    return (team.get("displayName") or team.get("shortDisplayName") or team.get("name") or "À déterminer").strip()

def is_completed(comp):
    status = (comp or {}).get("status") or {}
    return bool((status.get("type") or {}).get("completed"))

def french_country(raw, city=""):
    raw = (raw or "").strip()
    if raw: return COUNTRY_FR.get(raw, raw)
    return "États-Unis" if city else ""

def format_location(comp):
    venue = (comp or {}).get("venue") or {}
    stadium = (venue.get("fullName") or "").strip()
    address = venue.get("address") or {}
    city = (address.get("city") or "").strip()
    country = french_country(address.get("country"), city)
    if city and country and stadium: return f"{city} ({country}) - {stadium}"
    if city and stadium: return f"{city} - {stadium}"
    return stadium

def roman(n):
    pairs = [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),(50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
    out=[]
    for v,s in pairs:
        while n>=v:
            out.append(s); n-=v
    return "".join(out)

def playoff_stage(week, home_abbr, away_abbr, season):
    if week==1: return "Wild Card"
    if week==2: return "Divisional Round"
    if week==3:
        teams={home_abbr, away_abbr}
        if teams & AFC: return "AFC Championship"
        if teams & NFC: return "NFC Championship"
        return "Conference Championship"
    if week==5:
        return f"Super Bowl {roman(season-1965)}"
    return "Postseason"

def escape_ics(v):
    return str(v).replace("\\","\\\\").replace(";","\\;").replace(",","\\,").replace("\r","").replace("\n","\\n")

def fold_line(line, limit=73):
    if len(line.encode("utf-8"))<=limit: return [line]
    chunks=[]; current=""
    for ch in line:
        candidate=current+ch
        if current and len(candidate.encode("utf-8"))>limit:
            chunks.append(current); current=" "+ch
        else:
            current=candidate
    if current: chunks.append(current)
    return chunks

def make_summary(season_type, week, season, home, away, comp):
    hn, an = team_name(home), team_name(away)
    if season_type==1:
        if week == 1:
            prefix="NFL | 🏈 Hall of Fame Game"
        else:
            prefix=f"NFL | 🏈 Pré-saison J{week-1}"
    elif season_type==2:
        prefix=f"NFL | 🏈 J{week}"
    else:
        prefix=f"NFL | 🏈 {playoff_stage(week, abbreviation(home), abbreviation(away), season)}"
    if is_completed(comp):
        hs, a_s = score_value(home), score_value(away)
        matchup = f"{hn} {hs} - {a_s} {an}" if hs!="" and a_s!="" else f"{hn} - {an}"
    else:
        matchup=f"{hn} - {an}"
    return f"{prefix} - {matchup}"

def parse_start(v):
    return datetime.fromisoformat(v.replace("Z","+00:00")).astimezone(timezone.utc)

def wanted_event(event, season_type):
    home, away, _ = get_competitors(event)
    if not home or not away: return False
    if season_type==3: return True
    return bool({abbreviation(home),abbreviation(away)} & FOLLOWED_TEAMS)

def collect_events(season):
    collected={}
    ranges={1:range(1,6), 2:range(1,19), 3:(1,2,3,5)}
    for season_type,weeks in ranges.items():
        for week in weeks:
            data=fetch_json({"dates":season,"seasontype":season_type,"week":week,"limit":100})
            for event in data.get("events",[]):
                if not wanted_event(event,season_type): continue
                event_id=str(event.get("id") or "").strip()
                if event_id:
                    collected[event_id]={"event":event,"season_type":season_type,"week":week}
    return list(collected.values())

def write_calendar(items, season):
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prepared=[]
    for item in items:
        event=item["event"]; start_raw=event.get("date")
        if not start_raw: continue
        start=parse_start(start_raw); end=start+timedelta(hours=3)
        home,away,comp=get_competitors(event)
        prepared.append({
            "start":start, "end":end,
            "uid":f"nfl-{season}-{event['id']}@oliverthibaut-football-ical",
            "summary":make_summary(item["season_type"],item["week"],season,home,away,comp),
            "location":format_location(comp),
        })
    prepared.sort(key=lambda x:x["start"])
    lines=["BEGIN:VCALENDAR","VERSION:2.0","CALSCALE:GREGORIAN","METHOD:PUBLISH","PRODID:-//Oliver Thibaut//NFL Calendar//FR","X-WR-CALNAME:NFL","X-WR-TIMEZONE:Europe/Paris"]
    for item in prepared:
        lines += ["BEGIN:VEVENT",f"UID:{escape_ics(item['uid'])}",f"DTSTAMP:{stamp}",f"DTSTART:{item['start'].strftime('%Y%m%dT%H%M%SZ')}",f"DTEND:{item['end'].strftime('%Y%m%dT%H%M%SZ')}","SEQUENCE:0","STATUS:CONFIRMED","TRANSP:OPAQUE","CLASS:PUBLIC",f"SUMMARY:{escape_ics(item['summary'])}"]
        if item["location"]: lines.append(f"LOCATION:{escape_ics(item['location'])}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    folded=[]
    for line in lines: folded.extend(fold_line(line))
    OUTPUT.write_text("\r\n".join(folded)+"\r\n",encoding="utf-8")
    return prepared

def main():
    season=current_nfl_season()
    print(f"Saison NFL : {season}")
    print("Équipes suivies : 49ers, Rams, Chiefs, Bills")
    print("Postseason : tous les matchs à partir des Wild Cards")
    events=write_calendar(collect_events(season),season)
    print(f"Événements générés : {len(events)}")
    print(f"Fichier : {OUTPUT.name}")
    for e in events[:8]:
        print(e["start"].strftime("%Y-%m-%d %H:%M UTC"),"|",e["summary"])

if __name__=="__main__":
    main()
