"""
年度分析服务层
提供年度数据查询和计算功能
"""
from __future__ import annotations
from typing import List, Dict, Any
from db.connection import get_connection, release_connection
from db.table import get_table_name
from models.annual_analysis_types import (
    AnnualOverview,
    CategoryAnalysis,
    SubCategoryDetail,
    LocationDistribution,
    TimeDistribution,
    MonthlyData,
    LocationAnalysis,
    LocationItem,
    ResultAnalysis,
    OverallResult,
    SubCategoryResult,
    LocationResult,
)


def _calculate_rates(valid_count, contact_count, solved_count,
                     satisfied_count, basic_satisfied_count) -> Dict[str, float]:
    """
    计算各项率

    Args:
        valid_count: 有效回访数
        contact_count: 联系数
        solved_count: 已解决数
        satisfied_count: 满意数
        basic_satisfied_count: 基本满意数

    Returns:
        包含响应率、解决率、满意率、综合成绩的字典
    """
    # 将 Decimal 类型转换为 int，避免与 float 运算时出错
    valid_count = int(valid_count or 0)
    contact_count = int(contact_count or 0)
    solved_count = int(solved_count or 0)
    satisfied_count = int(satisfied_count or 0)
    basic_satisfied_count = int(basic_satisfied_count or 0)

    if valid_count == 0:
        return {
            "response_rate": 0.0,
            "solve_rate": 0.0,
            "satisfaction_rate": 0.0,
            "comprehensive_score": 0.0
        }

    response_rate = (contact_count / valid_count) * 100
    solve_rate = (solved_count / valid_count) * 100
    satisfaction_rate = ((satisfied_count + basic_satisfied_count * 0.9) / valid_count) * 100
    comprehensive_score = (response_rate * 0.1 + satisfaction_rate * 0.4 + solve_rate * 0.5) * 100

    return {
        "response_rate": round(response_rate, 2),
        "solve_rate": round(solve_rate, 2),
        "satisfaction_rate": round(satisfaction_rate, 2),
        "comprehensive_score": round(comprehensive_score, 2)
    }


def _format_yoy(current, last) -> str:
    """
    格式化同比变化

    Args:
        current: 当前值
        last: 去年值

    Returns:
        格式化的同比字符串，如 "+15.3%" 或 "-5.2%"
    """
    # 将 Decimal 类型转换为 float，避免类型错误
    current = float(current or 0)
    last = float(last or 0)

    if last == 0:
        return "+100.0%" if current > 0 else "0.0%"

    change = ((current - last) / last) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{round(change, 1)}%"


