"""Frozen extension experiments. Predictions precede every new-period label read."""
from dataclasses import replace
import gc
import json
from pathlib import Path
import platform
import resource
import subprocess
import time
import numpy as np
from .embeddings import train_embedding
from .experiment import evaluate,predictions,save_table
from .extension_data import PeriodStore,load_full,source_panels
from .extension_models import score_ppr,tie_scores,adaptive_scores,cycle_scores,rewire_graph,PreparedPPR
from .sparse_models import baseline_scores,transitions,fusion,hits_scores
from .study_data import load_study
from .evaluation import paired_bootstrap
from .utils import file_digest,digest,write_json


ROOT=Path(__file__).resolve().parents[2]


def signature():
    names=['extension_experiment.py','extension_models.py','extension_data.py','sparse_models.py',
           'embeddings.py','study_data.py','redirects.py','evaluation.py','ranking.py','utils.py','experiment.py']
    return {'code':{n:file_digest(Path(__file__).parent/n) for n in names},
            'protocol':file_digest(ROOT/'docs/EXTENSION_PROTOCOL.md'),
            'lock':file_digest(ROOT/'requirements-study.lock'),
            'prepared':file_digest(ROOT/'data/processed/study-v2/manifest.json'),
            'python':platform.python_version()}


def initialise(output):
    output.mkdir(parents=True,exist_ok=True);p=output/'signature.json';s=signature()
    if p.exists() and json.loads(p.read_text())!=s:raise ValueError('Changed extension signature: use fresh run, never retune test')
    if not p.exists():write_json(p,s)


def event(output,kind,**details):
    with (output/'events.jsonl').open('a') as f:
        f.write(json.dumps({'time_unix':time.time(),'event':kind,**details})+'\n')


def freeze(folder,prediction,selected,extra=None):
    if (folder/'freeze.json').exists():raise ValueError('Frozen stage already exists')
    write_json(folder/'predictions.json',prediction)
    write_json(folder/'freeze.json',{'signature':signature(),'selected':selected,
        'predictions_sha256':file_digest(folder/'predictions.json'),'frozen_at_unix':time.time(),
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'scope':extra or {}})


def frozen_predictions(folder):
    info=json.loads((folder/'freeze.json').read_text())
    if info['signature']!=signature():raise ValueError('Frozen signature differs')
    if file_digest(folder/'predictions.json')!=info['predictions_sha256']:raise ValueError('Frozen predictions changed')
    return json.loads((folder/'predictions.json').read_text())


def summaries(data,models,labels):
    aggregate={};rows={}
    for name,p in models.items():aggregate[name],rows[name]=evaluate(data,p,labels)
    return aggregate,rows


def paired(rows,left,right):
    a={r['source']:r['all_metrics']['ndcg@10'] for r in rows[left] if r['all_metrics']['ndcg@10'] is not None}
    b={r['source']:r['all_metrics']['ndcg@10'] for r in rows[right] if r['all_metrics']['ndcg@10'] is not None}
    return paired_bootstrap(a,b,seed=2026,resamples=2000) if len(a)>1 else {'sources':len(a),'ci95':None}


