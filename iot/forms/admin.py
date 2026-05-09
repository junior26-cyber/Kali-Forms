from django.contrib import admin
from .models import Sondage, Question, Option, Response, Answer

class OptionInline(admin.TabularInline):
    model = Option
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ('text', 'survey', 'type', 'is_required')
    list_filter = ('survey', 'type')

class SondageAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'created_at', 'is_active')
    list_filter = ('creator', 'is_active')

admin.site.register(Sondage, SondageAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option)
admin.site.register(Response)
admin.site.register(Answer)
