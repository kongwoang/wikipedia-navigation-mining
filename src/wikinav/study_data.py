"""Historical SQL/Parquet preparation; held-out files have separate entry point.

DuckDB is embedded and bounded to 4 GB, not a deployed database service.
Titles resolve only through the author's frozen ResolvedRedirects artifact.
"""

from collections import Counter
import csv
from dataclasses import dataclass
import gzip
import json
from pathlib import Path
import time
import tomllib

import duckdb
import numpy as np
from scipy import sparse

from .utils import digest, file_digest, write_json
from .redirects import latest_redirects, resolve_targets


def literal(value) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def study_config(path: Path) -> dict:
    with path.open("rb") as f:
        c = tomllib.load(f)
    months = c["train_months"] + [c["validation_month"]] + c["test_months"]
    if months != sorted(set(months)) or c["snapshot"][:7] > c["train_months"][-1]:
        raise ValueError("Invalid temporal study protocol")
    if c["graph_sampling"] != "induced_query_outgoing_closure":
        raise ValueError("Unsupported graph sampling")
    return c


def connection(path: Path):
    con = duckdb.connect(str(path))
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=4")
    con.execute("SET TimeZone='UTC'")
    con.execute("SET preserve_insertion_order=false")
    return con


def scalar(con, query):
    return con.execute(query).fetchone()[0]


def click_table(con, path: Path, minimum: int, duplicate_policy="error") -> dict:
    con.execute(f"""CREATE OR REPLACE TEMP TABLE clicks AS
        SELECT nfc_normalize(replace(prev,'_',' ')) AS prev,
               nfc_normalize(replace(curr,'_',' ')) AS curr, type, n,
               prev AS prev_raw, curr AS curr_raw
        FROM read_csv({literal(path)}, delim='\\t', header=false, quote='',
        columns={{'prev':'VARCHAR','curr':'VARCHAR','type':'VARCHAR','n':'BIGINT'}})""")
    invalid = scalar(con, f"""SELECT count(*) FROM clicks WHERE n IS NULL OR n < {minimum}
          OR prev IS NULL OR curr IS NULL OR type IS NULL OR type NOT IN ('link','external','other')""")
    duplicate = scalar(con, """SELECT count(*) FROM
        (SELECT prev_raw,curr_raw,type,count(*) n FROM clicks GROUP BY ALL HAVING n>1)""")
    if duplicate_policy not in ('error','quarantine'):
        raise ValueError('Unknown duplicate policy')
    if invalid or (duplicate and duplicate_policy=='error'):
        raise ValueError(f"Invalid/duplicate Clickstream records: {invalid}/{duplicate}")
    rows = con.execute("SELECT type,count(*),sum(n),min(n),max(n) FROM clicks GROUP BY type").fetchall()
    duplicate_rows=duplicate_mass=0
    if duplicate:
        con.execute('''CREATE OR REPLACE TEMP TABLE duplicate_keys AS
            SELECT prev_raw,curr_raw,type FROM clicks GROUP BY ALL HAVING count(*)>1''')
        duplicate_rows,duplicate_mass=con.execute('''SELECT count(*),sum(c.n) FROM clicks c
            JOIN duplicate_keys d USING(prev_raw,curr_raw,type)''').fetchone()
        con.execute('DELETE FROM clicks USING duplicate_keys d WHERE clicks.prev_raw=d.prev_raw AND clicks.curr_raw=d.curr_raw AND clicks.type=d.type')
    con.execute("""CREATE OR REPLACE TEMP TABLE matched AS
        SELECT c.*, p.canonical AS source, q.canonical AS target
        FROM clicks c LEFT JOIN titlemap p ON c.prev=p.title
        LEFT JOIN titlemap q ON c.curr=q.title""")
    ledger = con.execute("""SELECT
        CASE WHEN type!='link' THEN 'non_link'
             WHEN source IS NULL OR target IS NULL THEN 'unmapped'
             WHEN source=target THEN 'self_loop' ELSE 'kept' END AS reason,
        count(*) row_count,sum(n) mass FROM matched GROUP BY reason ORDER BY reason""").fetchall()
    if duplicate:
        ledger.append(('duplicate_raw_quarantined',duplicate_rows,duplicate_mass))
    return {"file": path.name, "duplicate_key_groups":duplicate, "types": [
        dict(zip(("type", "rows", "mass", "min", "max"), row)) for row in rows],
        "ledger": {r: {"rows": n, "mass": mass} for r, n, mass in ledger}}


