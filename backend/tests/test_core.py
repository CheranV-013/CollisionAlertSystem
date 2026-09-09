import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.geo import *
from app.risk import *

def test_haversine_one_degree_latitude(): assert 110000 < haversine_distance_m(0,0,1,0) < 112000
def test_bearing_cardinals(): assert initial_bearing_deg(0,0,0,1) == 90; assert initial_bearing_deg(0,0,1,0) == 0
def test_relative_bearing_wraps(): assert relative_bearing_deg(5,355) == 10; assert relative_bearing_deg(355,5) == -10
def test_ttc_only_when_closing(): assert time_to_collision(20, 5) == 4; assert time_to_collision(20, 0) is None
def test_critical_risk(): score, level = risk_score(5, 10, .5, 0); assert level == RiskLevel.CRITICAL and score >= .9

