from django.shortcuts import render


def page(request, template_name: str):
    return render(request, template_name)

