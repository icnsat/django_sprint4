from django.shortcuts import render

from django.views.generic import TemplateView


class AboutTemplateView(TemplateView):
    template_name = 'pages/about.html'


class RulesTemplateView(TemplateView):
    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    """Custom 404 page"""
    template = 'pages/404.html'
    return render(request, template, status=404)


def csrf_failure(request, reason=''):
    """Custom 403 csrf failure page"""
    return render(request, 'pages/403csrf.html', status=403)


def internal_500(request, reason=''):
    """Custom 500 failure page"""
    return render(request, 'pages/500.html', status=500)
