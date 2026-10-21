"""Validation selection, frozen predictions, then held-out evaluation.

Resume only model caches with identical code/config/data signatures. A completed
test evaluation is never overwritten or used to expand the search space.
"""

import csv
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np

from .embeddings import train_embedding
from .evaluation import aggregate_results, evaluate_source, paired_bootstrap
from .ranking import rank_candidates
from .sparse_models import baseline_scores, fusion, hits_scores, ppr_scores, transitions
from .study_data import heldout, load_study, study_config
from .utils import digest, file_digest, write_json


def predictions(data, scores, seed):
    result = {}
    for source in data.queries:
        candidates = [data.ids[i] for i in data.candidates(source)]
        values = {target: float(score) for target, score in zip(candidates,scores[source],strict=True)}
        result[data.ids[source]] = {
            "ranked": rank_candidates(data.ids[source], candidates, values, k=20, seed=seed),
            "scores": values,
        }
    return result


def evaluate(data, prediction, labels):
    rows = [
        evaluate_source(data.ids[s], [data.ids[i] for i in data.candidates(s)],
                        prediction[data.ids[s]]["ranked"], labels.get(data.ids[s], {}))
        for s in data.queries]
    return aggregate_results(rows), [r.as_dict() for r in rows]


def macro_value(data, scores, labels, seed):
    summary, _ = evaluate(data,predictions(data,scores,seed),labels)
    value = summary["all"]["ndcg@10"]["macro"]
    if value is None:
        raise ValueError("No observable validation labels; cannot select models")
    return value


def algorithm_hash():
    folder = Path(__file__).parent
    return digest({name: file_digest(folder/name) for name in (
        "experiment.py","embeddings.py","sparse_models.py","study_data.py","redirects.py",
        "evaluation.py","ranking.py","utils.py")})


