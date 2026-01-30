# 神煞完整性分析与天德贵人查法

## 一、当前代码已实现的神煞

根据 `bazi/domain/models/shensha.py`，当前实现了以下神煞：

### 吉星（8个）
| 神煞 | 代码常量 | 实现状态 |
|------|----------|----------|
| 天乙贵人 | TIAN_YI_GUI_REN | ✅ 已实现 |
| 天德贵人 | TIAN_DE | ⚠️ 有错误 |
| 月德贵人 | YUE_DE | ✅ 已实现 |
| 文昌贵人 | WEN_CHANG | ✅ 已实现 |
| 禄神 | LU_SHEN | ✅ 已实现 |
| 将星 | JIANG_XING | ✅ 已实现 |
| 华盖 | HUA_GAI | ✅ 已实现 |
| 三奇 | SAN_QI | ❌ 仅定义未实现 |

### 凶星（3个）
| 神煞 | 代码常量 | 实现状态 |
|------|----------|----------|
| 羊刃 | YANG_REN | ✅ 已实现 |
| 七杀 | QI_SHA | ❌ 仅定义未实现 |
| 空亡 | KONG_WANG | ❌ 仅定义未实现 |

### 桃花类（4个）
| 神煞 | 代码常量 | 实现状态 |
|------|----------|----------|
| 桃花 | TAO_HUA | ✅ 已实现 |
| 红艳煞 | HONG_YAN_SHA | ❌ 仅定义未实现 |
| 孤辰 | GU_CHEN | ❌ 仅定义未实现 |
| 寡宿 | GUA_SU | ❌ 仅定义未实现 |

### 其他（4个）
| 神煞 | 代码常量 | 实现状态 |
|------|----------|----------|
| 驿马 | YI_MA | ✅ 已实现 |
| 劫煞 | JIE_SHA | ❌ 仅定义未实现 |
| 亡神 | WANG_SHEN | ❌ 仅定义未实现 |

**统计：定义了19个神煞，仅实现了10个**

---

## 二、缺少的重要神煞