def get_annual_overview(year: int, category: str) -> AnnualOverview:
    """
    工具 1：获取年度总体基本情况

    Args:
        year: 年份
        category: 二级分类

    Returns:
        年度总体基本情况数据
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            # 查询当年数据
            sql_current = f"""
                SELECT
                    COUNT(*) as total_count,
                    SUM(CASE WHEN 是否有效回访 = '是' THEN 1 ELSE 0 END) as valid_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否联系 = '是' THEN 1 ELSE 0 END) as contact_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否解决 = '是' THEN 1 ELSE 0 END) as solved_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '满意' THEN 1 ELSE 0 END) as satisfied_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '基本满意' THEN 1 ELSE 0 END) as basic_satisfied_count
                FROM {table}
                WHERE YEAR(创建时间) = %s AND 二级分类 = %s
            """
            cur.execute(sql_current, (year, category))
            current_data = cur.fetchone()

            # 查询去年数据
            last_year = year - 1
            cur.execute(sql_current, (last_year, category))
            last_data = cur.fetchone()

            # 计算当年的率
            current_rates = _calculate_rates(
                current_data["valid_count"],
                current_data["contact_count"],
                current_data["solved_count"],
                current_data["satisfied_count"],
                current_data["basic_satisfied_count"]
            )

            # 计算去年的率
            last_rates = _calculate_rates(
                last_data["valid_count"],
                last_data["contact_count"],
                last_data["solved_count"],
                last_data["satisfied_count"],
                last_data["basic_satisfied_count"]
            )

            # 计算同比
            count_change = current_data["total_count"] - last_data["total_count"]
            count_yoy = _format_yoy(current_data["total_count"], last_data["total_count"])
            solve_rate_yoy = _format_yoy(current_rates["solve_rate"], last_rates["solve_rate"])
            satisfaction_rate_yoy = _format_yoy(current_rates["satisfaction_rate"], last_rates["satisfaction_rate"])

            return {
                "current_year_count": current_data["total_count"],
                "last_year_count": last_data["total_count"],
                "yoy_change": count_change,
                "yoy_percentage": count_yoy,
                "solve_rate": current_rates["solve_rate"],
                "solve_rate_last_year": last_rates["solve_rate"],
                "solve_rate_yoy": solve_rate_yoy,
                "satisfaction_rate": current_rates["satisfaction_rate"],
                "satisfaction_rate_last_year": last_rates["satisfaction_rate"],
                "satisfaction_rate_yoy": satisfaction_rate_yoy
            }
    finally:
        release_connection(conn)


def get_category_analysis(year: int, category: str) -> CategoryAnalysis:
    """
    工具 2：获取诉求分类分析

    Args:
        year: 年份
        category: 二级分类

    Returns:
        诉求分类分析数据
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            # 查询三级分类统计
            sql_sub_category = f"""
                SELECT
                    三级分类,
                    COUNT(*) as count
                FROM {table}
                WHERE YEAR(创建时间) = %s AND 二级分类 = %s
                GROUP BY 三级分类
                ORDER BY count DESC
            """
            cur.execute(sql_sub_category, (year, category))
            sub_categories = cur.fetchall()

            total_count = sum(row["count"] for row in sub_categories)

            result_sub_categories: List[SubCategoryDetail] = []

            for sub_cat in sub_categories:
                sub_cat_name = sub_cat["三级分类"]
                sub_cat_count = sub_cat["count"]
                sub_cat_percentage = round((sub_cat_count / total_count) * 100, 2) if total_count > 0 else 0.0

                # 查询该三级分类在各街镇的分布
                sql_locations = f"""
                    SELECT
                        被反映街乡镇 as town,
                        COUNT(*) as count
                    FROM {table}
                    WHERE YEAR(创建时间) = %s AND 二级分类 = %s AND 三级分类 = %s
                    GROUP BY 被反映街乡镇
                    ORDER BY count DESC
                """
                cur.execute(sql_locations, (year, category, sub_cat_name))
                locations = cur.fetchall()

                location_list: List[LocationDistribution] = []
                for loc in locations:
                    loc_percentage = round((loc["count"] / sub_cat_count) * 100, 2) if sub_cat_count > 0 else 0.0
                    location_list.append({
                        "town": loc["town"] or "未知",
                        "count": loc["count"],
                        "percentage": loc_percentage
                    })

                result_sub_categories.append({
                    "name": sub_cat_name or "未分类",
                    "count": sub_cat_count,
                    "percentage": sub_cat_percentage,
                    "locations": location_list
                })

            return {"sub_categories": result_sub_categories}
    finally:
        release_connection(conn)


def get_time_distribution(year: int, category: str) -> TimeDistribution:
    """
    工具 3：获取时间分布分析

    Args:
        year: 年份
        category: 二级分类

    Returns:
        时间分布分析数据
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            monthly_data_list: List[MonthlyData] = []

            for month in range(1, 13):
                # 查询当年该月数据
                sql_current = f"""
                    SELECT COUNT(*) as count
                    FROM {table}
                    WHERE YEAR(创建时间) = %s AND MONTH(创建时间) = %s AND 二级分类 = %s
                """
                cur.execute(sql_current, (year, month, category))
                current_count = cur.fetchone()["count"]

                # 查询去年该月数据
                last_year = year - 1
                cur.execute(sql_current, (last_year, month, category))
                last_count = cur.fetchone()["count"]

                # 计算同比
                yoy_change = current_count - last_count
                yoy_percentage = _format_yoy(current_count, last_count)

                monthly_data_list.append({
                    "month": month,
                    "current_year_count": current_count,
                    "last_year_count": last_count,
                    "yoy_change": yoy_change,
                    "yoy_percentage": yoy_percentage
                })

            # 计算月均
            total_current = sum(m["current_year_count"] for m in monthly_data_list)
            monthly_average = round(total_current / 12, 2)

            return {
                "monthly_average": monthly_average,
                "monthly_data": monthly_data_list
            }
    finally:
        release_connection(conn)


def get_location_distribution(year: int, category: str) -> LocationAnalysis:
    """
    工具 4：获取点位分析（按街镇）

    Args:
        year: 年份
        category: 二级分类

    Returns:
        点位分析数据
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            sql = f"""
                SELECT
                    被反映街乡镇 as town,
                    COUNT(*) as count
                FROM {table}
                WHERE YEAR(创建时间) = %s AND 二级分类 = %s
                GROUP BY 被反映街乡镇
                ORDER BY count DESC
            """
            cur.execute(sql, (year, category))
            locations = cur.fetchall()

            total_count = sum(row["count"] for row in locations)

            location_list: List[LocationItem] = []
            for loc in locations:
                percentage = round((loc["count"] / total_count) * 100, 2) if total_count > 0 else 0.0
                location_list.append({
                    "town": loc["town"] or "未知",
                    "count": loc["count"],
                    "percentage": percentage
                })

            return {"locations": location_list}
    finally:
        release_connection(conn)