def save_table(path, rows):
    if not rows:
        return
    with path.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(raw: Path, prepared: Path, output: Path, config_path: Path):
    start = time.perf_counter()
    c = study_config(config_path)
    data = load_study(prepared)
    if data.manifest["config_sha256"] != file_digest(config_path):
        raise ValueError("Preparation and experiment configs differ")
    for name, sha in data.manifest["artifacts"].items():
        if file_digest(prepared/name) != sha:
            raise ValueError("Prepared artifact changed")
    output.mkdir(parents=True,exist_ok=True)
    if (output/"test_results.json").exists():
        raise FileExistsError("Test results exist; use analysis command, do not rerun/tune against test")
    signature = {"config":file_digest(config_path),"data":file_digest(prepared/"manifest.json"),
                 "code":algorithm_hash(),"python":platform.python_version(),
                 "run_protocol":file_digest(Path(__file__).resolve().parents[2]/"docs/RUN_PROTOCOL.md"),
                 "dependency_lock":file_digest(Path(__file__).resolve().parents[2]/"requirements-study.lock"),
                 "native_patch_installer":file_digest(Path(__file__).resolve().parents[2]/"scripts/install_gensim_fix.py"),
                 "dependencies":{name:importlib.metadata.version(name) for name in
                                 ('numpy','scipy','gensim','duckdb')}}
    if (output/"run_signature.json").exists():
        if json.loads((output/"run_signature.json").read_text()) != signature:
            raise ValueError("Cache signature changed; start a new run before opening test")
    else:
        write_json(output/"run_signature.json",signature)
    cache=output/"cache"; cache.mkdir(exist_ok=True)
    validation, validation_audit=heldout(raw,prepared,c["validation_month"])
    write_once(output/"validation_audit.json",validation_audit)
    trials=[]; selected={}; model_info={}; scores_by_model={}

    def cached(name,params,compute):
        key=digest({"name":name,"params":params})[:24]
        file=cache/(key+".npz"); meta=cache/(key+".json")
        if file.exists() and meta.exists():
            with np.load(file,allow_pickle=False) as saved:
                scores={s:saved[str(s)].copy() for s in data.queries}
            info=json.loads(meta.read_text())
        else:
            print(f"fit {name} {params}",flush=True)
            before=time.perf_counter()
            scores,info=compute()
            info={"details":info,"wall_seconds":time.perf_counter()-before}
            np.savez_compressed(file,**{str(s):score for s,score in scores.items()})
            write_once(meta,info)
        return scores,info

    def choose(name, options):
        best=None
        for params, compute in options:
            scores,info=cached(name,params,compute)
            value=macro_value(data,scores,validation,c["seed"])
            trials.append({"model":name,"parameters":json.dumps(params,sort_keys=True),
                           "validation_macro_ndcg_all@10":value,"seconds":info["wall_seconds"]})
            if best is None or value>best[0]+1e-15:
                best=(value,params,scores,info)
        _,params,scores,info=best
        selected[name]=params; scores_by_model[name]=scores; model_info[name]=info
        print(f"selected {name}: {params}; validation NDCG={best[0]:.6f}",flush=True)

    for name,kind in (("M0_global","global"),("M1_local","local"),("M2_uniform","uniform"),("M2D_indegree","indegree")):
        choose(name,[({},lambda kind=kind:(baseline_scores(data,kind),{}))])
    choose("M1B_backoff",[
        ({"mu":mu,"eta":eta},lambda mu=mu,eta=eta:(baseline_scores(data,"backoff",mu,eta),{}))
        for mu in c["mu"] for eta in c["eta"]])
    # No dense N*N matrix: each solver keeps one source vector and caches candidate scores.
    for name,mode in (("M3_ppr_h","H"),("M4C_ppr_c","C"),("M4CH_ppr_ch","CH"),("M4H_ppr_wh","WH")):
        matrix=transitions(data,mode,mu=c["controlled_weight_mu"])
        choose(name,[({"damping":d,"mode":mode,"mu":c["controlled_weight_mu"]},
                      lambda d=d,matrix=matrix:ppr_scores(data,matrix,d,c["residual_tolerance"],c["max_iterations"]))
                     for d in c["damping"]])
    choose("M6B_fusion",[
        ({"lambda":w},lambda w=w:(fusion(scores_by_model["M1B_backoff"],scores_by_model["M3_ppr_h"],w),{}))
        for w in c["lambda"]])
    choose("M6A_matrix",[
        ({"lambda":w,"damping":c["controlled_damping"]},
         lambda w=w:ppr_scores(data,transitions(data,"MIX",mixing=w),c["controlled_damping"],c["residual_tolerance"],c["max_iterations"]))
        for w in c["lambda"]])
    choose("HITS",[({},lambda:hits_scores(data))])
    # Fixed-damping support-preserving ablation; not additional test-selected models.
    for name,mode in (("A4_H","H"),("A4_WH","WH"),("A4_CH","CH")):
        params={"damping":c["controlled_damping"],"mu":c["controlled_weight_mu"],"mode":mode}
        scores,info=cached(name,params,lambda mode=mode:ppr_scores(
            data,transitions(data,mode,mu=c["controlled_weight_mu"]),c["controlled_damping"],c["residual_tolerance"],c["max_iterations"]))
        selected[name]=params; scores_by_model[name]=scores; model_info[name]=info
    embedding_fixed={"walks":c["embedding_walks"],"length":c["embedding_walk_length"],
                     "window":c["embedding_window"],"epochs":c["embedding_epochs"],
                     "negative":c["embedding_negative"]}
    def embedding_compute(matrix,params):
        scores,_,info=train_embedding(data,matrix,**params,**embedding_fixed)
        return scores,info
    for name,mode in (("M5H_node2vec","H"),("M5W_node2vec","WH")):
        matrix=transitions(data,mode,mu=c["embedding_weight_mu"])
        choose(name,[
            ({"dimension":dim,"p":p,"q":q,"seed":c["embedding_seeds"][0]},
             lambda dim=dim,p=p,q=q,matrix=matrix:embedding_compute(matrix,
                 {"dimension":dim,"p":p,"q":q,"seed":c["embedding_seeds"][0]}))
            for dim in c["embedding_dimensions"] for p,q in c["embedding_pq"]])
        # Same selected knobs, seeds fixed a priori. No best-test-seed selection.
        for seed in c["embedding_seeds"][1:]:
            params={**selected[name],"seed":seed}
            key=f"{name}_s{seed}"
            scores,info=cached(key,params,lambda params=params,matrix=matrix:embedding_compute(matrix,params))
            selected[key]=params; scores_by_model[key]=scores; model_info[key]=info
    # A5 controls embedding architecture and seed as well as graph support.
    params=selected["M5H_node2vec"].copy()
    scores,info=cached("A5_weighted_matched",params,lambda:embedding_compute(
        transitions(data,"WH",mu=c["embedding_weight_mu"]),params))
    selected["A5_weighted_matched"]=params
    scores_by_model["A5_weighted_matched"]=scores; model_info["A5_weighted_matched"]=info
    # History ablation: trailing windows; frozen graph/query set, recomputed behavior/global priors.
    for length in (1,2):
        months=c["train_months"][-length:]
        shorter=load_study(prepared,months)
        for kind,base in (("local","M1_local"),("backoff","M1B_backoff")):
            params={"months":months,**(selected[base] if kind=="backoff" else {})}
            key=f"A8_{base}_{length}month"
            b=baseline_scores(shorter,kind,**(selected[base] if kind=="backoff" else {}))
            scores_by_model[key]=b; selected[key]=params; model_info[key]={"wall_seconds":None}
            if kind=="backoff":
                key=f"A8_fusion_{length}month"
                scores_by_model[key]=fusion(b,scores_by_model["M3_ppr_h"],selected["M6B_fusion"]["lambda"])
                selected[key]=params; model_info[key]={"wall_seconds":None}
    prediction={name:predictions(data,scores,c["seed"]) for name,scores in scores_by_model.items()}
    validation_results={name:evaluate(data,p,validation)[0] for name,p in prediction.items()}
    freeze={"signature":signature,"selected":selected,"selection":"validation macro NDCG full@10; ties <=1e-15 keep first declared grid option",
            "failure_policy":"fail run before test; no model-specific source removal",
            "queries":[data.ids[i] for i in data.queries],
            "candidates_hash":digest({data.ids[s]:[data.ids[i] for i in data.candidates(s)] for s in data.queries}),
            "prepared_artifacts":data.manifest["artifacts"],
            "test_periods":c["test_months"],"fixed_embedding_settings":embedding_fixed,
            "tie_seed":c["seed"],"scope":data.manifest["scope"],
            "git_commit":subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True).stdout.strip(),
            "git_dirty":bool(subprocess.run(["git","status","--porcelain"],capture_output=True,text=True).stdout)}
    write_once(output/"validation_results.json",validation_results)
    if not (output/"validation_trials.csv").exists():
        save_table(output/"validation_trials.csv",trials)
    write_once(output/"model_diagnostics.json",model_info)
    write_once(output/"freeze.json",freeze)
    write_once(output/"predictions.json",prediction)
    # Critical barrier: first test label read AFTER selection and all predictions are durable.
    frozen_sha={p.name:file_digest(p) for p in (output/"freeze.json",output/"predictions.json")}
    test_results={}; source_metrics={}; audits={}
    for month in c["test_months"]:
        labels,audit=heldout(raw,prepared,month)
        audits[month]=audit
        write_once(output/f"labels-{month}.json",labels)
        test_results[month]={}; source_metrics[month]={}
        for name,p in prediction.items():
            summary,rows=evaluate(data,p,labels)
            test_results[month][name]=summary; source_metrics[month][name]=rows
    for name,sha in frozen_sha.items():
        if file_digest(output/name)!=sha:
            raise RuntimeError("Frozen artifact changed")
    write_once(output/"test_audits.json",audits)
    write_once(output/"source_metrics.json",source_metrics)
    write_once(output/"test_results.json",test_results)
    contrasts={}
    for month,models in source_metrics.items():
        contrasts[month]={}
        for left,right in (("M6B_fusion","M1B_backoff"),("M3_ppr_h","M1B_backoff"),
                           ("A4_WH","A4_H"),("A5_weighted_matched","M5H_node2vec")):
            pair=[]
            for model in (left,right):
                pair.append({r["source"]:r["all_metrics"]["ndcg@10"] for r in models[model]
                             if r["all_metrics"]["ndcg@10"] is not None})
            contrasts[month][left+" - "+right]=paired_bootstrap(*pair,seed=c["seed"],resamples=c["bootstrap_resamples"])
    write_once(output/"paired_comparisons.json",contrasts)
    write_once(output/"completion.json",{"status":"complete","data_kind":"real_clickstream",
        "scope":data.manifest["scope"],"models":len(prediction),"queries":len(data.queries),
        "elapsed_seconds":time.perf_counter()-start,
        "artifacts":{p.name:file_digest(p) for p in output.glob("*.json")}})
    return test_results


def write_once(path,value):
    if path.exists():
        if json.loads(path.read_text()) != json.loads(json.dumps(value)):
            raise ValueError(f"Immutable artifact differs: {path.name}")
    else:
        write_json(path,value)


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--raw",type=Path,default=Path("data/raw/eswiki"))
    parser.add_argument("--prepared",type=Path,default=Path("data/processed/study-v2"))
    parser.add_argument("--output",type=Path,default=Path("results/study-v3"))
    parser.add_argument("--config",type=Path,default=Path("configs/study.toml"))
    args=parser.parse_args()
    run(args.raw,args.prepared,args.output,args.config)
