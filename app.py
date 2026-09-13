import pathlib, yaml, pandas as pd, streamlit as st
from dotenv import load_dotenv
load_dotenv()
from database import connect, upsert
from collectors.world_bank import fetch as wb_fetch
from collectors.imf import fetch as imf_fetch
from collectors.rbi import fetch as rbi_fetch
from collectors.fred import fetch as fred_fetch
from analytics.market import spread
from analytics.signals import inflation_signal, growth_signal, risk_score, regime
from analytics.regime import build_regime_history, regime_score_explainer
from analytics.metrics import latest_by_indicator, prepare, change_table
from analytics.surprise import calculate_surprises, macro_surprise_score
from analytics.brief import generate_daily_brief
from analytics.alerts import detect_alerts, freshness_alerts
from analytics.daily_report import build_report, save_report
from analytics.daily_engine import build_intelligence
from analytics.reaction import reaction_table
from analytics.attribution import cross_asset_attribution
from analytics.fusion import build_global_signal_fusion, cross_asset_context
from analytics.relative import build_relative_macro, pairwise_matrix
from analytics.decision import build_decision_dashboard, scenario_matrix
from analytics.portfolio import portfolio_attribution, factor_matrix
from analytics.backtest import build_macro_backtest, rolling_relationship
from event_db import init_events, upsert_fred_vintages
from collectors.fred_calendar import fetch_release_calendar
from collectors.fred_vintage import fetch_vintage, build_vintage_dates
from analytics.point_in_time import build_pit_history, explain_pit

st.set_page_config(page_title='Macro Intelligence Terminal v2.0',page_icon='📊',layout='wide',initial_sidebar_state='expanded')
BASE=pathlib.Path(__file__).parent
load=lambda p: yaml.safe_load(open(BASE/p,encoding='utf-8'))
cfg=load('config/indicators.yaml'); rbi_cfg=load('config/rbi_sources.yaml'); cb=load('config/central_banks.yaml'); cal=load('config/calendar.yaml'); targets=load('config/targets.yaml'); fred_cfg=load('config/fred.yaml'); sources=load('config/source_registry.yaml')
consensus_path=BASE/'data/consensus_template.csv'; con=connect(); init_events(con)
COUNTRIES={'India':'IND','United States':'USA','China':'CHN','Euro Area':'EMU','United Kingdom':'GBR','Japan':'JPN','Germany':'DEU','France':'FRA','Brazil':'BRA','Canada':'CAN','Australia':'AUS','South Korea':'KOR'}

def all_obs(): return prepare(pd.read_sql_query('SELECT * FROM observations',con))
def latest_df(): return latest_by_indicator(all_obs())
def getval(df, keys, country=None):
    if isinstance(keys,str): keys=[keys]
    for key in keys:
        x=df[df.indicator_id.str.contains(key,case=False,na=False)]
        if country: x=x[x.country.eq(country)]
        if not x.empty: return float(x.iloc[0].value)
    return None

def refresh_global(source):
    total=0; errors=[]
    if source=='World Bank':
        for country in COUNTRIES.values():
            for it in cfg.get('world_bank',[]):
                try: total += upsert(con,it['id'],wb_fetch(country,it['code']))
                except Exception as e: errors.append(f'WB {country}/{it["id"]}: {e}')
    else:
        for it in cfg.get('imf',[]):
            try: total += upsert(con,it['id'],imf_fetch(it['code']))
            except Exception as e: errors.append(f'IMF {it["id"]}: {e}')
    return total,errors

def refresh_fred():
    total=0; errors=[]
    for it in fred_cfg.get('series',[]):
        try: total += upsert(con,it['id'],fred_fetch(it['fred_id']))
        except Exception as e: errors.append(f"{it['id']}: {e}")
    return total,errors

