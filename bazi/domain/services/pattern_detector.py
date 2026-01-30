"""
特殊格局檢測器 (Special Pattern Detector)

按古籍規則檢測八字是否符合特殊格局（變格）的條件。
純布爾規則判斷，不使用數值閾值。

判斷順序：
1. 化氣格 (天干合化成功)
2. 專旺格 (一氣專旺)
3. 從格 (日元極弱)
4. 暗沖格 (虛邀暗官)
5. 暗合格 (暗合官星)
6. 兩神成象格 (只有兩種五行)

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import List, Optional, Set

from ..models.bazi import BaZi
from ..models.elements import WuXing, YinYang
from ..models.stems_branches import TianGan, DiZhi
from ..models.shishen import ShiShen, calculate_shishen
from ..models.pattern import (
    SpecialPattern,
    PatternType,
    PatternYongShen,
    ZHUAN_WANG_YONG_SHEN,
    HUA_QI_YONG_SHEN,
)
from .wuxing_calculator import WuXingCalculator


class PatternDetector:
    """
    特殊格局檢測器

    按古籍規則檢測，返回第一個符合的格局。
    """

    def detect(self, bazi: BaZi) -> Optional[SpecialPattern]:
        """
        檢測八字的主要特殊格局（返回第一個）

        Returns:
            SpecialPattern if detected, None if 正格
        """
        patterns = self.detect_all(bazi)
        return patterns[0] if patterns else None

    def detect_all(self, bazi: BaZi) -> List[SpecialPattern]:
        """
        檢測八字所有符合的特殊格局

        Returns:
            List of all matching SpecialPatterns
        """
        patterns = []

        # 1. 化氣格
        if result := self._check_hua_qi_ge(bazi):
            patterns.append(result)

        # 2. 專旺格
        if result := self._check_zhuan_wang_ge(bazi):
            patterns.append(result)

        # 3. 從格
        if result := self._check_cong_ge(bazi):
            patterns.append(result)

        # 4. 暗沖格
        if result := self._check_an_chong_ge(bazi):
            patterns.append(result)

        # 5. 暗合格
        if result := self._check_an_he_ge(bazi):
            patterns.append(result)

        # 6. 兩神成象格
        if result := self._check_liang_shen_ge(bazi):
            patterns.append(result)

        return patterns

    # =========================================================================
    # 從格檢測 (Following Pattern Detection)
    # =========================================================================

    def _check_cong_ge(self, bazi: BaZi) -> Optional[SpecialPattern]:
        """
        檢查從格（用五行能量判斷）

        成格條件：
        1. 日主五行能量 < 20%（極弱）
        2. 印比五行能量 < 20%（無生扶）
        3. 某類五行能量 > 40%（從神極強）

        從格分類：
        - 從官殺格：官殺(剋日主) > 40%
        - 從財格：財星(被日主剋) > 40%
        - 從兒格：食傷(日主生) > 40%
        """
        day_master = bazi.day_master
        dm_wuxing = day_master.wuxing

        # 計算五行能量
        wx_dist = self._calculate_wuxing_distribution(bazi)

        # 五行關係
        yin_wuxing = dm_wuxing.generated_by   # 印星（生日主）
        bi_wuxing = dm_wuxing                  # 比劫
        shi_wuxing = dm_wuxing.generates       # 食傷（日主生）
        cai_wuxing = dm_wuxing.overcomes       # 財星（被日主剋）
        guan_wuxing = dm_wuxing.overcome_by    # 官殺（剋日主）

        dm_pct = wx_dist[dm_wuxing]
        yin_pct = wx_dist[yin_wuxing]
        shi_pct = wx_dist[shi_wuxing]
        cai_pct = wx_dist[cai_wuxing]
        guan_pct = wx_dist[guan_wuxing]

        # 條件1: 日主極弱 (< 20%)
        if dm_pct >= 20:
            return None

        # 條件2: 印比無力 (合計 < 25%)
        if (dm_pct + yin_pct) >= 25:
            return None

        # 條件3: 確定從何神 (> 40%)
        if guan_pct >= 40 and guan_pct >= cai_pct and guan_pct >= shi_pct:
            return SpecialPattern(
                pattern_type=PatternType.CONG_GUAN_SHA,
                yong_shen_info=PatternYongShen(
                    yong_shen=guan_wuxing,
                    xi_shen=[cai_wuxing],
                    ji_shen=[shi_wuxing],
                    bu_xi=[yin_wuxing, bi_wuxing],
                ),
                description=f"從官殺格：{dm_wuxing.chinese}{dm_pct:.0f}%，{guan_wuxing.chinese}{guan_pct:.0f}%",
            )

        elif cai_pct >= 40 and cai_pct >= shi_pct:
            return SpecialPattern(
                pattern_type=PatternType.CONG_CAI,
                yong_shen_info=PatternYongShen(
                    yong_shen=cai_wuxing,
                    xi_shen=[shi_wuxing],
                    ji_shen=[bi_wuxing],
                    bu_xi=[yin_wuxing],
                ),
                description=f"從財格：{dm_wuxing.chinese}{dm_pct:.0f}%，{cai_wuxing.chinese}{cai_pct:.0f}%",
            )

        elif shi_pct >= 40:
            return SpecialPattern(
                pattern_type=PatternType.CONG_ER,
                yong_shen_info=PatternYongShen(
                    yong_shen=shi_wuxing,
                    xi_shen=[cai_wuxing],
                    ji_shen=[yin_wuxing],
                    bu_xi=[guan_wuxing],
                ),
                description=f"從兒格：{dm_wuxing.chinese}{dm_pct:.0f}%，{shi_wuxing.chinese}{shi_pct:.0f}%",
            )

        return None

    # =========================================================================
    # 專旺格檢測 (Specialized Dominant Pattern Detection)
    # =========================================================================

    def _check_zhuan_wang_ge(self, bazi: BaZi) -> Optional[SpecialPattern]:
        """
        檢查專旺格（一行得氣格）

        成格條件：
        1. 日主五行與格局相符
        2. 地支成方（三會）或成局（三合）
        3. 月令當令
        4. 天干地支無忌神（剋制專旺之神）
        """
        dm_wuxing = bazi.day_master.wuxing
        branches = bazi.all_branches
        branch_set = set(branches)
        month_branch = bazi.month_pillar.branch

        # 三會方
        san_hui = {
            WuXing.WOOD: {DiZhi.YIN, DiZhi.MAO, DiZhi.CHEN},   # 東方木
            WuXing.FIRE: {DiZhi.SI, DiZhi.WU, DiZhi.WEI},      # 南方火
            WuXing.METAL: {DiZhi.SHEN, DiZhi.YOU, DiZhi.XU},   # 西方金
            WuXing.WATER: {DiZhi.HAI, DiZhi.ZI, DiZhi.CHOU},   # 北方水
        }

        # 三合局
        san_he = {
            WuXing.WOOD: {DiZhi.HAI, DiZhi.MAO, DiZhi.WEI},    # 木局
            WuXing.FIRE: {DiZhi.YIN, DiZhi.WU, DiZhi.XU},      # 火局
            WuXing.METAL: {DiZhi.SI, DiZhi.YOU, DiZhi.CHOU},   # 金局
            WuXing.WATER: {DiZhi.SHEN, DiZhi.ZI, DiZhi.CHEN},  # 水局
        }

        # 格局對應
        patterns = {
            WuXing.WOOD: (PatternType.QU_ZHI, WuXing.METAL, "曲直格"),
            WuXing.FIRE: (PatternType.YAN_SHANG, WuXing.WATER, "炎上格"),
            WuXing.METAL: (PatternType.CONG_GE_METAL, WuXing.FIRE, "從革格"),
            WuXing.WATER: (PatternType.RUN_XIA, WuXing.EARTH, "潤下格"),
        }

        # 檢查木火金水專旺格
        if dm_wuxing in patterns:
            pattern_type, ji_shen, name = patterns[dm_wuxing]
            hui = san_hui.get(dm_wuxing, set())
            he = san_he.get(dm_wuxing, set())

            # 條件2: 地支成方或成局
            has_hui = hui <= branch_set
            has_he = he <= branch_set
            if not has_hui and not has_he:
                return None

            matched_combo = hui if has_hui else he

            # 條件3: 月令當令（月支在組合內或本氣為該五行）
            if month_branch not in matched_combo and month_branch.wuxing != dm_wuxing:
                return None

            # 條件4: 無忌神
            # 天干不可見忌神
            if self._has_stem_element(bazi, ji_shen):
                return None
            # 地支（組合外）不可見忌神本氣
            for b in branches:
                if b not in matched_combo and b.wuxing == ji_shen:
                    return None

            return SpecialPattern(
                pattern_type=pattern_type,
                yong_shen_info=ZHUAN_WANG_YONG_SHEN[pattern_type],
                description=f"{name}：{dm_wuxing.chinese}專旺，地支{'三會' if has_hui else '三合'}",
            )

        # 稼穡格（土）特殊處理
        if dm_wuxing == WuXing.EARTH:
            si_ku = {DiZhi.CHEN, DiZhi.XU, DiZhi.CHOU, DiZhi.WEI}
            ku_in_branches = [b for b in branches if b in si_ku]

            # 條件: 四庫見齊（或至少三個且月令為庫）
            if len(ku_in_branches) >= 3 and month_branch in si_ku:
                # 無木忌神
                if self._has_stem_element(bazi, WuXing.WOOD):
                    return None
                # 地支（庫外）無木
                for b in branches:
                    if b not in si_ku and b.wuxing == WuXing.WOOD:
                        return None

                return SpecialPattern(
                    pattern_type=PatternType.JIA_SE,
                    yong_shen_info=ZHUAN_WANG_YONG_SHEN[PatternType.JIA_SE],
                    description=f"稼穡格：土專旺，四庫見{len(ku_in_branches)}個",
                )

        return None

    # =========================================================================
    # 化氣格檢測 (Transformation Pattern Detection)
    # =========================================================================

    def _check_hua_qi_ge(self, bazi: BaZi) -> Optional[SpecialPattern]:
        """
        檢查化氣格

        天干五合：甲己化土、乙庚化金、丙辛化水、丁壬化木、戊癸化火

        成格條件：
        1. 日干與月干或時干相合
        2. 化神當令（月支本氣為化神五行）
        3. 無妒合（同干爭合）
        4. 無剋制化神之五行
        """
        day_stem = bazi.day_pillar.stem
        month_stem = bazi.month_pillar.stem
        hour_stem = bazi.hour_pillar.stem
        year_stem = bazi.year_pillar.stem
        month_branch = bazi.month_pillar.branch

        # 天干五合
        wu_he = {
            (TianGan.JIA, TianGan.JI): (WuXing.EARTH, PatternType.HUA_TU),
            (TianGan.JI, TianGan.JIA): (WuXing.EARTH, PatternType.HUA_TU),
            (TianGan.YI, TianGan.GENG): (WuXing.METAL, PatternType.HUA_JIN),
            (TianGan.GENG, TianGan.YI): (WuXing.METAL, PatternType.HUA_JIN),
            (TianGan.BING, TianGan.XIN): (WuXing.WATER, PatternType.HUA_SHUI),
            (TianGan.XIN, TianGan.BING): (WuXing.WATER, PatternType.HUA_SHUI),
            (TianGan.DING, TianGan.REN): (WuXing.WOOD, PatternType.HUA_MU),
            (TianGan.REN, TianGan.DING): (WuXing.WOOD, PatternType.HUA_MU),
            (TianGan.WU, TianGan.GUI): (WuXing.FIRE, PatternType.HUA_HUO),
            (TianGan.GUI, TianGan.WU): (WuXing.FIRE, PatternType.HUA_HUO),
        }

        # 條件1: 找合神
        hua_info = None
        partner = None

        if (day_stem, month_stem) in wu_he:
            hua_info = wu_he[(day_stem, month_stem)]
            partner = month_stem
        elif (day_stem, hour_stem) in wu_he:
            hua_info = wu_he[(day_stem, hour_stem)]
            partner = hour_stem

        if not hua_info:
            return None

        hua_wuxing, pattern_type = hua_info

        # 條件2: 化神得勢（當令或五行能量 > 30%）
        wx_dist = self._calculate_wuxing_distribution(bazi)
        hua_pct = wx_dist[hua_wuxing]

        is_dang_ling = month_branch.wuxing == hua_wuxing
        is_strong = hua_pct >= 30

        if not is_dang_ling and not is_strong:
            return None

        # 條件3: 檢查妒合（年干或其他干與日干相同造成爭合）
        partner_pair_stem = day_stem
        other_stems = [year_stem, month_stem, hour_stem]
        other_stems = [s for s in other_stems if s != partner]

        has_duhe = any(s == partner_pair_stem for s in other_stems)

        # 有妒合時，若化神夠強(>=40%)且當令，仍可成假化
        if has_duhe:
            if not (is_dang_ling and hua_pct >= 40):
                return None
            is_jia_hua = True  # 假化
        else:
            is_jia_hua = False  # 真化

        # 條件4: 無剋制化神（天干地支本氣）
        # 注意：合神雙方(日干和合神)都在化，不算剋制
        ke_wuxing = hua_wuxing.overcome_by
        combining_wuxings = {day_stem.wuxing, partner.wuxing}

        # 檢查天干（排除正在合化的干）
        for stem in bazi.all_stems:
            if stem.wuxing == ke_wuxing and stem.wuxing not in combining_wuxings:
                return None

        # 檢查地支本氣
        for branch in bazi.all_branches:
            if branch.wuxing == ke_wuxing:
                return None

        hua_type = "假化" if is_jia_hua else "真化"
        return SpecialPattern(
            pattern_type=pattern_type,
            yong_shen_info=HUA_QI_YONG_SHEN[pattern_type],
            description=f"{pattern_type.chinese}（{hua_type}）：{day_stem.chinese}{partner.chinese}合化{hua_wuxing.chinese}，{hua_pct:.0f}%",
        )

    # =========================================================================
    # 兩神成象格檢測 (Two Gods Forming Image)
    # =========================================================================

    def _check_liang_shen_ge(self, bazi: BaZi) -> Optional[SpecialPattern]:
        """
        檢查兩神成象格

        成格條件：
        1. 八字只有兩種五行
        2. 兩者力量相約（各佔4個左右）
        """
        wuxing_count = {}
        for wx in WuXing:
            wuxing_count[wx] = self._count_element(bazi, wx)

        present = [wx for wx, c in wuxing_count.items() if c > 0]

        if len(present) != 2:
            return None

        wx1, wx2 = present
        c1, c2 = wuxing_count[wx1], wuxing_count[wx2]

        # 力量相約（差距不超過2）
        if abs(c1 - c2) > 2:
            return None

        # 判斷相生或相剋
        if wx1.overcomes == wx2 or wx2.overcomes == wx1:
            # 相剋 - 兩神相成格，需通關
            if wx1.overcomes == wx2:
                tong_guan = wx1.generates
            else:
                tong_guan = wx2.generates

            return SpecialPattern(
                pattern_type=PatternType.LIANG_SHEN_XIANG_CHENG,
                yong_shen_info=PatternYongShen(
                    yong_shen=tong_guan,
                    xi_shen=[],
                    ji_shen=[],
                ),
                description=f"兩神相成格：{wx1.chinese}{wx2.chinese}相剋，喜{tong_guan.chinese}通關",
            )

        elif wx1.generates == wx2 or wx2.generates == wx1:
            # 相生 - 兩神相生格，洩旺氣
            if wx1.generates == wx2:
                xie = wx2.generates
            else:
                xie = wx1.generates

            return SpecialPattern(
                pattern_type=PatternType.LIANG_SHEN_XIANG_SHENG,
                yong_shen_info=PatternYongShen(
                    yong_shen=xie,
                    xi_shen=[],
                    ji_shen=[],
                ),
                description=f"兩神相生格：{wx1.chinese}{wx2.chinese}相生，喜{xie.chinese}洩旺氣",
            )

        return None

    # =========================================================================
    # 暗沖格檢測 (Hidden Clash Patterns)
    # =========================================================================

    def _check_an_chong_ge(self, bazi: BaZi) -> Optional[SpecialPattern]:
        """
        檢查暗沖格

        成格條件：
        1. 八字無正官明現
        2. 特定日柱 + 三個以上相同地支沖出暗官
        """
        day_stem = bazi.day_pillar.stem
        day_branch = bazi.day_pillar.branch
        branches = bazi.all_branches

        # 檢查無正官明現
        guan_wuxing = day_stem.wuxing.overcome_by
        for stem in bazi.all_stems:
            if stem.wuxing == guan_wuxing and stem.yinyang != day_stem.yinyang:
                return None

        # 倒沖祿馬格
        dao_chong = [
            (TianGan.BING, DiZhi.WU, DiZhi.WU, 3, "三午沖子得癸水官"),
            (TianGan.DING, DiZhi.SI, DiZhi.SI, 3, "三巳沖亥得壬水官"),
        ]
        for req_stem, req_day_br, req_br, min_count, desc in dao_chong:
            if day_stem == req_stem and day_branch == req_day_br:
                if branches.count(req_br) >= min_count:
                    return SpecialPattern(
                        pattern_type=PatternType.DAO_CHONG_LU_MA,
                        yong_shen_info=PatternYongShen(
                            yong_shen=guan_wuxing, xi_shen=[], ji_shen=[]
                        ),
                        description=f"倒沖祿馬格：{day_stem.chinese}{day_branch.chinese}日，{desc}",
                    )

        # 飛天祿馬格
        fei_tian = [
            (TianGan.GENG, DiZhi.ZI, DiZhi.ZI, 3, "三子沖午得丁火官"),
            (TianGan.REN, DiZhi.ZI, DiZhi.ZI, 3, "三子沖午得己土官"),
            (TianGan.XIN, DiZhi.HAI, DiZhi.HAI, 3, "三亥沖巳得丙火官"),
            (TianGan.GUI, DiZhi.HAI, DiZhi.HAI, 3, "三亥沖巳得戊土官"),
        ]
        for req_stem, req_day_br, req_br, min_count, desc in fei_tian:
            if day_stem == req_stem and day_branch == req_day_br:
                if branches.count(req_br) >= min_count:
                    return SpecialPattern(
                        pattern_type=PatternType.FEI_TIAN_LU_MA,
                        yong_shen_info=PatternYongShen(
                            yong_shen=guan_wuxing, xi_shen=[], ji_shen=[]
                        ),
                        description=f"飛天祿馬格：{day_stem.chinese}{day_branch.chinese}日，{desc}",
                    )

        # 井欄叉格
        if day_stem == TianGan.GENG:
            shen_zi_chen = {DiZhi.SHEN, DiZhi.ZI, DiZhi.CHEN}
            if shen_zi_chen <= set(branches):
                return SpecialPattern(
                    pattern_type=PatternType.JING_LAN_CHA,
                    yong_shen_info=PatternYongShen(
                        yong_shen=guan_wuxing,
                        xi_shen=[WuXing.WOOD],
                        ji_shen=[WuXing.FIRE],
                    ),
                    description="井欄叉格：庚日地支申子辰全，暗沖寅午戌",
                )

        return None

    # =========================================================================
    # 暗合格檢測 (Hidden Combination Patterns)
    # =========================================================================

    def _check_an_he_ge(self, bazi: BaZi) -> Optional[SpecialPattern]:
        """
        檢查暗合格

        成格條件：
        1. 八字無正官明現
        2. 特定日柱 + 三個以上相同地支暗合出官星
        """
        day_stem = bazi.day_pillar.stem
        day_branch = bazi.day_pillar.branch
        branches = bazi.all_branches

        # 檢查無正官明現
        guan_wuxing = day_stem.wuxing.overcome_by
        for stem in bazi.all_stems:
            if stem.wuxing == guan_wuxing and stem.yinyang != day_stem.yinyang:
                return None

        # 暗合官格日柱
        an_he = [
            (TianGan.JIA, DiZhi.CHEN, DiZhi.CHEN, 3, "三辰暗合酉中辛官"),
            (TianGan.WU, DiZhi.XU, DiZhi.XU, 3, "三戌暗合卯中乙官"),
            (TianGan.GUI, DiZhi.MAO, DiZhi.MAO, 3, "三卯暗合戌中戊官"),
            (TianGan.GUI, DiZhi.YOU, DiZhi.YOU, 3, "三酉暗合辰中戊官"),
        ]

        for req_stem, req_day_br, req_br, min_count, desc in an_he:
            if day_stem == req_stem and day_branch == req_day_br:
                if branches.count(req_br) >= min_count:
                    return SpecialPattern(
                        pattern_type=PatternType.AN_HE_GUAN,
                        yong_shen_info=PatternYongShen(
                            yong_shen=guan_wuxing, xi_shen=[], ji_shen=[]
                        ),
                        description=f"暗合官格：{day_stem.chinese}{day_branch.chinese}日，{desc}",
                    )

        return None

    # =========================================================================
    # 輔助方法 (Helper Methods)
    # =========================================================================

    def _has_root(self, bazi: BaZi, wuxing: WuXing) -> bool:
        """檢查某五行是否在地支有根（本氣或中餘氣）"""
        for branch in bazi.all_branches:
            if branch.wuxing == wuxing:
                return True
            for hidden, ratio in branch.hidden_stems.items():
                if hidden.wuxing == wuxing and ratio >= 0.2:
                    return True
        return False

    def _has_stem_element(self, bazi: BaZi, wuxing: WuXing, exclude_day: bool = False) -> bool:
        """檢查天干是否有某五行"""
        for i, stem in enumerate(bazi.all_stems):
            if exclude_day and i == 2:
                continue
            if stem.wuxing == wuxing:
                return True
        return False

    def _count_element(self, bazi: BaZi, wuxing: WuXing) -> int:
        """統計某五行在八字中出現次數（天干+地支本氣）"""
        count = 0
        for stem in bazi.all_stems:
            if stem.wuxing == wuxing:
                count += 1
        for branch in bazi.all_branches:
            if branch.wuxing == wuxing:
                count += 1
        return count

    def _calculate_shishen_distribution(self, bazi: BaZi) -> dict:
        """
        計算十神分佈（天干+地支本氣）

        Returns:
            dict: {"比劫": n, "印星": n, "食傷": n, "財星": n, "官殺": n}
        """
        dm = bazi.day_master
        stats = {"比劫": 0, "印星": 0, "食傷": 0, "財星": 0, "官殺": 0}

        bi_jie = [ShiShen.BI_JIAN, ShiShen.JIE_CAI]
        yin_xing = [ShiShen.ZHENG_YIN, ShiShen.PIAN_YIN]
        shi_shang = [ShiShen.SHI_SHEN, ShiShen.SHANG_GUAN]
        cai_xing = [ShiShen.ZHENG_CAI, ShiShen.PIAN_CAI]
        guan_sha = [ShiShen.ZHENG_GUAN, ShiShen.QI_SHA]

        # 天干（跳過日主）
        for i, stem in enumerate(bazi.all_stems):
            if i == 2:
                continue
            ss = calculate_shishen(dm, stem)
            if ss in bi_jie:
                stats["比劫"] += 1
            elif ss in yin_xing:
                stats["印星"] += 1
            elif ss in shi_shang:
                stats["食傷"] += 1
            elif ss in cai_xing:
                stats["財星"] += 1
            elif ss in guan_sha:
                stats["官殺"] += 1

        # 地支本氣
        for branch in bazi.all_branches:
            main_stem = list(branch.hidden_stems.keys())[0]
            ss = calculate_shishen(dm, main_stem)
            if ss in bi_jie:
                stats["比劫"] += 1
            elif ss in yin_xing:
                stats["印星"] += 1
            elif ss in shi_shang:
                stats["食傷"] += 1
            elif ss in cai_xing:
                stats["財星"] += 1
            elif ss in guan_sha:
                stats["官殺"] += 1

        return stats

    def _calculate_wuxing_distribution(self, bazi: BaZi) -> dict:
        """
        計算五行能量分佈

        Returns:
            dict: {WuXing.WOOD: pct, ...}
        """
        calculator = WuXingCalculator()
        strength = calculator.calculate_strength(bazi)
        return {wx: strength.percentage(wx) for wx in WuXing}
