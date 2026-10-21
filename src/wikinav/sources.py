"""Bounded, resumable acquisition of the fixed historical study inputs."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from .utils import file_digest, write_json

BASE = "https://dumps.wikimedia.org/other/clickstream/"
REDIRECT_BASE = "https://cricca.disi.unitn.it/datasets/wikilinkgraphs-resolved-redirects/eswiki/20180301/"
CATALOG = [
    {"name": f"clickstream-eswiki-2018-{m:02d}.tsv.gz",
     "url": f"{BASE}2018-{m:02d}/clickstream-eswiki-2018-{m:02d}.tsv.gz",
     "bytes": size, "license": "CC0", "role": "train" if m < 4 else "validation" if m == 4 else "test"}
    for m, size in enumerate((35123848, 33883323, 37221600, 37817594, 39037289, 36221902), 1)
] + [
    {"name": "eswiki.wikilink_graph.2018-03-01.csv.gz",
     "url": "https://zenodo.org/records/2539424/files/eswiki.wikilink_graph.2018-03-01.csv.gz",
     "bytes": 477431253, "md5": "9f56ab28f123837c1f998d313d676b09",
     "license": "CC BY 4.0", "role": "historical_hyperlinks"},
    {"name": "eswiki.snapshot.resolve_redirect.2018-03-01.csv.gz",
     "url": REDIRECT_BASE + "eswiki.snapshot.resolve_redirect.2018-03-01.csv.gz",
     "sha512": "b7eff2d5cd88ad0380caccbfd7ca294fb95e5cc38d52c39b14e7e01c19008d3c342aee9817009b448d2ec13aa833a1e4883d5a1393e99f1a2eace06d3daff898",
     "checksum_source": REDIRECT_BASE + "eswiki.resolved-redirects.sha512sums.txt",
     "license": "CC BY 4.0", "role": "historical_mapping"},
    {"name": "eswiki.redirects.20180301.csv.gz",
     "url": "https://cricca.disi.unitn.it/datasets/wikilinkgraphs-redirects/eswiki/20180301/eswiki.redirects.20180301.csv.gz",
     "bytes": 38083785,
     "sha512": "8a4fda12e48379a516bde75b9c2dacdc7c229db2b8c00ee6ff8c41fa313937ae050741a540b30a6daf3fc24a265eeeee9f23c734000215f6bafc14aa3019ecb4",
     "checksum_source": "https://cricca.disi.unitn.it/datasets/wikilinkgraphs-redirects/eswiki/20180301/eswiki.redirects.sha512sums.txt",
     "license": "CC BY 4.0", "role": "raw_historical_redirect_events"},
]


# Exact bytes audited for the published historical benchmark.
PINNED_SHA256 = {
    "clickstream-eswiki-2018-01.tsv.gz": "4131d738c34a32befda41620e30b89d2c083d7cab945ceae521428e037768fa8",
    "clickstream-eswiki-2018-02.tsv.gz": "8886d7d75c65470cc3da317a9d1f7244cc859e3468197b6278361e281fa5a91d",
    "clickstream-eswiki-2018-03.tsv.gz": "80ce9555307003dd6490f742e6b754309ae20504b173de5a9ab05e3d379f9724",
    "clickstream-eswiki-2018-04.tsv.gz": "43025e1e975bbaaf453f56f686a7bf90e30c65e08901dca12a521ea7015e0bec",
    "clickstream-eswiki-2018-05.tsv.gz": "a6451093338b31cebb2dc97f5d4e7819c24ab97aa97d989f17aa4764ead24467",
    "clickstream-eswiki-2018-06.tsv.gz": "3ad57457df1a1f737466cf358f05dd2fa8a00f8df9456f35c0995be709d53fc2",
    "eswiki.wikilink_graph.2018-03-01.csv.gz": "5d0fba8c8500cd1e273b4c46f2d34d780cd30df20187e8e015fcd33d32fd8122",
    "eswiki.snapshot.resolve_redirect.2018-03-01.csv.gz": "201513b3c9cdd81b3614203460a3009f051cbfb23ed55982deca73a2d3895d0d",
    "eswiki.redirects.20180301.csv.gz": "4444d6da300b76d73cd825800ef9ba142abd734f73593ad974634ec5b3c2aa42"
}
for _source in CATALOG:
    _source["sha256"] = PINNED_SHA256[_source["name"]]


def acquire(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)

    def one(source):
        target = root / source["name"]
        if not target.exists():
            partial = target.with_suffix(target.suffix + ".part")
            subprocess.run(["curl", "-fLsS", "--retry", "3", "--connect-timeout", "30",
                            "--max-time", "3600", "--max-filesize", "600000000",
                            "-C", "-", source["url"], "-o", str(partial)], check=True)
            check_file(partial, source)
            partial.rename(target)
        check_file(target, source)
        result = {**source, "actual_bytes": target.stat().st_size,
                  "sha256": file_digest(target),
                  "verified_at": datetime.now(timezone.utc).isoformat()}
        print(json.dumps({"acquired": source["name"], "bytes": result["actual_bytes"]}), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=3) as pool:
        files = list(pool.map(one, CATALOG))
    result = {"files": files, "content_snapshot": "2018-03-01",
              "note": "Downloaded held-out bytes are opaque; only evaluator may parse test labels."}
    manifest = root / "manifest-v2.json"
    if not manifest.exists():
        write_json(manifest, result)
    else:
        previous = json.loads(manifest.read_text())
        if [(f["name"], f["sha256"]) for f in previous["files"]] != [
                (f["name"], f["sha256"]) for f in files]:
            raise ValueError("Existing acquisition manifest differs")
    return result


def check_file(path: Path, source: dict) -> None:
    if "bytes" in source and path.stat().st_size != source["bytes"]:
        raise ValueError(f"Byte mismatch: {source['name']}")
    for algorithm in ("md5", "sha512", "sha256"):
        if algorithm in source:
            h = hashlib.new(algorithm)
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(chunk)
            if h.hexdigest() != source[algorithm]:
                raise ValueError(f"{algorithm} mismatch: {source['name']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/raw/eswiki"))
    acquire(parser.parse_args().output)
