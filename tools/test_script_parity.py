#!/usr/bin/env python3
"""Regression corpus comparing JSON and exit codes, not universal or live-agent E2 evidence."""
from pathlib import Path
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile, unittest
from datetime import date
ROOT=Path(__file__).resolve().parents[1];PACKAGE=ROOT/'skill/orchestrate-agent-organization';SCRIPTS=PACKAGE/'scripts'
SHELL=shutil.which('pwsh') or shutil.which('powershell')
def asset(name):return json.loads((PACKAGE/'assets'/name).read_text(encoding='utf-8'))
def write(path,value):path.write_text(json.dumps(value)+'\n',encoding='utf-8',newline='\n')
class Parity(unittest.TestCase):
    def pair(self,stem,pyargs,psargs,code):
        self.assertIsNotNone(SHELL,'PowerShell is required; parity must not silently skip')
        outputs=[]
        for command in [[sys.executable,str(SCRIPTS/(stem+'.py')),*pyargs],[SHELL,'-NoProfile','-NonInteractive','-File',str(SCRIPTS/(stem+'.ps1')),*psargs]]:
            environment=dict(os.environ,PYTHONIOENCODING='cp1252')
            result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=30,cwd=ROOT,env=environment)
            self.assertEqual(code,result.returncode,result.stdout+result.stderr)
            outputs.append(json.loads(result.stdout.lstrip('\ufeff')))
        self.assertEqual(*outputs);return outputs[0]
    def test_capacity(self):
        valid=asset('first-trial-capacity.json');valid.update(runtime_active_agents=['/root'],runtime_snapshot_source='collaboration.list_agents',decision_level=2)
        boundary=copy.deepcopy(valid);boundary['runtime_active_limit']=1
        invalid=copy.deepcopy(valid);invalid['runtime_snapshot_source']='manual'
        with tempfile.TemporaryDirectory() as raw:
            for label,value,code in [('valid',valid,0),('boundary',boundary,0),('invalid',invalid,2)]:
                path=Path(raw)/(label+'.json');write(path,value);out=self.pair('plan_capacity',[str(path)],[str(path)],code)
                if label=='valid':
                    self.assertEqual(out['recommended_children'],2)
                    self.assertEqual(out['allowed_pre_authorization_stages'],['control','design','discovery','verify'])
                if label=='boundary':self.assertEqual(out['recommended_children'],0)
                if label=='invalid':self.assertEqual(out['error'],'runtime_snapshot_source is not allowed')
    def test_portfolio(self):
        valid=asset('first-trial-studio.json');item=valid['portfolio_items'][0]
        item.update(current_state='discovery',founder_charter_status='authorized',user_evidence=3,outcome_evidence=0,urgency=2,confidence=2,investment_units=4,human_attention_units=1,maintenance_units=1,risk_capacity_units=1,reality_evidence_refs=[])
        boundary=copy.deepcopy(valid);boundary['portfolio_active_limit']=0
        invalid=copy.deepcopy(valid);invalid['company_policy_version']='company-v4'
        with tempfile.TemporaryDirectory() as raw:
            for label,value,code in [('valid',valid,0),('boundary',boundary,0),('invalid',invalid,2)]:
                path=Path(raw)/(label+'.json');write(path,value);out=self.pair('plan_portfolio',[str(path)],[str(path)],code)
                if label=='valid':self.assertEqual(out['selected_new_investments'],['first-idea'])
                if label=='boundary':self.assertEqual(out['queued_investments'],['first-idea'])
                if label=='invalid':self.assertEqual(out['error'],'company_policy_version must be company-v5')
    def test_charter(self):
        parent=dict(id='/root',runtime_snapshot_source='collaboration.list_agents',runtime_active_agents=['/root'],authorized_auditor_ids=['/root'],company_policy_version='company-v5',delegable_permissions=['repo:read'],authorized_workspace_ids=[],reserved_workspace_ids=[],reserved_write_scopes=[],budget=dict(token_units=10,cash=0,compute_units=0),reserved_budget=dict(token_units=2,cash=0,compute_units=0),spawn_quota=1,reserved_spawn_units=0,current_depth=0,max_depth=1,ttl_minutes=30)
        child=dict(id='/root/review',parent_id='/root',mission='Review one artifact',deliverables=['Findings'],success_criteria=['Evidence cited'],company_policy_version='company-v5',lifecycle_stage='verify',cognitive_mode='adversarial-review',context_budget_units=2,artifact_budget_units=1,context_sources=['src/'],learning_authority='none',token_tier='low',permissions=['repo:read'],delegable_permissions=[],budget=dict(token_units=4,cash=0,compute_units=0),spawn_quota=0,current_depth=1,max_depth=1,ttl_minutes=15,auditor_id='/root',auditor_independence='parent-accountable',write_scope_mode='read-only',write_scope=[],workspace_id='none',stop_conditions=['Review complete'])
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'parent.json';c=Path(raw)/'child.json';write(p,parent)
            for units,ttl,code in [(4,15,0),(8,30,0),(9,30,2)]:
                child['budget']['token_units']=units;child['ttl_minutes']=ttl;write(c,child)
                out=self.pair('validate_charter',['--parent',str(p),'--child',str(c)],['-Parent',str(p),'-Child',str(c)],code)
                self.assertEqual(out['valid'],code==0)
                if code:self.assertEqual(out['errors'],['reserved plus child budget for token_units exceeds parent.budget.token_units'])
            child['budget']['token_units']=4;child['ttl_minutes']=15;parent['delegable_permissions']=[]
            child['permissions']=['\U00010000','\ue000','x_1','x-2'];write(p,parent);write(c,child)
            out=self.pair('validate_charter',['--parent',str(p),'--child',str(c)],['-Parent',str(p),'-Child',str(c)],2)
            self.assertEqual(out['errors'],['child permissions exceed parent delegation: x-2, x_1, \ue000, \U00010000'])
    def test_integration(self):
        empty=dict(schema_version='assurance-v1',manifest_id='M-empty',decision_id='D-empty',as_of='2026-10-12',authorized_verifiers=['verifier-example'],findings=[],required_subjects=[],evidence_catalog=[])
        packet=dict(schema_version='integration-v2',decision_id='',assurance_manifest={},review_findings=[],obligations=[],operating_controls=[],authority_gates=[])
        bound=asset('assurance-manifest.template.json');bound.update(manifest_id='M-boundary',decision_id='D-boundary',as_of='2026-10-12')
        good=asset('integration-packet.template.json');bad=copy.deepcopy(good);bad['operating_controls'][0]['recommended_action']='resume'
        empty['as_of']=date.today().isoformat();bound['as_of']=date.today().isoformat()
        with tempfile.TemporaryDirectory() as raw:
            m=Path(raw)/'manifest.json';p=Path(raw)/'packet.json'
            for label,manifest,value,code in [('valid',empty,packet,0),('boundary',bound,good,0),('invalid',bound,bad,2)]:
                write(m,manifest);digest=hashlib.sha256(m.read_bytes()).hexdigest();value=copy.deepcopy(value);value.update(decision_id=manifest['decision_id'],assurance_manifest=dict(id=manifest['manifest_id'],sha256=digest));write(p,value)
                out=self.pair('validate_integration',[str(p),str(m),digest],[str(p),str(m),digest],code)
                if label=='valid':self.assertTrue(out['canonical_delivery_sha256'])
                if label=='boundary':self.assertFalse(out['advancement_allowed_by_subject']['asset-example']);self.assertEqual(out['open_high_severity_obligations'],['F-001'])
                if label=='invalid':self.assertIn('operating_controls[0] attempts advancement while blockers remain',out['errors'])
            multi=copy.deepcopy(bound);multi['findings']=[];multi['required_subjects']=[]
            for subject_id in ['x_1','x-2']:
                subject=copy.deepcopy(bound['required_subjects'][0]);subject['subject_id']=subject_id;subject['required_authority_gates']=[];multi['required_subjects'].append(subject)
            multi_packet=copy.deepcopy(good);multi_packet.update(review_findings=[],obligations=[],authority_gates=[],operating_controls=[])
            for subject_id in ['x_1','x-2']:
                control=copy.deepcopy(good['operating_controls'][0]);control['subject_id']=subject_id;multi_packet['operating_controls'].append(control)
            write(m,multi);digest=hashlib.sha256(m.read_bytes()).hexdigest();multi_packet.update(decision_id=multi['decision_id'],assurance_manifest=dict(id=multi['manifest_id'],sha256=digest));write(p,multi_packet)
            out=self.pair('validate_integration',[str(p),str(m),digest],[str(p),str(m),digest],0)
            self.assertEqual(list(out['advancement_allowed_by_subject']),['x-2','x_1'])
            text=out['canonical_delivery_markdown'];self.assertLess(text.index('- x-2:'),text.index('- x_1:'))
            self.assertEqual(out['canonical_delivery_sha256'],hashlib.sha256(text.encode('utf-8')).hexdigest())
    def test_capacity_unicode_scalar_tie_break(self):
        value=asset('first-trial-capacity.json');exemplar=value['items'][0];value['items']=[]
        for item_id in ['x_1','x-2']:
            item=copy.deepcopy(exemplar);item['id']=item_id;value['items'].append(item)
        value.update(runtime_active_limit=2,runtime_active_agents=['/root'],runtime_snapshot_source='collaboration.list_agents')
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/'capacity.json';write(path,value);out=self.pair('plan_capacity',[str(path)],[str(path)],0)
        self.assertEqual(out['delegated_workstreams'],['x-2']);self.assertEqual(out['lead_or_queued_workstreams'],['x_1'])
    def test_portfolio_unicode_scalar_tie_break(self):
        value=asset('first-trial-studio.json');exemplar=value['portfolio_items'][0]
        exemplar.update(current_state='discovery',founder_charter_status='authorized',user_evidence=3,outcome_evidence=0,urgency=2,confidence=2,investment_units=4,human_attention_units=1,maintenance_units=1,risk_capacity_units=1,reality_evidence_refs=[])
        value['portfolio_active_limit']=1;value['portfolio_items']=[]
        for item_id in ['x_1','x-2']:
            item=copy.deepcopy(exemplar);item['id']=item_id;value['portfolio_items'].append(item)
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/'portfolio.json';write(path,value);out=self.pair('plan_portfolio',[str(path)],[str(path)],0)
        self.assertEqual(out['selected_new_investments'],['x-2']);self.assertEqual(out['queued_investments'],['x_1'])
        self.assertEqual([item['id'] for item in out['recommendations']],['x-2','x_1'])
    def test_first_trial_is_non_authoritative(self):
        for stem,name in [('plan_capacity','first-trial-capacity.json'),('plan_portfolio','first-trial-studio.json')]:
            path=str(PACKAGE/'assets'/name);out=self.pair(stem,[path],[path],0)
            if stem=='plan_capacity':
                self.assertFalse(out['runtime_snapshot_authoritative']);self.assertEqual(out['recommended_children'],1)
                self.assertEqual(out['delegated_workstreams'],['implementation']);self.assertEqual(out['lead_or_queued_workstreams'],['documentation'])
            else:
                self.assertEqual(out['recommendations'][0]['recommended_action'],'discover')
                self.assertEqual(out['recommendations'][0]['recommended_next_state'],'discovery')
                self.assertTrue(out['recommendations'][0]['hard_gate_or_obligation'])
if __name__=='__main__':unittest.main(verbosity=2)
