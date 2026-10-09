import unittest,json
from pathlib import Path
from main import *
class Tests(unittest.TestCase):
    def sample(self):return json.loads(Path(__file__).with_name('sample-input.json').read_text(encoding='utf-8'))

    def test_improves_and_no_actuation(self):
        o=run(self.sample());self.assertTrue(o['approved']);self.assertEqual(o['proposed_offset'],2);self.assertAlmostEqual(o['candidate_validation_mae'],0.1);self.assertFalse(o['applied_to_production'])
    def test_validation_shift_blocks(self):
        d=self.sample()
        for r in d['validation']:r['observed']=r['predicted']-2
        o=run(d);self.assertFalse(o['approved']);self.assertIn('insufficient_improvement',o['reasons'])
    def test_offset_bound(self):
        d=self.sample();d['max_offset']=1;self.assertIn('offset_limit_exceeded',run(d)['reasons'])
    def test_temporal_leakage_and_nan(self):
        d=self.sample();d['validation'][0]['time_s']=2
        with self.assertRaises(ValueError):run(d)
        d=self.sample();d['train'][0]['observed']=float('nan')
        with self.assertRaises(ValueError):run(d)

if __name__=="__main__":unittest.main()
