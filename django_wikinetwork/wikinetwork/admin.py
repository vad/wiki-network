from django_wikinetwork.wikinetwork.models import WikiRunData, WikiRunGroupData, WikiStat
from django.contrib import admin

class WikiRunDataAdmin(admin.ModelAdmin):
    list_display    = ('lang', 'date', 'created')
    list_filter     = ('lang', 'date', 'created')
    date_hierarchy  = 'created'

class WikiRunGroupDataAdmin(admin.ModelAdmin):
    list_display    = ('lang', 'group', 'date', 'created')
    list_filter     = ('lang', 'group', 'date', 'created')
    date_hierarchy  = 'created'    

class WikiStatAdmin(admin.ModelAdmin):
    list_display    = ('lang', 'created')
    list_filter     = ('lang',)
    date_hierarchy  = 'created'

admin.site.register(WikiRunData, WikiRunDataAdmin)
admin.site.register(WikiRunGroupData, WikiRunGroupDataAdmin)
admin.site.register(WikiStat, WikiStatAdmin)
