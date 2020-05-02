from django.contrib import admin

from challenge.models import Challenge, Category, Solve, Score

admin.site.register(Challenge)
admin.site.register(Category)
admin.site.register(Solve)
admin.site.register(Score)
