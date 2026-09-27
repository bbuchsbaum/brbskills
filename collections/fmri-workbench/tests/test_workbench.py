import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'shared/scripts'));import workbench as w
sys.path.insert(0,str(ROOT/'skills/fmri-bids/scripts'));import profile_table
sys.path.insert(0,str(ROOT/'tools'));import install,audit_bundle
import jsonschema

class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=Path(self.temp.name)
    def ready(self,stage='first_level',purpose='pilot'):
        p=w.new_plan('demo',[stage]);p['stage_configs'][stage]={'reviewed_native_code':'analysis.R'}
        p['decisions'][0].update(value='A minus B',status='confirmed')
        for c in p['checks']:c.update(status='pass',evidence='synthetic test evidence')
        if purpose=='full' and stage in ('first_level','group'):p['checks'].append(dict(id='pilot_qc',stage=stage,status='pass',blocking=True,evidence='test pilot'))
        p['data_policy']['model_visible']='synthetic';p['budget'].update(approved=True,cpu_hours=1,max_memory_gb=1)
        for name in ['inputs','code','environment']:
            path=self.p/name;path.write_text('fixture '+name);p['fingerprints'][name]={'path':str(path),'sha256':w.file_sha(path)}
        return p
    def pref(self,key='first_level.confounds',value='motion24',when=None):
        return w.mutate_preference(w.empty_preferences(),key,when or {},value,confirmed=True,evidence='explicit test consent')
    def row(self,**kw):
        d=dict(path='bold.nii.gz',selected=True,subject='01',session='01',task='memory',run='01',tr=2,nvols=100,
               confound_rows=100,event_file='events.tsv',confound_file='confounds.tsv',mask='mask.nii.gz',grid_id='grid',timing_origin='first_stored_volume',pipeline='fmriprep',space='MNI',resolution='2')
        d.update(kw);return d
    def test_new_plan_blocked(self):self.assertTrue(w.plan_errors(w.new_plan('a',['first_level'])))
    def test_plan_schema(self):jsonschema.validate(self.ready(),json.loads((ROOT/'shared/schemas/plan.schema.json').read_text()))
    def test_approval_requires_consent(self):
        p=self.ready()
        with self.assertRaises(ValueError):w.authorize(p,'first_level','pilot',w.plan_digest(p),False,'test')
    def test_approval_requires_evidence(self):
        p=self.ready()
        with self.assertRaises(ValueError):w.authorize(p,'first_level','pilot',w.plan_digest(p),True,'')
    def test_pilot_approval(self):
        p=self.ready();p=w.authorize(p,'first_level','pilot',w.plan_digest(p),True,'test approval');self.assertEqual(w.approval_errors(p,'first_level','pilot'),[])
    def test_full_needs_pilot(self):self.assertTrue(any('pilot_qc' in x for x in w.plan_errors(self.ready(),'first_level','full')))
    def test_full_valid(self):self.assertEqual(w.plan_errors(self.ready(purpose='full'),'first_level','full'),[])
    def test_material_unresolved(self):
        p=self.ready();p['decisions'][0]['status']='proposed';self.assertTrue(w.plan_errors(p,'first_level','pilot'))
    def test_changed_plan_invalidates(self):
        p=self.ready();p=w.authorize(p,'first_level','pilot',w.plan_digest(p),True,'test');p['stage_configs']['first_level']['changed']=True
        self.assertTrue(any('stale' in x for x in w.approval_errors(p,'first_level','pilot')))
    def test_changed_code_invalidates(self):
        p=self.ready();p=w.authorize(p,'first_level','pilot',w.plan_digest(p),True,'test');(self.p/'code').write_text('changed')
        self.assertTrue(any('Changed sealed file' in x for x in w.approval_errors(p,'first_level','pilot')))
    def test_digest_ignores_approval_only(self):
        p=self.ready();q=copy.deepcopy(p);q['approval']['x']={};self.assertEqual(w.plan_digest(p),w.plan_digest(q));q['budget']['max_workers']=2;self.assertNotEqual(w.plan_digest(p),w.plan_digest(q))
    def test_scope_mismatch(self):self.assertTrue(w.plan_errors(self.ready(),'group','pilot'))
    def test_bad_budget(self):
        p=self.ready();p['budget']['max_workers']=True;self.assertTrue(w.plan_errors(p,'first_level','pilot'))
    def test_duplicate_check(self):
        p=self.ready();p['checks'].append(p['checks'][0]);self.assertTrue(w.plan_errors(p,'first_level','pilot'))
    def test_preference_consent(self):
        with self.assertRaises(ValueError):w.mutate_preference(w.empty_preferences(),'first_level.confounds',{},'motion24')
    def test_preference_schema(self):jsonschema.validate(self.pref(),json.loads((ROOT/'shared/schemas/preferences.schema.json').read_text()))
    def test_empty_defaults(self):self.assertEqual(w.empty_preferences()['preferences'],[])
    def test_conditional_scope(self):
        p=self.pref(when={'analysis':'task_glm'});self.assertEqual(w.resolve_preferences(p,w.empty_preferences(),{'analysis':'rest'})['values'],{})
    def test_exact_bool_vs_integer(self):
        p=self.pref(when={'flag':True});self.assertEqual(w.resolve_preferences(p,w.empty_preferences(),{'flag':1})['values'],{})
    def test_project_over_user(self):
        out=w.resolve_preferences(self.pref(),self.pref(value='motion6'),{});self.assertEqual(out['values']['first_level.confounds'],'motion6')
    def test_current_over_profiles(self):
        out=w.resolve_preferences(self.pref(),w.empty_preferences(),{},current={'first_level.confounds':'motion6'});self.assertEqual(out['values']['first_level.confounds'],'motion6')
    def test_locked_conflict(self):
        out=w.resolve_preferences(self.pref(),w.empty_preferences(),{},locked_values={'first_level.confounds':'motion6'});self.assertTrue(out['conflicts']);self.assertNotIn('first_level.confounds',out['values'])
    def test_ambiguous_specificity(self):
        p=self.pref(when={'task':'memory'});p=w.mutate_preference(p,'first_level.confounds',{'pipeline':'fmriprep'},'motion6',confirmed=True,evidence='test')
        self.assertTrue(w.resolve_preferences(p,w.empty_preferences(),{'task':'memory','pipeline':'fmriprep'})['conflicts'])
    def test_most_specific(self):
        p=self.pref();p=w.mutate_preference(p,'first_level.confounds',{'task':'memory'},'motion6',confirmed=True,evidence='test')
        self.assertEqual(w.resolve_preferences(p,w.empty_preferences(),{'task':'memory'})['values']['first_level.confounds'],'motion6')
    def test_remove(self):
        p=w.mutate_preference(self.pref(),'first_level.confounds',{},remove=True,confirmed=True,evidence='forget test');self.assertEqual(p['preferences'],[])
    def test_preference_not_authorization(self):
        with self.assertRaises(ValueError):self.pref(key='authorization.approved',value=True)
    def test_json_value_inert(self):
        p=self.pref(key='x.demo',value='__import__("os").system("never")');self.assertEqual(p['preferences'][0]['value'],'__import__("os").system("never")')
    def test_inventory_requires_selection(self):self.assertTrue(w.audit_inventory({'runs':[self.row(selected=False)]})['errors'])
    def test_inventory_never_certifies(self):self.assertFalse(w.audit_inventory({'runs':[self.row()]})['from_bids_certified'])
    def test_duplicate_echo(self):
        out=w.audit_inventory({'runs':[self.row(echo='1'),self.row(path='echo2.nii.gz',echo='2')]});self.assertTrue(out['errors'])
    def test_sessions_repeat_run(self):
        out=w.audit_inventory({'runs':[self.row(),self.row(session='02',path='ses2.nii.gz')]});self.assertEqual(out['errors'],[]);self.assertTrue(any('repeated run' in x for x in out['from_bids_shortcut_blockers']))
    def test_mixed_tr(self):
        out=w.audit_inventory({'runs':[self.row(),self.row(run='02',path='run2.nii.gz',tr=1.5)]});self.assertTrue(any('Mixed TR' in x for x in out['from_bids_shortcut_blockers']))
    def test_confound_rows(self):self.assertTrue(w.audit_inventory({'runs':[self.row(confound_rows=99)]})['errors'])
    def test_profile_does_not_expose_labels(self):
        p=self.p/'events.tsv';p.write_text('onset\tduration\ttrial_type\n-2\t0\tsecret\n2\t1\tother\n')
        out=profile_table.profile(p);self.assertNotIn('secret',json.dumps(out));self.assertEqual(out['columns']['onset']['min'],-2);self.assertEqual(out['columns']['duration']['min'],0)
    def test_profile_na(self):
        p=self.p/'c.tsv';p.write_text('x\nNA\n1\n3\n');out=profile_table.profile(p);self.assertEqual(out['columns']['x']['missing'],1);self.assertEqual(out['columns']['x']['mean'],2)
    def test_profile_malformed(self):
        p=self.p/'c.tsv';p.write_text('a\tb\n1\n')
        with self.assertRaises(ValueError):profile_table.profile(p)
    def test_install_single_leaf(self):
        out=install.install('codex',self.p,skills=['fmrireg']);target=Path(out[0]);self.assertTrue((target/'scripts/workbench.py').is_file());self.assertFalse((target.parent/'fmrigds').exists());self.assertFalse((self.p/'AGENTS.md').exists());self.assertFalse((self.p/'.claude').exists())
        result=subprocess.run([sys.executable,str(target/'scripts/workbench.py'),'--help'],capture_output=True);self.assertEqual(result.returncode,0)
    def test_install_no_overwrite(self):
        install.install('claude',self.p,skills=['fmrireg'])
        with self.assertRaises(ValueError):install.install('claude',self.p,skills=['fmrireg'])
    def test_install_unknown(self):
        with self.assertRaises(ValueError):install.install('claude',self.p,skills=['../bad'])
    def test_bundle_audit(self):self.assertEqual(audit_bundle.audit()['errors'],[])
    def test_new_plan_cli_no_overwrite(self):
        args=[sys.executable,str(ROOT/'shared/scripts/workbench.py'),'init',str(self.p/'p.json'),'--analysis-id','a','--scope','first_level']
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,0);self.assertEqual(subprocess.run(args,capture_output=True).returncode,2)
    def test_lock_exclusion(self):
        with w.locked(self.p/'data.json'):
            with self.assertRaises(ValueError):
                with w.locked(self.p/'data.json'):pass
if __name__=='__main__':unittest.main()