def refresh_fred_vintages(start_date='2018-01-01', end_date=None, vintage_freq='QE'):
    total=0; errors=[]
    dates=build_vintage_dates(start=start_date,end=end_date,freq=vintage_freq)
    series=[x for x in fred_cfg.get('series',[]) if x.get('id') in {'us_real_gdp_growth','us_cpi','us_unemployment','us_fed_funds'}]
    for it in series:
        for vd in dates:
            try:
                df=fetch_vintage(it['fred_id'],it['id'],vd)
                total += upsert_fred_vintages(con,df)
            except Exception as e: errors.append(f"{it['id']} @ {vd}: {e}")
    return total,errors,len(dates),len(series)

def refresh_rbi():
    total=0; errors=[]
    for it in rbi_cfg['india_rbi']['indicators']:
        if not it.get('url'): continue
        try: total += upsert(con,it['id'],rbi_fetch(it['url'],it['id'],fmt=it.get('format','csv')))
        except Exception as e: errors.append(f'{it["id"]}: {e}')
    return total,errors

st.title('📊 Macro Intelligence Terminal')
st.caption('v2.0 • point-in-time macro research • revision-aware • official/open-data-first • transparent analytics')
with st.sidebar:
    st.subheader('Refresh')
    source=st.selectbox('Global source',['World Bank','IMF DataMapper'])
    if st.button('🔄 Refresh global data',type='primary'):
        with st.spinner('Fetching latest source data…'):
            n,errs=refresh_global(source)
        st.success(f'{n:,} observations processed'); [st.warning(e) for e in errs[:8]]; st.rerun()
    if st.button('🇺🇸 Refresh FRED market data'):
        with st.spinner('Fetching FRED market/rates data…'):
            n,errs=refresh_fred()
        st.success(f'{n:,} observations processed'); [st.warning(e) for e in errs[:8]]; st.rerun()
    if st.button('🕰 Build FRED point-in-time history'):
        with st.spinner('Fetching quarterly FRED/ALFRED vintages…'):
            n,errs,nd,ns=refresh_fred_vintages(start_date='2018-01-01')
        st.success(f'{n:,} vintage observations processed ({ns} series × {nd} vintage dates)')
        [st.warning(e) for e in errs[:5]]
        st.rerun()
    if st.button('🇮🇳 Refresh configured RBI feeds'):
        with st.spinner('Fetching validated RBI feeds…'):
            n,errs=refresh_rbi()
        st.success(f'{n:,} observations processed'); [st.warning(e) for e in errs[:8]]; st.rerun()
    st.divider(); country_name=st.selectbox('Focus country',list(COUNTRIES)); st.caption('Only explicitly configured RBI feeds are ingested.')

obs=all_obs(); latest=latest_by_indicator(obs); ccode=COUNTRIES[country_name]
G=getval(latest,['gdp_growth','growth'],ccode); I=getval(latest,['inflation_cpi','inflation'],ccode); U=getval(latest,['unemployment'],ccode)
repo=getval(latest,['rbi_repo','repo_rate'],'India'); real_policy=(repo-I) if repo is not None and I is not None else None; risk=risk_score(G,I,U,real_policy)
cols=st.columns(5); cols[0].metric('Growth',f'{G:.2f}%' if G is not None else '—',growth_signal(G)); cols[1].metric('Inflation',f'{I:.2f}%' if I is not None else '—',inflation_signal(I)); cols[2].metric('Unemployment',f'{U:.2f}%' if U is not None else '—'); cols[3].metric('Macro risk',f'{risk}/100',regime(risk)); cols[4].metric('Stored observations',f'{len(obs):,}')

