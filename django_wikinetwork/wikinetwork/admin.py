from django_wikinetwork.wikinetwork.models import WikiRunData, \
     WikiRunGroupData, WikiStat, WikiLang, BigWikiStat, CeleryRun, \
     WikiEvent
from django.contrib import admin
from django.forms import Textarea
from datetime import date, timedelta

class DictTimeField(Textarea):
    def render(self, name, value, attrs=None):
        if attrs is None: attrs = {}
        attrs['readonly'] = 'readonly'
        if isinstance(value, dict):
            d = {}
            for k, v in value.iteritems():
                da = date(2000, 1, 1) + timedelta(k)
                d['%s-%s-%s' % (da.year, da.month, da.day)] = v
            value = d

        return super(DictTimeField, self).render(name, value, attrs)

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
    fields          = ('lang', 'title', 'normal', 'talk', 'desired')
    list_display    = ('lang', 'title')
    list_filter     = ('lang',)
    search_fields   = ('title',)
    readonly_fields = ('lang', 'title', 'desired')

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ('talk', 'normal'):
            kwargs['widget'] = DictTimeField

        return super(WikiEventAdmin, self
                     ).formfield_for_dbfield(db_field, **kwargs)

admin.site.register(WikiRunData, WikiRunDataAdmin)
admin.site.register(WikiRunGroupData, WikiRunGroupDataAdmin)
admin.site.register(WikiStat, WikiStatAdmin)
admin.site.register(WikiLang)
admin.site.register(BigWikiStat)
admin.site.register(CeleryRun)
admin.site.register(WikiEvent, WikiEventAdmin)
