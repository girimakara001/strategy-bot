# strategy_bot.py
# 入力：出目列 → 出力：P / B / LOOK（のみ）
# 仕様：T は常に LOOK、評価からも除外。優位性・規則性・連続性を併用して判定。

import sys
import argparse
from collections import Counter

VALID = {"P", "B", "T"}

def _clean(raw: str):
    s = []
    for c in raw.upper():
        if c in VALID:
            s.append(c)
    return s

def _strip_T(seq):
    return [c for c in seq if c != "T"]

def _last_is_T(seq):
    return len(seq) > 0 and seq[-1] == "T"

def _runs(seq):
    if not seq:
        return []
    runs = []
    cur = seq[0]; cnt = 1
    for c in seq[1:]:
        if c == cur:
            cnt += 1
        else:
            runs.append((cur, cnt))
            cur = c; cnt = 1
    runs.append((cur, cnt))
    return runs

def _advantage(seq_wo_t):
    p = seq_wo_t.count("P")
    b = seq_wo_t.count("B")
    if p > b:
        return "P", p - b
    if b > p:
        return "B", b - p
    return None, 0

def _is_teleco(seq_wo_t, min_len=4):
    if len(seq_wo_t) < min_len:
        return False
    tail = seq_wo_t[-min_len:]
    for i in range(1, len(tail)):
        if tail[i] == tail[i-1]:
            return False
    return True

def _regularity_votes(runs_list):
    votes = Counter()
    if not runs_list:
        return votes
    cur_c, cur_n = runs_list[-1]
    if len(runs_list) >= 3:
        l2, l3 = runs_list[-2][1], runs_list[-3][1]
        if l2 == 2 and l3 == 2:
            if cur_n == 1:
                votes[cur_c] += 2
            elif cur_n == 2:
                votes["P" if cur_c == "B" else "B"] += 2
    if len(runs_list) >= 4 and cur_n == 1:
        last3 = [runs_list[-4][1], runs_list[-3][1], runs_list[-2][1]]
        if last3 == [2,1,2] or last3 == [1,2,1]:
            votes["P" if cur_c == "B" else "B"] += 2
        if last3 == [3,1,3] or last3 == [1,3,1]:
            votes["P" if cur_c == "B" else "B"] += 2
    return votes

def _continuity_picks(runs_list):
    picks = set()
    if not runs_list:
        return picks
    cur_c, cur_n = runs_list[-1]
    if cur_n >= 7:
        picks.add(cur_c)
    if len(runs_list) >= 2:
        prev_c, prev_n = runs_list[-2]
        if prev_n >= 7 and cur_n == 1:
            picks.add(prev_c)
    return picks

def recommend(raw_seq: str) -> str:
    seq = _clean(raw_seq)
    if not seq:
        return "LOOK"
    if _last_is_T(seq):
        return "LOOK"
    seq_nb = _strip_T(seq)
    if not seq_nb:
        return "LOOK"
    adv_side, diff = _advantage(seq_nb)
    if diff >= 20:
        return "LOOK"
    runs_list = _runs(seq_nb)
    cur_c, cur_n = runs_list[-1]
    cont_picks = _continuity_picks(runs_list)
    reg_votes = _regularity_votes(runs_list)
    if _is_teleco(seq_nb, min_len=4):
        reg_votes["P" if cur_c == "B" else "B"] += 2
    if diff >= 5 and adv_side is not None:
        support = 0
        if adv_side in cont_picks:
            support += 2
        support += reg_votes.get(adv_side, 0)
        if cur_c == adv_side and cur_n >= 3:
            support += 1
        if support > 0:
            return adv_side
        return "LOOK"
    scores = {"P": 0, "B": 0}
    for s in ("P", "B"):
        if s in cont_picks:
            scores[s] += 3
        scores[s] += reg_votes.get(s, 0)
        if adv_side == s and diff >= 1:
            scores[s] += 1
        if s == cur_c and cur_n >= 3:
            scores[s] += 1
    if scores["P"] > scores["B"]:
        return "P"
    if scores["B"] > scores["P"]:
        return "B"
    if scores["P"] == scores["B"] == 0:
        return "LOOK"
    return cur_c

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recommend", help="例: PPBBPBTBB")
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    if args.recommend:
        print(recommend(args.recommend))
        return
    if args.live:
        history = []
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                token = line.strip().upper()
                if token not in VALID:
                    continue
                history.append(token)
                print(recommend("".join(history)))
                sys.stdout.flush()
        except KeyboardInterrupt:
            pass
        return
    print("LOOK")

if __name__ == "__main__":
    main()
