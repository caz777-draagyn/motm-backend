#!/usr/bin/env python3
"""
Merge new male Chinese (pinyin) given names into country_CHN.json and re-tier
20 / 30 / 50 / rest by estimated real-world commonness (most common first).

Uses the same pinyin validation as cleanse_chn_nonchinese_givens.py.

Run: python scripts/enrich_chn_given_names.py
"""

from __future__ import annotations

import importlib.util
import json
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_POOL = _REPO / "data" / "name_pools" / "country_CHN.json"

_spec = importlib.util.spec_from_file_location(
    "cleanse_chn",
    Path(__file__).resolve().parent / "cleanse_chn_nonchinese_givens.py",
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(_mod)
_load_syllables = _mod._load_syllables
_is_pinyin_only = _mod._is_pinyin_only


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip())
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _tier(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


# Most common first within each band; bands concatenate to full rarity order.
# Estimates from common mainland naming patterns (single-character + 双名).
_TOP20: list[str] = [
    "Wei",
    "Jun",
    "Hao",
    "Ming",
    "Yong",
    "Jie",
    "Lei",
    "Peng",
    "Tao",
    "Yan",
    "Bin",
    "Gang",
    "Dong",
    "Bo",
    "Yu",
    "Yang",
    "Chao",
    "Cheng",
    "Xu",
    "Feng",
]

# Next 30 (positions 21–50)
_NEXT30: list[str] = [
    "Yuan",
    "Jian",
    "Kai",
    "Rui",
    "Qiang",
    "Wen",
    "Fan",
    "Wu",
    "Guo",
    "Zheng",
    "Xiang",
    "Zhou",
    "Zhao",
    "Liang",
    "Han",
    "Huang",
    "Hu",
    "Tian",
    "Jin",
    "Dan",
    "Jiang",
    "Chen",
    "Song",
    "Tong",
    "He",
    "Xuan",
    "Fei",
    "Hui",
    "Xin",
    "Zhi",
]

# Next 50 (positions 51–100)
_NEXT50: list[str] = [
    "Lin",
    "Hong",
    "Ping",
    "Yi",
    "Min",
    "Hua",
    "Jing",
    "Qi",
    "Shan",
    "Shi",
    "Ze",
    "Ren",
    "Jia",
    "Ying",
    "Qian",
    "Qing",
    "Luo",
    "Fang",
    "Hai",
    "Yue",
    "Lang",
    "Rong",
    "Ning",
    "An",
    "Mo",
    "Kun",
    "Zhen",
    "Chang",
    "Long",
    "Shen",
    "Tang",
    "Sheng",
    "Bowen",
    "Shuo",
    "Guan",
    "Yiming",
    "Wang",
    "Zhang",
    "Ke",
    "Xing",
    "Shuai",
    "Zhong",
    "Chan",
    "Yulin",
    "Heng",
    "Yao",
    "Ben",
    "Zihao",
    "Zihan",
    "Zixuan",
]

# Long tail: rarer singles, classical, regional, and two-syllable compound pinyin (~250+)
_RARE: list[str] = [
    "Haoyu",
    "Haoran",
    "Yichen",
    "Yuming",
    "Weijie",
    "Zhiyuan",
    "Jiarui",
    "Yifan",
    "Boyu",
    "Mingze",
    "Yuxi",
    "Ziqi",
    "Haoming",
    "Chenxi",
    "Yihang",
    "Zirui",
    "Boyang",
    "Guowei",
    "Jianjun",
    "Xiaoming",
    "Zhiwei",
    "Guoliang",
    "Yongjun",
    "Haifeng",
    "Zhihua",
    "Limin",
    "Guoping",
    "Weidong",
    "Jianmin",
    "Shihua",
    "Guoyong",
    "Xinjie",
    "Zhiqiang",
    "Yonghui",
    "Haibo",
    "Linhao",
    "Yufei",
    "Chenyu",
    "Zewen",
    "Ronghua",
    "Jianguo",
    "Guohua",
    "Hongwei",
    "Linxuan",
    "Yipeng",
    "Haolin",
    "Xinyu",
    "Jiahao",
    "Yuchen",
    "Minghao",
    "Haoxuan",
    "Yiran",
    "Zeyu",
    "Chenrui",
    "Yijie",
    "Haoyang",
    "Zining",
    "Junchen",
    "Yueyang",
    "Xinchen",
    "Zhiming",
    "Haoyuan",
    "Yizhou",
    "Haonan",
    "Zhiyong",
    "Guoqiang",
    "Xiaolong",
    "Zhiwen",
    "Yansong",
    "Linjie",
    "Weicheng",
    "Junhao",
    "Yuntao",
    "Zixiang",
    "Ruize",
    "Mingxuan",
    "Yifeng",
    "Zhenhua",
    "Jinyu",
    "Xingyu",
    "Zimo",
    "Haochuan",
    "Zhennan",
    "Yikai",
    "Haoxi",
    "Ziyou",
    "Yucheng",
    "Junjie",
    "Haotian",
    "Ruixuan",
    "Yixuan",
    "Zihanrui",
    "Yuchenhao",
    "Chenyao",
    "Xinyang",
    "Zhimin",
    "Haosen",
    "Yunlong",
    "Jingtao",
    "Weihang",
    "Guanghui",
    "Yunfeng",
    "Zhikai",
    "Haocheng",
    "Junlin",
    "Yihan",
    "Chenghan",
    "Xingchen",
    "Ziheng",
    "Yumingze",
    "En",
    "Sen",
    "Teng",
    "Zhan",
    "Duan",
    "Hang",
    "Jiao",
    "Lun",
    "Qiu",
    "Qu",
    "Shao",
    "Cai",
    "Cong",
    "Dai",
    "Dun",
    "Gao",
    "Gen",
    "Gong",
    "Guang",
    "Gui",
    "Hou",
    "Huan",
    "Kan",
    "Kuang",
    "Lai",
    "Leng",
    "Lian",
    "Lie",
    "Ling",
    "Mao",
    "Meng",
    "Miao",
    "Mu",
    "Nuo",
    "Ou",
    "Pan",
    "Pei",
    "Pu",
    "Qiao",
    "Que",
    "Sai",
    "Shuang",
    "Taoheng",
    "Xi",
    "Xue",
    "Yanlin",
    "Yefeng",
    "Yichenhao",
    "You",
    "Yuanming",
    "Zan",
    "Zehao",
    "Zhelun",
    "Zhigang",
    "Zhihong",
    "Zhipeng",
    "Zhiqi",
    "Zun",
    "Biao",
    "Binwei",
    "Chengmin",
    "Dawei",
    "Fuyang",
    "Guangyu",
    "Hanlin",
    "Hongtao",
    "Huimin",
    "Jianping",
    "Kaisheng",
    "Leifu",
    "Longfei",
    "Minhao",
    "Peimin",
    "Qifeng",
    "Ruilin",
    "Songlin",
    "Taoyuan",
    "Weihua",
    "Xianjun",
    "Xuelin",
    "Yanhao",
    "Yongtao",
    "Yuhao",
    "Zhaoming",
    "Zhenyu",
    "Zhijian",
    "Zijian",
    "Ziyu",
    "Bing",
    "Can",
    "Chaoqi",
    "Chengbin",
    "Chuan",
    "Da",
    "Di",
    "Fanwei",
    "Guangming",
    "Hanxiao",
    "Hongbin",
    "Huaijun",
    "Jianfeng",
    "Jianwei",
    "Jieting",
    "Kang",
    "Keyan",
    "Lejun",
    "Lujun",
    "Minsheng",
    "Nan",
    "Pengcheng",
    "Qihang",
    "Rujie",
    "Runfeng",
    "Shimin",
    "Tianyu",
    "Weihao",
    "Xihao",
    "Xinpeng",
    "Xudong",
    "Yanchao",
    "Yingjie",
    "Yuanchao",
    "Yunhao",
    "Zhicheng",
    "Zijie",
    "Chengyu",
    "Deshan",
    "Guangjun",
    "Hanwei",
    "Hongyi",
    "Jianhua",
    "Jianyi",
    "Junfeng",
    "Junwei",
    "Leyi",
    "Lujiang",
    "Minze",
    "Pengfei",
    "Qinwei",
    "Ruhan",
    "Shilin",
    "Tianhao",
    "Weiqi",
    "Xiaofeng",
    "Xinwei",
    "Yangyang",
    "Yifanhao",
    "Yongjian",
    "Yuanhao",
    "Yufan",
    "Yujie",
    "Yunpeng",
    "Zeming",
    "Zepeng",
    "Zhenjie",
    "Zhonghua",
    "Zhourui",
    "Zhuoran",
]


def _dedupe_keep_order(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        k = _norm(n).casefold()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(_norm(n))
    return out


def main() -> None:
    syl = _load_syllables()
    mx = max(len(x) for x in syl)

    data = json.loads(_POOL.read_text(encoding="utf-8"))
    g = data.get("given_names_male")
    if not isinstance(g, dict):
        raise SystemExit("missing given_names_male")
    existing: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        arr = g.get(tier)
        if isinstance(arr, list):
            existing.extend(_norm(x) for x in arr if isinstance(x, str) and _norm(x))

    full_order = _TOP20 + _NEXT30 + _NEXT50 + _RARE
    merged = _dedupe_keep_order(full_order + existing)

    valid: list[str] = []
    invalid: list[str] = []
    for n in merged:
        if _is_pinyin_only(_norm(n).casefold(), syl, mx):
            valid.append(n)
        else:
            invalid.append(n)

    if invalid:
        print("dropped invalid pinyin:", invalid[:25], "..." if len(invalid) > 25 else "")

    data["given_names_male"] = _tier(valid)
    _POOL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(valid)} given names (very:{len(data['given_names_male']['very_common'])} "
          f"com:{len(data['given_names_male']['common'])} "
          f"mid:{len(data['given_names_male']['mid'])} "
          f"rare:{len(data['given_names_male']['rare'])})")


if __name__ == "__main__":
    main()
