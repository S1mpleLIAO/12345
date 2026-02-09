from datetime import date
from utils.dates import parse_date, format_date, get_yesterday
from services.daily_report_service import get_lagging_street_rank_trends,_query_raw_period_data,get_street_assessment_data,get_unit_assessment_data,get_full_daily_report_data,get_assessment_data_for_date
from services.heating_report_service import get_full_heating_report_data,_query_overall_stats,get_off_season_stats
from services.emergency_report_service import get_emergency_month_daily_rates,get_emergency_appeals_for_date,get_emergency_category_stats
from services.annual_analysis_service import (
    get_annual_overview,
    get_category_analysis,
    get_time_distribution,
    get_location_distribution,
    get_result_analysis
)
from services.custom_period_service import (
    get_period_overview,
    get_period_category_analysis,
    get_unit_analysis
)
import json

if __name__ == "__main__":
    start_date = "2025-01-01 00:00:00"
    end_date = "2025-06-30 23:59:59"
    category = "违法建设"
    print("\n" + "-" * 80)
    print("工具 1：总体基本情况")
    print("-" * 80)
    result1 = get_period_overview(start_date, end_date, category)
    print(json.dumps(result1, ensure_ascii=False, indent=2))

    print("\n" + "-" * 80)
    print("工具 2：诉求分类分析")
    print("-" * 80)
    result2 = get_period_category_analysis(start_date, end_date, category)
    print(f"三级分类数量: {len(result2['sub_categories'])}")
    for sub in result2['sub_categories'][:5]:
        print(f"  - {sub['name']}: {sub['count']}件 ({sub['percentage']}%)")

    print("\n" + "-" * 80)
    print("工具 3：承办单位分析")
    print("-" * 80)
    result3 = get_unit_analysis(start_date, end_date, category)
    print(f"承办单位数量: {len(result3['units'])}")
    for unit in result3['units'][:5]:
        print(f"\n  - {unit['name']}: {unit['count']}件 ({unit['percentage']}%)")
        print(f"    所在村社区 TOP3:")
        for comm in unit['top_communities'][:5]:
            print(f"      - {comm['name']}: {comm['count']}件")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
