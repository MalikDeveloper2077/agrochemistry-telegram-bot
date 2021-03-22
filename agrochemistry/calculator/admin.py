from django.contrib import admin

from .models import Brand, Product, ProductTarget, Phase, TelegramUser


class PhaseAdminInline(admin.TabularInline):
    model = Phase
    extra = 1
    fields = ('name', 'weeks', 'formula')


class BrandAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class ProductAdmin(admin.ModelAdmin):
    inlines = (PhaseAdminInline,)
    search_fields = ('name', 'environment')
    list_filter = ('environment', 'target__tag', 'brand__name')


class ProductTargetAdmin(admin.ModelAdmin):
    search_fields = ('tag',)


admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductTarget, ProductTargetAdmin)
admin.site.register(Phase)
admin.site.register(TelegramUser)
