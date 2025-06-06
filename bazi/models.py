from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Model to store user's saved birth information"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=100, verbose_name="姓名")
    birth_year = models.IntegerField(verbose_name="出生年")
    birth_month = models.IntegerField(verbose_name="出生月")
    birth_day = models.IntegerField(verbose_name="出生日")
    birth_hour = models.IntegerField(verbose_name="出生时")
    birth_minute = models.IntegerField(verbose_name="出生分")
    is_male = models.BooleanField(default=True, verbose_name="性别")
    is_default = models.BooleanField(default=False, verbose_name="默认资料")
    
    # Calculated fields for optimization
    is_day_master_strong = models.BooleanField(null=True, blank=True, verbose_name="日主强")
    day_master_wuxing = models.CharField(max_length=10, null=True, blank=True, verbose_name="日主五行")
    favorable_wuxing = models.CharField(max_length=50, null=True, blank=True, verbose_name="有利五行")
    unfavorable_wuxing = models.CharField(max_length=50, null=True, blank=True, verbose_name="不利五行")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "用户八字资料"
        verbose_name_plural = "用户八字资料"
        ordering = ['-created_at']
    
    def __str__(self):
        gender = "男" if self.is_male else "女"
        return f"{self.name} - {self.birth_year}年{self.birth_month}月{self.birth_day}日 {self.birth_hour}时{self.birth_minute}分 ({gender})"