tabs=st.tabs(['Executive','🇮🇳 India','🌎 Global','🏦 Central Banks','📈 Markets','📊 Trends','📅 Calendar','🧠 Analytics','🚦 Regime','📰 Daily Brief','🎯 Surprises','🚨 Alerts','⚡ Event Engine','📉 Market Reaction','🧭 Attribution','🕰 Revisions','🌐 Global Fusion','⚖️ Relative Macro','💼 Decision Support','💼 Portfolio Macro','📐 Macro Backtest','🧭 Point-in-Time','🔎 Data Quality','📚 Sources'])
with tabs[0]:
    st.subheader(f'{country_name} — executive monitor'); x=latest[latest.country.eq(ccode)].copy()
    st.dataframe(x[['indicator_id','date','value','source','retrieved_at']] if not x.empty else pd.DataFrame(),use_container_width=True,hide_index=True)
with tabs[1]:
    st.subheader('India Macro Terminal'); st.info('RBI DBIE/SDMX feeds are intentionally strict: no guessed identifiers.')
    m1,m2,m3=st.columns(3); m1.metric('Repo rate',f'{repo:.2f}%' if repo is not None else '—'); m2.metric('Inflation gap vs target',f'{I-targets["india"]["inflation_target"]:.2f} pp' if I is not None else '—'); m3.metric('Real policy rate',f'{real_policy:.2f} pp' if real_policy is not None else '—')
    st.dataframe(pd.DataFrame(rbi_cfg['india_rbi']['indicators']),use_container_width=True,hide_index=True); st.link_button('Open RBI DBIE',rbi_cfg['india_rbi']['portal']); st.link_button('Open RBI Statistics',rbi_cfg['india_rbi']['statistics'])
with tabs[2]:
    st.subheader('Global Macro Cross-Section'); g=latest[latest.country.isin(COUNTRIES.values())]; st.dataframe(g[['country','indicator_id','date','value','source']] if not g.empty else pd.DataFrame(),use_container_width=True,hide_index=True)
with tabs[3]:
    st.subheader('Central-bank monitor'); st.dataframe(pd.DataFrame(cb['central_banks']),use_container_width=True,hide_index=True); st.caption('Registry until validated live policy feeds are configured.')
with tabs[4]:
    st.subheader('Market & Yield Curve'); a,b,c,d=st.columns(4)
    for col,ind,label in [(a,'us_2y','US 2Y'),(b,'us_5y','US 5Y'),(c,'us_10y','US 10Y'),(d,'us_30y','US 30Y')]:
        v=getval(latest,[ind],'United States'); col.metric(label,f'{v:.2f}%' if v is not None else '—')
    y=spread(obs,'us_10y','us_2y');
    if not y.empty: st.metric('US 10Y–2Y spread',f"{y.iloc[-1].spread:.2f} pp"); st.line_chart(y.set_index('date')[['long','short','spread']])
    else: st.info('Refresh FRED after configuring FRED_API_KEY.')
with tabs[5]:
    st.subheader('Historical trends'); choices=sorted(obs[obs.country.eq(ccode)].indicator_id.unique()) if not obs.empty else []
    if choices:
        indicator=st.selectbox('Indicator',choices); chart=obs[(obs.country==ccode)&(obs.indicator_id==indicator)][['date','value']].set_index('date').sort_index(); st.line_chart(chart); st.dataframe(change_table(obs[(obs.country==ccode)&(obs.indicator_id==indicator)])[['date','value','change','pct_change']].tail(20),use_container_width=True,hide_index=True)
    else: st.info('No observations for this country yet.')
with tabs[6]:
    st.subheader('Economic release calendar'); st.dataframe(pd.DataFrame(cal['releases']),use_container_width=True,hide_index=True); st.caption('Consensus is never invented; populate the consensus template with a validated source.')
with tabs[7]:
    st.subheader('Analyst analytics'); st.dataframe(pd.DataFrame({'Metric':['Growth regime','Inflation regime','Inflation gap','Real policy rate','Macro risk regime'], 'Value':[growth_signal(G),inflation_signal(I),f'{I-targets["india"]["inflation_target"]:.2f} pp' if I is not None else '—',f'{real_policy:.2f} pp' if real_policy is not None else '—',regime(risk)]}),use_container_width=True,hide_index=True)
