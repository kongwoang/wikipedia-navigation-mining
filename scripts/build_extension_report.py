"""Publish auditable extension results; never fit models or select settings."""
import argparse
import csv
import gzip
import json
import math
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import duckdb
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wikinav.evaluation import aggregate_results,evaluate_source,paired_bootstrap
from wikinav.utils import file_digest,write_json
from wikinav.verify_extensions import verify,verify_payload,verify_timeline
from wikinav.extension_data import PeriodStore
from wikinav.study_data import load_study

MONTHS=['2018-07','2018-08','2018-09']
CORE=['M1_local','M1B_backoff','M3_ppr_h','M4C_ppr_c','M4H_ppr_wh','M6B_fusion','topology_tie','adaptive_fusion','CycleRank']

def read(path):return json.loads(path.read_text())
def table(path,rows):
    if not rows:return
    with path.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)

def figure(out,name):
    plt.tight_layout()
    for ext in ('png','svg'):plt.savefig(out/'figures'/f'{name}.{ext}',dpi=180,bbox_inches='tight')
    svg=out/'figures'/f'{name}.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close()

def source_labels(db,months,sources):
    c=duckdb.connect(str(db),read_only=True);labels={}
    for m in months:
        labels[m]={}
        query=','.join(str(int(s)) for s in sources)
        for s,t,n in c.execute(f'SELECT s,target,sum(n) FROM labels WHERE month=? AND s IN ({query}) GROUP BY s,target',[m]).fetchall():
            labels[m].setdefault(str(s),{})[t]=int(n)
    c.close();return labels

