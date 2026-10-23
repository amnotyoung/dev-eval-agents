import copy
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import score_calculate as sc


def example():
    scores = [3,3,3,2,2]
    counts = [('relevance',2),('coherence',2),('effectiveness',3),('efficiency',2),('sustainability',2)]
    return {"schema_version":1, "project":"example", "source_sha256":"0"*64,
            "profile":"koica-2024", "verification":"conditional", "criteria":[
        {"criterion":name, "questions":[{"id":f"q{j}", "status":"scored", "score":scores[i],
         "fact_ids":[f"F{i+1}"], "reason":"합성 시험의 출처에 근거한 질문 판단"} for j in range(1,count+1)]}
        for i,(name,count) in enumerate(counts)]}


class Arithmetic(unittest.TestCase):
    def test_known_fixture(self):
        r=sc.calculate(example());self.assertEqual(r['total'],'13.00');self.assertEqual(r['grade'],'D')

    def test_question_mean_rounds_before_composite(self):
        d=example();d['criteria'][2]['questions'][0]['score']=2.5
        r=sc.calculate(d)
        self.assertEqual(r['criteria'][2]['score'],'2.83')
        self.assertEqual(r['total'],'12.83')

    def test_weights_and_missing_question_renormalization(self):
        d=example();c=d['criteria'][0];c.update(aggregation='weighted_mean',weight_basis='TOR p.7')
        c['questions'][0].update(score=2,weight=.25)
        c['questions'][1].update(score=4,weight=.75)
        self.assertEqual(sc.calculate(d)['criteria'][0]['score'],'3.50')
        c['questions'][1].update(score=None,status='unavailable',fact_ids=[],reason='자료 미제공')
        r=sc.calculate(d);self.assertEqual(r['criteria'][0]['score'],'2.00')
        self.assertEqual(r['criteria'][0]['excluded_questions'],['q2'])
        self.assertTrue(r['conditional'])

    def test_unevaluable_criterion_withholds_total_and_grade(self):
        d=example();d['verification']='passed'
        for q in d['criteria'][4]['questions']:q.update(score=None,status='unavailable',fact_ids=[],reason='운영 원자료 없음')
        r=sc.calculate(d)
        self.assertIsNone(r['total']);self.assertIsNone(r['grade']);self.assertEqual(r['verification'],'conditional')

    def test_grade_boundaries(self):
        for score,grade in [(1,'F'),(2,'E'),(2.5,'D'),(3,'C'),(3.5,'B'),(4,'A')]:
            d=example()
            for c in d['criteria']:
                for q in c['questions']:q['score']=score
            self.assertEqual(sc.calculate(d)['grade'],grade)

    def test_omitted_conflict_metadata_is_not_rendered_as_no_conflicts(self):
        d=example();d['verification']='passed'
        r=sc.calculate(d)
        self.assertEqual(r['verification'],'conditional')
        self.assertIn('[INFO: 상충 ID 미기재',sc.summary_block(r))
        for c in d['criteria']:c['conflict_ids']=[]
        self.assertEqual(sc.calculate(d)['verification'],'passed')

    def test_invalid_question_scores_are_not_coerced(self):
        for score in (True,'3',0,4.5,3.25,float('nan'),float('inf')):
            with self.subTest(score=score):
                d=example();d['criteria'][0]['questions'][0]['score']=score
                with self.assertRaises(sc.Invalid):sc.calculate(d)

    def test_missing_evidence_and_false_unavailable_score_rejected(self):
        d=example();d['criteria'][0]['questions'][0]['fact_ids']=[]
        with self.assertRaises(sc.Invalid):sc.calculate(d)

    def test_local_conflicts_are_valid_before_verification_only(self):
        d=example();d['verification']='not_reviewed';d['criteria'][0]['conflict_ids']=['REL-X1']
        self.assertEqual(sc.calculate(d)['total'],'13.00')
        d['verification']='conditional'
        with self.assertRaises(sc.Invalid):sc.calculate(d)
        d['verification']='not_reviewed';d['criteria'][0]['conflict_ids']=['EFF-X1']
        with self.assertRaises(sc.Invalid):sc.calculate(d)
        d=example();d['criteria'][0]['questions'][0]['status']='unavailable'
        with self.assertRaises(sc.Invalid):sc.calculate(d)

    def test_missing_duplicate_and_extra_fields_rejected(self):
        variants=[]
        d=example();d['criteria'].pop();variants.append(d)
        d=example();d['criteria'][1]=copy.deepcopy(d['criteria'][0]);variants.append(d)
        d=example();d['criteria'][0]['questions'].pop();variants.append(d)
        d=example();d['criteria'][0]['questions'][1]['id']='q1';variants.append(d)
        d=example();d['total']=19;variants.append(d)
        d=example();d['criteria'][0]['questions'][0]['reason']='';variants.append(d)
        for d in variants:
            with self.assertRaises(sc.Invalid):sc.calculate(d)

    def test_invalid_or_unsourced_weights_rejected(self):
        d=example();c=d['criteria'][0];c['aggregation']='weighted_mean'
        for q in c['questions']:q['weight']=.5
        with self.assertRaises(sc.Invalid):sc.calculate(d)
        c['weight_basis']='TOR p.7';c['questions'][0]['weight']=.4
        with self.assertRaises(sc.Invalid):sc.calculate(d)

    def test_legacy_form_keeps_all_questions_and_documented_weights(self):
        d=example();d['profile']='koica-legacy-weighted'
        q=copy.deepcopy(d['criteria'][0]['questions'][0]);q.update(id='q3',score=1.5)
        d['criteria'][0]['questions'].append(q)
        for c in d['criteria']:
            c.update(aggregation='weighted_mean',weight_basis='해당 평가표 p.7')
            weights=[.4,.4,.2] if c['criterion']=='relevance' else ([.5,.3,.2] if c['criterion']=='effectiveness' else [.5,.5])
            for question,weight in zip(c['questions'],weights):question['weight']=weight
        self.assertEqual(sc.calculate(d)['criteria'][0]['score'],'2.70')

    def test_duplicate_json_keys_and_nan_rejected(self):
        for text in ('{"score":2,"score":4}','{"score":NaN}'):
            with self.assertRaises(sc.Invalid):sc.loads(text)

    def test_sensitivity_uses_changed_question_inputs(self):
        d=example();d['scenarios']=[{'id':'S1','reason':'X1의 다른 근거를 채택하는 경우','changes':[
            {'criterion':'relevance','question':'q1','score':4,'fact_ids':['F1'],'reason':'대안 근거'}]}]
        r=sc.calculate(d)
        self.assertEqual(r['total'],'13.00');self.assertEqual(r['scenarios'][0]['total'],'13.50')
        self.assertIn('13~13.5/20',sc.summary_block(r))
        d['scenarios'][0]['changes'][0]['question']='q9'
        with self.assertRaises(sc.Invalid):sc.calculate(d)


