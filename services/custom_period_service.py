"""
自定义时间段分析服务层
提供自定义时间段数据查询和计算功能
"""
from __future__ import annotations
from typing import List, Dict
from db.connection import get_connection, release_connection
from db.table import get_table_name
from models.custom_period_types import (
    PeriodOverview,
    SubCategoryItem,
    PeriodCategoryAnalysis,
    CommunityItem,
    UnitItem,
    UnitAnalysis,
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
        包含解决率、满意率的字典
    """
    # 将 Decimal 类型转换为 int，避免与 float 运算时出错
    valid_count = int(valid_count or 0)
    contact_count = int(contact_count or 0)
    solved_count = int(solved_count or 0)
    satisfied_count = int(satisfied_count or 0)
    basic_satisfied_count = int(basic_satisfied_count or 0)

    if valid_count == 0:
        return {
            "solve_rate": 0.0,
            "satisfaction_rate": 0.0
        }

    solve_rate = (solved_count / valid_count) * 100
    satisfaction_rate = ((satisfied_count + basic_satisfied_count * 0.9) / valid_count) * 100

    return {
        "solve_rate": round(solve_rate, 2),
        "satisfaction_rate": round(satisfaction_rate, 2)
    }


def get_period_overview(start_date: str, end_date: str, category: str) -> PeriodOverview:
    """
    工具 1：获取时间段总体基本情况

    Args:
        start_date: 开始时间，格式 YYYY-MM-DD HH:MM:SS
        end_date: 结束时间，格式 YYYY-MM-DD HH:MM:SS
        category: 二级分类

    Returns:
        时间段总体基本情况数据
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            sql = f"""
                SELECT
                    COUNT(*) as total_count,
                    SUM(CASE WHEN 是否有效回访 = '是' THEN 1 ELSE 0 END) as valid_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否联系 = '是' THEN 1 ELSE 0 END) as contact_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否解决 = '是' THEN 1 ELSE 0 END) as solved_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '满意' THEN 1 ELSE 0 END) as satisfied_count,
                    SUM(CASE WHEN 是否有效回访 = '是' AND 是否满意 = '基本满意' THEN 1 ELSE 0 END) as basic_satisfied_count
                FROM {table}
                WHERE 创建时间 >= %s AND 创建时间 <= %s AND 二级分类 = %s
            """
            cur.execute(sql, (start_date, end_date, category))
            data = cur.fetchone()

            rates = _calculate_rates(
                data["valid_count"],
                data["contact_count"],
                data["solved_count"],
                data["satisfied_count"],
                data["basic_satisfied_count"]
            )

            return {
                "total_count": int(data["total_count"] or 0),
                "solve_rate": rates["solve_rate"],
                "satisfaction_rate": rates["satisfaction_rate"]
            }
    finally:
        release_connection(conn)


def get_period_category_analysis(start_date: str, end_date: str, category: str) -> PeriodCategoryAnalysis:
    """
    工具 2：获取诉求分类分析

    Args:
        start_date: 开始时间，格式 YYYY-MM-DD HH:MM:SS
        end_date: 结束时间，格式 YYYY-MM-DD HH:MM:SS
        category: 二级分类

    Returns:
        诉求分类分析数据（三级分类统计）
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            sql = f"""
                SELECT
                    三级分类,
                    COUNT(*) as count
                FROM {table}
                WHERE 创建时间 >= %s AND 创建时间 <= %s AND 二级分类 = %s
                GROUP BY 三级分类
                ORDER BY count DESC
            """
            cur.execute(sql, (start_date, end_date, category))
            sub_categories = cur.fetchall()

            total_count = sum(int(row["count"]) for row in sub_categories)

            result: List[SubCategoryItem] = []
            for row in sub_categories:
                count = int(row["count"])
                percentage = round((count / total_count) * 100, 2) if total_count > 0 else 0.0
                result.append({
                    "name": row["三级分类"] or "未分类",
                    "count": count,
                    "percentage": percentage
                })

            return {"sub_categories": result}
    finally:
        release_connection(conn)


def get_unit_analysis(start_date: str, end_date: str, category: str) -> UnitAnalysis:
    """
    工具 3：获取承办单位分析

    Args:
        start_date: 开始时间，格式 YYYY-MM-DD HH:MM:SS
        end_date: 结束时间，格式 YYYY-MM-DD HH:MM:SS
        category: 二级分类

    Returns:
        承办单位分析数据（按二级承办单位简称统计，含所在村社区 TOP3）
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            table = get_table_name()

            # 查询各承办单位的件数
            sql_units = f"""
                SELECT
                    二级承办单位简称 as unit_name,
                    COUNT(*) as count
                FROM {table}
                WHERE 创建时间 >= %s AND 创建时间 <= %s AND 二级分类 = %s
                GROUP BY 二级承办单位简称
                ORDER BY count DESC
            """
            cur.execute(sql_units, (start_date, end_date, category))
            units = cur.fetchall()

            total_count = sum(int(row["count"]) for row in units)

            result: List[UnitItem] = []
            for unit in units:
                unit_name = unit["unit_name"] or "未知"
                unit_count = int(unit["count"])
                percentage = round((unit_count / total_count) * 100, 2) if total_count > 0 else 0.0

                # 查询该承办单位的所在村社区统计
                sql_communities = f"""
                    SELECT
                        所在村社区 as community,
                        COUNT(*) as count
                    FROM {table}
                    WHERE 创建时间 >= %s AND 创建时间 <= %s
                        AND 二级分类 = %s
                        AND 二级承办单位简称 = %s
                    GROUP BY 所在村社区
                    ORDER BY count DESC
                """
                cur.execute(sql_communities, (start_date, end_date, category, unit["unit_name"]))
                communities = cur.fetchall()

                # 获取 TOP3（并列也算）
                top_communities: List[CommunityItem] = []
                if communities:
                    # 获取前3个不同的件数值
                    unique_counts = sorted(set(int(c["count"]) for c in communities), reverse=True)[:3]
                    min_count_for_top3 = unique_counts[-1] if unique_counts else 0

                    for comm in communities:
                        comm_count = int(comm["count"])
                        if comm_count >= min_count_for_top3:
                            top_communities.append({
                                "name": comm["community"] or "未知",
                                "count": comm_count
                            })

                result.append({
                    "name": unit_name,
                    "count": unit_count,
                    "percentage": percentage,
                    "top_communities": top_communities
                })

            return {"units": result}
    finally:
        release_connection(conn)
