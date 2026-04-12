"""
core/context_processors.py
Barcha template larda mavjud bo'lgan global context
"""
from .models import SiteSettings, NavbarExtraLink, FooterSettings


def site_context(request):
    """
    Har bir so'rovda ishga tushadi.
    site, drawer_extra_links, footer — barcha template larda mavjud.
    """
    site   = SiteSettings.get()
    footer = FooterSettings.objects.prefetch_related('columns__links').filter(pk=1).first()
    drawer_extra_links = NavbarExtraLink.objects.filter(is_active=True).order_by('order')

    return {
        'site':               site,
        'footer':             footer,
        'drawer_extra_links': drawer_extra_links,
    }
