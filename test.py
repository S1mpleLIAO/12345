from services.daily_report_service import get_full_daily_report_data
if __name__ == "__main__":
    # 测试调用
    data = get_full_daily_report_data("2025-05-19")
    import pprint

    pprint.pprint(data)