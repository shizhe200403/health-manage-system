from datetime import date, timedelta

from apps.tracking.models import HealthGoal, MealRecord


GOAL_TYPE_MAP = {
    "weight_loss": "减重", "muscle_gain": "增肌", "blood_sugar_control": "控糖",
    "fat_control": "控脂", "protein_up": "提升蛋白摄入", "diet_balance": "饮食均衡",
}


def build_user_context(user):
    parts = [
        "你是一位专业的营养师AI助手，名叫「小食」。请基于以下用户档案提供个性化的营养和饮食建议。",
        "所有回复必须使用中文。建议应具体、可执行。如果用户问非营养相关问题，礼貌地引导回营养话题。",
    ]

    # 基本信息
    try:
        p = user.profile
        info = []
        if p.gender:
            info.append(f"性别：{p.gender}")
        if p.birthday:
            age = (date.today() - p.birthday).days // 365
            info.append(f"年龄：{age}岁")
        if p.height_cm:
            info.append(f"身高：{p.height_cm}cm")
        if p.weight_kg:
            info.append(f"体重：{p.weight_kg}kg")
        if p.target_weight_kg:
            info.append(f"目标体重：{p.target_weight_kg}kg")
        if p.activity_level:
            info.append(f"活动水平：{p.activity_level}")
        if p.cooking_skill:
            info.append(f"烹饪水平：{p.cooking_skill}")
        if p.diet_type:
            info.append(f"饮食类型：{p.diet_type}")
        if info:
            parts.append(f"\n## 用户基本信息\n{'，'.join(info)}")
    except Exception:
        pass

    # 健康状况
    try:
        h = user.health_condition
        items = []
        if h.allergy_tags:
            items.append(f"过敏原：{', '.join(h.allergy_tags)}")
        if h.avoid_food_tags:
            items.append(f"忌口：{', '.join(h.avoid_food_tags)}")
        if h.has_hypertension:
            items.append("高血压：是")
        if h.has_diabetes:
            items.append("糖尿病：是")
        if h.has_hyperlipidemia:
            items.append("高血脂：是")
        if h.is_pregnant:
            items.append("孕期：是")
        if h.is_lactating:
            items.append("哺乳期：是")
        if items:
            parts.append(f"\n## 健康状况\n{'；'.join(items)}")
    except Exception:
        pass

    # 当前目标
    goals = HealthGoal.objects.filter(user=user, status="active")
    if goals.exists():
        lines = []
        for g in goals[:3]:
            label = GOAL_TYPE_MAP.get(g.goal_type, g.goal_type)
            line = f"- {label}"
            if g.target_value:
                line += f"，目标值{g.target_value}"
            if g.current_value:
                line += f"，当前{g.current_value}"
            lines.append(line)
        parts.append(f"\n## 当前健康目标\n" + "\n".join(lines))

    # 近7天饮食
    week_ago = date.today() - timedelta(days=7)
    records = (
        MealRecord.objects.filter(user=user, record_date__gte=week_ago)
        .prefetch_related("items")
        .order_by("-record_date")[:14]
    )
    if records:
        meal_lines = []
        for r in records:
            items_str = "、".join(
                f"{i.ingredient_name_snapshot or '食物'}({int(i.energy or 0)}kcal)"
                for i in r.items.all()[:5]
            )
            if items_str:
                meal_type_map = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "snack": "加餐"}
                meal_lines.append(f"- {r.record_date} {meal_type_map.get(r.meal_type, r.meal_type)}：{items_str}")
        if meal_lines:
            parts.append(f"\n## 近7天饮食记录\n" + "\n".join(meal_lines[:10]))

    # 收藏菜谱
    favs = user.favorite_recipes.select_related("recipe").order_by("-created_at")[:10]
    if favs:
        titles = [f.recipe.title for f in favs if f.recipe]
        if titles:
            parts.append(f"\n## 收藏的菜谱\n{'、'.join(titles)}")

    parts.append("\n## 注意事项\n- 必须考虑用户的过敏原和忌口\n- 回复简洁实用，避免过长")
    return "\n".join(parts)