def get_result_analysis(year: int, category: str) -> ResultAnalysis:
    """
    工具 5：获取办理结果综合分析

    Args:
        year: 年份
        category: 二级分类

    Returns:
        办理结果综合分析数据
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            # 5.0 总体结果
            sql_overall = f"""
                SELECT
                    COUNT(*) as total_count,
                    SUM(CASE WHEN 是否有效回访 = '是' THEN 1 ELSE 0 END) as valid_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否联系 = '是' THEN 1 ELSE 0 END) as contact_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否解决 = '是' THEN 1 ELSE 0 END) as solved_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '满意' THEN 1 ELSE 0 END) as satisfied_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '基本满意' THEN 1 ELSE 0 END) as basic_satisfied_count
                FROM {table}
                WHERE YEAR(创建时间) = %s AND 二级分类 = %s
            """
            cur.execute(sql_overall, (year, category))
            overall_data = cur.fetchone()

            overall_rates = _calculate_rates(
                overall_data["valid_count"],
                overall_data["contact_count"],
                overall_data["solved_count"],
                overall_data["satisfied_count"],
                overall_data["basic_satisfied_count"]
            )

            overall_result: OverallResult = {
                "total_count": overall_data["total_count"],
                "solve_rate": overall_rates["solve_rate"],
                "satisfaction_rate": overall_rates["satisfaction_rate"]
            }

            # 5.1 按三级分类
            sql_by_sub_category = f"""
                SELECT
                    三级分类,
                    SUM(CASE WHEN 是否有效回访 = '是' THEN 1 ELSE 0 END) as valid_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否联系 = '是' THEN 1 ELSE 0 END) as contact_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否解决 = '是' THEN 1 ELSE 0 END) as solved_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '满意' THEN 1 ELSE 0 END) as satisfied_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '基本满意' THEN 1 ELSE 0 END) as basic_satisfied_count
                FROM {table}
                WHERE YEAR(创建时间) = %s AND 二级分类 = %s
                GROUP BY 三级分类
            """
            cur.execute(sql_by_sub_category, (year, category))
            sub_category_data = cur.fetchall()

            by_sub_category: List[SubCategoryResult] = []
            for row in sub_category_data:
                rates = _calculate_rates(
                    row["valid_count"],
                    row["contact_count"],
                    row["solved_count"],
                    row["satisfied_count"],
                    row["basic_satisfied_count"]
                )
                by_sub_category.append({
                    "name": row["三级分类"] or "未分类",
                    "solve_rate": rates["solve_rate"],
                    "satisfaction_rate": rates["satisfaction_rate"]
                })

            # 5.2 按街镇
            sql_by_location = f"""
                SELECT
                    被反映街乡镇 as town,
                    SUM(CASE WHEN 是否有效回访 = '是' THEN 1 ELSE 0 END) as valid_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否联系 = '是' THEN 1 ELSE 0 END) as contact_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否解决 = '是' THEN 1 ELSE 0 END) as solved_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '满意' THEN 1 ELSE 0 END) as satisfied_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '基本满意' THEN 1 ELSE 0 END) as basic_satisfied_count
                FROM {table}
                WHERE YEAR(创建时间) = %s AND 二级分类 = %s
                GROUP BY 被反映街乡镇
            """
            cur.execute(sql_by_location, (year, category))
            location_data = cur.fetchall()

            by_location: List[LocationResult] = []
            for row in location_data:
                rates = _calculate_rates(
                    row["valid_count"],
                    row["contact_count"],
                    row["solved_count"],
                    row["satisfied_count"],
                    row["basic_satisfied_count"]
                )
                by_location.append({
                    "town": row["town"] or "未知",
                    "solve_rate": rates["solve_rate"],
                    "satisfaction_rate": rates["satisfaction_rate"]
                })

            return {
                "overall": overall_result,
                "by_sub_category": by_sub_category,
                "by_location": by_location
            }
    finally:
        release_connection(conn)