with tabs[8]:
    st.subheader('Macro Regime Engine'); hist=build_regime_history(obs,target=targets['india']['inflation_target'])
    if hist.empty: st.info('Load enough historical observations.')
    else:
        r=hist.iloc[-1]; a,b,c,d=st.columns(4); a.metric('Current score',f"{r['score']:.0f}/100"); b.metric('Current regime',r['regime']); c.metric('History points',f'{len(hist):,}'); d.metric('Latest date',str(r['date'])); st.line_chart(hist.set_index('date')[['score']]); st.dataframe(hist.tail(40),use_container_width=True,hide_index=True); st.expander('Scoring methodology').write(regime_score_explainer())
with tabs[9]:
    st.subheader('📰 Daily Macro Analyst Brief'); events=pd.read_csv(consensus_path) if consensus_path.exists() else pd.DataFrame(); report=build_report(obs,events); st.markdown(report.replace('\n','  \n')); st.download_button('Download daily brief',report,'daily_macro_brief.md','text/markdown')
with tabs[10]:
    st.subheader('🎯 Economic Surprise Engine'); events=pd.read_csv(consensus_path) if consensus_path.exists() else pd.DataFrame(); sx=calculate_surprises(events)
    if sx.empty: st.info('Populate data/consensus_template.csv with validated consensus data.')
    else: st.metric('Average normalized surprise',f'{macro_surprise_score(events):.2f}%'); st.dataframe(sx,use_container_width=True,hide_index=True); st.download_button('Download surprise table',sx.to_csv(index=False),'macro_surprises.csv','text/csv')
with tabs[11]:
    st.subheader('🚨 Alerts'); a=detect_alerts(obs); f=freshness_alerts(obs); alerts=pd.concat([a,f],ignore_index=True)
    if alerts.empty: st.success('No threshold or freshness alerts detected.')
    else: st.dataframe(alerts,use_container_width=True,hide_index=True); st.download_button('Download alerts',alerts.to_csv(index=False),'macro_alerts.csv','text/csv')
with tabs[12]:
    st.subheader('⚡ Event-driven Intelligence Engine')
    c1,c2=st.columns(2)
    if c1.button('Refresh FRED release calendar'):
        try:
            rel=fetch_release_calendar(yaml.safe_load(open(BASE/'config/releases.yaml'))['releases'], start=pd.Timestamp.utcnow().strftime('%Y-%m-%d'), end=(pd.Timestamp.utcnow()+pd.Timedelta(days=90)).strftime('%Y-%m-%d'))
            from event_db import upsert_release_dates
            n=upsert_release_dates(con,rel); st.success(f'{n:,} release-date rows processed'); st.rerun()
        except Exception as e: st.error(str(e))
    caldb=pd.read_sql_query("SELECT * FROM release_calendar ORDER BY release_date",con)
    ev=build_intelligence(obs,pd.read_csv(consensus_path) if consensus_path.exists() else pd.DataFrame(),caldb)
    for b in ev: st.markdown('• '+b)
    if not caldb.empty: st.dataframe(caldb.tail(60),use_container_width=True,hide_index=True)
with tabs[13]:
    st.subheader('📉 Market Reaction Engine')
    st.caption('Descriptive event-window analysis: nearest market observations before/after a release. It is not a causal attribution model.')
    consensus=pd.read_csv(consensus_path) if consensus_path.exists() else pd.DataFrame()
    reaction=reaction_table(obs, consensus)
    if reaction.empty:
        st.info('Add validated event dates to data/consensus_template.csv and refresh FRED market data.')
    else:
        st.dataframe(reaction.sort_values('event_date', ascending=False),use_container_width=True,hide_index=True)
        st.download_button('Download market reactions',reaction.to_csv(index=False),'market_reactions.csv','text/csv')
