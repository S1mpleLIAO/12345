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
import json

if __name__ == "__main__":
    year = 2025
    category = "违法建设"  # 请根据实际数据库中的二级分类修改
    result1 = get_annual_overview(year, category)
    print("Annual Overview:", json.dumps(result1, ensure_ascii=False, indent=2))
