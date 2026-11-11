"""CPU regression checks of pinned reset implementation; not a renderer test."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'third_party/IsaacLab/source/isaaclab/isaaclab'
def method(path,cls,name):
    tree=ast.parse(path.read_text());c=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==cls)
    f=next(x for x in c.body if isinstance(x,ast.FunctionDef) and x.name==name)
    f.returns=None
    for arg in f.args.args:arg.annotation=None
    f.decorator_list=[]
    module=ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[]));ns={};exec(compile(module,str(path),'exec'),ns);return ns[name]

class ResetContractTest(unittest.TestCase):
    def exercise(self, enabled):
        events=[];env=NS(num_envs=1,cfg=NS(rerender_on_reset=enabled,wait_for_textures=False),extras={},state='previous',rendered='previous')
        env.seed=lambda seed:events.append('seed')
        def reset(ids):env.state='reset';events.append('new_state');env.outdated=True
        env._reset_idx=reset
        env.scene=NS(write_data_to_sim=lambda:events.append('write_state'))
        def render():env.rendered=env.state;events.append('render')
        env.sim=NS(forward=lambda:events.append('forward'),has_rtx_sensors=lambda:True,render=render)
        env.recorder_manager=NS(record_pre_reset=lambda ids:events.append('pre_reset'),record_post_reset=lambda ids:events.append('initial_state'))
        def compute(**kw):
            events.append('camera_read');events.append('policy_compute')
            return {'policy':{'rgb':env.rendered,'robot':env.state}}
        env.observation_manager=NS(compute=compute)
        result=method(LAB/'envs/manager_based_env.py','ManagerBasedEnv','reset')(env,seed=1,env_ids=[0])
        key,value=method(LAB/'envs/mdp/recorders/recorders.py','PreStepFlatPolicyObservationsRecorder','record_pre_step')(NS(_env=env))
        events.append('first_obs_record');events.append('first_action_physics')
        self.assertEqual(key,'obs');self.assertIs(value,result[0]['policy'])
        return value,events
    def test_disabled_reproduces_stale_rgb(self):
        v,_=self.exercise(False);self.assertEqual(v,{'rgb':'previous','robot':'reset'})
    def test_native_refresh_before_first_record(self):
        v,events=self.exercise(True);self.assertEqual(v,{'rgb':'reset','robot':'reset'})
        self.assertLess(events.index('new_state'),events.index('render'))
        self.assertLess(events.index('render'),events.index('camera_read'))
        self.assertLess(events.index('policy_compute'),events.index('first_obs_record'))
        self.assertLess(events.index('first_obs_record'),events.index('first_action_physics'))
    def test_both_launchers_enable_native_refresh_before_creation(self):
        for filename in ('teleop_toast.py','record_toast_noinput.py'):
            tree=ast.parse(Path(__file__).with_name(filename).read_text())
            settings=[x for x in ast.walk(tree) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='rerender_on_reset' for t in x.targets)]
            self.assertEqual(len(settings),1);self.assertIs(settings[0].value.value,True)
            creations=[x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='make']
            self.assertLess(settings[0].lineno,min(x.lineno for x in creations))
    def test_native_step_records_before_physics(self):
        s=(LAB/'envs/manager_based_rl_env.py').read_text()
        self.assertLess(s.index('self.recorder_manager.record_pre_step()'),s.index('self.sim.step(render=False)'))
    def test_native_sensor_reset_invalidates_cache(self):
        s=(LAB/'sensors/sensor_base.py').read_text();self.assertIn('self._is_outdated[env_ids] = True',s)
        s=(LAB/'envs/manager_based_env.py').read_text();self.assertLess(s.index('if self.sim.has_rtx_sensors() and self.cfg.rerender_on_reset:'),s.index('self.obs_buf = self.observation_manager.compute(update_history=True)'))

if __name__=='__main__':unittest.main()
