from services.daily_report_service import get_assessment_data_for_date
if __name__ == "__main__":

    assess_data = get_assessment_data_for_date("2025-06-08")
    print("考核期数据：", assess_data)