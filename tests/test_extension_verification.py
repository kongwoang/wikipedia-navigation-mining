"""Regression checks for portable evidence and chronology contracts."""
import copy
import hashlib
import json
import unittest
from wikinav.evaluation import aggregate_results,evaluate_source
from wikinav.verify_extensions import verify_payload,verify_timeline


class ExtensionVerificationTests(unittest.TestCase):
    def payload(self):
        predictions={'M':{'s':{'scores':{'a':2.,'b':1.},'ranked':['a','b']}}}
        raw=(json.dumps(predictions,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
        metrics=aggregate_results([evaluate_source('s',['a','b'],['a','b'],{'a':10,'outside':20})])
        return {'prediction_groups':{'g':predictions},'freezes':{'g':{'predictions_sha256':hashlib.sha256(raw).hexdigest()}},
                'candidates':{'s':['a','b']},'labels':{'m':{'s':{'a':10,'outside':20}}},
                'evaluations':[{'name':'fixture','month':'m','group':'g','sources':['s'],'metrics':{'M':metrics}}]}

    def test_recomputes_metrics_and_keeps_outside_labels(self):
        self.assertEqual(verify_payload(self.payload()),{'source_model_period_evaluations':1,'ranking_checks':1})

    def test_changed_prediction_rejected_against_original_freeze(self):
        p=self.payload();p['prediction_groups']['g']['M']['s']['scores']['a']=3.
        with self.assertRaisesRegex(ValueError,'differs from frozen'):verify_payload(p)

    def test_silent_label_discard_changes_metrics(self):
        p=self.payload();p['labels']['m']['s'].pop('outside')
        with self.assertRaisesRegex(ValueError,'mismatch'):verify_payload(p)

    def test_temporal_contract_rejects_early_read_and_nonchronological_train(self):
        freeze={'2018-07':{'frozen_at_unix':10,'predictions_sha256':'sha','scope':{'train':['2018-03','2018-04','2018-05'],'validation':'2018-06','test':'2018-07'}}}
        events=[{'event':'predictions_frozen','test':'2018-07','time_unix':11,'sha256':'sha'},
                {'event':'test_read_start','test':'2018-07','time_unix':12}]
        verify_timeline(events,freeze)
        bad=copy.deepcopy(events);bad[1]['time_unix']=9
        with self.assertRaisesRegex(ValueError,'before freeze'):verify_timeline(bad,freeze)
        freeze['2018-07']['scope']['train'].append('2018-08')
        with self.assertRaisesRegex(ValueError,'Nonchronological'):verify_timeline(events,freeze)