def prepare(raw: Path, output: Path, config_path: Path) -> dict:
    c = study_config(config_path)
    if output.exists():
        raise FileExistsError("Preparation output exists; use a new version")
    output.mkdir(parents=True)
    start = time.perf_counter()
    con = connection(output / "study.duckdb")
    metadata = raw / "eswiki.snapshot.resolve_redirect.2018-03-01.csv.gz"
    topology = raw / "eswiki.wikilink_graph.2018-03-01.csv.gz"
    # Only train/graph inputs are fingerprinted here. No held-out content is parsed.
    redirects_path = raw / "eswiki.redirects.20180301.csv.gz"
    input_paths = [metadata, topology, redirects_path] + [raw / f"clickstream-eswiki-{m}.tsv.gz" for m in c["train_months"]]
    inputs = {p.name: {"sha256": file_digest(p), "bytes": p.stat().st_size} for p in input_paths}
    print("prepare: historical mapping", flush=True)
    con.execute(f"""CREATE TABLE metadata AS SELECT * FROM read_csv(
        {literal(metadata)}, header=true, all_varchar=true)""")
    expected = ["page_id", "page_title", "revision_id", "revision_parent_id", "revision_timestamp",
                "redirect_id", "redirect_title", "redirect_revision_id",
                "redirect_revision_parent_id", "redirect_revision_timestamp"]
    if [r[0] for r in con.execute("DESCRIBE metadata").fetchall()] != expected:
        raise ValueError("Unexpected ResolvedRedirects schema")
    con.execute("""CREATE TABLE archived_pages AS SELECT cast(page_id AS BIGINT) AS id,
        nfc_normalize(replace(page_title,'_',' ')) AS title,
        cast(redirect_id AS BIGINT) AS canonical,
        nfc_normalize(replace(redirect_title,'_',' ')) AS canonical_title,
        revision_timestamp, redirect_revision_timestamp FROM metadata""")
    if scalar(con, "SELECT count(*)-count(DISTINCT id) FROM archived_pages"):
        raise ValueError("Duplicate page IDs")
    invalid = scalar(con, f"""SELECT count(*) FROM archived_pages WHERE id IS NULL
        OR title IS NULL OR id<=0 OR try_cast(revision_timestamp AS TIMESTAMPTZ) IS NULL
        OR cast(revision_timestamp AS TIMESTAMPTZ)>cast({literal(c['snapshot'])} AS TIMESTAMPTZ)""")
    if invalid:
        raise ValueError(f"Invalid/future mapping rows: {invalid}")
    # The supplied ResolvedRedirects has verified missed aliases. Rebuild from event history.
    states, redirect_audit = latest_redirects(redirects_path, c['snapshot'])
    state_path = output/'redirect_states.csv'
    with state_path.open('x', newline='', encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['id','target'])
        writer.writerows(sorted(states.items()))
    del states
    con.execute(f'''CREATE TABLE redirect_states AS SELECT * FROM read_csv({literal(state_path)},
        header=true,delim=',',quote='"',escape='"',columns={{'id':'BIGINT','target':'VARCHAR'}})''')
    con.execute("""CREATE TABLE unique_titles AS SELECT title,min(id) id FROM archived_pages
        GROUP BY title HAVING count(*)=1""")
    con.execute("""CREATE TABLE target_links AS SELECT s.id,coalesce(t.id,u.id) AS target_id FROM redirect_states s
        JOIN archived_pages p ON s.id=p.id
        LEFT JOIN unique_titles t ON s.target=t.title
        LEFT JOIN unique_titles u ON concat(upper(substr(s.target,1,1)),substr(s.target,2))=u.title
        WHERE s.target!='#NOREDIRECT'""")
    targets = dict(con.execute('SELECT id,target_id FROM target_links').fetchall())
    resolved, statuses = resolve_targets(targets)
    redirect_audit['resolution_status'] = dict(Counter(statuses.values()))
    redirect_audit['redirect_nodes_in_inventory'] = len(targets)
    resolution_path=output/'redirect_resolution.csv'
    with resolution_path.open('x',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['id','canonical','status'])
        writer.writerows((node,resolved[node],statuses[node]) for node in sorted(resolved))
    del targets, resolved, statuses
    con.execute(f"CREATE TABLE resolution AS SELECT * FROM read_csv({literal(resolution_path)},header=true,columns={{'id':'BIGINT','canonical':'BIGINT','status':'VARCHAR'}})")
    con.execute("""CREATE TABLE pages AS SELECT p.id,p.title,
        CASE WHEN r.id IS NULL THEN p.id ELSE r.canonical END canonical
        FROM archived_pages p LEFT JOIN resolution r ON p.id=r.id""")
    redirect_audit['disagreements_with_supplied_mapping']=scalar(con,
        'SELECT count(*) FROM pages p JOIN archived_pages a ON p.id=a.id WHERE p.canonical IS DISTINCT FROM a.canonical')
    redirect_audit['quarantined_pages']=scalar(con,'SELECT count(*) FROM pages WHERE canonical IS NULL')
    ambiguous = scalar(con, """SELECT count(*) FROM
        (SELECT title,count(DISTINCT canonical) n FROM pages GROUP BY title HAVING n>1)""")
    con.execute("""CREATE TABLE titlemap AS SELECT title,min(canonical) canonical FROM pages
        GROUP BY title HAVING count(DISTINCT canonical)=1 AND count(*)=count(canonical)""")
    print("prepare: independent hyperlink graph", flush=True)
    with gzip.open(topology, "rt", encoding="utf-8") as stream:
        if stream.readline().rstrip("\r\n").split("\t") != [
                "page_id_from", "page_title_from", "page_id_to", "page_title_to"]:
            raise ValueError("Unexpected historical hyperlink header")
    con.execute(f"""CREATE TABLE raw_h AS SELECT * FROM read_csv({literal(topology)},
        delim='\\t',header=true,quote='',
        columns={{'s':'BIGINT','st':'VARCHAR','t':'BIGINT','tt':'VARCHAR'}})""")
    raw_edges = scalar(con, "SELECT count(*) FROM raw_h")
    con.execute("""CREATE TABLE mapped_h AS SELECT p.canonical s,q.canonical t
        FROM raw_h h LEFT JOIN pages p ON h.s=p.id LEFT JOIN pages q ON h.t=q.id
        WHERE p.id=p.canonical OR p.canonical IS NULL""")
    graph_unmapped = scalar(con, "SELECT count(*) FROM mapped_h WHERE s IS NULL OR t IS NULL")
    self_loops = scalar(con, "SELECT count(*) FROM mapped_h WHERE s=t")
    con.execute("CREATE TABLE h AS SELECT DISTINCT s,t FROM mapped_h WHERE s IS NOT NULL AND t IS NOT NULL AND s!=t")
    con.execute("CREATE TABLE degrees AS SELECT s,count(*) degree FROM h GROUP BY s")
    con.execute("CREATE TABLE incoming AS SELECT t,count(*) degree FROM h GROUP BY t")
    con.execute("CREATE TABLE train_monthly(month VARCHAR,s BIGINT,t BIGINT,n BIGINT)")
    train_audits = []
    for month in c["train_months"]:
        print(f"prepare: train {month}", flush=True)
        audit = click_table(con, raw / f"clickstream-eswiki-{month}.tsv.gz", c["minimum_published_count"],c.get('duplicate_policy','error'))
        train_audits.append(audit)
        con.execute(f"""INSERT INTO train_monthly SELECT {literal(month)},source,target,sum(n)
            FROM matched WHERE type='link' AND source IS NOT NULL AND target IS NOT NULL
            AND source!=target GROUP BY source,target""")
    con.execute("CREATE TABLE train AS SELECT s,t,sum(n)::BIGINT n FROM train_monthly GROUP BY s,t")
    con.execute("CREATE TABLE traffic AS SELECT s,sum(n) traffic FROM train GROUP BY s")
    con.execute("CREATE TABLE popularity AS SELECT t,sum(n) n FROM train GROUP BY t")
    con.execute(f"""CREATE TABLE query_pool AS SELECT d.s,d.degree,coalesce(t.traffic,0) traffic,
        CASE WHEN coalesce(t.traffic,0)=0 THEN 0 WHEN t.traffic<100 THEN 1
             WHEN t.traffic<1000 THEN 2 ELSE 3 END stratum
        FROM degrees d LEFT JOIN traffic t ON d.s=t.s
        WHERE d.degree BETWEEN {int(c['query_degree_min'])} AND {int(c['query_degree_max'])}""")
    con.execute(f"""CREATE TABLE queries AS SELECT s,degree,traffic,stratum FROM
        (SELECT *,row_number() OVER (PARTITION BY stratum ORDER BY
         sha256(concat({literal(c['seed'])},':',s::VARCHAR)),s) rank FROM query_pool)
        WHERE rank<={int(c['query_per_stratum'])}""")
    con.execute("""CREATE TABLE sample_nodes AS
        SELECT s id FROM queries UNION SELECT h.t id FROM h JOIN queries q ON h.s=q.s""")
    n = scalar(con, "SELECT count(*) FROM sample_nodes")
    if n > c["max_sample_nodes"]:
        raise ValueError(f"Outgoing closure has {n} nodes; budget exceeded before validation/test")
    con.execute("""CREATE TABLE sample_h AS SELECT h.s,h.t FROM h
        JOIN sample_nodes a ON h.s=a.id JOIN sample_nodes b ON h.t=b.id""")
    m = scalar(con, "SELECT count(*) FROM sample_h")
    if m > c["max_sample_edges"]:
        raise ValueError(f"Sample edges {m} exceed resource gate")
    con.execute("""CREATE TABLE node_features AS SELECT s.id,p.title,
        coalesce(d.degree,0) out_degree_full,coalesce(i.degree,0) in_degree_full,
        coalesce(t.traffic,0) traffic,coalesce(g.n,0) popularity
        FROM sample_nodes s JOIN pages p ON s.id=p.id
        LEFT JOIN degrees d ON s.id=d.s LEFT JOIN incoming i ON s.id=i.t
        LEFT JOIN traffic t ON s.id=t.s LEFT JOIN popularity g ON s.id=g.t""")
    for name, sql in {
        "nodes": "SELECT * FROM node_features ORDER BY id",
        "edges": "SELECT * FROM sample_h ORDER BY s,t",
        "queries": "SELECT * FROM queries ORDER BY s",
        "train": """SELECT tr.* FROM train_monthly tr JOIN sample_nodes a ON tr.s=a.id
                    JOIN sample_nodes b ON tr.t=b.id ORDER BY month,s,t""",
    }.items():
        con.execute(f"COPY ({sql}) TO {literal(output / (name+'.parquet'))} (FORMAT PARQUET)")
    full = {
        "metadata_rows": scalar(con, "SELECT count(*) FROM pages"),
        "mapping_nonidentity_rows": scalar(con, "SELECT count(*) FROM pages WHERE id!=canonical"),
        "canonical_nodes": scalar(con, "SELECT count(*) FROM pages WHERE id=canonical"),
        "ambiguous_titles_quarantined": ambiguous, "raw_h_edges": raw_edges,
        "h_unmapped_edges": graph_unmapped, "h_self_loops": self_loops,
        "h_unique_edges": scalar(con, "SELECT count(*) FROM h"),
        "sample_nodes": n, "sample_edges": m,
        "queries": scalar(con, "SELECT count(*) FROM queries"),
        "sample_outgoing_full_edges": scalar(con, "SELECT count(*) FROM h JOIN sample_nodes a ON h.s=a.id"),
        "query_pool_by_stratum": con.execute("SELECT stratum,count(*) FROM query_pool GROUP BY stratum ORDER BY stratum").fetchall(),
        "query_sample_by_stratum": con.execute("SELECT stratum,count(*) FROM queries GROUP BY stratum ORDER BY stratum").fetchall(),
        "train_pairs": scalar(con, "SELECT count(*) FROM train"),
        "train_mass": scalar(con, "SELECT sum(n) FROM train"),
        "train_h_matched_mass": scalar(con, "SELECT sum(tr.n) FROM train tr JOIN h ON tr.s=h.s AND tr.t=h.t"),
        "train_h_matched_pairs": scalar(con, "SELECT count(*) FROM train tr JOIN h ON tr.s=h.s AND tr.t=h.t"),
        "sample_train_rows": scalar(con, f"SELECT count(*) FROM read_parquet({literal(output/'train.parquet')})"),
    }
    result = {"protocol": c, "config_sha256": file_digest(config_path), "inputs": inputs,
              "scope": "sample-conditional induced outgoing closure; not full-graph PPR",
              "mapping_policy": "latest raw redirect event per page <= UTC snapshot; resolve chains; quarantine cycles/dangling; exclude redirect sources",
              "redirect_audit": redirect_audit,
              "full": full, "training_audits": train_audits,
              "artifacts": {p.name: file_digest(p) for p in output.glob("*.parquet")},
              "elapsed_seconds": time.perf_counter()-start}
    con.execute("CHECKPOINT")
    con.close()
    write_json(output / "manifest.json", result)
    return result


