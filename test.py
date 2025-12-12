from datetime import date
from utils.dates import parse_date, format_date, get_yesterday
from services.daily_report_service import _query_raw_period_data,get_street_assessment_data,get_unit_assessment_data,get_full_daily_report_data,get_assessment_data_for_date
from services.heating_report_service import get_full_heating_report_data,_query_overall_stats,get_off_season_stats
from services.emergency_report_service import get_emergency_month_daily_rates,get_emergency_appeals_for_date,get_emergency_category_stats
if __name__ == "__main__":

    s_data = get_emergency_month_daily_rates("2025-10-15")
    print("2024年非 gongneng season 统计结果为：",s_data)

