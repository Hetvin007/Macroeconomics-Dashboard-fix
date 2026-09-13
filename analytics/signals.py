def inflation_signal(x,target=4.0):
    if x is None:return '—'
    if x>=target+2:return 'High'
    if x>=target+0.5:return 'Elevated'
    if x>=target-0.5:return 'Near target'
    return 'Low'

def growth_signal(x):
    if x is None:return '—'
    if x>=6:return 'Strong'
    if x>=3:return 'Moderate'
    if x>=0:return 'Weak'
    return 'Stress'

def risk_score(growth=None,inflation=None,unemployment=None,real_policy=None):
    s=0
    if growth is not None and growth<2:s+=25
    if growth is not None and growth<0:s+=20
    if inflation is not None and inflation>6:s+=25
    if unemployment is not None and unemployment>8:s+=15
    if real_policy is not None and real_policy<0:s+=10
    return min(100,s)

def regime(score):
    if score>=70:return 'High stress'
    if score>=40:return 'Caution'
    if score>=20:return 'Watch'
    return 'Stable'
