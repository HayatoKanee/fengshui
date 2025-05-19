from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.http import HttpResponse
from django.test.client import RequestFactory
from django.contrib.staticfiles.storage import StaticFilesStorage

from lunar_python import Solar, Lunar, EightChar
from .forms import BirthTimeForm
from .helper import (
    extract_form_data, get_relations, get_wang_xiang, calculate_values,
    get_hidden_gans, calculate_wang_xiang_values, calculate_values_for_bazi,
    calculate_gan_liang_value, accumulate_wuxing_values, calculate_shenghao,
    calculate_shenghao_percentage
)
from .views import home_view, bazi_view, get_bazi_detail, zeri_view
from .constants import gan_wuxing, gan_yinyang
import datetime


class BirthTimeFormTests(TestCase):
    def test_form_valid_data(self):
        form_data = {
            'year': 2000,
            'month': 1,
            'day': 1,
            'hour': 12,
            'minute': 0,
        }
        form = BirthTimeForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_data(self):
        # Test with invalid month
        form_data = {
            'year': 2000,
            'month': 13,  # Invalid month
            'day': 1,
            'hour': 12,
            'minute': 0,
        }
        form = BirthTimeForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Test with invalid day
        form_data = {
            'year': 2000,
            'month': 1,
            'day': 32,  # Invalid day
            'hour': 12,
            'minute': 0,
        }
        form = BirthTimeForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Test with invalid hour
        form_data = {
            'year': 2000,
            'month': 1,
            'day': 1,
            'hour': 24,  # Invalid hour
            'minute': 0,
        }
        form = BirthTimeForm(data=form_data)
        self.assertFalse(form.is_valid())


# Create a simple static files storage for testing
class TestStaticFilesStorage(StaticFilesStorage):
    def url(self, name):
        return f'/static/{name}'


@override_settings(STATICFILES_STORAGE='bazi.tests.TestStaticFilesStorage')
class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
    
    def test_home_view_direct(self):
        request = self.factory.get('/')
        response = home_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_bazi_view_get_direct(self):
        request = self.factory.get('/bazi')
        response = bazi_view(request)
        self.assertEqual(response.status_code, 200)
        
    def test_bazi_view_post_direct(self):
        form_data = {
            'year': 2000,
            'month': 1,
            'day': 1,
            'hour': 12,
            'minute': 0,
            'gender': 'male',
            'liunian': '2023',
        }
        request = self.factory.post('/bazi', form_data)
        response = bazi_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_get_bazi_detail_direct(self):
        form_data = {
            'year': 2000,
            'month': 1,
            'day': 1,
            'hour': 12,
        }
        request = self.factory.post('/bazi_detail', form_data)
        response = get_bazi_detail(request)
        self.assertEqual(response.status_code, 200)
    
    def test_zeri_view_get_direct(self):
        request = self.factory.get('/zeri')
        response = zeri_view(request)
        self.assertEqual(response.status_code, 200)


class HelperFunctionTests(TestCase):
    def setUp(self):
        # Create a sample bazi for testing helper functions
        self.solar = Solar.fromYmdHms(2000, 1, 1, 12, 0, 0)
        self.lunar = self.solar.getLunar()
        self.bazi = self.lunar.getEightChar()
        
    def test_extract_form_data(self):
        form_data = {
            'year': 2000,
            'month': 1,
            'day': 1,
            'hour': 12,
            'minute': 0,
        }
        form = BirthTimeForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        extracted_data = extract_form_data(form)
        self.assertEqual(extracted_data['year'], 2000)
        self.assertEqual(extracted_data['month'], 1)
        self.assertEqual(extracted_data['day'], 1)
        self.assertEqual(extracted_data['hour'], 12)
        self.assertEqual(extracted_data['minute'], 0)
    
    def test_calculate_values(self):
        values = calculate_values(self.bazi)
        self.assertEqual(len(values), 4)  # Year, Month, Day, Hour
        for value_pair in values:
            self.assertEqual(len(value_pair), 2)  # Each pair has gan and zhi values
            
    def test_get_hidden_gans(self):
        hidden_gans = get_hidden_gans(self.bazi)
        self.assertEqual(len(hidden_gans), 4)  # Year, Month, Day, Hour
        for gan_dict in hidden_gans:
            self.assertIsInstance(gan_dict, dict)
            
    def test_get_wang_xiang(self):
        month_zhi = self.bazi.getMonthZhi()
        wang_xiang = get_wang_xiang(month_zhi, self.lunar)
        self.assertIsInstance(wang_xiang, dict)
        self.assertEqual(len(wang_xiang), 5)  # Five elements
        
    def test_calculate_wang_xiang_values(self):
        month_zhi = self.bazi.getMonthZhi()
        wang_xiang = get_wang_xiang(month_zhi, self.lunar)
        wang_xiang_values = calculate_wang_xiang_values(self.bazi, wang_xiang)
        self.assertEqual(len(wang_xiang_values), 4)  # Year, Month, Day, Hour
        
    def test_calculate_values_for_bazi(self):
        wuxing = calculate_values_for_bazi(self.bazi, gan_wuxing)
        self.assertEqual(len(wuxing), 4)  # Year, Month, Day, Hour
        
        yinyang = calculate_values_for_bazi(self.bazi, gan_yinyang)
        self.assertEqual(len(yinyang), 4)  # Year, Month, Day, Hour
        
    def test_calculate_gan_liang_value(self):
        values = calculate_values(self.bazi)
        hidden_gans = get_hidden_gans(self.bazi)
        month_zhi = self.bazi.getMonthZhi()
        wang_xiang = get_wang_xiang(month_zhi, self.lunar)
        wang_xiang_values = calculate_wang_xiang_values(self.bazi, wang_xiang)
        
        gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
        self.assertEqual(len(gan_liang_values), 4)  # Year, Month, Day, Hour
        
    def test_accumulate_wuxing_values(self):
        wuxing = calculate_values_for_bazi(self.bazi, gan_wuxing)
        values = calculate_values(self.bazi)
        hidden_gans = get_hidden_gans(self.bazi)
        month_zhi = self.bazi.getMonthZhi()
        wang_xiang = get_wang_xiang(month_zhi, self.lunar)
        wang_xiang_values = calculate_wang_xiang_values(self.bazi, wang_xiang)
        gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
        
        wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
        self.assertEqual(len(wuxing_value), 5)  # Five elements
        
    def test_calculate_shenghao(self):
        wuxing = calculate_values_for_bazi(self.bazi, gan_wuxing)
        values = calculate_values(self.bazi)
        hidden_gans = get_hidden_gans(self.bazi)
        month_zhi = self.bazi.getMonthZhi()
        wang_xiang = get_wang_xiang(month_zhi, self.lunar)
        wang_xiang_values = calculate_wang_xiang_values(self.bazi, wang_xiang)
        gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
        wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
        
        main_wuxing = self.bazi.getDayWuXing()[0]
        sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
        self.assertEqual(len(sheng_hao), 2)
        
    def test_calculate_shenghao_percentage(self):
        sheng_hao = (60, 40)  # Example values
        sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
        self.assertEqual(len(sheng_hao_percentage), 2)
        self.assertEqual(sheng_hao_percentage[0], 60.0)
        self.assertEqual(sheng_hao_percentage[1], 40.0)
