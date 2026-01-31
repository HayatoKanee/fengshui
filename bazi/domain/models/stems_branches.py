"""
天干地支 (TianGan DiZhi) - Heavenly Stems and Earthly Branches

干支是中国古代纪年法的基础，也是八字命理的核心元素。
- 天干 (TianGan): 甲乙丙丁戊己庚辛壬癸
- 地支 (DiZhi): 子丑寅卯辰巳午未申酉戌亥

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, Tuple

from .elements import WuXing, YinYang


class TianGan(Enum):
    """
    天干 (Heavenly Stems)

    十天干代表天的能量，与五行阴阳对应：
    - 甲乙 → 木 (Wood)
    - 丙丁 → 火 (Fire)
    - 戊己 → 土 (Earth)
    - 庚辛 → 金 (Metal)
    - 壬癸 → 水 (Water)

    奇数位为阳，偶数位为阴。
    """
    JIA = "甲"    # 甲木 阳
    YI = "乙"     # 乙木 阴
    BING = "丙"   # 丙火 阳
    DING = "丁"   # 丁火 阴
    WU = "戊"     # 戊土 阳
    JI = "己"     # 己土 阴
    GENG = "庚"   # 庚金 阳
    XIN = "辛"    # 辛金 阴
    REN = "壬"    # 壬水 阳
    GUI = "癸"    # 癸水 阴

    @property
    def chinese(self) -> str:
        """返回中文字符"""
        return self.value

    @property
    def wuxing(self) -> WuXing:
        """获取天干对应的五行"""
        return _STEM_WUXING[self]

    @property
    def yinyang(self) -> YinYang:
        """获取天干的阴阳属性"""
        return _STEM_YINYANG[self]

    @classmethod
    def from_chinese(cls, char: str) -> TianGan:
        """从中文字符创建天干"""
        for stem in cls:
            if stem.value == char:
                return stem
        raise ValueError(f"未知天干: {char}")

    @classmethod
    def all_ordered(cls) -> Tuple[TianGan, ...]:
        """按传统顺序返回所有天干"""
        return tuple(cls)


class DiZhi(Enum):
    """
    地支 (Earthly Branches)

    十二地支代表地的能量，与五行、生肖对应：
    - 子(鼠)亥(猪) → 水
    - 寅(虎)卯(兔) → 木
    - 巳(蛇)午(马) → 火
    - 申(猴)酉(鸡) → 金
    - 丑(牛)辰(龙)未(羊)戌(狗) → 土

    每个地支含有藏干（本气、中气、余气）。
    """
    ZI = "子"     # 子 鼠 水
    CHOU = "丑"   # 丑 牛 土
    YIN = "寅"    # 寅 虎 木
    MAO = "卯"    # 卯 兔 木
    CHEN = "辰"   # 辰 龙 土
    SI = "巳"     # 巳 蛇 火
    WU = "午"     # 午 马 火
    WEI = "未"    # 未 羊 土
    SHEN = "申"   # 申 猴 金
    YOU = "酉"    # 酉 鸡 金
    XU = "戌"     # 戌 狗 土
    HAI = "亥"    # 亥 猪 水

    @property
    def chinese(self) -> str:
        """返回中文字符"""
        return self.value

    @property
    def wuxing(self) -> WuXing:
        """获取地支对应的五行"""
        return _BRANCH_WUXING[self]

    @property
    def hidden_stems(self) -> Dict[TianGan, float]:
        """
        获取地支藏干及其比例

        藏干分为：
        - 本气：主要藏干，比例最大 (≥0.5)
        - 中气：次要藏干
        - 余气：最弱藏干
        """
        return dict(_HIDDEN_STEMS[self])

    @classmethod
    def from_chinese(cls, char: str) -> DiZhi:
        """从中文字符创建地支"""
        for branch in cls:
            if branch.value == char:
                return branch
        raise ValueError(f"未知地支: {char}")

    @classmethod
    def all_ordered(cls) -> Tuple[DiZhi, ...]:
        """按传统顺序返回所有地支"""
        return tuple(cls)


# =============================================================================
# 天干五行对应 (Stem → WuXing)
# =============================================================================
_STEM_WUXING: Dict[TianGan, WuXing] = {
    TianGan.JIA: WuXing.WOOD,   # 甲木
    TianGan.YI: WuXing.WOOD,    # 乙木
    TianGan.BING: WuXing.FIRE,  # 丙火
    TianGan.DING: WuXing.FIRE,  # 丁火
    TianGan.WU: WuXing.EARTH,   # 戊土
    TianGan.JI: WuXing.EARTH,   # 己土
    TianGan.GENG: WuXing.METAL, # 庚金
    TianGan.XIN: WuXing.METAL,  # 辛金
    TianGan.REN: WuXing.WATER,  # 壬水
    TianGan.GUI: WuXing.WATER,  # 癸水
}

# =============================================================================
# 天干阴阳对应 (Stem → YinYang)
# =============================================================================
_STEM_YINYANG: Dict[TianGan, YinYang] = {
    TianGan.JIA: YinYang.YANG,  # 甲 阳
    TianGan.YI: YinYang.YIN,    # 乙 阴
    TianGan.BING: YinYang.YANG, # 丙 阳
    TianGan.DING: YinYang.YIN,  # 丁 阴
    TianGan.WU: YinYang.YANG,   # 戊 阳
    TianGan.JI: YinYang.YIN,    # 己 阴
    TianGan.GENG: YinYang.YANG, # 庚 阳
    TianGan.XIN: YinYang.YIN,   # 辛 阴
    TianGan.REN: YinYang.YANG,  # 壬 阳
    TianGan.GUI: YinYang.YIN,   # 癸 阴
}

# =============================================================================
# 地支五行对应 (Branch → WuXing)
# =============================================================================
_BRANCH_WUXING: Dict[DiZhi, WuXing] = {
    DiZhi.ZI: WuXing.WATER,    # 子 水
    DiZhi.CHOU: WuXing.EARTH,  # 丑 土
    DiZhi.YIN: WuXing.WOOD,    # 寅 木
    DiZhi.MAO: WuXing.WOOD,    # 卯 木
    DiZhi.CHEN: WuXing.EARTH,  # 辰 土
    DiZhi.SI: WuXing.FIRE,     # 巳 火
    DiZhi.WU: WuXing.FIRE,     # 午 火
    DiZhi.WEI: WuXing.EARTH,   # 未 土
    DiZhi.SHEN: WuXing.METAL,  # 申 金
    DiZhi.YOU: WuXing.METAL,   # 酉 金
    DiZhi.XU: WuXing.EARTH,    # 戌 土
    DiZhi.HAI: WuXing.WATER,   # 亥 水
}

# =============================================================================
# 地支藏干 (Hidden Stems / CangGan)
# 本气、中气、余气的比例分配
# =============================================================================
_HIDDEN_STEMS: Dict[DiZhi, Dict[TianGan, float]] = {
    DiZhi.ZI: {TianGan.GUI: 1.0},                                          # 子藏癸
    DiZhi.CHOU: {TianGan.JI: 0.5, TianGan.GUI: 0.3, TianGan.XIN: 0.2},    # 丑藏己癸辛
    DiZhi.YIN: {TianGan.JIA: 0.6, TianGan.BING: 0.3, TianGan.WU: 0.1},    # 寅藏甲丙戊
    DiZhi.MAO: {TianGan.YI: 1.0},                                          # 卯藏乙
    DiZhi.CHEN: {TianGan.WU: 0.5, TianGan.YI: 0.3, TianGan.GUI: 0.2},     # 辰藏戊乙癸
    DiZhi.SI: {TianGan.BING: 0.6, TianGan.WU: 0.3, TianGan.GENG: 0.1},    # 巳藏丙戊庚
    DiZhi.WU: {TianGan.DING: 0.5, TianGan.JI: 0.5},                        # 午藏丁己
    DiZhi.WEI: {TianGan.YI: 0.2, TianGan.JI: 0.5, TianGan.DING: 0.3},     # 未藏乙己丁
    DiZhi.SHEN: {TianGan.GENG: 0.6, TianGan.REN: 0.3, TianGan.WU: 0.1},   # 申藏庚壬戊
    DiZhi.YOU: {TianGan.XIN: 1.0},                                         # 酉藏辛
    DiZhi.XU: {TianGan.WU: 0.5, TianGan.XIN: 0.3, TianGan.DING: 0.2},     # 戌藏戊辛丁
    DiZhi.HAI: {TianGan.REN: 0.7, TianGan.JIA: 0.3},                       # 亥藏壬甲
}


# =============================================================================
# 干支关系 (GanZhi Relations)
# =============================================================================

@dataclass(frozen=True)
class GanZhiRelations:
    """
    干支关系常量

    包含：
    - 六合 (LiuHe): 地支相合
    - 五合 (WuHe): 天干相合
    - 天干相冲 (GanChong)
    - 地支相冲 (ZhiChong)
    """

    # 六合 - 地支相合
    # 子丑合、寅亥合、卯戌合、辰酉合、巳申合、午未合
    LIU_HE: FrozenSet[Tuple[DiZhi, DiZhi]] = frozenset({
        (DiZhi.ZI, DiZhi.CHOU),    # 子丑合
        (DiZhi.YIN, DiZhi.HAI),    # 寅亥合
        (DiZhi.MAO, DiZhi.XU),     # 卯戌合
        (DiZhi.CHEN, DiZhi.YOU),   # 辰酉合
        (DiZhi.SI, DiZhi.SHEN),    # 巳申合
        (DiZhi.WU, DiZhi.WEI),     # 午未合
    })

    # 五合 - 天干相合
    # 甲己合、乙庚合、丙辛合、丁壬合、戊癸合
    WU_HE: FrozenSet[Tuple[TianGan, TianGan]] = frozenset({
        (TianGan.JIA, TianGan.JI),   # 甲己合
        (TianGan.YI, TianGan.GENG),  # 乙庚合
        (TianGan.BING, TianGan.XIN), # 丙辛合
        (TianGan.DING, TianGan.REN), # 丁壬合
        (TianGan.WU, TianGan.GUI),   # 戊癸合
    })

    # 天干相冲
    # 甲庚冲、乙辛冲、丙壬冲、丁癸冲
    GAN_CHONG: FrozenSet[Tuple[TianGan, TianGan]] = frozenset({
        (TianGan.JIA, TianGan.GENG),  # 甲庚冲
        (TianGan.YI, TianGan.XIN),    # 乙辛冲
        (TianGan.BING, TianGan.REN),  # 丙壬冲
        (TianGan.DING, TianGan.GUI),  # 丁癸冲
    })

    # 地支相冲
    # 子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲
    ZHI_CHONG: FrozenSet[Tuple[DiZhi, DiZhi]] = frozenset({
        (DiZhi.ZI, DiZhi.WU),     # 子午冲
        (DiZhi.CHOU, DiZhi.WEI),  # 丑未冲
        (DiZhi.YIN, DiZhi.SHEN),  # 寅申冲
        (DiZhi.MAO, DiZhi.YOU),   # 卯酉冲
        (DiZhi.CHEN, DiZhi.XU),   # 辰戌冲
        (DiZhi.SI, DiZhi.HAI),    # 巳亥冲
    })

    # 地支相刑 (Punishments)
    # 无恩之刑：寅刑巳、巳刑申、申刑寅
    # 恃势之刑：丑刑戌、戌刑未、未刑丑
    # 无礼之刑：子刑卯、卯刑子
    # 自刑：辰辰、午午、酉酉、亥亥
    XING_WU_EN: FrozenSet[FrozenSet[DiZhi]] = frozenset({
        frozenset({DiZhi.YIN, DiZhi.SI, DiZhi.SHEN}),  # 寅巳申 无恩之刑
    })
    XING_CHI_SHI: FrozenSet[FrozenSet[DiZhi]] = frozenset({
        frozenset({DiZhi.CHOU, DiZhi.XU, DiZhi.WEI}),  # 丑戌未 恃势之刑
    })
    XING_WU_LI: FrozenSet[Tuple[DiZhi, DiZhi]] = frozenset({
        (DiZhi.ZI, DiZhi.MAO),  # 子卯 无礼之刑
    })
    XING_ZI: FrozenSet[DiZhi] = frozenset({
        DiZhi.CHEN, DiZhi.WU, DiZhi.YOU, DiZhi.HAI,  # 辰午酉亥 自刑
    })

    # 地支相害 (Harms)
    # 六害：子未害、丑午害、寅巳害、卯辰害、申亥害、酉戌害
    ZHI_HAI: FrozenSet[Tuple[DiZhi, DiZhi]] = frozenset({
        (DiZhi.ZI, DiZhi.WEI),    # 子未害
        (DiZhi.CHOU, DiZhi.WU),   # 丑午害
        (DiZhi.YIN, DiZhi.SI),    # 寅巳害
        (DiZhi.MAO, DiZhi.CHEN),  # 卯辰害
        (DiZhi.SHEN, DiZhi.HAI),  # 申亥害
        (DiZhi.YOU, DiZhi.XU),    # 酉戌害
    })

    # 地支相破 (Breaks)
    # 子酉破、午卯破、寅亥破、巳申破、辰丑破、戌未破
    ZHI_PO: FrozenSet[Tuple[DiZhi, DiZhi]] = frozenset({
        (DiZhi.ZI, DiZhi.YOU),    # 子酉破
        (DiZhi.WU, DiZhi.MAO),    # 午卯破
        (DiZhi.YIN, DiZhi.HAI),   # 寅亥破
        (DiZhi.SI, DiZhi.SHEN),   # 巳申破
        (DiZhi.CHEN, DiZhi.CHOU), # 辰丑破
        (DiZhi.XU, DiZhi.WEI),    # 戌未破
    })

    # =========================================================================
    # 以下为 Dict 类型常量，使用 property 避免 dataclass 默认值问题
    # =========================================================================

    @property
    def SAN_HE(self) -> Dict[WuXing, FrozenSet[DiZhi]]:
        """地支三合局"""
        return _SAN_HE

    @property
    def SAN_HUI(self) -> Dict[WuXing, FrozenSet[DiZhi]]:
        """地支三会方"""
        return _SAN_HUI

    @property
    def WU_HE_HUA(self) -> Dict[Tuple[TianGan, TianGan], WuXing]:
        """天干五合化神"""
        return _WU_HE_HUA

    @property
    def LIU_HE_HUA(self) -> Dict[Tuple[DiZhi, DiZhi], WuXing]:
        """地支六合化神"""
        return _LIU_HE_HUA


# =============================================================================
# Dict 类型常量 (模块级别，避免 dataclass 默认值问题)
# =============================================================================

# 地支三合局 (Triangular Combinations)
# 申子辰合水局、亥卯未合木局、寅午戌合火局、巳酉丑合金局
_SAN_HE: Dict[WuXing, FrozenSet[DiZhi]] = {
    WuXing.WATER: frozenset({DiZhi.SHEN, DiZhi.ZI, DiZhi.CHEN}),   # 申子辰 水局
    WuXing.WOOD: frozenset({DiZhi.HAI, DiZhi.MAO, DiZhi.WEI}),     # 亥卯未 木局
    WuXing.FIRE: frozenset({DiZhi.YIN, DiZhi.WU, DiZhi.XU}),       # 寅午戌 火局
    WuXing.METAL: frozenset({DiZhi.SI, DiZhi.YOU, DiZhi.CHOU}),    # 巳酉丑 金局
}

# 地支三会方 (Directional Combinations)
# 寅卯辰会东方木、巳午未会南方火、申酉戌会西方金、亥子丑会北方水
_SAN_HUI: Dict[WuXing, FrozenSet[DiZhi]] = {
    WuXing.WOOD: frozenset({DiZhi.YIN, DiZhi.MAO, DiZhi.CHEN}),    # 寅卯辰 东方木
    WuXing.FIRE: frozenset({DiZhi.SI, DiZhi.WU, DiZhi.WEI}),       # 巳午未 南方火
    WuXing.METAL: frozenset({DiZhi.SHEN, DiZhi.YOU, DiZhi.XU}),    # 申酉戌 西方金
    WuXing.WATER: frozenset({DiZhi.HAI, DiZhi.ZI, DiZhi.CHOU}),    # 亥子丑 北方水
}

# 天干五合化神 (Stem Combination Transformations)
_WU_HE_HUA: Dict[Tuple[TianGan, TianGan], WuXing] = {
    (TianGan.JIA, TianGan.JI): WuXing.EARTH,    # 甲己合化土
    (TianGan.YI, TianGan.GENG): WuXing.METAL,   # 乙庚合化金
    (TianGan.BING, TianGan.XIN): WuXing.WATER,  # 丙辛合化水
    (TianGan.DING, TianGan.REN): WuXing.WOOD,   # 丁壬合化木
    (TianGan.WU, TianGan.GUI): WuXing.FIRE,     # 戊癸合化火
}

# 地支六合化神 (Branch Six Combination Transformations)
_LIU_HE_HUA: Dict[Tuple[DiZhi, DiZhi], WuXing] = {
    (DiZhi.ZI, DiZhi.CHOU): WuXing.EARTH,     # 子丑合化土
    (DiZhi.YIN, DiZhi.HAI): WuXing.WOOD,      # 寅亥合化木
    (DiZhi.MAO, DiZhi.XU): WuXing.FIRE,       # 卯戌合化火
    (DiZhi.CHEN, DiZhi.YOU): WuXing.METAL,   # 辰酉合化金
    (DiZhi.SI, DiZhi.SHEN): WuXing.WATER,    # 巳申合化水
    (DiZhi.WU, DiZhi.WEI): WuXing.FIRE,      # 午未合化火/土 (主火)
}


# 关系单例
RELATIONS = GanZhiRelations()


# =============================================================================
# 辅助函数 (Helper Functions)
# =============================================================================

def check_he_by_chinese(char1: str, char2: str) -> bool:
    """
    检查两个字符是否形成合的关系

    支持六合（地支）和五合（天干）

    Args:
        char1: 第一个中文字符
        char2: 第二个中文字符

    Returns:
        如果形成合的关系返回 True
    """
    # 先尝试作为地支（六合）
    try:
        branch1 = DiZhi.from_chinese(char1)
        branch2 = DiZhi.from_chinese(char2)
        pair = (branch1, branch2)
        reverse = (branch2, branch1)
        if pair in RELATIONS.LIU_HE or reverse in RELATIONS.LIU_HE:
            return True
    except ValueError:
        pass

    # 再尝试作为天干（五合）
    try:
        stem1 = TianGan.from_chinese(char1)
        stem2 = TianGan.from_chinese(char2)
        pair = (stem1, stem2)
        reverse = (stem2, stem1)
        if pair in RELATIONS.WU_HE or reverse in RELATIONS.WU_HE:
            return True
    except ValueError:
        pass

    return False


def check_he(
    elem1: TianGan | DiZhi | str,
    elem2: TianGan | DiZhi | str,
) -> bool:
    """
    检查两个元素是否形成合的关系

    支持天干、地支枚举和中文字符串

    Args:
        elem1: 第一个元素（天干、地支或中文字符）
        elem2: 第二个元素（天干、地支或中文字符）

    Returns:
        如果形成合的关系返回 True
    """
    char1 = elem1.chinese if hasattr(elem1, 'chinese') else str(elem1)
    char2 = elem2.chinese if hasattr(elem2, 'chinese') else str(elem2)
    return check_he_by_chinese(char1, char2)


# =============================================================================
# 向后兼容别名 (Backward Compatibility Aliases)
# =============================================================================
HeavenlyStem = TianGan
EarthlyBranch = DiZhi
StemBranchRelations = GanZhiRelations