with tabs[14]:
    st.subheader('🧭 Cross-Asset Macro Attribution')
    st.caption('Descriptive consistency analysis across rates, USD and equities. It does not claim causal attribution.')
    consensus=pd.read_csv(consensus_path) if consensus_path.exists() else pd.DataFrame()
    reaction=reaction_table(obs, consensus)
    attr=cross_asset_attribution(reaction)
    if attr.empty:
        st.info('Add validated event dates/consensus and refresh market data to populate cross-asset attribution.')
    else:
        k1,k2,k3=st.columns(3)
        k1.metric('Events analysed', f'{len(attr):,}')
        k2.metric('High-consistency responses', f'{(attr.response_consistency=="High").sum():,}')
        k3.metric('Mixed responses', f'{(attr.response_consistency=="Mixed").sum():,}')
        cols=[c for c in ['event_date','event_name','surprise','macro_impulse','rates_change','usd_change','equity_change','market_response','response_consistency'] if c in attr.columns]
        st.dataframe(attr.sort_values('event_date', ascending=False)[cols],use_container_width=True,hide_index=True)
        st.download_button('Download cross-asset attribution',attr.to_csv(index=False),'cross_asset_attribution.csv','text/csv')
with tabs[15]:
    st.subheader('🕰 Data Revisions')
    rev=pd.read_sql_query('SELECT * FROM revision_log ORDER BY detected_at DESC',con)
    if rev.empty: st.success('No revisions detected yet. Revisions are captured when a previously stored observation changes.')
    else: st.dataframe(rev.head(200),use_container_width=True,hide_index=True); st.download_button('Download revisions',rev.to_csv(index=False),'macro_revisions.csv','text/csv')
with tabs[16]:
    st.subheader('🌐 Global Macro Signal Fusion')
    st.caption('Composite descriptive regime across configured economies. It is a heuristic, not a forecast.')
    fusion=build_global_signal_fusion(obs)
    if fusion.empty:
        st.info('Refresh macro sources to populate the global signal-fusion layer.')
    else:
        valid=fusion.dropna(subset=['score'])
        gscore=float(valid['score'].iloc[0]) if not valid.empty else None
        gregime=str(valid['global_regime'].iloc[0]) if not valid.empty else 'Insufficient data'
        c1,c2,c3=st.columns(3)
        c1.metric('Global macro score', '—' if gscore is None else f'{gscore:.1f}/100')
        c2.metric('Global regime', gregime)
        c3.metric('Economies in stress', f'{int(valid["stress_flag"].sum())}/{len(valid)}' if not valid.empty else '—')
        cols=['country','growth','inflation','unemployment','policy_rate','real_policy','score','regime']
        st.dataframe(fusion[cols],use_container_width=True,hide_index=True)
        st.download_button('Download global signal fusion',fusion.to_csv(index=False),'global_macro_fusion.csv','text/csv')
with tabs[17]:
    st.subheader('⚖️ India-vs-Global Relative Macro')
    st.caption('Relative strength/weakness across configured economies. Higher is stronger on the transparent growth/inflation/labor/real-rate heuristic; it is not an investment recommendation.')
    anchor=st.selectbox('Anchor economy',list(COUNTRIES.keys()),index=list(COUNTRIES.keys()).index('India'))
    fusion=build_global_signal_fusion(obs)
    rel=build_relative_macro(fusion, anchor=anchor)
    if rel.empty:
        st.info('Refresh World Bank/IMF data to populate relative macro analysis.')
    else:
        rr=rel.dropna(subset=['vs_anchor'])
        a,b,c,d=st.columns(4)
        a.metric('Anchor',anchor)
        arow=rr[rr.country.eq(anchor)]
        a.metric('Anchor score', f"{arow.iloc[0].relative_score:.1f}" if not arow.empty else '—')
        stronger=int((rr.vs_anchor>5).sum()); weaker=int((rr.vs_anchor<-5).sum())
        c.metric('Stronger than anchor',str(stronger)); d.metric('Weaker than anchor',str(weaker))
        cols=['country','growth','inflation','unemployment','real_policy','relative_score','vs_anchor','relative_regime']
        st.dataframe(rel[cols],use_container_width=True,hide_index=True)
        matrix=pairwise_matrix(rel)
        if not matrix.empty:
            st.subheader('Pairwise relative-strength matrix')
            st.dataframe(matrix.round(1),use_container_width=True)
        st.download_button('Download relative macro table',rel.to_csv(index=False),'relative_macro.csv','text/csv')