def fit_suite(data,validation,folder,embeddings=True):
    trials=[];selected={};scores={};diagnostics={}
    def choose(name,options):
        best=None
        for params,compute in options:
            start=time.perf_counter();s,info=compute();duration=time.perf_counter()-start
            value=evaluate(data,predictions(data,s,2026),validation)[0]['all']['ndcg@10']['macro']
            if value is None:raise ValueError('No observable validation sources')
            trials.append({'model':name,'parameters':json.dumps(params,sort_keys=True),'validation_ndcg':value,'seconds':duration})
            if best is None or value>best[0]+1e-15:best=(value,params,s,info,duration)
        value,params,s,info,duration=best;selected[name]=params;scores[name]=s
        diagnostics[name]={'seconds':duration,'details':info}
        print(folder.name,name,params,'validation',round(value,6),flush=True)
    for name,kind in [('M0_global','global'),('M1_local','local'),('M2_uniform','uniform'),('M2D_indegree','indegree')]:
        choose(name,[({},lambda kind=kind:(baseline_scores(data,kind),{}))])
    choose('M1B_backoff',[({'mu':mu,'eta':eta},lambda mu=mu,eta=eta:(baseline_scores(data,'backoff',mu,eta),{}))
                           for mu in [0.,10.,100.,1000.] for eta in [0.,.5,1.]])
    for name,mode in [('M3_ppr_h','H'),('M4C_ppr_c','C'),('M4H_ppr_wh','WH')]:
        weights=transitions(data,mode,mu=100.)
        choose(name,[({'damping':d,'mode':mode},lambda d=d:score_ppr(data,weights,d)) for d in [.15,.5,.85]])
    choose('M6B_fusion',[({'lambda':w},lambda w=w:(fusion(scores['M1B_backoff'],scores['M3_ppr_h'],w),{})) for w in [0.,.25,.5,.75,1.]])
    choose('topology_tie',[({},lambda:(tie_scores(data,scores['M3_ppr_h']),{}))])
    choose('adaptive_fusion',[({'tau':t},lambda t=t:(adaptive_scores(data,scores['M1B_backoff'],scores['M3_ppr_h'],t),{})) for t in [10.,100.,1000.]])
    choose('CycleRank',[({'max_length':k},lambda k=k:cycle_scores(data,k)) for k in [2,3]])
    choose('HITS',[({},lambda:hits_scores(data))])
    if embeddings:
        for mode,dim in [('H',32),('WH',64)]:
            weights=transitions(data,mode,mu=100.)
            for seed in [17,29,43]:
                name=f'N2V_{mode}_s{seed}'
                params={'dimension':dim,'p':.5,'q':2.,'seed':seed}
                def compute(params=params,weights=weights):
                    s,_,info=train_embedding(data,weights,**params,walks=3,length=20,window=5,epochs=5,negative=5)
                    return s,info
                choose(name,[(params,compute)])
    save_table(folder/'validation_trials.csv',trials)
    write_json(folder/'diagnostics.json',diagnostics)
    return {m:predictions(data,s,2026) for m,s in scores.items()},selected


def rolling(prepared,raw,output):
    initialise(output);data=load_study(prepared);ids=[data.ids[i] for i in data.queries]
    store=PeriodStore(prepared,raw,output/'periods.duckdb')
    windows=[(['2018-03','2018-04','2018-05'],'2018-06','2018-07'),
             (['2018-04','2018-05','2018-06'],'2018-07','2018-08'),
             (['2018-05','2018-06','2018-07'],'2018-08','2018-09')]
    start=time.perf_counter()
    for months,val,test in windows:
        folder=output/test;folder.mkdir(exist_ok=True)
        if (folder/'completion.json').exists():
            frozen_predictions(folder)
            continue
        if not (folder/'freeze.json').exists():
            # Existing new test labels without a freeze cannot be used for a fresh fit.
            if store.con.execute('SELECT count(*) FROM loaded WHERE month=?',[test]).fetchone()[0]:
                raise ValueError('Test was parsed before freeze; refuse fitting')
            event(output,'training_start',train=months,validation=val,test=test)
            train=store.training(data,months);validation,_=store.period(val,ids)
            models,selected=fit_suite(train,validation,folder)
            freeze(folder,models,selected,{'train':months,'validation':val,'test':test,'graph':'original induced H; fixed candidates'})
            event(output,'predictions_frozen',test=test,sha256=file_digest(folder/'predictions.json'))
            del train;gc.collect()
        models=frozen_predictions(folder)
        event(output,'test_read_start',test=test)
        labels,audit=store.period(test,ids)
        metrics,rows=summaries(data,models,labels)
        contrasts={f'{left} - {right}':paired(rows,left,right) for left,right in [
            ('topology_tie','M1_local'),('topology_tie','M1B_backoff'),('adaptive_fusion','M1B_backoff'),
            ('M6B_fusion','M1B_backoff'),('CycleRank','M3_ppr_h')]}
        for name,value in [('labels',labels),('audit',audit),('metrics',metrics),('source_metrics',rows),('contrasts',contrasts)]:
            write_json(folder/(name+'.json'),value)
        write_json(folder/'completion.json',{'status':'complete','test':test,'models':len(models),
            'artifacts':{p.name:file_digest(p) for p in folder.glob('*.json') if p.name!='completion.json'}})
        event(output,'window_completed',test=test)
    store.close();write_json(output/'completion.json',{'status':'complete','seconds':time.perf_counter()-start,'windows':[w[2] for w in windows]})


