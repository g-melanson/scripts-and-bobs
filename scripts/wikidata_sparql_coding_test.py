import json, re, time
from dataclasses import dataclass, asdict
from urllib.parse import urlencode
from urllib.request import Request, urlopen


INTENTS = [
    (re.compile(r"(?:how old is|what age is)\s+(.+?)\??$", re.IGNORECASE), "P569", "age"),
    (re.compile(r"(?:what is the population of|population of)\s+(.+?)\??$", re.IGNORECASE), "P1082", "pop"),
]
HEADERS = {"User-Agent": "wikidata-ask/1.0"}
WIKIDATA_ENTITIES_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


@dataclass
class WikiDataEntitiesAPIConfig:
    search: str
    action: str = "wbsearchentities"
    format: str = "json"
    language: str = "en"
    limit: int = 1


@dataclass
class WikiDataSPARQLConfig:
    query: str
    format: str = "json"


def _url(endpoint, config, sep: str = "?"):
    return f"{endpoint}{sep}{urlencode(asdict(config))}"


def _get(url):
    time.sleep(1) 
    with urlopen(Request(url, headers=HEADERS)) as r:
        return json.loads(r.read().decode())


def _qid(name):
    _config = WikiDataEntitiesAPIConfig(search=name)
    data = _get(_url(endpoint=WIKIDATA_ENTITIES_API, config=_config))
    return data["search"][0]["id"]


def _sparql(query):
    _config = WikiDataSPARQLConfig(query=query)
    data = _get(_url(endpoint=WIKIDATA_SPARQL_ENDPOINT, config=_config))
    return data["results"]["bindings"]


def ask(question: str) -> str | None:
    for pattern, pid, intent in INTENTS:
        intent = pattern.search(question)
        if not intent:
            continue
        qid = _qid(intent.group(1).strip())
        query = (
            f"SELECT (YEAR(NOW())-YEAR(?v) AS ?value) WHERE {{wd:{qid} wdt:{pid} ?v}} LIMIT 1"
            if intent == "age" else
            f"SELECT ?value WHERE {{wd:{qid} wdt:{pid} ?value}} ORDER BY DESC(?value) LIMIT 1"
        )
        rows = _sparql(query)
        return str(int(float(rows[0]["value"]["value"]))) if rows else None
    return None


if __name__ == "__main__":
    assert "48" == ask("how old is Usher")
    assert "63" == ask("what age is Brad Pitt?")
    assert "8799728" == ask("what is the population of London")
    assert "20201249" == ask("what is the population of New York?")
    print("All assertions passed")
