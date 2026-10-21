"""Generate report tables, scientific figures and real-model demo payload."""

import csv
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import csgraph
from scipy.stats import spearmanr

from .evaluation import evaluate_source, aggregate_results
from .experiment import save_table
from .study_data import load_study, connection
from .utils import file_digest, write_json

MAIN = ['M0_global','M1_local','M1B_backoff','M2_uniform','M2D_indegree','M3_ppr_h',
        'M4C_ppr_c','M4CH_ppr_ch','M4H_ppr_wh','M6B_fusion','M6A_matrix','HITS',
        'M5H_node2vec','M5W_node2vec']
METRICS = ['recall@5','recall@10','recall@20','mrr@10','ndcg@10','mass_recall@10','expected_rr@10']


def generate(prepared: Path, run: Path, output: Path):
    if not (run/'completion.json').exists():
        raise ValueError('Analysis requires completed frozen experiment')
    output.mkdir(parents=True,exist_ok=False)
    figures=output/'figures'; figures.mkdir()
    tables=output/'tables'; tables.mkdir()
    read=lambda name:json.loads((run/name).read_text())
    results=read('test_results.json'); sources=read('source_metrics.json')
    predictions=read('predictions.json'); diagnostics=read('model_diagnostics.json')
    freeze=read('freeze.json'); contrasts=read('paired_comparisons.json')
    data=load_study(prepared); n=len(data.ids); idx={node:i for i,node in enumerate(data.ids)}
    con=connection(prepared/'study.duckdb')
    train_pairs={(str(s),str(t)):int(count) for s,t,count in con.execute(
        'SELECT t.s,t.t,t.n FROM train t JOIN queries q ON t.s=q.s').fetchall()}
    # All figures use the same prepared graph or frozen results, never alter models.
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'figure.dpi':130,'savefig.dpi':160})
    inventory=[]
    def finish(name,caption):
        plt.tight_layout(); plt.savefig(figures/(name+'.png')); plt.savefig(figures/(name+'.svg'))
        plt.close(); inventory.append({'figure':name,'caption':caption})
    def ccdf(ax,values,label):
        values=np.sort(np.asarray(values)); values=values[values>0]
        ax.plot(values,1-np.arange(len(values))/max(len(values),1),label=label)
        ax.set(xscale='log',yscale='log',ylabel='Fraction >= x'); ax.grid(alpha=.15)
    row=[]
    for month,models in results.items():
        for name,summary in models.items():
            for estimand in ('all','conditional'):
                for weighting in ('macro','traffic_weighted'):
                    row.append({'month':month,'model':name,'denominator':estimand,'aggregation':weighting,
                                'sources':summary['q_all' if estimand=='all' else 'q_conditional'],
                                **{m:summary[estimand][m][weighting] for m in METRICS}})
    save_table(tables/'metrics.csv',row)
    coverage=[{'month':month,**{key:next(iter(models.values()))[key] for key in (
        'queries','q_all','q_conditional','label_pairs','label_mass','eligible_pairs','eligible_mass',
        'pair_candidate_coverage','mass_candidate_coverage','service_coverage')}} for month,models in results.items()]
    save_table(tables/'coverage.csv',coverage)
    save_table(tables/'paired_bootstrap.csv',[
        {'month':month,'contrast':name,'delta':v['difference'],'ci_low':v['ci95'][0],
         'ci_high':v['ci95'][1],'sources':v['sources']} for month,cs in contrasts.items() for name,v in cs.items()])
    for name in ('freeze.json','validation_results.json','paired_comparisons.json','completion.json','test_audits.json'):
        shutil.copyfile(run/name,output/name)
    shutil.copyfile(prepared/'manifest.json',output/'data_manifest.json')
    shutil.copyfile(run/'validation_trials.csv',tables/'validation_trials.csv')
    save_table(tables/'selected_parameters.csv',[{'model':name,'parameters':json.dumps(params,sort_keys=True)}
                                                for name,params in freeze['selected'].items()])
    fig,axs=plt.subplots(1,2,figsize=(10,3.7))
    ccdf(axs[0],data.counts.data,'Sample transition counts'); axs[0].set_xlabel('Published train count (sum Jan–Mar)')
    ccdf(axs[1],data.features['traffic'],'Full-graph traffic of sampled nodes'); axs[1].set_xlabel('Observed outgoing training mass')
    finish('01_traffic_tail','Training traffic and transition count tails; nodes/edges in induced sample, not a population estimate.')
    degree=np.asarray(data.adjacency.sum(axis=1)).ravel()
    indegree=np.asarray(data.adjacency.sum(axis=0)).ravel()
    fig,axs=plt.subplots(1,2,figsize=(10,3.7))
    ccdf(axs[0],degree,'Induced out-degree'); ccdf(axs[0],indegree,'Induced in-degree'); axs[0].legend(); axs[0].set_xlabel('Degree')
    axs[1].scatter(data.features['out_degree_full'],degree,s=3,alpha=.3)
    axs[1].set(xscale='log',yscale='log',xlabel='Full historical out-degree',ylabel='Induced out-degree')
    finish('02_graph_degree_boundary','Induced graph degree distributions and boundary loss; query nodes retain all eligible outgoing links.')
    fig,axs=plt.subplots(1,2,figsize=(10,3.7))
    axs[0].scatter(data.features['in_degree_full']+1,data.features['popularity']+1,s=3,alpha=.25)
    axs[0].set(xscale='log',yscale='log',xlabel='Full in-degree + 1',ylabel='Training inbound mass + 1')
    top=[]
    for s in data.queries:
        vals=data.counts[s].data; top.append(float(vals.max()/vals.sum()) if vals.size else 0)
    axs[1].scatter(degree[data.queries],top,s=15,alpha=.6)
    axs[1].set(xlabel='Query out-degree',ylabel='Largest observed destination share')
    finish('03_topology_traffic','Structural popularity is compared with observed traffic; per-query click concentration motivates local baselines.')
    first_month=next(iter(results))
    fig,axs=plt.subplots(1,2,figsize=(13,5.4))
    for ax,weight in zip(axs,('macro','traffic_weighted')):
        values=[results[first_month][m]['all']['ndcg@10'][weight] for m in MAIN]
        ax.barh(MAIN[::-1],values[::-1],color='#297a8c'); ax.set_xlim(0,1); ax.set_xlabel(f'{weight}: full NDCG@10')
    finish('04_main_comparison','Main test month: shared queries/candidates. Node2Vec rows use preregistered seed 17; other seeds are reported separately.')
    with (run/'validation_trials.csv').open() as f: trials=list(csv.DictReader(f))
    fig,axs=plt.subplots(1,2,figsize=(10,3.7))
    for model in ('M6B_fusion','M6A_matrix'):
        points=[(json.loads(r['parameters'])['lambda'],float(r['validation_macro_ndcg_all@10'])) for r in trials if r['model']==model]
        axs[0].plot(*zip(*points),marker='o',label=model)
    axs[0].set(xlabel='Behavior weight lambda',ylabel='Validation macro NDCG@10'); axs[0].legend()
    for model in ('M3_ppr_h','M4C_ppr_c','M4H_ppr_wh'):
        points=[(json.loads(r['parameters'])['damping'],float(r['validation_macro_ndcg_all@10'])) for r in trials if r['model']==model]
        axs[1].plot(*zip(*points),marker='o',label=model)
    axs[1].set(xlabel='Damping',ylabel='Validation macro NDCG@10'); axs[1].legend(fontsize=8)
    finish('05_validation_sensitivity','Hyperparameters selected using validation only; lambda endpoints and damping sensitivity are displayed.')
    fig,axs=plt.subplots(1,2,figsize=(10,3.7))
    for name in ('M3_ppr_h','M4C_ppr_c','M4H_ppr_wh'):
        diag=diagnostics[name]['details']
        first=next(v for v in diag.values() if 'residual_curve' in v)
        axs[0].semilogy(first['residual_curve'],label=name)
    axs[0].axhline(1e-8,color='grey',ls='--'); axs[0].set(xlabel='Iteration',ylabel='Fixed-point L1 residual'); axs[0].legend(fontsize=8)
    for model in ('M5H_node2vec','M5W_node2vec'):
        history=diagnostics[model]['details']['loss']
        axs[1].plot([r['epoch'] for r in history],[r['epoch_loss_delta'] for r in history],marker='o',label=model)
    axs[1].set(xlabel='Epoch',ylabel='Auxiliary SGNS loss delta'); axs[1].legend(fontsize=8)
    finish('06_numerical_diagnostics','PPR residual for the first fixed query; Node2Vec loss deltas are optimization diagnostics, not navigation validation loss.')
    fig,axs=plt.subplots(1,2,figsize=(10,3.7))
    for base,small in [('M1_local','A8_M1_local_'),('M1B_backoff','A8_M1B_backoff_'),('M6B_fusion','A8_fusion_')]:
        values=[results[first_month][f'{small}{i}month']['all']['ndcg@10']['macro'] for i in (1,2)]
        values.append(results[first_month][base]['all']['ndcg@10']['macro'])
        axs[0].plot([1,2,3],values,marker='o',label=base)
    axs[0].set(xlabel='Trailing training months (fixed graph/queries)',ylabel='Test full macro NDCG@10',xticks=[1,2,3]); axs[0].legend(fontsize=8)
    for model in ('M1B_backoff','M3_ppr_h','M6B_fusion'):
        axs[1].plot(list(results),[results[month][model]['all']['ndcg@10']['macro'] for month in results],marker='o',label=model)
    axs[1].set(xlabel='Held-out month (fixed model)',ylabel='Full macro NDCG@10'); axs[1].legend(fontsize=8)
    finish('07_history_and_horizon','History ablation recomputes all behavior priors. Monthly aggregate curves may change composition; common-source results are in tables.')
    paired_temporal=[]
    common=set.intersection(*[{r['source'] for r in sources[m]['M1_local'] if r['all_metrics']['ndcg@10'] is not None} for m in sources])
    for m in sources:
        for model in MAIN:
            vals=[r['all_metrics']['ndcg@10'] for r in sources[m][model] if r['source'] in common]
            paired_temporal.append({'month':m,'model':model,'common_sources':len(vals),'macro_ndcg@10':float(np.mean(vals)) if vals else None})
    save_table(tables/'temporal_common_sources.csv',paired_temporal)
    # Post-hoc descriptive source groups fixed using training features, not outcome.
    groups={}
    for s in data.queries:
        traffic=int(data.features['traffic'][s])
        groups[data.ids[s]]='cold' if traffic==0 else 'low_<100' if traffic<100 else 'mid_<1000' if traffic<1000 else 'high_>=1000'
    grouped=[]
    for month in sources:
        for model in MAIN:
            for group in ('cold','low_<100','mid_<1000','high_>=1000'):
                vals=[r['all_metrics']['ndcg@10'] for r in sources[month][model]
                      if groups[r['source']]==group and r['all_metrics']['ndcg@10'] is not None]
                grouped.append({'month':month,'model':model,'group':group,'sources':len(vals),
                                'macro_ndcg@10':float(np.mean(vals)) if vals else None})
    save_table(tables/'source_groups.csv',grouped)
    fig,ax=plt.subplots(figsize=(8,4))
    for model in ('M1B_backoff','M3_ppr_h','M6B_fusion','M5H_node2vec'):
        rows=[r for r in grouped if r['month']==first_month and r['model']==model]
        ax.plot([r['group'] for r in rows],[np.nan if r['macro_ndcg@10'] is None else r['macro_ndcg@10'] for r in rows],marker='o',label=model)
    ax.set(ylabel='Full macro NDCG@10',xlabel='Training traffic group'); ax.legend(fontsize=8)
    finish('08_source_sparsity','Training-defined groups; each group uses only sources with observable test labels, with sample sizes in the table.')
    edge_groups=[]
    for month in results:
        labels=read(f'labels-{month}.json')
        for group in ('unobserved','low_1_99','high_100plus'):
            subset={}
            for s,row in labels.items():
                subset[s]={t:n for t,n in row.items() if (
                    'unobserved' if train_pairs.get((s,t),0)==0 else 'low_1_99' if train_pairs[(s,t)]<100 else 'high_100plus')==group}
            for model in MAIN:
                evaluated=[evaluate_source(data.ids[s],[data.ids[i] for i in data.candidates(s)],
                    predictions[model][data.ids[s]]['ranked'],subset.get(data.ids[s],{})) for s in data.queries]
                summary=aggregate_results(evaluated)
                edge_groups.append({'month':month,'model':model,'edge_group':group,'sources':summary['q_all'],
                    'pairs':summary['label_pairs'],'mass':summary['label_mass'],
                    'macro_recall@10':summary['all']['recall@10']['macro'],
                    'mass_recall@10':summary['all']['mass_recall@10']['traffic_weighted']})
    save_table(tables/'transition_sparsity.csv',edge_groups)
    seed_rows=[]
    for month in results:
        for model in ('M5H_node2vec','M5W_node2vec'):
            values=[results[month][key]['all']['ndcg@10']['macro'] for key in (model,model+'_s29',model+'_s43')]
            seed_rows.append({'month':month,'model':model,'seeds':'17,29,43','mean':float(np.mean(values)),
                              'std_sample':float(np.std(values,ddof=1)),'min':min(values),'max':max(values)})
    save_table(tables/'embedding_seed_stability.csv',seed_rows)
    fig,ax=plt.subplots(figsize=(8,4))
    for model in MAIN:
        seconds=diagnostics[model].get('wall_seconds')
        if seconds and seconds>0:
            value=results[first_month][model]['all']['ndcg@10']['macro']
            ax.scatter(seconds,value,s=25); ax.annotate(model,(seconds,value),fontsize=6,xytext=(3,3),textcoords='offset points')
    ax.set(xscale='log',xlabel='Selected configuration preparation + scoring seconds',ylabel='Test full macro NDCG@10')
    finish('09_cost_accuracy','Cached selected configuration cost excludes tuning and ingestion; global baselines include only scoring in this shared preprocessed pipeline.')
    graph_stats={'nodes':n,'edges':int(data.adjacency.nnz),'dangling_nodes':int((degree==0).sum()),
                 'reciprocity':float(data.adjacency.multiply(data.adjacency.T).sum()/data.adjacency.nnz)}
    for kind in ('strong','weak'):
        count,labels_cc=csgraph.connected_components(data.adjacency,directed=True,connection=kind)
        graph_stats[kind+'_components']=int(count)
        graph_stats[kind+'_largest']=int(np.bincount(labels_cc).max())
    graph_stats['degree_popularity_spearman']=float(spearmanr(data.features['in_degree_full'],data.features['popularity']).statistic)
    graph_stats['unobserved_h_edge_fraction']=1-data.counts.multiply(data.adjacency).nnz/data.adjacency.nnz
    graph_stats['retained_outgoing_fraction_sample_nodes']=data.adjacency.nnz/data.manifest['full']['sample_outgoing_full_edges']
    graph_stats['query_candidate_preservation']=bool(np.all(degree[data.queries]==data.features['out_degree_full'][data.queries]))
    if not graph_stats['query_candidate_preservation']:
        raise ValueError('Query candidates were truncated')
    write_json(output/'graph_statistics.json',graph_stats)
    # Deep cases selected descriptively after test; selection is not evidence of average gains.
    by_source={model:{r['source']:r for r in sources[first_month][model]} for model in MAIN}
    valid=[s for s in groups if by_source['M1B_backoff'][s]['all_metrics']['ndcg@10'] is not None]
    metric=lambda m,s:by_source[m][s]['all_metrics']['ndcg@10']
    selectors=[('PPR_gain',lambda s:metric('M3_ppr_h',s)-metric('M1B_backoff',s)),
               ('Markov_gain',lambda s:metric('M1B_backoff',s)-metric('M3_ppr_h',s)),
               ('Hybrid_gain',lambda s:metric('M6B_fusion',s)-max(metric('M1B_backoff',s),metric('M3_ppr_h',s))),
               ('Hybrid_failure',lambda s:max(metric('M1B_backoff',s),metric('M3_ppr_h',s))-metric('M6B_fusion',s)),
               ('Many_links',lambda s:degree[idx[s]]),('Low_traffic',lambda s:-data.features['traffic'][idx[s]])]
    labels_all={month:read(f'labels-{month}.json') for month in results}
    cases=[]; chosen=set()
    for reason,key in selectors:
        available=[s for s in valid if s not in chosen]
        if not available: break
        source=max(sorted(available),key=key); chosen.add(source)
        cases.append({'reason':reason,'source':source,'title':data.titles[idx[source]],'selection_value':float(key(source))})
    write_json(output/'case_selection.json',cases)
    payload={'scope':data.manifest['scope'],'snapshot':'2018-03-01','train':['2018-01','2018-02','2018-03'],
             'months':list(results),'models':MAIN,'cases':cases,'queries':[]}
    for s in data.queries:
        node=data.ids[s]; candidates={data.ids[i] for i in data.candidates(s)}
        destinations=set(candidates)
        for month in labels_all: destinations.update(labels_all[month].get(node,{}))
        payload['queries'].append({'id':node,'title':data.titles[s],'degree':int(degree[s]),
            'traffic':int(data.features['traffic'][s]),'group':groups[node],
            'predictions':{model:predictions[model][node] for model in MAIN},
            'destinations':{target:{'title':data.titles[idx[target]] if target in idx else target.removeprefix('oov:'),
                'hyperlink':target in candidates,'train_count':train_pairs.get((node,target),0),
                'future':{month:labels_all[month].get(node,{}).get(target,0) for month in labels_all}} for target in sorted(destinations)},
            'metrics':{month:{model:{'all':next(r for r in sources[month][model] if r['source']==node)['all_metrics'],
                                   'conditional':next(r for r in sources[month][model] if r['source']==node)['conditional_metrics']}
                              for model in MAIN} for month in results}})
    write_json(output/'demo_data.json',payload)
    write_json(output/'figure_inventory.json',inventory)
    write_json(output/'summary.json',{'scope':data.manifest['scope'],'coverage':coverage,'graph':graph_stats,
               'selected':freeze['selected'],'main_models':MAIN,'figures':len(inventory),
               'source_artifacts_sha256':{name:file_digest(run/name) for name in ('freeze.json','predictions.json','test_results.json')},
               'case_selection':cases})
    con.close()
    return output


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepared',type=Path,default=Path('data/processed/study-v2'))
    parser.add_argument('--run',type=Path,default=Path('results/study-v1'))
    parser.add_argument('--output',type=Path,default=Path('reports/generated'))
    args=parser.parse_args(); generate(args.prepared,args.run,args.output)