def boundary(prepared,raw,full,output):
    initialise(output)
    if (output/'completion.json').exists():return
    pilot=json.loads((full/'pilot.json').read_text())
    if not pilot['pass']:raise ValueError('Full graph resource gate failed')
    small=load_study(prepared);original=[small.ids[i] for i in small.queries]
    panels=source_panels(prepared,original);all_ids=sum(panels.values(),[])
    write_json(output/'panels.json',panels)
    store=PeriodStore(prepared,raw,output/'periods.duckdb')
    # All May/June work here is explicitly exploratory. April still selects new knobs.
    val,_=store.period('2018-04',original)
    localfolder=output/'induced';localfolder.mkdir(exist_ok=True)
    if not (localfolder/'freeze.json').exists():
        models,selected=fit_suite(small,val,localfolder,embeddings=False)
        freeze(localfolder,models,selected,{'context':'original induced graph','test_use':'exploratory'})
    data=load_full(full,all_ids)
    # Candidate identity is checked before any scoring quality is examined.
    for old,new in zip(small.queries,data.queries[:200],strict=True):
        if {small.ids[i] for i in small.candidates(old)}!={data.ids[i] for i in data.candidates(new)}:
            raise ValueError('Boundary comparison changed query candidates')
    folder=output/'full';folder.mkdir(exist_ok=True)
    if not (folder/'freeze.json').exists():
        start=time.perf_counter();h,diag=score_ppr(data,data.adjacency,.15)
        b=baseline_scores(data,'backoff',0.,0.)
        models={'M1_local':predictions(data,baseline_scores(data,'local'),2026),
                'M1B_backoff':predictions(data,b,2026),'M3_ppr_h':predictions(data,h,2026),
                'M6B_fusion':predictions(data,fusion(b,h,.5),2026),
                'topology_tie':predictions(data,tie_scores(data,h),2026)}
        qoriginal=replace(data,queries=data.queries[:200])
        options=[]
        for tau in [10.,100.,1000.]:
            p=predictions(qoriginal,adaptive_scores(qoriginal,b,h,tau),2026)
            value=evaluate(qoriginal,p,val)[0]['all']['ndcg@10']['macro'];options.append((tau,value,p))
        best=max(range(len(options)),key=lambda i:(options[i][1],-i));tau,_,p=options[best]
        models['adaptive_fusion']=p
        for name,mode in [('M4C_ppr_c','C'),('M4H_ppr_wh','WH')]:
            w=transitions(qoriginal,mode,mu=100.);s,info=score_ppr(qoriginal,w,.15)
            models[name]=predictions(qoriginal,s,2026)
            write_json(folder/(name+'-diagnostics.json'),info)
            del w,s;gc.collect()
        write_json(folder/'diagnostics.json',{'H_queries':diag,'seconds':time.perf_counter()-start,
            'max_rss_native_units':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'candidate_identity':True,'nodes':len(data.ids),'edges':data.adjacency.nnz,
            'adaptive_validation':[{'tau':t,'ndcg':v} for t,v,p in options]})
        freeze(folder,models,{'H_damping':.15,'C_WH_damping':.15,'fusion_lambda':.5,'adaptive_tau':tau},
               {'context':'full historical canonical graph','primary_queries':200,'additional_queries':400,'test_use':'exploratory'})
    full_models=frozen_predictions(folder);induced=frozen_predictions(localfolder)
    for month in ['2018-05','2018-06']:
        labels,audit=store.period(month,all_ids)
        primary=replace(data,queries=data.queries[:200]);metrics,rows=summaries(primary,full_models,labels)
        small_metrics,small_rows=summaries(small,induced,labels)
        contrasts={}
        for m in ['M1_local','M3_ppr_h','M6B_fusion','topology_tie']:
            a={r['source']:r['all_metrics']['ndcg@10'] for r in rows[m] if r['all_metrics']['ndcg@10'] is not None}
            b={r['source']:r['all_metrics']['ndcg@10'] for r in small_rows[m] if r['all_metrics']['ndcg@10'] is not None}
            contrasts[m]=paired_bootstrap(a,b)
        panel_results={}
        for i,seed in enumerate(panels):
            panel_data=replace(data,queries=data.queries[200*i:200*(i+1)])
            selected={m:full_models[m] for m in ['M1_local','M3_ppr_h','M6B_fusion','topology_tie']}
            panel_results[seed]=summaries(panel_data,selected,labels)[0]
        rank_overlap={}
        for m in ['M3_ppr_h','M6B_fusion']:
            rank_overlap[m]=sum(len(set(full_models[m][s]['ranked'][:10])&set(induced[m][s]['ranked'][:10]))/
                len(set(full_models[m][s]['ranked'][:10])|set(induced[m][s]['ranked'][:10])) for s in original)/len(original)
        write_json(output/(month+'.json'),{'full':metrics,'induced':small_metrics,'full_sources':rows,
            'induced_sources':small_rows,'full_minus_induced':contrasts,'panels':panel_results,
            'mean_top10_jaccard':rank_overlap,'audit':audit})
    store.close();write_json(output/'completion.json',{'status':'complete','context':'full historical H','panels':3})


