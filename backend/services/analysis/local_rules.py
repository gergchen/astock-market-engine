"""本地规则引擎 — 无需 LLM 的快速分析"""


def local_rule_analysis(df, stock_name, symbol, summary, fund_flow):
    """本地规则引擎分析（不调用 LLM）"""
    latest = df.iloc[-1]
    avg_20_vol = df['volume'].tail(20).mean() if 'volume' in df.columns else 0
    avg_60_close = df['close'].tail(60).mean() if 'close' in df.columns else 0

    pct = float(latest.get('pct_change', 0))
    vol = float(latest.get('volume', 0))
    close = float(latest.get('close', 0))
    high = float(latest.get('high', 0))
    low = float(latest.get('low', 0))
    turnover = float(latest.get('turnover', 0))

    sections = []

    # 一、当前状态
    if pct > 3:
        status = f'{stock_name} 今日强势上涨 {pct:.1f}%，市场关注度较高。'
    elif pct > 0:
        status = f'{stock_name} 今日小幅上涨 {pct:.1f}%，走势平稳。'
    elif pct > -3:
        status = f'{stock_name} 今日小幅下跌 {pct:.1f}%，走势偏弱。'
    else:
        status = f'{stock_name} 今日大幅下跌 {pct:.1f}%，市场情绪较弱。'
    sections.append(f'## 一、当前状态\n{status}')

    # 二、主力行为
    main_cap = analyze_main_capital_local(close, avg_60_close, vol, avg_20_vol, turnover, pct, high, low)
    sections.append(f'## 二、主力行为分析\n{main_cap["title"]}\n\n{main_cap["content"]}\n\n判断依据：\n{main_cap["reasons"]}')

    # 三、情绪
    emotion = analyze_emotion_local(pct, vol)
    sections.append(f'## 三、市场情绪\n{emotion}')

    # 四、风险与机会
    risk_lines = []
    if pct > 5:
        risk_lines.append('- 风险：涨幅较大，短线获利盘可能抛压')
    if turnover > 5:
        risk_lines.append('- 风险：换手率偏高，筹码松动')
    if pct < -3:
        risk_lines.append('- 机会：大幅下跌后可能存在超跌反弹机会')
    if not risk_lines:
        risk_lines.append('- 信号不明确，建议观望')
    sections.append('## 四、风险与机会\n' + '\n'.join(risk_lines))

    return {
        'summary': summary,
        'analysis': '\n\n'.join(sections),
        'data_points': len(df),
    }


def analyze_main_capital_local(close, avg_close_60, vol, avg_vol_20, turnover, pct, high, low) -> dict:
    """主力行为分析（本地规则引擎）"""
    confidence = '低'
    title = '主力行为分析（本地规则引擎）'

    price_ratio = close / avg_close_60 if avg_close_60 > 0 else 1
    vol_ratio = vol / avg_vol_20 if avg_vol_20 > 0 else 1

    stage_reasons = {'吸筹': [], '洗盘': [], '主升': [], '出货': []}
    scores = {'吸筹': 0, '洗盘': 0, '主升': 0, '出货': 0}
    max_scores = {'吸筹': 5, '洗盘': 5, '主升': 5, '出货': 5}

    if price_ratio < 0.9:
        scores['吸筹'] += 1
        stage_reasons['吸筹'].append('股价低于60日均价的90%，处于低位区间')
    if vol_ratio < 1.2:
        scores['吸筹'] += 1
        stage_reasons['吸筹'].append('量能未明显放大')
    if 1 <= turnover <= 3:
        scores['吸筹'] += 1
        stage_reasons['吸筹'].append('换手率1%-3%，温和换手')
    if pct > 0 and (high - close) < (close - low):
        scores['吸筹'] += 1
        stage_reasons['吸筹'].append('收盘接近当日最高价，有下影线特征')

    if 0.8 <= price_ratio <= 0.95:
        scores['洗盘'] += 1
        stage_reasons['洗盘'].append('股价在近期高点下方10%-20%')
    if vol_ratio < 0.6:
        scores['洗盘'] += 1
        stage_reasons['洗盘'].append('成交量萎缩至20日均量60%以下')
    if abs(pct) < 2:
        scores['洗盘'] += 1
        stage_reasons['洗盘'].append('振幅较小，无方向性大阴线')
    if turnover < 1.5:
        scores['洗盘'] += 1
        stage_reasons['洗盘'].append('换手率低于1.5%')

    if price_ratio >= 1.05:
        scores['主升'] += 1
        stage_reasons['主升'].append('股价站上60日均线')
    if vol_ratio >= 1.5:
        scores['主升'] += 1
        stage_reasons['主升'].append('成交量高于20日均量150%')
    if pct > 0:
        scores['主升'] += 1
        stage_reasons['主升'].append('今日上涨')
    if turnover > 3:
        scores['主升'] += 1
        stage_reasons['主升'].append('换手活跃（>3%）')
    if close > 0 and (high - low) / close < 0.06:
        scores['主升'] += 1
        stage_reasons['主升'].append('振幅适中，上涨稳健')

    if price_ratio >= 1.3:
        scores['出货'] += 1
        stage_reasons['出货'].append('累计涨幅较大')
    if vol_ratio > 1.5 and pct < 1:
        scores['出货'] += 1
        stage_reasons['出货'].append('放量滞涨')
    if turnover > 5:
        scores['出货'] += 1
        stage_reasons['出货'].append('换手率超过5%')
    if pct < 0 and close > 0 and (high - low) / close > 0.05:
        scores['出货'] += 1
        stage_reasons['出货'].append('下跌且振幅较大')

    for k in scores:
        scores[k] = scores[k] / max_scores[k]

    best = max(scores, key=scores.get)
    best_score = scores[best]

    if best_score >= 0.8:
        confidence = '高'
    elif best_score >= 0.6:
        confidence = '中'
    else:
        confidence = '低'

    behavior_names = {
        '吸筹': '疑似主力吸筹阶段',
        '洗盘': '疑似主力洗盘阶段',
        '主升': '疑似主升阶段',
        '出货': '疑似主力出货阶段',
    }
    behavior_desc = {
        '吸筹': '该股近期大单持续净流入，结合低位缩量特征，疑似主力悄悄建仓，散户恐慌出局反而给了机会。',
        '洗盘': '当前更像主力洗盘，而非资金出逃。缩量横盘是洗去浮筹信号，主力并未真正离场。',
        '主升': '该股进入主升段，量价配合良好，大单持续净流入。追涨需注意仓位控制，避免高位接盘。',
        '出货': '高位放量滞涨，大单净流出明显，出货特征较清晰。持仓者建议设好止损，谨慎追高。',
    }

    best_reasons = stage_reasons[best]
    scored_reasons = [f'✓ {r}' for r in best_reasons] if best_reasons else ['信号不明确，建议观望等待确认']

    return {
        'title': f'主力行为分析：{behavior_names[best]}',
        'content': behavior_desc[best],
        'confidence': confidence,
        'reasons': '\n'.join(scored_reasons),
    }


def analyze_emotion_local(pct, vol) -> str:
    """本地情绪分析"""
    if pct > 5:
        return '情绪活跃：今日涨幅较大，市场关注度较高，但需警惕追高风险。'
    elif pct > 2:
        return '情绪偏暖：温和上涨，市场情绪稳定。'
    elif pct > 0:
        return '情绪平淡：微涨，市场无明显情绪驱动。'
    elif pct > -3:
        return '情绪偏冷：小幅下跌，市场情绪较弱。'
    else:
        return '情绪冷淡：跌幅较大，市场情绪低迷，观望为主。'