def heldout(raw: Path, prepared: Path, month: str) -> tuple[dict, dict]:
    """Call only after validation selection (test), from evaluator."""
    manifest = json.loads((prepared / "manifest.json").read_text())
    c = manifest["protocol"]
    if month not in [c["validation_month"], *c["test_months"]]:
        raise ValueError("Unexpected evaluation period")
    con = connection(prepared / "study.duckdb")
    audit = click_table(con, raw / f"clickstream-eswiki-{month}.tsv.gz", c["minimum_published_count"],c.get('duplicate_policy','error'))
    # Unknown targets retained as stable title labels in full denominator.
    rows = con.execute("""SELECT source,
        CASE WHEN target IS NULL THEN concat('oov:',curr) ELSE target::VARCHAR END target_label,
        sum(n) n FROM matched JOIN queries ON source=queries.s
        WHERE type='link' AND (target IS NULL OR source!=target) GROUP BY source,target_label""").fetchall()
    labels = {}
    for source, target, count in rows:
        labels.setdefault(str(source), {})[target] = count
    audit["input_sha256"] = file_digest(raw / f"clickstream-eswiki-{month}.tsv.gz")
    con.close()
    return labels, audit


@dataclass
class StudyData:
    ids: list[str]
    titles: list[str]
    adjacency: sparse.csr_matrix
    counts: sparse.csr_matrix
    queries: list[int]
    features: dict
    manifest: dict

    def candidates(self, source: int) -> np.ndarray:
        return self.adjacency.indices[self.adjacency.indptr[source]:self.adjacency.indptr[source+1]]


