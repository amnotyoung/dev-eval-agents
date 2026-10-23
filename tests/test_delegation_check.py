"""Isolation is based on native calls, not an agent's assertion that it was independent."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import delegation_check as dc


class DelegationContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.brief = self.root / "brief.md"
        self.brief.write_text("# Example\n## 1. 평가 범위·자료·방법\nSource\n## 2. 원문 사실대장\nF1: fact\n## 3. 종합 평정\nPEER_SCORE_CANARY=4\n")
        self.source = self.root / "source.md"; self.source.write_text("source")
        self.index = self.root / "index.md"; self.index.write_text("index")
        self.path, self.manifest = dc.prepare(self.brief, self.source, self.index, self.root)
        self.prompt = f"Read {self.manifest['packet']} [DEVEVAL_PACKET_SHA256: {self.manifest['packet_sha256']}] [DEVEVAL_INPUT_SHA256: {self.manifest['input_sha256']}]"

    def trace(self, rows):
        path = self.root / "trace.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return path

    def codex(self, fork="none"):
        rows = [{"type": "session_meta", "payload": {"id": "root", "cwd": str(self.root)}}]
        # Parent-only data must not become part of a worker's input packet.
        rows.append({"type": "response_item", "payload": {"type": "message", "content": "PEER_SCORE_CANARY=4"}})
        for name in dc.CRITERIA:
            rows.extend([
                {"type": "response_item", "payload": {"type": "function_call", "name": "spawn_agent", "call_id": name,
                    "arguments": json.dumps({"task_name": self.manifest['task_names'][name], "fork_turns": fork, "message": self.prompt})}},
                {"type": "response_item", "payload": {"type": "function_call_output", "call_id": name,
                    "output": json.dumps({"task_name": "/root/" + self.manifest['task_names'][name]})}},
            ])
        return rows

    def test_prepare_excludes_peer_ratings_and_preserves_existing_run(self):
        self.assertNotIn("PEER_SCORE_CANARY", Path(self.manifest['packet']).read_text())
        with self.assertRaisesRegex(ValueError, "이미 생성됨"):
            dc.prepare(self.brief, self.source, self.index, self.root)
        self.path.unlink()
        self.brief.write_text(self.brief.read_text().replace("F1: fact", "F1: changed"))
        with self.assertRaisesRegex(ValueError, "새 실행 폴더"):
            dc.prepare(self.brief, self.source, self.index, self.root)

    def test_new_run_cannot_reuse_old_native_calls(self):
        trace=self.trace(self.codex())
        self.path.unlink()
        new_path,new_manifest=dc.prepare(self.brief,self.source,self.index,self.root)
        self.assertNotEqual(new_manifest['run_id'],self.manifest['run_id'])
        self.assertEqual(dc.verify(new_path,trace)['status'],'failed')

    def test_five_successful_empty_history_calls_pass(self):
        result = dc.verify(self.path, self.trace(self.codex()))
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(len(result['criterion_calls']), 5)

    def test_inherited_or_omitted_fork_is_rejected(self):
        for fork in ("all", None):
            result = dc.verify(self.path, self.trace(self.codex(fork)))
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(len(result['violations']), 5)

    def test_missing_role_and_failed_spawn_cannot_pass(self):
        rows = self.codex()[:-2]
        self.assertEqual(dc.verify(self.path, self.trace(rows))['status'], 'failed')
        rows = self.codex(); rows[-1]['payload']['output'] = '{"error":"limit"}'
        self.assertEqual(dc.verify(self.path, self.trace(rows))['status'], 'failed')

    def test_stale_packet_and_wrong_workspace_cannot_pass(self):
        rows = self.codex(); rows[0]['payload']['cwd'] = str(self.root / "other")
        self.assertEqual(dc.verify(self.path, self.trace(rows))['status'], 'failed')
        self.source.write_text('changed after delegation')
        self.assertEqual(dc.verify(self.path, self.trace(self.codex()))['status'], 'failed')

    def test_peer_result_path_in_explicit_prompt_is_rejected(self):
        self.prompt += ' also read criterion-drafts.md'
        result = dc.verify(self.path, self.trace(self.codex()))
        self.assertEqual(result['status'], 'failed')

    def test_rehashing_changed_source_does_not_rewrite_native_call_evidence(self):
        trace=self.trace(self.codex())
        self.source.write_text('changed')
        self.manifest['source_sha256']=dc.digest(self.source)
        self.manifest['input_sha256']=dc.input_digest(self.manifest)
        self.path.write_text(json.dumps(self.manifest))
        self.assertEqual(dc.verify(self.path,trace)['status'],'failed')

    def test_another_project_in_same_parent_trace_does_not_invalidate_receipt(self):
        rows=self.codex(); extra=copy.deepcopy(rows[-2:])
        a=json.loads(extra[0]['payload']['arguments'])
        a['message']='Other /work/other/source-pack.md [DEVEVAL_INPUT_SHA256: '+'a'*64+']'
        a['task_name']='sustainability_r'+'a'*16
        extra[0]['payload']['arguments']=json.dumps(a)
        extra[0]['payload']['call_id']='other';extra[1]['payload']['call_id']='other'
        result=dc.verify(self.path,self.trace(rows+extra))
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(len(result['criterion_calls']),5)

    def test_native_redacted_messages_use_clear_scope_and_disclose_limit(self):
        rows=self.codex()
        for row in rows:
            p=row.get('payload',{})
            if p.get('type')=='function_call':
                a=json.loads(p['arguments']);a['message']='gAAAAA'+'x'*100+'=='
                p['arguments']=json.dumps(a)
        r=dc.verify(self.path,self.trace(rows))
        self.assertEqual(r['status'],'passed',r)
        self.assertFalse(r['prompt_bodies_verified']);self.assertTrue(r['limitations'])
        for row in rows:
            p=row.get('payload',{})
            if p.get('type')=='function_call':
                a=json.loads(p['arguments']);a['fork_turns']='all';p['arguments']=json.dumps(a)
        self.assertEqual(dc.verify(self.path,self.trace(rows))['status'],'failed')

    def test_receipt_is_rechecked_against_native_evidence(self):
        trace = self.trace(self.codex())
        receipt = self.root / 'isolation.json'
        receipt.write_text(json.dumps(dc.verify(self.path, trace)))
        self.assertEqual(dc.verify_receipt(receipt)['status'], 'passed')
        self.trace(self.codex('all'))
        self.assertEqual(dc.verify_receipt(receipt)['status'], 'failed')

    def test_claude_fresh_registered_agent_and_resume(self):
        rows = [{'sessionId':'root','cwd':str(self.root),'type':'user'}]
        for name in dc.CRITERIA:
            rows.extend([
                {'type':'assistant','message':{'content':[{'type':'tool_use','id':name,'name':'Agent',
                    'input':{'subagent_type':'deveval:dac-'+name+'-evaluator','run_in_background':False,'prompt':self.prompt}}]}},
                {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':name,'content':'result'}]}},
            ])
        self.assertEqual(dc.verify(self.path, self.trace(rows))['status'], 'passed')
        rows[1]['message']['content'][0]['input']['resume'] = 'old-session'
        self.assertEqual(dc.verify(self.path, self.trace(rows))['status'], 'failed')

    def test_unsupported_or_missing_trace_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            dc.verify(self.path, self.trace([{'unknown':'format'}]))
        with self.assertRaises(OSError):
            dc.verify(self.path, self.root/'missing.jsonl')

    def test_claude_project_directory_escapes_dots_and_spaces(self):
        project=self.root/'project.with space';project.mkdir()
        config=self.root/'claude-config'
        folder=config/'projects'/re.sub(r'[^A-Za-z0-9]','-',str(project))
        folder.mkdir(parents=True)
        transcript=folder/'session.jsonl'
        transcript.write_text(json.dumps({'sessionId':'session','cwd':str(project),'type':'user'})+'\n')
        with patch.dict('os.environ',{'CODEX_HOME':str(self.root/'empty-codex'),'CLAUDE_CONFIG_DIR':str(config)}):
            self.assertEqual(dc.find_transcript(project),transcript)

    def test_final_audit_requires_and_rechecks_receipt(self):
        final = self.root/'final.md'
        final.write_text((ROOT/'tests/fixtures/auditable-brief-clean.md').read_text())
        command = [sys.executable,str(ROOT/'scripts/auditable_output_check.py'),str(final),'--require-isolation']
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,3)
        trace = self.trace(self.codex())
        receipt = self.root/'isolation.json'
        receipt.write_text(json.dumps(dc.verify(self.path,trace)))
        good = subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(good.returncode,0,good.stdout+good.stderr)
        self.trace(self.codex('all'))
        bad = subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(bad.returncode,2,bad.stdout+bad.stderr)


if __name__ == '__main__':
    unittest.main()