with tabs[18]:
    st.subheader('💼 Macro Decision Support')
    st.caption('Decision-support signals only. This layer summarizes macro conditions and scenarios; it is not investment advice or a price forecast.')
    anchor=st.selectbox('Decision-support economy',list(COUNTRIES.keys()),index=list(COUNTRIES.keys()).index('India'),key='decision_anchor')
    fusion=build_global_signal_fusion(obs)
    decision=build_decision_dashboard(fusion, obs, anchor=anchor)
    a,b,c=st.columns(3)
    a.metric('Macro score', '—' if decision['score'] is None else f"{decision['score']:.1f}/100")
    b.metric('Macro regime', decision['regime'])
    c.metric('Anchor', anchor)
    if decision['signals']:
        st.subheader('Current macro signals')
        st.dataframe(pd.DataFrame(decision['signals'],columns=['factor','interpretation','value']),use_container_width=True,hide_index=True)
    if decision['watchlist']:
        st.subheader('Relative macro watchlist')
        st.dataframe(pd.DataFrame(decision['watchlist']),use_container_width=True,hide_index=True)
    scen=scenario_matrix(decision['score'])
    if not scen.empty:
        st.subheader('Scenario stress matrix')
        st.dataframe(scen,use_container_width=True,hide_index=True)
        st.download_button('Download scenario matrix',scen.to_csv(index=False),'macro_scenarios.csv','text/csv')
with tabs[19]:
    st.subheader('💼 Portfolio Macro Attribution')
    st.caption('Directional macro sensitivity only. This is not a portfolio return forecast, valuation model, or investment recommendation.')
    yspread=None
    y=spread(obs,'us_10y','us_2y')
    if not y.empty: yspread=float(y.iloc[-1].spread)
    portfolio, factors = portfolio_attribution(regime_score=risk, inflation=I, real_policy=real_policy, yield_spread=yspread)
    a,b,c=st.columns(3)
    a.metric('Macro regime score',f'{risk}/100')
    b.metric('10Y–2Y spread', '—' if yspread is None else f'{yspread:.2f} pp')
    c.metric('Non-zero factor inputs',str(sum(v!=0 for v in factors.values())))
    st.subheader('Directional sensitivity by asset')
    st.dataframe(portfolio,use_container_width=True,hide_index=True)
    st.subheader('Sensitivity matrix')
    st.dataframe(factor_matrix().round(2),use_container_width=True)
    st.download_button('Download portfolio attribution',portfolio.to_csv(index=False),'portfolio_macro_attribution.csv','text/csv')
    st.info('Positive scores indicate directional support under the predefined sensitivity assumptions; negative scores indicate headwinds. Coefficients are illustrative and configurable.')
