
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django_wikinetwork.wikinetwork.models import WikiRunData, WikiRunGroupData
from django.db.models import Max

#for wing debugging
#import wingdbstub


it_wikis = sorted(("scn", "nap", "fur", "eml", "lmo", "co", "pms", "vec", "it"))

## HELPERS
def get_big(qs, limit=10000):
    return sorted(set(r.lang for r in qs.filter(nodes_number__gt=limit)))


def get_header(qs):
    r"""
    qs: QuerySet
    @returns: a list with the headers
    """
    
    r = qs[0]
    header = [f.name for f in r._meta.fields]
    header.remove('id')
    header.remove('created')
    header.remove('modified')
    
    return header


def format_percentage(number, ref):
    import types
    
    if type(number) in (types.IntType, ):
        return '%d (%.1f%%)' % (number, 100.*number/ref)
    else:
        return '%.6f (%.1f%%)' % (number, 100.*number/ref)



## VIEWS

def index(request):
    return render_to_response('index.html')



def all(request, cls=None):
    all_run = WikiRunData.objects.all()
    
    header = get_header(all_run)
    
    if cls == "it":
        lang_list = it_wikis
        title = "Italian wikis"
    elif cls == "big":
        lang_list = get_big(all_run)
        title = "Big wikis"
    else:
        lang_list = sorted(set(r.lang for r in all_run))
        title = "All wikis"

    data = []
    for lang in lang_list:
        lang_all_run = all_run.filter(lang=lang)
        
        if not lang_all_run:
            continue
        
        #assert False, lang_all_run.annotate(max_date=Max('date')).values_list('max_date')
        newer_date = str(int(lang_all_run.annotate(max_date=Max('date')).values_list('max_date')[0][0]))
        
        # all wikipedia run on this lang and on the most recent date
        newer_run = lang_all_run.filter(date=newer_date).order_by('modified').values()

        #join all values in a single model instance
        complete_run = {}
        for run in newer_run:
            for h in header:
                
                if run[h]:
                    complete_run[h] = run[h]
        
        #TODO:
                            
        complete_run['nodes_with_out_edges_number'] = format_percentage(
            complete_run['nodes_with_out_edges_number'], complete_run['nodes_number']
        )
        complete_run['nodes_with_in_edges_number'] = format_percentage(
            complete_run['nodes_with_in_edges_number'], complete_run['nodes_number']
        )
        
        data.append([complete_run.get(h, 'NA') for h in header])
                    
    #filter(private=False).order_by('-created')[:5]
    return render_to_response('all.html', {
        'data': data,
        'header': header,
        'title': title,
    })



def group(request, cls=None):
    # define
    ref_group = "all"
    values_to_be_referred = ("nodes_number", "mean_IN_degree_no_weights",
        "mean_OUT_degree_no_weights", "density", "reciprocity", "average_betweenness",
        "average_pagerank", "average_IN_degree_centrality_weighted",
        "average_OUT_degree_centrality_weighted")
    
    # query
    all_run = WikiRunGroupData.objects.all()
    
    # which headers?
    header = get_header(all_run)
    header.remove('wikirun')
     
    # for which languages? groups
    if cls == "it":
        lang_list = it_wikis
        title = "Italian wikis"
    elif cls == "big":
        lang_list = get_big(all_run)
        title = "Big wikis"
    else:
        lang_list = sorted(set(r.lang for r in all_run))
        title = "All wikis"
    
    # for which languages? single languages
    get_lang = request.GET.get('lang', "")
    if get_lang:
        lang_list = (get_lang,)

    # for which groups?
    get_group = request.GET.get('group', "")
    if get_group:
        get_group_list = get_group.split(',')
        group_list = sorted(set(get_group_list + [ref_group,]))
    else:
        group_list = sorted(set([e[0] for e in all_run.values_list('group')]))
        
    group_list.remove(ref_group)
    group_list.insert(0, ref_group)
        
    data = []
    for lang in lang_list:
        lang_all_run = all_run.filter(lang=lang)
        
        if not lang_all_run:
            continue
        
        for group in group_list:
            group_lang_all_run = lang_all_run.filter(group=group)
        
            if not group_lang_all_run:
                continue
            
            newer_date = str(int(group_lang_all_run.annotate(max_date=Max('date')).values_list('max_date')[0][0]))
        
            # all wikipedia run on this lang and for this group and on the most recent date
            newer_run = group_lang_all_run.filter(date=newer_date).order_by('modified').values()

            #merge all the runs with the same (date, lang, group) in a single model instance
            complete_run = {}
            for run in newer_run:
                for h in header:
                    if run[h]:
                        complete_run[h] = run[h]
                    
            # create percentage referred to the ref_group
            #print lang, group
            if group == ref_group:
                ref_group_values = complete_run
                
            else:
                for h in values_to_be_referred:
                    try:
                        complete_run[h] = format_percentage(complete_run[h], ref_group_values[h])
                    except KeyError:
                        pass
                    
            data.append([complete_run.get(h, 'NA') for h in header])

        
    #filter(private=False).order_by('-created')[:5]
    return render_to_response('all.html', {
        'data': data,
        'header': header,
        'title': title,
    })


def celery(request):
    if 'lang' in request.GET and 'date' in request.GET: # If the form has been submitted...
        from django_wikinetwork.wikinetwork.tasks import AnalyseTask
        
        task = AnalyseTask.delay(lang=request.GET['lang'], date=request.GET['date'])
        
        return HttpResponse("<pre>%s</pre>" % task.task_id)
    
    else:
        from django_wikinetwork.wikinetwork.models import WikiLang
        
        results = WikiLang.objects.values()
        
        langs = [str(l['lang']) for l in results]
        


    return render_to_response('celery-create-run.html', {
        'langs': langs
    })


def task_list(request):
    from celery.registry import TaskRegistry
    reg = TaskRegistry()
    print reg.get_all()
    return render_to_response('index.html')