def build(run,prepared,raw,out):
    if out.exists():raise FileExistsError('Use a fresh report folder; published bundles are immutable')
    for stage in ('rolling','boundary','null'):
        if read(run/stage/'completion.json')['status']!='complete':raise ValueError('Incomplete experiment')
    out.mkdir(parents=True);(out/'figures').mkdir();(out/'tables').mkdir();(out/'payloads').mkdir();(out/'provenance').mkdir()
    allmetrics=[];coverage=[];contrasts=[];selected=[];trials=[];resources=[];payloads=[];rolling={};freeze_map={}
    def publish(name,payload):
        candidates={}
        for models in payload['prediction_groups'].values():
            for predictions in models.values():
                for s,p in predictions.items():
                    cs=sorted(p['scores'])
                    if s in candidates and candidates[s]!=cs:raise ValueError('Candidate mismatch across contexts/models')
                    candidates[s]=cs
        payload['candidates']=candidates
        payload['labels']={m:{s:ls[s] for s in candidates if s in ls} for m,ls in payload['labels'].items()}
        verify_payload(payload)
        path=out/'payloads'/f'{name}.json.gz'
        path.write_bytes(gzip.compress(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
        payloads.append(str(path.relative_to(out)))
        for e in payload['evaluations']:
            for model,metrics in e['metrics'].items():
                base={'study':e['name'],'month':e['month'],'model':model}
                coverage.append({**base,**{k:v for k,v in metrics.items() if k not in ('all','conditional')}})
                for den in ('all','conditional'):
                    for agg in ('macro','traffic_weighted'):
                        allmetrics.append({**base,'denominator':den,'aggregation':agg,**{k:v[agg] for k,v in metrics[den].items()}})
        for group,f in payload['freezes'].items():
            write_json(out/'provenance'/f'{name}-{group}-freeze.json',f)
    events=[json.loads(l) for l in (run/'rolling/events.jsonl').read_text().splitlines()]
    shutil.copyfile(run/'rolling/events.jsonl',out/'provenance/rolling-events.jsonl')
    for m in MONTHS:
        folder=run/'rolling'/m;pred=read(folder/'predictions.json');f=read(folder/'freeze.json');metrics=read(folder/'metrics.json')
        qs=sorted(pred['M1_local']);freeze_map[m]=f
        p={'kind':'rolling','month':m,'prediction_groups':{'rolling':pred},'freezes':{'rolling':f},
           'labels':{m:read(folder/'labels.json')},'evaluations':[{'name':'rolling','month':m,'group':'rolling','sources':qs,'metrics':metrics}]}
        publish('rolling-'+m,p);rolling[m]=p
        for model,params in f['selected'].items():selected.append({'month':m,'model':model,'parameters':json.dumps(params,sort_keys=True)})
        for name in ('diagnostics.json','audit.json','completion.json','contrasts.json'):
            shutil.copyfile(folder/name,out/'provenance'/f'{m}-{name}')
        for row in csv.DictReader((folder/'validation_trials.csv').open()):trials.append({'month':m,**row})
        for contrast,info in read(folder/'contrasts.json').items():
            contrasts.append({'study':'rolling','month':m,'contrast':contrast,'difference':info['difference'],'ci_low':info['ci95'][0],'ci_high':info['ci95'][1],'sources':info['sources']})
    verify_timeline(events,freeze_map)
    panels=read(run/'boundary/panels.json');original=panels['2026'];bc={};evaluations=[]
    for m in ('2018-05','2018-06'):
        b=read(run/'boundary'/f'{m}.json');bc[m]=b
        evaluations.extend([{'name':'boundary-'+g,'month':m,'group':g,'sources':original,'metrics':b[g]} for g in ('full','induced')])
        for seed,metrics in b['panels'].items():evaluations.append({'name':'panel-'+seed,'month':m,'group':'full','sources':panels[seed],'metrics':metrics})
        for model,info in b['full_minus_induced'].items():contrasts.append({'study':'boundary','month':m,'contrast':model+' full - induced','difference':info['difference'],'ci_low':info['ci95'][0],'ci_high':info['ci95'][1],'sources':info['sources']})
        shutil.copyfile(run/'boundary'/f'{m}.json',out/'provenance'/f'boundary-{m}.json')
    bpayload={'kind':'boundary','prediction_groups':{g:read(run/'boundary'/g/'predictions.json') for g in ('full','induced')},
              'freezes':{g:read(run/'boundary'/g/'freeze.json') for g in ('full','induced')},'labels':source_labels(run/'boundary/periods.duckdb',['2018-05','2018-06'],sum(panels.values(),[])),'evaluations':evaluations}
    publish('boundary',bpayload)
    nullmetrics={m:read(run/'null'/f'{m}.json') for m in ('2018-05','2018-06')}
    npayload={'kind':'null','prediction_groups':{'null':read(run/'null/frozen/predictions.json')},'freezes':{'null':read(run/'null/frozen/freeze.json')},
              'labels':bpayload['labels'],'evaluations':[{'name':'null','month':m,'group':'null','sources':original,'metrics':v['metrics']} for m,v in nullmetrics.items()]}
    publish('null',npayload)
    for src,name in [(run/'null/frozen/rewiring_audits.json','rewiring_audits.json'),(run/'boundary/full/diagnostics.json','full-diagnostics.json'),
                     (Path('docs/evidence/extension-acquisition.json'),'acquisition.json'),(Path('docs/evidence/full-graph-pilot.json'),'pilot.json'),
                     (Path('docs/evidence/full-graph-export.json'),'full-graph.json'),(Path('docs/evidence/extension-pretest-correction.json'),'pretest-correction.json')]:shutil.copyfile(src,out/'provenance'/name)
    # Train-defined strata and title metadata, not selected by future observations.
    con=duckdb.connect(str(prepared/'study.duckdb'),read_only=True)
    strata={str(s):str(g) for s,g in con.execute('SELECT s,stratum FROM query_pool').fetchall()}
    con.close()
    group_rows=[]
    for e in bpayload['evaluations']:
        if not e['name'].startswith('panel-'):continue
        for group in sorted(set(strata[s] for s in e['sources'])):
            ss=[s for s in e['sources'] if strata[s]==group]
            for model in e['metrics']:
                pred=bpayload['prediction_groups'][e['group']][model]
                rows=[evaluate_source(s,bpayload['candidates'][s],pred[s]['ranked'],bpayload['labels'][e['month']].get(s,{})) for s in ss]
                v=aggregate_results(rows)
                group_rows.append({'panel':e['name'],'month':e['month'],'stratum':group,'model':model,'queries':len(ss),'observable':v['q_all'],'candidate_mass_coverage':v['mass_candidate_coverage'],'macro_ndcg':v['all']['ndcg@10']['macro']})
    # Common-source summaries preserve the same source cohort across all three windows.
    common=set.intersection(*[set(p['labels'][m]) for m,p in rolling.items()]);common_rows=[];seed_rows=[]
    for m,p in rolling.items():
        for model,pred in p['prediction_groups']['rolling'].items():
            rows=[evaluate_source(s,p['candidates'][s],pred[s]['ranked'],p['labels'][m][s]) for s in sorted(common)]
            v=aggregate_results(rows);common_rows.append({'month':m,'model':model,'sources':len(common),'macro_ndcg':v['all']['ndcg@10']['macro'],'weighted_ndcg':v['all']['ndcg@10']['traffic_weighted']})
        for mode in ('H','WH'):
            vals=[p['evaluations'][0]['metrics'][f'N2V_{mode}_s{s}']['all']['ndcg@10']['macro'] for s in (17,29,43)]
            seed_rows.append({'month':m,'mode':mode,'seeds':3,'mean':float(np.mean(vals)),'sample_sd':float(np.std(vals,ddof=1)),'min':min(vals),'max':max(vals),'warning':'H dimension32 vs WH64: not matched-knob weighting ablation'})
    # Mechanism diagnostics use already-frozen rankings. Counts come only from each window's train period.
    data=load_study(prepared);store=PeriodStore(prepared,raw,run/'rolling/periods.duckdb');mechanism=[];demo=[]
    title_by_id={s:t for s,t in zip(data.ids,data.titles)}
    for m,p in rolling.items():
        train=store.training(data,freeze_map[m]['scope']['train']);index={s:i for i,s in enumerate(train.ids)}
        for s in original:
            i=index[s];counts={train.ids[t]:int(n) for t,n in zip(train.counts.getrow(i).indices,train.counts.getrow(i).data)}
            labels=p['labels'][m].get(s,{})
            idcg=sum(math.log2(1+n)/math.log2(r+1) for r,n in enumerate(sorted(labels.values(),reverse=True)[:10],1))
            per_source={}
            for model in ('M1_local','M6B_fusion','topology_tie','adaptive_fusion','M3_ppr_h','CycleRank'):
                pred=p['prediction_groups']['rolling'][model][s];rank=pred['ranked'];observed=unobserved=0.
                if idcg:
                    for r,t in enumerate(rank[:10],1):
                        gain=math.log2(1+labels.get(t,0))/math.log2(r+1)/idcg
                        if counts.get(t,0)>0:observed+=gain
                        else:unobserved+=gain
                    result=evaluate_source(s,p['candidates'][s],rank,labels)
                    if not math.isclose(observed+unobserved,result.all_metrics['ndcg@10'],abs_tol=1e-12):raise ValueError('Nonadditive decomposition')
                inversions=sum(counts.get(a,0)<counts.get(b,0) for j,a in enumerate(rank) for b in rank[j+1:])
                if model=='topology_tie' and inversions:raise ValueError('Tie-break violated local count order')
                mechanism.append({'month':m,'source':s,'title':title_by_id[s],'model':model,'observable':bool(idcg),'observed_ndcg':observed if idcg else None,'unobserved_ndcg':unobserved if idcg else None,'top20_count_inversions':inversions,'eligible_train_mass':sum(counts.get(t,0) for t in p['candidates'][s])})
                per_source[model]={'ranked':rank[:10],'ndcg':observed+unobserved if idcg else None,'scores':{t:pred['scores'][t] for t in rank[:10]}}
            # Compact offline demo: actual scores and evidence; no predictions handcrafted.
            targets=set(labels)|{t for v in per_source.values() for t in v['ranked']}
            demo.append({'month':m,'id':s,'title':title_by_id[s],'scope':freeze_map[m]['scope'],'models':per_source,
                         'candidates':len(p['candidates'][s]),'future_pairs':len(labels),'targets':{t:{'title':title_by_id.get(t,t),'train':counts.get(t,0),'future':labels.get(t,0),'eligible':t in p['candidates'][s]} for t in targets}})
    store.close()
    mech_summary=[]
    for m in MONTHS:
        base={r['source']:r for r in mechanism if r['month']==m and r['model']=='M1_local' and r['observable']}
        for model in ('M6B_fusion','topology_tie','adaptive_fusion','M3_ppr_h','CycleRank'):
            rows={r['source']:r for r in mechanism if r['month']==m and r['model']==model and r['observable']}
            for component in ('observed_ndcg','unobserved_ndcg'):
                contrast=paired_bootstrap({s:r[component] for s,r in rows.items()},{s:r[component] for s,r in base.items()})
                mech_summary.append({'month':m,'model':model,'component':component,'delta_vs_markov':contrast['difference'],'ci_low':contrast['ci95'][0],'ci_high':contrast['ci95'][1],'sources':contrast['sources']})
    fallback_groups=[]
    for m in MONTHS:
        for group in ('positive_eligible_mass','zero_eligible_mass'):
            base={r['source']:r for r in mechanism if r['month']==m and r['model']=='M1_local'
                  and ((r['eligible_train_mass']>0)==(group=='positive_eligible_mass'))}
            observed={s:r for s,r in base.items() if r['observable']}
            for model in ('topology_tie','M6B_fusion','adaptive_fusion'):
                target={r['source']:r for r in mechanism if r['month']==m and r['model']==model and r['source'] in observed}
                a={s:r['observed_ndcg']+r['unobserved_ndcg'] for s,r in target.items()}
                b={s:r['observed_ndcg']+r['unobserved_ndcg'] for s,r in observed.items()}
                c=paired_bootstrap(a,b) if len(a)>1 else None
                fallback_groups.append({'month':m,'group':group,'model':model,'queries':len(base),'observable':len(a),
                    'delta_vs_local':sum(a[s]-b[s] for s in a)/len(a) if a else None,
                    'ci_low':c['ci95'][0] if c else None,'ci_high':c['ci95'][1] if c else None,
                    'interpretation':'post-hoc train-mass subgroup; zero-mass changes fallback policy'})
    table(out/'tables/fallback_groups.csv',fallback_groups)
    for name,rows in [('metrics',allmetrics),('coverage',coverage),('contrasts',contrasts),('selected_parameters',selected),('validation_trials',trials),('panel_strata',group_rows),('common_sources',common_rows),('embedding_seeds',seed_rows),('source_mechanism',mechanism),('mechanism_summary',mech_summary)]:table(out/'tables'/f'{name}.csv',rows)
    # Figures use observed outputs only; no anticipated improvements.
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(9,5))
    for model in CORE:
        ax.plot(MONTHS,[rolling[m]['evaluations'][0]['metrics'][model]['all']['ndcg@10']['macro'] for m in MONTHS],marker='o',label=model)
    ax.set(ylabel='Macro full NDCG@10',title='Fixed-topology rolling evaluation');ax.legend(bbox_to_anchor=(1,1),loc='upper left');figure(out,'01_rolling')
    fig,ax=plt.subplots(figsize=(8,4));primary=[r for r in contrasts if r['study']=='rolling' and r['contrast']=='topology_tie - M1_local']
    for i,r in enumerate(primary):ax.errorbar(r['difference'],i,xerr=[[r['difference']-r['ci_low']],[r['ci_high']-r['difference']]],fmt='o',capsize=4)
    ax.axvline(0,color='gray',ls='--');ax.set(yticks=range(3),yticklabels=MONTHS,xlabel='Tie-break minus Markov; paired source bootstrap 95% CI',title='Primary new-period contrast');figure(out,'02_primary_intervals')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,m in zip(axes,('2018-05','2018-06')):
        models=['M1_local','M3_ppr_h','M6B_fusion'];x=np.arange(3)
        for j,g in enumerate(('induced','full')):ax.bar(x+(j-.5)*.35,[bc[m][g][s]['all']['ndcg@10']['macro'] for s in models],.35,label=g)
        ax.set(xticks=x,xticklabels=['Markov','PPR-H','Fusion'],title=m,ylabel='Macro full NDCG@10',ylim=(0,1));ax.legend()
    figure(out,'03_boundary')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,m in zip(axes,('2018-05','2018-06')):
        for i,(prefix,real) in enumerate([('null_ppr','M3_ppr_h'),('null_fusion','M6B_fusion')]):
            vals=[v['all']['ndcg@10']['macro'] for k,v in nullmetrics[m]['metrics'].items() if k.startswith(prefix)]
            ax.scatter([i]*5,vals,label='5 rewired graphs' if i==0 else None,marker='x',color='#b4553a')
            ax.scatter(i,bc[m]['induced'][real]['all']['ndcg@10']['macro'],label='Real induced H' if i==0 else None,color='#117b83',s=55)
        ax.set(xticks=[0,1],xticklabels=['PPR-H','Fusion'],title=m,ylabel='Macro full NDCG@10');ax.legend()
    figure(out,'04_degree_null')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,m in zip(axes,('2018-05','2018-06')):
        for model in ('M1_local','M3_ppr_h','M6B_fusion','topology_tie'):
            ax.plot(list(panels),[bc[m]['panels'][s][model]['all']['ndcg@10']['macro'] for s in panels],marker='o',label=model)
        ax.set(title=m,xlabel='Disjoint query panel seed; same full graph',ylabel='Macro full NDCG@10');ax.legend(fontsize=8)
    figure(out,'05_query_panels')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,model,key in [(axes[0],'adaptive_fusion','tau'),(axes[1],'CycleRank','max_length')]:
        for m in MONTHS:
            rs=[r for r in trials if r['month']==m and r['model']==model]
            ax.plot([json.loads(r['parameters'])[key] for r in rs],[float(r['validation_ndcg']) for r in rs],marker='o',label=m+' window')
        if key=='tau':ax.set_xscale('log')
        ax.set(xlabel=key,ylabel='Validation macro full NDCG@10',title=model);ax.legend(fontsize=8)
    figure(out,'06_validation')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,model in zip(axes,('topology_tie','M6B_fusion')):
        for component in ('observed_ndcg','unobserved_ndcg'):
            rows=[r for r in mech_summary if r['model']==model and r['component']==component]
            ax.plot([r['month'] for r in rows],[r['delta_vs_markov'] for r in rows],marker='o',label=component)
        ax.axhline(0,color='gray',ls='--');ax.set(title=model,ylabel='Additive NDCG contribution vs Markov');ax.legend(fontsize=8)
    figure(out,'07_mechanism')
    write_json(out/'demo_data.json',{'queries':demo,'models':list(demo[0]['models']),'months':MONTHS})
    from wikinav.extension_demo import build as build_demo
    build_demo(out)
    write_json(out/'summary.json',{'run':str(run),'windows':MONTHS,'common_observable_sources':len(common),'graphs':read(out/'provenance/full-graph.json')['graphs'],
        'query_panels':panels,'primary_contrasts':primary,'interpretation':'Boundary/null/panel exploratory; July--September protocol locked before label reads; source bootstrap is conditional, not event-iid.'})
    # Source files in each freeze must still match their exact execution bytes.
    sig=freeze_map[MONTHS[0]]['signature']
    for name,sha in sig['code'].items():
        if file_digest(Path('src/wikinav')/name)!=sha:raise ValueError('Algorithm changed after freeze: '+name)
    if file_digest(Path('docs/EXTENSION_PROTOCOL.md'))!=sig['protocol']:raise ValueError('Protocol changed')
    write_json(out/'provenance/verification_scope.json',{'algorithm_bytes_match_freeze':True,'chronology_checked':True,'candidate_consistency_checked':True,'original_study_unchanged':True,'note':'Local artifact audit, not an external timestamp certification.'})
    manifest={'payloads':payloads,'sha256':{str(p.relative_to(out)):file_digest(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    write_json(out/'bundle_manifest.json',manifest)
    print(json.dumps(verify(out),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,default=Path('results/extensions-v2'));parser.add_argument('--prepared',type=Path,default=Path('data/processed/study-v2'))
    parser.add_argument('--raw',type=Path,default=Path('data/raw/eswiki'));parser.add_argument('--output',type=Path,default=Path('reports/extensions/study-v2'))
    a=parser.parse_args();build(a.run,a.prepared,a.raw,a.output)