with tabs[20]:
    st.subheader('📐 Empirical Macro Factor Backtest')
    st.caption('Historical relationship analysis only. The engine uses stored macro regimes and subsequent market observations; it does not imply causation or forecast future returns.')
    bt_country=st.selectbox('Macro regime country',list(COUNTRIES.keys()),index=list(COUNTRIES.keys()).index('India'),key='bt_country')
    horizon=st.selectbox('Forward horizon (months)',[1,3,6],index=1,key='bt_horizon')
    panel,summary,betas=build_macro_backtest(obs,country=COUNTRIES[bt_country],target=targets['india']['inflation_target'],horizon_months=horizon)
    if panel.empty:
        st.info('Not enough stored macro + market history yet. Refresh the macro and FRED sources, then rerun the backtest.')
    else:
        k1,k2,k3=st.columns(3)
        k1.metric('Observations',f"{len(panel):,}")
        k2.metric('Assets tested',f"{panel.asset.nunique():,}")
        k3.metric('Forward horizon',f"{horizon}M")
        st.subheader('Historical regime performance')
        st.dataframe(summary.round(3),use_container_width=True,hide_index=True)
        st.subheader('Macro-score-change relationship')
        st.dataframe(betas.round(4),use_container_width=True,hide_index=True)
        asset=st.selectbox('Asset relationship chart',sorted(panel.asset.unique()),key='bt_asset')
        rr=rolling_relationship(panel,asset,window=min(12,max(4,len(panel[panel.asset.eq(asset)]))))
        if not rr.empty:
            st.line_chart(rr.set_index('date')['rolling_corr'])
            st.caption('Rolling correlation between monthly macro-score changes and subsequent asset outcomes. Small samples should be treated cautiously.')
        st.download_button('Download backtest panel',panel.to_csv(index=False),'macro_backtest_panel.csv','text/csv')
        st.download_button('Download backtest summary',summary.to_csv(index=False),'macro_backtest_summary.csv','text/csv')
with tabs[21]:
    st.subheader('🧭 Point-in-Time Macro Backtest')
    st.caption(explain_pit())
    vdf=pd.read_sql_query('SELECT * FROM fred_vintages ORDER BY vintage_date,date',con)
    if vdf.empty:
        st.info('No FRED/ALFRED vintage history is stored yet. Use the sidebar button to build quarterly vintages. FRED requires an API key.')
    else:
        pit=build_pit_history(vdf)
        c1,c2,c3=st.columns(3)
        c1.metric('Vintage dates',f"{pit.asof_date.nunique():,}")
        c2.metric('Earliest as-of',pit.asof_date.min().strftime('%Y-%m-%d'))
        c3.metric('Latest as-of',pit.asof_date.max().strftime('%Y-%m-%d'))
        st.subheader('Historical information set')
        st.dataframe(pit,use_container_width=True,hide_index=True)
        if not pit.empty:
            st.subheader('Point-in-time macro regime')
            chart=pit.set_index('asof_date')[['score']]
            st.line_chart(chart)
            st.subheader('Regime counts')
            st.dataframe(pit.groupby('regime').size().rename('observations').reset_index(),use_container_width=True,hide_index=True)
            st.download_button('Download point-in-time history',pit.to_csv(index=False),'point_in_time_macro_history.csv','text/csv')
        st.subheader('Stored vintage observations')
        st.dataframe(vdf.head(500),use_container_width=True,hide_index=True)
with tabs[21]:
    st.subheader('Data quality & provenance')
    if obs.empty: st.info('No observations yet.')
    else:
        q=obs.copy(); now=pd.Timestamp.utcnow().tz_localize(None); q['age_days']=(now-pd.to_datetime(q['date'],errors='coerce').dt.tz_localize(None)).dt.days; q['retrieved']=pd.to_datetime(q['retrieved_at'],errors='coerce'); q['retrieval_age_h']=(now-q['retrieved'].dt.tz_localize(None)).dt.total_seconds()/3600; st.dataframe(q[['indicator_id','country','date','value','source','source_url','retrieved_at','age_days','retrieval_age_h']],use_container_width=True,hide_index=True)
with tabs[22]:
    st.subheader('Source registry'); st.dataframe(pd.DataFrame(sources['sources']),use_container_width=True,hide_index=True)

st.divider(); st.caption('v2.0 • Point-in-time backtesting • Decision support • Global signal fusion • Cross-asset attribution • Free/open-data-first • official observations ≠ derived analytics ≠ model alerts')
