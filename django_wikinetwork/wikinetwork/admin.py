from django_wikinetwork.wikinetwork.models import WikiRunData, \
     WikiRunGroupData, WikiStat, WikiLang, BigWikiStat, CeleryRun, \
     WikiEvent
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

class WikiEventAdmin(admin.ModelAdmin):
    list_display    = ('lang', 'title') #, 'created')
    list_filter     = ('lang',)
    search_fields   = ('title',)
    #date_hierarchy  = 'created'

admin.site.register(WikiRunData, WikiRunDataAdmin)
admin.site.register(WikiRunGroupData, WikiRunGroupDataAdmin)
admin.site.register(WikiStat, WikiStatAdmin)
admin.site.register(WikiLang)
admin.site.register(BigWikiStat)
admin.site.register(CeleryRun)
admin.site.register(WikiEvent, WikiEventAdmin)
