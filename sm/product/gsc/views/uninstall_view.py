from django.shortcuts import render


def uninstalled(request):
    return render(request, "sm/product/gsc/uninstall.html")