def load_study(prepared: Path, months=None) -> StudyData:
    con = duckdb.connect()
    nodes = con.execute(f"SELECT * FROM read_parquet({literal(prepared/'nodes.parquet')}) ORDER BY id").fetchnumpy()
    ids = [str(x) for x in nodes["id"]]
    index = {int(node): i for i, node in enumerate(ids)}
    n = len(ids)
    edges = con.execute(f"SELECT * FROM read_parquet({literal(prepared/'edges.parquet')})").fetchnumpy()
    s = np.fromiter((index[int(i)] for i in edges["s"]), dtype=np.int32)
    t = np.fromiter((index[int(i)] for i in edges["t"]), dtype=np.int32)
    a = sparse.csr_matrix((np.ones(len(s)), (s, t)), shape=(n, n))
    query = f"SELECT s,t,sum(n)::BIGINT n FROM read_parquet({literal(prepared/'train.parquet')})"
    if months is not None:
        query += " WHERE month IN (" + ",".join(map(literal, months)) + ")"
    rows = con.execute(query + " GROUP BY s,t").fetchnumpy()
    s = np.fromiter((index[int(i)] for i in rows["s"]), dtype=np.int32)
    t = np.fromiter((index[int(i)] for i in rows["t"]), dtype=np.int32)
    counts = sparse.csr_matrix((rows["n"], (s, t)), shape=(n, n))
    q = con.execute(f"SELECT s FROM read_parquet({literal(prepared/'queries.parquet')}) ORDER BY s").fetchall()
    con.close()
    if months is not None:
        # History-size ablation must not use full-window global priors or traffic.
        con = connection(prepared / "study.duckdb")
        condition = ",".join(map(literal, months))
        popularity = dict(con.execute(f"SELECT t,sum(n) FROM train_monthly WHERE month IN ({condition}) GROUP BY t").fetchall())
        traffic = dict(con.execute(f"SELECT s,sum(n) FROM train_monthly WHERE month IN ({condition}) GROUP BY s").fetchall())
        nodes["popularity"] = np.array([popularity.get(int(node), 0) for node in ids], dtype=np.int64)
        nodes["traffic"] = np.array([traffic.get(int(node), 0) for node in ids], dtype=np.int64)
        con.close()
    return StudyData(ids, list(nodes["title"]), a, counts, [index[int(i)] for i, in q],
                     {key: nodes[key] for key in ("out_degree_full", "in_degree_full", "traffic", "popularity")},
                     json.loads((prepared / "manifest.json").read_text()))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("data/raw/eswiki"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/study-v2"))
    parser.add_argument("--config", type=Path, default=Path("configs/study.toml"))
    args = parser.parse_args()
    print(json.dumps(prepare(args.raw, args.output, args.config), ensure_ascii=False, indent=2))
