from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

admin.site.site_header = "Nagarawa Admin"
admin.site.site_title = "Nagarawa"
admin.site.index_title = "Complaint Management Dashboard"

# URLs that should NOT be language-prefixed
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # enables the language switch view
]

# URLs that SHOULD be language-prefixed (e.g. /en/..., /ne/...)
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('complaints/', include('complaints.urls')),
    path('comments/', include('comments.urls')),
    path('messages/', include('messaging.urls')),
    prefix_default_language=False,  # keeps English URLs clean, without a /en/ prefix
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)