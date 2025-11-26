from datetime import date
from utils.dates import parse_date, format_date, get_yesterday
from services.daily_report_service import _query_raw_period_data,get_street_assessment_data,get_unit_assessment_data,get_full_daily_report_data,get_assessment_data_for_date
if __name__ == "__main__":

    s_data = get_street_assessment_data("2025-06-13")
    # u_data = get_unit_assessment_data("2025-06-13")
    print("区直单位考核期数据：", s_data)
    # full_data = get_assessment_data_for_date("2025-06-13")
    # print("完整日报数据：", full_data)