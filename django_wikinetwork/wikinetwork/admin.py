from django_wikinetwork.wikinetwork.models import WikiRunData, \
     WikiRunGroupData, WikiStat, WikiLang, BigWikiStat, CeleryRun, \
     WikiEvent, WikiWord
from django.contrib import admin
from django.forms import Textarea
from datetime import date, timedelta
from django.utils.safestring import mark_safe

class DictTimeField(Textarea):
    def render(self, name, value, attrs=None):
        if attrs is None: attrs = {}
        attrs['readonly'] = 'readonly'
        if isinstance(value, dict):
            out = []
            for k, v in sorted(value.iteritems()):
                da = date(2000, 1, 1) + timedelta(k)
                sk = '%s-%.2d-%.2d' % (da.year, da.month, da.day)
                out.append("%s:\t%3d" % (sk, v))
            value = '</tr></td><tr><td>'.join(out)

        return mark_safe(u"<table><tr><td>%s</tr></td></table>" % (value,))

class DictField(Textarea):
    def render(self, name, value, attrs=None):
        if attrs is None: attrs = {}
        attrs['readonly'] = 'readonly'
        if isinstance(value, dict):
            out = []
            for k, v in sorted(value.iteritems()):
            #    #da = date(2000, 1, 1) + timedelta(k)
            #    #sk = '%s-%.2d-%.2d' % (da.year, da.month, da.day)
                out.append("%s:\t%f" % (k, v))
            value = '</tr></td><tr><td>'.join(out)

        return mark_safe(u"<table><tr><td>%s</tr></td></table>" % (value,))

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
    fields          = ('title', 'lang', 'data', 'talk', 'desired')
    list_display    = ('title', 'lang', 'talk')
    list_filter     = ('lang',)
    search_fields   = ('title',)
    readonly_fields = ('lang', 'title', 'desired')

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ('data'):
            kwargs['widget'] = DictTimeField

        return super(WikiEventAdmin, self
                     ).formfield_for_dbfield(db_field, **kwargs)

class WikiWordAdmin(admin.ModelAdmin):
    fields          = ('lang', 'title', 'data', 'data_first', 'talk', 'desired')
    list_display    = ('title', 'lang', 'talk')
    list_filter     = ('lang',)
    search_fields   = ('title',)
    readonly_fields = ('lang', 'title', 'desired')

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ('data_first', 'data'):
            kwargs['widget'] = DictField

        return super(WikiWordAdmin, self
                     ).formfield_for_dbfield(db_field, **kwargs)

admin.site.register(WikiRunData, WikiRunDataAdmin)
admin.site.register(WikiRunGroupData, WikiRunGroupDataAdmin)
admin.site.register(WikiStat, WikiStatAdmin)
admin.site.register(WikiLang)
admin.site.register(BigWikiStat)
admin.site.register(CeleryRun)
admin.site.register(WikiEvent, WikiEventAdmin)
admin.site.register(WikiWord, WikiWordAdmin)
