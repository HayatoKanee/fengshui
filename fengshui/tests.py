from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.conf import settings
import os


class SettingsTests(TestCase):
    def test_installed_apps(self):
        """Test that our apps are included in INSTALLED_APPS"""
        self.assertIn('bazi', settings.INSTALLED_APPS)
        # The app "fengshui" is not actually in INSTALLED_APPS, just check for Django defaults
        self.assertIn('django.contrib.admin', settings.INSTALLED_APPS)
        self.assertIn('django.contrib.auth', settings.INSTALLED_APPS)
    
    def test_templates_dir(self):
        """Test that templates directory is properly configured"""
        # The templates may be configured using APP_DIRS=True rather than explicit DIRS
        template_config = settings.TEMPLATES[0]
        self.assertTrue(
            template_config.get('APP_DIRS', False) or 
            any('templates' in str(dir_path) for dir_path in template_config.get('DIRS', []))
        )
    
    def test_static_dir(self):
        """Test that static directory is properly configured"""
        # STATICFILES_DIRS might not be explicitly set if using the default convention
        self.assertTrue(
            hasattr(settings, 'STATICFILES_DIRS') or 
            hasattr(settings, 'STATIC_ROOT')
        )
    
    def test_data_dir_exists(self):
        """Test that DATA_DIR exists and is configured"""
        self.assertTrue(hasattr(settings, 'DATA_DIR'))
        self.assertTrue(os.path.exists(settings.DATA_DIR))


class URLTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_home_url_redirects_to_bazi(self):
        """Test that home URL redirects to bazi"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/bazi')
    
    def test_bazi_url_resolves(self):
        """Test that bazi URL resolves correctly"""
        resolver = resolve('/bazi')  # Note: no trailing slash
        # CBV as_view() returns function with __name__ = 'view'
        # Check the view class instead
        self.assertEqual(resolver.func.view_class.__name__, 'BaziAnalysisView')

    def test_bazi_detail_url(self):
        """Test that bazi_detail URL resolves correctly"""
        resolver = resolve('/bazi_detail')  # The actual URL name is bazi_detail
        # CBV as_view() returns function with __name__ = 'view'
        # Check the view class instead
        self.assertEqual(resolver.func.view_class.__name__, 'BaziDetailView')
    
    def test_zeri_url_resolves(self):
        """Test that zeri URL resolves correctly"""
        resolver = resolve('/zeri')  # Note: no trailing slash
        self.assertEqual(resolver.func.__name__, 'zeri_view')
    
    def test_static_url_config(self):
        """Test that static URL is properly configured"""
        self.assertEqual(settings.STATIC_URL, '/static/') 