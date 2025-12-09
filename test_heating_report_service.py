import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from services.heating_report_service import get_full_heating_report_data


class TestHeatingReportService(unittest.TestCase):

    @patch('services.heating_report_service.get_connection')
    @patch('services.heating_report_service.release_connection')
    @patch('services.heating_report_service.get_table_name')
    def test_get_full_heating_report_data_with_zero_total(
            self, 
            mock_get_table_name, 
            mock_release_connection, 
            mock_get_connection):
        """
        测试当供暖季内无相关诉求数据时的情况
        """
        # 设置mock
        mock_get_table_name.return_value = "`2024gongnuan`"
        
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # 模拟查询结果：总请求数为0
        mock_cursor.fetchone.return_value = {"total_count": 0, "valid_count": 0, 
                                             "contact_count": 0, "solved_count": 0,
                                             "satisfied_count": 0, "basic_satisfied_count": 0}
        
        # 执行函数
        result = get_full_heating_report_data(2024)
        result = result["stats"]
        result = result["central_heating"]
        result = result["central_heating"]
        result = result["categories"]

        
        # 验证结果
        self.assertEqual(result["stats"]["total"], 0)
        self.assertEqual(result["stats"]["total"], 0)
        self.assertEqual(result["monthly"], [])
        self.assertEqual(result["central_heating"]["total"], 0)
        self.assertEqual(result["categories"], [])
        self.assertEqual(result["companies"], [])
        
        # 验证调用
        mock_get_table_name.assert_called_once()
        mock_get_connection.assert_called_once()
        mock_release_connection.assert_called_once_with(mock_conn)

    @patch('services.heating_report_service.get_connection')
    @patch('services.heating_report_service.release_connection')
    @patch('services.heating_report_service.get_table_name')
    def test_get_full_heating_report_data_with_data(
            self, 
            mock_get_table_name, 
            mock_release_connection, 
            mock_get_connection):
        """
        测试有数据时的正常情况
        """
        # 设置mock
        mock_get_table_name.return_value = "`2024gongnuan`"
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # 模拟今年总体统计结果和去年总体统计结果
        mock_cursor.fetchone.side_effect = [
            {"total_count": 1000, "valid_count": 900, 
             "contact_count": 850, "solved_count": 800,
             "satisfied_count": 750, "basic_satisfied_count": 50},  # 今年总体统计
            {"total_count": 950, "valid_count": 850, 
             "contact_count": 800, "solved_count": 750,
             "satisfied_count": 700, "basic_satisfied_count": 50},  # 去年总体统计
            {"total_count": 600, "valid_count": 550, "solved_count": 500,  # 今年集中供暖统计
             "satisfied_count": 480, "basic_satisfied_count": 20},
            {"total_count": 580, "valid_count": 530, "solved_count": 490,  # 去年集中供暖统计
             "satisfied_count": 460, "basic_satisfied_count": 20}
        ]
        
        # 模拟月度统计数据
        mock_cursor.fetchall.side_effect = [
            [  # 今年月度数据
                {"month_label": "2024-11", "total_count": 300, "valid_count": 280,
                 "solved_count": 250, "satisfied_count": 240, "basic_satisfied_count": 10},
                {"month_label": "2024-12", "total_count": 400, "valid_count": 370,
                 "solved_count": 350, "satisfied_count": 330, "basic_satisfied_count": 20}
            ],
            [  # 去年月度数据
                {"month_label": "2023-11", "total_count": 280, "valid_count": 260,
                 "solved_count": 240, "satisfied_count": 230, "basic_satisfied_count": 10},
                {"month_label": "2023-12", "total_count": 350, "valid_count": 330,
                 "solved_count": 310, "satisfied_count": 300, "basic_satisfied_count": 15}
            ],
            [  # 分类数据
                {"category_name": "供暖不足", "cnt": 200},
                {"category_name": "管道问题", "cnt": 150}
            ],
            [  # 公司数据
                {"company_name": "第一热力公司", "cnt": 300},
                {"company_name": "第二热力公司", "cnt": 200}
            ]
        ]
        
        # 执行函数
        result = get_full_heating_report_data(2024)
        
        # 验证总体统计结果
        self.assertEqual(result["stats"]["total"], 1000)
        self.assertEqual(result["stats"]["last_total"], 950)
        self.assertEqual(result["stats"]["yoy_diff"], 50)
        
        # 验证月度统计数据
        self.assertEqual(len(result["monthly"]), 2)
        self.assertEqual(result["monthly"][0]["month"], "2024-11")
        self.assertEqual(result["monthly"][0]["total"], 300)
        self.assertEqual(result["monthly"][0]["last_total"], 280)
        
        # 验证集中供暖统计
        self.assertEqual(result["central_heating"]["total"], 600)
        self.assertEqual(result["central_heating"]["last_total"], 580)
        self.assertEqual(result["central_heating"]["yoy_diff"], 20)
        
        # 验证分类统计
        self.assertEqual(len(result["categories"]), 2)
        self.assertEqual(result["categories"][0]["category_name"], "供暖不足")
        self.assertEqual(result["categories"][0]["count"], 200)
        
        # 验证公司统计
        self.assertEqual(len(result["companies"]), 2)
        self.assertEqual(result["companies"][0]["company_name"], "第一热力公司")
        self.assertEqual(result["companies"][0]["count"], 300)
        
        # 验证调用
        mock_get_table_name.assert_called_once()
        mock_get_connection.assert_called_once()
        mock_release_connection.assert_called_once_with(mock_conn)

if __name__ == '__main__':
    unittest.main()