from django.contrib import admin



class MyAdminSite(admin.AdminSite):
    site_header = "Monty Python administration"


admin_site = MyAdminSite(name="myadmin")