class Projection(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.data=example()
        self.scores=self.root/'verified-scores.json';self.scores.write_text(sc.dumps(self.data))
        self.brief=self.root/'brief.md'
        self.text=(ROOT/'tests/fixtures/auditable-brief-clean.md').read_text()
        rendered,_=sc.render_text(self.text,self.data)
        self.brief.write_text(rendered)

    def test_rendered_blocks_are_recomputable_and_idempotent(self):
        self.assertEqual(sc.verify_projection(self.brief)['grade'],'D')
        rendered,_=sc.render_text(self.brief.read_text(),self.data)
        self.assertEqual(rendered,self.brief.read_text())

    def test_tampered_total_grade_question_score_or_deleted_block_fails(self):
        good=self.brief.read_text()
        for bad in [good.replace('13/20, D','19/20, A'),good.replace('13/20, D','13/20, [A]'),
                    good.replace('| q1 | 평가 | 3 |','| q1 | 평가 | 4 |',1),
                    good.replace(sc.SUMMARY_END,'',1)]:
            self.brief.write_text(bad)
            with self.assertRaises(sc.Invalid):sc.verify_projection(self.brief)

    def test_modified_json_requires_new_projection(self):
        self.data['criteria'][0]['questions'][0]['score']=4
        self.scores.write_text(sc.dumps(self.data))
        with self.assertRaises(sc.Invalid):sc.verify_projection(self.brief)

    def test_cross_project_before_after_is_rejected(self):
        old=example();old['project']='other'
        with self.assertRaises(sc.Invalid):sc.render_text(self.text,self.data,old)

    def test_not_reviewed_and_rejected_are_not_final_reports(self):
        for status in ('not_reviewed','rejected'):
            self.data['verification']=status
            with self.assertRaises(sc.Invalid):sc.render_text(self.text,self.data)

    def test_cli_does_not_overwrite_score_input_with_result(self):
        before=self.scores.read_bytes()
        r=subprocess.run([sys.executable,str(ROOT/'scripts/score_calculate.py'),'calculate','--input',str(self.scores),'--out',str(self.scores)],capture_output=True)
        self.assertEqual(r.returncode,2);self.assertEqual(self.scores.read_bytes(),before)

    def test_collection_reads_each_role_json_without_averaging_by_llm(self):
        for c in self.data['criteria']:
            (self.root/(c['criterion']+'.md')).write_text('Judgment\n```json\n'+sc.dumps(c)+'```\n')
        manifest=self.root/'manifest.json';manifest.write_text('{"source_sha256":"'+'0'*64+'"}')
        out=self.root/'ratings.json'
        r=subprocess.run([sys.executable,str(ROOT/'scripts/score_calculate.py'),'collect','--directory',str(self.root),'--manifest',str(manifest),'--project','example','--out',str(out)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(sc.calculate(sc.load(out))['total'],'13.00')
        self.assertEqual(sc.load(out)['verification'],'not_reviewed')

    def test_final_audit_binds_json_and_generated_values(self):
        cmd=[sys.executable,str(ROOT/'scripts/auditable_output_check.py'),str(self.brief),'--require-scores']
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.brief.write_text(self.brief.read_text().replace('13/20, D','13/20, [A]'))
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertIn('정본',r.stderr)

    def test_final_audit_rejects_absent_contract_and_unknown_evidence(self):
        self.brief.write_text(self.text)
        cmd=[sys.executable,str(ROOT/'scripts/auditable_output_check.py'),str(self.brief),'--require-scores']
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
        self.data['criteria'][0]['questions'][0]['fact_ids']=['F999']
        self.scores.write_text(sc.dumps(self.data))
        self.brief.write_text(sc.render_text(self.text,self.data)[0])
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertIn('F999',r.stderr)

    def test_final_score_conflicts_must_exist_in_register(self):
        self.data['criteria'][0]['conflict_ids']=['X999']
        self.scores.write_text(sc.dumps(self.data));self.brief.write_text(sc.render_text(self.text,self.data)[0])
        r=subprocess.run([sys.executable,str(ROOT/'scripts/auditable_output_check.py'),str(self.brief),'--require-scores'],capture_output=True,text=True)
        self.assertEqual(r.returncode,2,r.stdout+r.stderr);self.assertIn('X999',r.stderr)


if __name__=='__main__':unittest.main()