根据[国易堂](https://www.guoyi360.com/shensha/)和[百度百科](https://baike.baidu.com/item/%E5%9B%9B%E6%9F%B1%E7%A5%9E%E7%85%9E/9604255)，以下是常用但未实现的神煞：

### 重要吉神（建议添加）

| 神煞 | 说明 | 查法 |
|------|------|------|
| **太极贵人** | 聪明好学、悟性高 | 甲乙→子午，丙丁→卯酉，戊己→辰戌丑未，庚辛→寅亥，壬癸→巳申 |
| **国印贵人** | 掌权、诚实可靠 | 甲→戌，乙→亥，丙戊→丑，丁己→寅，庚→辰，辛→巳，壬→未，癸→申 |
| **天医贵人** | 医药、健康 | 同天德查法（见下文） |
| **福星贵人** | 福禄双全 | 甲→寅，乙→卯，丙→巳，丁→午，戊→巳，己→午，庚→申，辛→酉，壬→亥，癸→子 |
| **金舆** | 得妻财、富贵 | 甲→辰，乙→巳，丙戊→未，丁己→申，庚→戌，辛→亥，壬→丑，癸→寅 |
| **魁罡** | 领导威权 | 庚辰、庚戌、壬辰、戊戌四日 |
| **天赦** | 逢凶化吉 | 特定日期（如春甲子、夏甲午等） |

### 重要凶煞（建议添加）

| 神煞 | 说明 | 查法 |
|------|------|------|
| **灾煞** | 灾祸、意外 | 申子辰→午，寅午戌→子，巳酉丑→卯，亥卯未→酉 |
| **天罗地网** | 牢狱、疾病 | 辰为天罗，戌为地网 |
| **阴阳差错** | 婚姻不顺 | 丙子、丁丑、戊寅等特定日 |
| **六厄** | 困难、阻碍 | 甲己→卯酉，乙庚→辰戌，丙辛→巳亥，丁壬→午子，戊癸→丑未 |
| **勾绞煞** | 官非、口舌 | 按年支查月日时支 |

---

## 三、天德贵人正确查法

### 权威来源：《问真神煞大全》

**古诀**：
> 寅月丁。卯月申。辰月壬。巳月辛。午月亥。未月甲。
> 申月癸。酉月寅。戌月丙。亥月乙。子月巳。丑月庚。

**查法**：以月支查四柱干支

### 当前代码错误分析

代码位置：`shensha_calculator.py:37-51`

```python
# 当前错误实现 - 注释显示开发者知道原始值是地支但错误地转换了
_TIAN_DE: Dict[EarthlyBranch, HeavenlyStem] = {
    EarthlyBranch.MAO: HeavenlyStem.GENG,  # Note: original was '申' but should be stem  ❌
    EarthlyBranch.WU: HeavenlyStem.JIA,    # Note: original was '亥' but should be stem  ❌
    EarthlyBranch.YOU: HeavenlyStem.BING,  # Note: original was '寅'                     ❌
    EarthlyBranch.ZI: HeavenlyStem.BING,   # Note: original was '巳'                     ❌
    # ...
}
```

**错误原因**：开发者误以为天德贵人只能是天干，所以将地支（申、亥、寅、巳）错误地转换为了天干（庚、甲、丙、丙）。

**正确理解**：天德贵人是**混合类型**，8个月查天干，4个月查地支！

### 传统口诀

根据[阐微堂](https://chanweitang.com/post/120.html)和[国易堂](https://www.guoyi360.com/tdgr/1868.html)：

> 正月生者见**丁**，二月生者见**申**，三月生者见**壬**，
> 四月生者见**辛**，五月生者见**亥**，六月生者见**甲**，
> 七月生者见**癸**，八月生者见**寅**，九月生者见**丙**，
> 十月生者见**乙**，十一月生者见**巳**，十二月生者见**庚**。

### 完整查表

| 月支 | 天德 | 类型 | 说明 |
|------|------|------|------|
| 寅（正月） | **丁** | 天干 | 寅午戌合火局，丁为阴火 |
| 卯（二月） | **申** | 地支 | 卯未亥合木局，木墓在坤（申） |
| 辰（三月） | **壬** | 天干 | 辰申子合水局，壬为阳水 |
| 巳（四月） | **辛** | 天干 | 寅午戌合火局，辛金为阴 |
| 午（五月） | **亥** | 地支 | 寅午戌合火局，火墓在乾（亥） |
| 未（六月） | **甲** | 天干 | 卯未亥合木局，甲为阳木 |
| 申（七月） | **癸** | 天干 | 辰申子合水局，癸为阴水 |
| 酉（八月） | **寅** | 地支 | 巳酉丑合金局，金墓在艮（寅） |
| 戌（九月） | **丙** | 天干 | 寅午戌合火局，丙为阳火 |
| 亥（十月） | **乙** | 天干 | 卯未亥合木局，乙为阴木 |
| 子（十一月） | **巳** | 地支 | 辰申子合水局，水墓在巽（巳） |
| 丑（十二月） | **庚** | 天干 | 巳酉丑合金局，庚为阳金 |

### 理论依据（《考原》）

> "寅申巳亥月，乃五行长生之位，故配**阴干**；
> 辰戌丑未月，乃五行墓库之位，故配**阳干**；
> 子午卯酉月，乃五行当旺之位，故配以墓辰本宫之**地支**。"

---

## 四、天德合（新发现）

### 权威来源：《问真神煞大全》

**问真精评**：性格好，主化险为夷，不犯刑律，不遇危难。（天德的**一半效果**）

**古诀**：
> 寅月壬。卯月巳。辰月丁。巳月丙。午月寅。未月己。
> 申月戊。酉月亥。戌月辛。亥月庚。子月申。丑月乙。

**原理**：天德与天干五合或地支六合者即为天德合。如没有天德贵人，有天德合也起到天德贵人的作用。

### 天德与天德合对照表

| 月支 | 天德 | 天德合 | 合的类型 |
|------|------|--------|----------|
| 寅月 | 丁 | **壬** | 丁壬合（天干五合） |
| 卯月 | 申 | **巳** | 巳申合（地支六合） |
| 辰月 | 壬 | **丁** | 壬丁合（天干五合） |
| 巳月 | 辛 | **丙** | 丙辛合（天干五合） |
| 午月 | 亥 | **寅** | 寅亥合（地支六合） |
| 未月 | 甲 | **己** | 甲己合（天干五合） |
| 申月 | 癸 | **戊** | 戊癸合（天干五合） |
| 酉月 | 寅 | **亥** | 寅亥合（地支六合） |
| 戌月 | 丙 | **辛** | 丙辛合（天干五合） |
| 亥月 | 乙 | **庚** | 乙庚合（天干五合） |
| 子月 | 巳 | **申** | 巳申合（地支六合） |
| 丑月 | 庚 | **乙** | 乙庚合（天干五合） |

### 验证结论

**天德合完美验证了天德贵人的查法是正确的**：
- 卯、午、酉、子月的天德是**地支**（申、亥、寅、巳）
- 对应的天德合也是**地支**（巳、寅、亥、申）- 通过六合关系相合

这进一步证明代码中将地支转换为天干的做法是**错误**的！

### 建议：添加天德合神煞

当前代码未实现天德合，建议添加：

```python
class ShenShaType(Enum):
    TIAN_DE = "天德"
    TIAN_DE_HE = "天德合"  # 新增
```

---

### 代码修复建议

当前代码错误地将所有月份都查天干，正确实现应该是：

```python
from typing import Union

# 天德贵人 - 混合天干和地支
_TIAN_DE: Dict[EarthlyBranch, Union[HeavenlyStem, EarthlyBranch]] = {
    # 寅申巳亥月 - 配阴干
    EarthlyBranch.YIN: HeavenlyStem.DING,   # 正月见丁
    EarthlyBranch.SHEN: HeavenlyStem.GUI,   # 七月见癸
    EarthlyBranch.SI: HeavenlyStem.XIN,     # 四月见辛
    EarthlyBranch.HAI: HeavenlyStem.YI,     # 十月见乙

    # 辰戌丑未月 - 配阳干
    EarthlyBranch.CHEN: HeavenlyStem.REN,   # 三月见壬
    EarthlyBranch.XU: HeavenlyStem.BING,    # 九月见丙
    EarthlyBranch.CHOU: HeavenlyStem.GENG,  # 十二月见庚
    EarthlyBranch.WEI: HeavenlyStem.JIA,    # 六月见甲

    # 子午卯酉月 - 配地支（墓库位置）
    EarthlyBranch.ZI: EarthlyBranch.SI,     # 十一月见巳
    EarthlyBranch.WU: EarthlyBranch.HAI,    # 五月见亥
    EarthlyBranch.MAO: EarthlyBranch.SHEN,  # 二月见申
    EarthlyBranch.YOU: EarthlyBranch.YIN,   # 八月见寅
}


def is_tian_de(month_branch: EarthlyBranch, target: Union[HeavenlyStem, EarthlyBranch]) -> bool:
    """检查天德贵人"""
    expected = _TIAN_DE.get(month_branch)
    if expected is None:
        return False

    # 天德可能是天干或地支，需要类型匹配
    if isinstance(expected, HeavenlyStem) and isinstance(target, HeavenlyStem):
        return expected == target
    elif isinstance(expected, EarthlyBranch) and isinstance(target, EarthlyBranch):
        return expected == target
    return False
```

### 检查逻辑修改

在 `calculate_for_bazi` 中，天德检查需要同时检查天干和地支：

```python
# 检查天德（基于月支）
month_branch = bazi.month_pillar.branch
tian_de_target = _TIAN_DE.get(month_branch)

if tian_de_target:
    for pos_name, pillar in positions:
        # 检查天干是否匹配
        if isinstance(tian_de_target, HeavenlyStem):
            if pillar.stem == tian_de_target:
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_DE,
                    position=f"{pos_name}_stem",
                    triggered_by=month_branch.chinese,
                ))
        # 检查地支是否匹配
        elif isinstance(tian_de_target, EarthlyBranch):
            if pillar.branch == tian_de_target:
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_DE,
                    position=f"{pos_name}_branch",
                    triggered_by=month_branch.chinese,
                ))
```

---

## 五、已定义但未实现的神煞查法

### 1. 三奇贵人（SAN_QI）

天上三奇：甲戊庚
地上三奇：乙丙丁
人中三奇：壬癸辛

查法：四柱天干顺序出现以上组合

### 2. 空亡（KONG_WANG）

查法：以日柱为准，按六十甲子旬中空亡
- 甲子旬：空亡在戌亥
- 甲戌旬：空亡在申酉
- 甲申旬：空亡在午未
- 甲午旬：空亡在辰巳
- 甲辰旬：空亡在寅卯
- 甲寅旬：空亡在子丑

### 3. 孤辰寡宿（GU_CHEN / GUA_SU）

| 年支 | 孤辰 | 寡宿 |
|------|------|------|
| 亥子丑 | 寅 | 戌 |
| 寅卯辰 | 巳 | 丑 |
| 巳午未 | 申 | 辰 |
| 申酉戌 | 亥 | 未 |

### 4. 劫煞（JIE_SHA）

| 年/日支 | 劫煞 |
|---------|------|
| 申子辰 | 巳 |
| 寅午戌 | 亥 |
| 巳酉丑 | 寅 |
| 亥卯未 | 申 |

### 5. 亡神（WANG_SHEN）

| 年/日支 | 亡神 |
|---------|------|
| 申子辰 | 亥 |
| 寅午戌 | 巳 |
| 巳酉丑 | 申 |
| 亥卯未 | 寅 |

### 6. 红艳煞（HONG_YAN_SHA）

| 日干 | 红艳 |
|------|------|
| 甲 | 午 |
| 乙 | 申 |
| 丙 | 寅 |
| 丁 | 未 |
| 戊 | 辰 |
| 己 | 辰 |
| 庚 | 戌 |
| 辛 | 酉 |
| 壬 | 子 |
| 癸 | 申 |

---

## 六、神煞实现优先级建议

### 高优先级（常用且重要）

1. **修复天德贵人** - 当前实现有错误
2. **空亡** - 非常重要的凶煞
3. **太极贵人** - 常用吉星
4. **孤辰寡宿** - 婚姻分析必用
5. **劫煞/亡神** - 已定义未实现

### 中优先级

6. **国印贵人** - 事业分析有用
7. **金舆** - 财运分析有用
8. **灾煞** - 凶煞预警
9. **魁罡** - 特殊日柱

### 低优先级

10. **三奇** - 较少见
11. **红艳煞** - 桃花类已有
12. **天医** - 专业领域

---

## 参考资料

- [神煞大全 - 国易堂](https://www.guoyi360.com/shensha/)
- [天德贵人查法 - 阐微堂](https://chanweitang.com/post/120.html)
- [四柱神煞 - 百度百科](https://baike.baidu.com/item/%E5%9B%9B%E6%9F%B1%E7%A5%9E%E7%85%9E/9604255)
- [太极贵人 - 国易堂](https://www.guoyi360.com/tjgr/1863.html)
- [国印贵人 - 国易堂](https://www.guoyi360.com/grgr/2032.html)