def null_study(prepared,raw,output):
    initialise(output)
    if (output/'completion.json').exists():return
    data=load_study(prepared);b=baseline_scores(data,'backoff',0.,0.)
    models={};audits={}
    frozen=output/'frozen';frozen.mkdir(exist_ok=True)
    if not (frozen/'freeze.json').exists():
        for seed in range(101,106):
            a,audit=rewire_graph(data.adjacency,data.queries,seed)
            s,info=score_ppr(data,a,.15)
            models[f'null_ppr_{seed}']=predictions(data,s,2026)
            models[f'null_fusion_{seed}']=predictions(data,fusion(b,s,.5),2026)
            audits[str(seed)]={**audit,'ppr_max_residual':max(r['residual'] for r in info.values())}
            print('null complete',seed,audit,flush=True)
        write_json(frozen/'rewiring_audits.json',audits)
        freeze(frozen,models,{'seeds':list(range(101,106)),'damping':.15,'lambda':.5},
               {'test_use':'exploratory','graph':'degree-matched perturbation, protected query outgoing edges'})
    models=frozen_predictions(frozen)
    store=PeriodStore(prepared,raw,output/'periods.duckdb')
    for month in ['2018-05','2018-06']:
        labels,audit=store.period(month,[data.ids[i] for i in data.queries])
        metrics,rows=summaries(data,models,labels)
        write_json(output/(month+'.json'),{'metrics':metrics,'sources':rows,'audit':audit})
    store.close();write_json(output/'completion.json',{'status':'complete','seeds':5})


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['boundary','rolling','null'])
    p.add_argument('--prepared',type=Path,default=Path('data/processed/study-v2'))
    p.add_argument('--raw',type=Path,default=Path('data/raw/eswiki'))
    p.add_argument('--full',type=Path,default=Path('data/processed/full-extension'))
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.stage=='boundary':boundary(args.prepared,args.raw,args.full,args.output)
    elif args.stage=='rolling':rolling(args.prepared,args.raw,args.output)
    else:null_study(args.prepared,args.raw,args.output)
